from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import structlog
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.domain.exceptions import NanocadError
from src.presentation.context import get_factory, get_repository
from src.presentation.tool_defs import TOOL_DEFS
from src.presentation.tool_validation import ToolValidationError, validate_tool_input

if TYPE_CHECKING:
    from collections.abc import Callable

# -- Logging Setup -------------------------------------------------------------


def setup_logging(*, debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO
    log_path = Path(__file__).resolve().parent.parent.parent / "logs" / "ncad-mcp-python.log"
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_path), encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger()


# -- Global State (contextvars) -------------------------------------------------

_routing_cache: object = None


def _ensure_connected() -> None:
    """Ensure the CAD repository is connected for this request context.

    Uses ``contextvars`` for request-scoped state — safe for concurrent SSE.
    ``get_repository()`` lazily creates the repository on first call.
    """
    repo = get_repository()
    if not repo.is_available():
        if not repo.connect():
            log.warning(
                "nanoCAD connection failed, mode=%s",
                getattr(repo, "connection_mode", "unknown"),
            )

    # Invalidate routing cache on reconnection
    global _routing_cache
    _routing_cache = None


# -- Tool Definitions ----------------------------------------------------------

# Mode priority for capability filtering (higher = more capable)
_MODE_ORDER: Final[dict[str, int]] = {
    "offline": 0,
    "com": 1,
    "full": 2,
}


def _get_tools(mode: str = "full") -> list[Tool]:
    """Return MCP tool definitions filtered by connection mode.

    Each tool definition has a ``requires_mode`` field:
      ``None`` / missing — always available (no CAD needed)
      ``"com"`` — requires at least COM bridge
      ``"full"`` — requires .NET engine (HTTP bridge)
    """
    required = _MODE_ORDER.get(mode, 0)
    return [
        Tool(
            name=td["name"],
            description=td["description"],
            inputSchema={
                "type": "object",
                "properties": td["properties"],
                "required": td["required"],
            },
        )
        for td in TOOL_DEFS
        if _MODE_ORDER.get(td.get("requires_mode", "full"), 0) <= required
    ]


# -- Routing -------------------------------------------------------------------


# Maps tool names to factory-property + method.
# Format: tool_name -> (factory_attr, method_name)
_TOOL_HANDLER_MAP: dict[str, tuple[str, str]] = {
    # Health & System
    "health_check": ("system", "is_available"),
    "get_system_fonts": ("system", "get_fonts"),
    "get_system_info": ("system", "get_info"),
    "execute_command": ("system", "execute_command"),
    "get_system_variable": ("system", "get_variable"),
    "set_system_variable": ("system", "set_variable"),
    # 2D Primitives
    "create_line": ("entity", "create_line"),
    "create_circle": ("entity", "create_circle"),
    "create_arc": ("entity", "create_arc"),
    "create_polyline": ("entity", "create_polyline"),
    "create_rectangle": ("entity", "create_rectangle"),
    "create_text": ("entity", "create_text"),
    "create_mtext": ("entity", "create_mtext"),
    "create_point": ("entity", "create_point"),
    "create_ellipse": ("entity", "create_ellipse"),
    "create_spline": ("entity", "create_spline"),
    "create_helix": ("entity", "create_helix"),
    "create_region": ("entity", "create_region"),
    "create_boundary": ("entity", "create_boundary"),
    "delete_entity": ("entity", "delete_entity"),
    "get_entity": ("entity", "get_entity"),
    # Entity Transformations
    "move_entity": ("entity", "move_entity"),
    "copy_entity": ("entity", "copy_entity"),
    "rotate_entity": ("entity", "rotate_entity"),
    "scale_entity": ("entity", "scale_entity"),
    "mirror_entity": ("entity", "mirror_entity"),
    "stretch_entity": ("transform", "stretch_entity"),
    "explode_entity": ("transform", "explode_entity"),
    "divide_entity": ("transform", "divide_entity"),
    "measure_entity": ("transform", "measure_entity"),
    "array_3d": ("transform", "array_3d"),
    "align_3d": ("transform", "align_3d"),
    "mirror_3d": ("transform", "mirror_3d"),
    # Layers
    "create_layer": ("layer", "create_layer"),
    "get_linetypes": ("layer", "get_linetypes"),
    "get_layers": ("layer", "get_layers"),
    "set_current_layer": ("layer", "set_current_layer"),
    "set_layer_state": ("layer", "set_layer_state"),
    "delete_layer": ("layer", "delete_layer"),
    "layer_isolate": ("layer_mgmt", "layer_isolate"),
    "layer_off": ("layer_mgmt", "layer_off"),
    "layer_freeze": ("layer_mgmt", "layer_freeze"),
    "layer_on_all": ("layer_mgmt", "layer_on_all"),
    "layer_thaw_all": ("layer_mgmt", "layer_thaw_all"),
    # Blocks
    "get_blocks": ("block", "get_blocks"),
    "insert_block": ("block", "insert_block"),
    "delete_block": ("block", "delete_block"),
    "get_block_entities": ("block", "get_block_entities"),
    "create_block": ("block_mgmt", "create_block"),
    "explode_block": ("block_mgmt", "explode_block"),
    # Document
    "get_document_info": ("document", "get_info"),
    "save_document": ("document", "save"),
    "export_pdf": ("document", "export_pdf"),
    "export_dwg": ("document", "export_dwg"),
    "export_dxf": ("document", "export_dxf"),
    "zoom_extents": ("document", "zoom_extents"),
    "new_document": ("document", "new_document"),
    "create_project": ("document", "create_project"),
    "save_project": ("document", "save_project"),
    "open_document": ("document", "open_document"),
    "close_document": ("document", "close_document"),
    # Document Management
    "undo": ("doc_mgmt", "undo"),
    "redo": ("doc_mgmt", "redo"),
    "purge": ("doc_mgmt", "purge"),
    "import_step": ("doc_mgmt", "import_step"),
    "export_step": ("doc_mgmt", "export_step"),
    "export_ifc": ("document", "export_ifc"),
    # 3D Solids
    "create_box": ("solid", "create_box"),
    "create_sphere": ("solid", "create_sphere"),
    "create_cylinder": ("solid", "create_cylinder"),
    "create_cone": ("solid", "create_cone"),
    "create_torus": ("solid", "create_torus"),
    "create_wedge": ("solid", "create_wedge"),
    "create_pyramid": ("solid", "create_pyramid"),
    "boolean_union": ("solid", "boolean_union"),
    "boolean_subtract": ("solid", "boolean_subtract"),
    "boolean_intersect": ("solid", "boolean_intersect"),
    "extrude_solid": ("solid", "extrude_solid"),
    "revolve_solid": ("solid", "revolve_solid"),
    "sweep_solid": ("sweep_loft", "sweep_solid"),
    "loft_solid": ("sweep_loft", "loft_solid"),
    "fillet_edge": ("edge_op", "fillet_edge"),
    "chamfer_edge": ("edge_op", "chamfer_edge"),
    "set_3d_view": ("solid", "set_3d_view"),
    "get_solid_properties": ("solid", "get_solid_properties"),
    "move_solid": ("solid", "move_solid"),
    # Symbols
    "create_roughness": ("symbol", "create_roughness"),
    "create_old_roughness": ("symbol", "create_old_roughness"),
    "create_tolerance": ("symbol", "create_tolerance"),
    "create_datum": ("symbol", "create_datum"),
    "create_weld": ("symbol", "create_weld"),
    "create_leader": ("symbol", "create_leader"),
    "create_note_comb": ("symbol", "create_note_comb"),
    "create_dim_number": ("symbol", "create_dim_number"),
    "create_mleader": ("mleader", "create_mleader"),
    # Tables
    "create_table": ("table", "create_table"),
    "edit_table_cell": ("table", "edit_table_cell"),
    "get_table_info": ("table", "get_table_info"),
    "delete_table": ("table", "delete_table"),
    # Hatch
    "create_hatch": ("hatch", "create_hatch"),
    "create_gradient": ("hatch", "create_gradient"),
    "get_hatch_info": ("hatch", "get_hatch_info"),
    "edit_hatch": ("hatch", "edit_hatch"),
    # Dimensions
    "create_aligned_dimension": ("dimension", "create_aligned_dimension"),
    "create_rotated_dimension": ("dimension", "create_rotated_dimension"),
    "create_radial_dimension": ("dimension", "create_radial_dimension"),
    "create_diametric_dimension": ("dimension", "create_diametric_dimension"),
    "create_angular_dimension": ("dimension", "create_angular_dimension"),
    "create_ordinate_dimension": ("dimension", "create_ordinate_dimension"),
    "create_arc_length_dimension": ("dimension", "create_arc_length_dimension"),
    "create_linear_dimension": ("linear_dim", "create_linear_dimension"),
    # Measurements
    "get_distance": ("measurement", "get_distance"),
    "get_angle": ("measurement", "get_angle"),
    "get_area": ("measurement", "get_area"),
    "get_entity_info": ("measurement", "get_entity_info"),
    "get_all_entities": ("measurement", "get_all_entities"),
    "get_entity_detail": ("selection", "get_entity_detail"),
    # Trim / Extend / Offset
    "trim_entity": ("teo", "trim_entity"),
    "extend_entity": ("teo", "extend_entity"),
    "offset_entity": ("teo", "offset_entity"),
    # Primitives
    "create_polygon": ("primitive", "create_polygon"),
    "create_donut": ("primitive", "create_donut"),
    "create_xline": ("primitive", "create_xline"),
    "create_ray": ("primitive", "create_ray"),
    # Selection
    "select_entities": ("selection", "select_entities"),
    "select_by_handles": ("selection", "select_by_handles"),
    # 2D Constraints
    "constraint_parallel": ("constraint", "constraint_parallel"),
    "constraint_coincident": ("constraint", "constraint_coincident"),
    "constraint_fix": ("constraint", "constraint_fix"),
    "constraint_horizontal": ("constraint", "constraint_horizontal"),
    "constraint_vertical": ("constraint", "constraint_vertical"),
    "constraint_tangent": ("constraint", "constraint_tangent"),
    "constraint_perpendicular": ("constraint", "constraint_perpendicular"),
    "constraint_collinear": ("constraint", "constraint_collinear"),
    "constraint_concentric": ("constraint", "constraint_concentric"),
    "constraint_equal": ("constraint", "constraint_equal"),
    "constraint_symmetric": ("constraint", "constraint_symmetric"),
    "constraint_distance": ("constraint", "constraint_distance"),
    # Assembly
    "insert_part": ("assembly", "insert_part"),
    "assembly_mate": ("assembly", "assembly_mate"),
    "assembly_angle": ("assembly", "assembly_angle"),
    "assembly_tangent": ("assembly", "assembly_tangent"),
    "assembly_symmetry": ("assembly", "assembly_symmetry"),
    # STL Export
    "export_stl": ("stl", "export_stl"),
    # Sheet Metal
    "create_base_flange": ("sheet_metal", "create_base_flange"),
    "create_edge_flange": ("sheet_metal", "create_edge_flange"),
    "create_bend": ("sheet_metal", "create_bend"),
    "unfold_sheet_metal": ("sheet_metal", "unfold_sheet_metal"),
    "create_base_plate": ("sheet_metal", "create_base_plate"),
    # 3D Features
    "create_simple_hole": ("feature", "create_simple_hole"),
    "create_threaded_hole": ("feature", "create_threaded_hole"),
    "create_standard_hole": ("feature", "create_standard_hole"),
    "create_shell": ("feature", "create_shell"),
    "create_mirror_feature": ("feature", "create_mirror_feature"),
    "create_circular_pattern": ("feature", "create_circular_pattern"),
    "create_rectangular_pattern": ("feature", "create_rectangular_pattern"),
    "create_sketch": ("feature", "create_sketch"),
    "add_sketch_circle": ("feature", "add_sketch_circle"),
    "add_sketch_line": ("feature", "add_sketch_line"),
    "create_profile": ("feature", "create_profile"),
    "create_extrude_feature": ("feature", "create_extrude_feature"),
    "create_revolve_feature": ("feature", "create_revolve_feature"),
    # Mesh / Viewport / Render
    "create_mesh": ("entity", "create_mesh"),
    "edit_mesh": ("entity", "edit_mesh"),
    "set_viewport": ("entity", "set_viewport"),
    "render": ("entity", "render"),
    # NURBS / IFC
    "create_nurb_curve": ("nurb_ifc", "create_nurb_curve"),
    "create_nurb_surface": ("nurb_ifc", "create_nurb_surface"),
    "modify_nurb": ("nurb_ifc", "modify_nurb"),
    "import_ifc": ("nurb_ifc", "import_ifc"),
    "get_ifc_entities": ("nurb_ifc", "get_ifc_entities"),
    # MultiCAD API
    "create_grid_axis": ("multicad", "create_grid_axis"),
    "create_grid_label": ("multicad", "create_grid_label"),
    "create_room": ("multicad", "create_room"),
    "get_room_properties": ("multicad", "get_room_properties"),
    "create_custom_object": ("multicad", "create_custom_object"),
    "create_parametric_object": ("multicad", "create_parametric_object"),
    "create_reactor": ("multicad", "create_reactor"),
    "create_2d_break": ("multicad", "create_2d_break"),
    "start_motion_preview": ("multicad", "start_motion_preview"),
    "stop_motion_preview": ("multicad", "stop_motion_preview"),
    "create_body_contour": ("multicad", "create_body_contour"),
    "check_3d_faces": ("multicad", "check_3d_faces"),
}


def _build_routing() -> dict[str, Callable[..., Any]]:
    """Build tool_name -> handler routing from the handler map via UseCaseFactory."""
    global _routing_cache
    if _routing_cache is not None:
        return _routing_cache  # type: ignore[return-value]

    factory = get_factory()
    routing: dict[str, Callable[..., Any]] = {}
    for tool_name, (attr_name, method_name) in _TOOL_HANDLER_MAP.items():
        uc = getattr(factory, attr_name, None)
        if uc is None:
            continue
        handler = getattr(uc, method_name, None)
        if handler is not None:
            routing[tool_name] = handler

    _routing_cache = routing
    return routing


def _has_kwargs(handler: Callable[..., Any]) -> bool:
    import inspect

    try:
        sig = inspect.signature(handler)
        return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    except (ValueError, TypeError):
        return False


def _format_result(result: Any) -> str:
    """Format a tool result for user display.

    Handles common return types (dict, list, str, None) and formats them
    as readable text with English labels.
    """
    if result is None:
        return "nil (no result)"
    if isinstance(result, dict):
        # If error field present, show it
        if result.get("success") is False:
            err = result.get("error") or "unknown error"
            return f"ERROR: {err}"
        if result.get("success") is True:
            # Strip success=True for cleaner output
            d = {k: v for k, v in result.items() if k != "success"}
            if not d:
                return "OK"
            parts = [f"{_label(k)}: {v}" for k, v in d.items()]
            return "\n".join(parts)
        # General dict
        parts = [f"{_label(k)}: {v}" for k, v in result.items()]
        return "\n".join(parts)
    if isinstance(result, list):
        if not result:
            return "(empty)"
        lines = [f"  {i + 1}. {v}" for i, v in enumerate(result)]
        return "\n".join(lines)
    return str(result)


def _label(key: str) -> str:
    """Map JSON keys to human-readable English labels for user-facing output."""
    labels: dict[str, str] = {
        "handle": "Handle",
        "name": "Name",
        "version": "Version",
        "path": "Path",
        "is_saved": "Saved",
        "entities_count": "Entities",
        "layers_count": "Layers",
        "blocks_count": "Blocks",
        "active_documents": "Active documents",
        "success": "Success",
        "error": "Error",
        "error_message": "Error",
        "output": "Result",
        "command": "Command",
        "is_on": "On",
        "is_frozen": "Frozen",
        "is_locked": "Locked",
        "color": "Color",
        "value": "Value",
        "type": "Type",
    }
    return labels.get(key, key.capitalize())


# -- Server --------------------------------------------------------------------


def create_server() -> Server:
    server = Server("ncad-mcp-server")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        try:
            repo = get_repository()
            mode = repo.connection_mode
        except Exception:
            mode = "offline"
        return _get_tools(mode)

    @server.list_prompts()
    async def handle_list_prompts() -> list[Any]:
        return []

    @server.list_resources()
    async def handle_list_resources() -> list[Any]:
        return []

    @server.call_tool()
    async def handle_call_tool(
        name: str,
        arguments: dict[str, Any] | None,
    ) -> list[TextContent]:
        args = arguments or {}
        log.info("Tool call", tool=name, args=args)

        try:
            _ensure_connected()
        except Exception:
            log.exception("Failed to connect to CAD")
            return [
                TextContent(
                    type="text",
                    text=(
                        "ERROR: Failed to connect to nanoCAD.\n"
                        "Please check:\n"
                        "  1. Is nanoCAD running?\n"
                        "  2. Is the .NET plugin (CadEngine.Plugin) loaded?\n"
                        "  3. Is port 5080 available?\n"
                        "Run health_check for diagnostics."
                    ),
                )
            ]

        # Capability discovery at list_tools() level handles tool filtering.
        # If a tool is called but CAD is unavailable, the use case or repository
        # will raise NanocadError (caught below).
        routing = _build_routing()
        handler = routing.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"UNKNOWN TOOL: {name}")]


        try:
            validate_tool_input(name, args)
        except ToolValidationError as e:
            return [TextContent(type="text", text=f"VALIDATION ERROR: {e}")]

        try:
            result = handler(**args)
            log.info("Tool result", tool=name, result=result)
            return [TextContent(type="text", text=_format_result(result))]
        except NanocadError as e:
            msg = f"nanoCAD ERROR: {e}"
            log.warning("Tool error (nanoCAD)", tool=name, error=msg)
            return [TextContent(type="text", text=msg)]
        except NotImplementedError as e:
            msg = f"NOT IMPLEMENTED: {e}. Requires .NET engine in nanoCAD."
            log.warning("Tool not implemented", tool=name, error=msg)
            return [TextContent(type="text", text=msg)]
        except Exception as e:
            log.exception("Tool error", tool=name)
            return [TextContent(type="text", text=f"ERROR: {e}")]
    return server


# -- Entry Point ---------------------------------------------------------------


def create_sse_app(
    mcp_server: Server,
    *,
    mount_path: str = "",
    message_path: str = "/messages/",
) -> Any:
    """Create a Starlette ASGI app for SSE transport."""
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route

    full_message_path = mount_path.rstrip("/") + message_path
    sse = SseServerTransport(full_message_path)

    async def handle_sse(scope: Any, receive: Any, send: Any) -> None:
        try:
            async with sse.connect_sse(scope, receive, send) as streams:
                await mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp_server.create_initialization_options(),
                )
        except Exception as e:
            log.exception("SSE handler error", error=str(e))
            # Send error response if headers not sent yet
            try:
                from starlette.responses import Response

                resp = Response("Internal Server Error", status_code=500, media_type="text/plain")
                await resp(scope, receive, send)
            except Exception:
                log.exception("Failed to send SSE error response")

    async def handle_messages(scope: Any, receive: Any, send: Any) -> None:
        await sse.handle_post_message(scope, receive, send)

    routes: list[Route | Mount] = []
    if mount_path:
        routes.append(
            Mount(
                mount_path,
                routes=[
                    Route("/", handle_sse, methods=["GET"]),
                    Route(message_path, handle_messages, methods=["POST"]),
                ],
            )
        )
    else:
        routes.append(Route("/", handle_sse, methods=["GET"]))
        routes.append(Route(message_path, handle_messages, methods=["POST"]))

    return Starlette(routes=routes)


async def _sse_error_handler(_request: Any, exc: Exception) -> Any:
    """Log SSE errors."""
    from starlette.responses import Response

    log.error("SSE error", error=str(exc))
    return Response("Internal Server Error", status_code=500)


async def run_sse(port: int = 8081, host: str = "0.0.0.0") -> None:
    """Run MCP server with SSE transport."""
    import uvicorn

    debug = "NANOCAD_MCP_DEBUG" in os.environ
    setup_logging(debug=debug)
    log.info("Starting nanoCAD MCP SSE Server", host=host, port=port)
    server = create_server()
    app = create_sse_app(server)
    config = uvicorn.Config(app, host=host, port=port, log_level="debug" if debug else "info")
    srv = uvicorn.Server(config)
    await srv.serve()


async def run_stdio() -> None:
    """Run MCP server with stdio transport."""
    debug = "NANOCAD_MCP_DEBUG" in os.environ
    setup_logging(debug=debug)
    log.info("Starting nanoCAD MCP Stdio Server", debug=debug)
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(description="nanoCAD MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--port", type=int, default=8081, help="SSE port (default: 8081)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="SSE host (default: 0.0.0.0)")
    args = parser.parse_args()

    if args.transport == "sse":
        asyncio.run(run_sse(port=args.port, host=args.host))
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
