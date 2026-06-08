from __future__ import annotations

# ruff: noqa: RUF001 — Cyrillic in Russian error messages is intentional
import argparse
import asyncio
import logging
import os
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.application.extended_use_cases import (
    AssemblyUseCase,
    BlockManagementUseCase,
    ConstraintUseCase,
    DimensionUseCase,
    DocumentManagementUseCase,
    EdgeOpUseCase,
    FeatureUseCase,
    HatchUseCase,
    LayerManagementUseCase,
    LinearDimUseCase,
    MeasurementUseCase,
    MLeaderUseCase,
    MultiCadUseCase,
    NurbIfcUseCase,
    PrimitiveUseCase,
    SelectionUseCase,
    SheetMetalUseCase,
    StlExportUseCase,
    SweepLoftUseCase,
    SymbolUseCase,
    TableUseCase,
    TransformationUseCase,
    TrimExtendOffsetUseCase,
)
from src.application.use_cases import (
    BlockUseCase,
    DocumentUseCase,
    EntityUseCase,
    LayerUseCase,
    SolidUseCase,
    SystemUseCase,
)
from src.infrastructure.cad_repository import CadRepository
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


# -- Global State --------------------------------------------------------------

_lock = threading.Lock()
_routing_cache: object = None
_repository: CadRepository | None = None
_entity_uc: EntityUseCase | None = None
_layer_uc: LayerUseCase | None = None
_block_uc: BlockUseCase | None = None
_document_uc: DocumentUseCase | None = None
_system_uc: SystemUseCase | None = None
_solid_uc: SolidUseCase | None = None
_symbol_uc: SymbolUseCase | None = None
_table_uc: TableUseCase | None = None
_hatch_uc: HatchUseCase | None = None
_dimension_uc: DimensionUseCase | None = None
_measurement_uc: MeasurementUseCase | None = None
_transform_uc: TransformationUseCase | None = None
_primitive_uc: PrimitiveUseCase | None = None
_doc_mgmt_uc: DocumentManagementUseCase | None = None
_block_mgmt_uc: BlockManagementUseCase | None = None
_teo_uc: TrimExtendOffsetUseCase | None = None
_layer_mgmt_uc: LayerManagementUseCase | None = None
_linear_dim_uc: LinearDimUseCase | None = None
_sweep_loft_uc: SweepLoftUseCase | None = None
_edge_op_uc: EdgeOpUseCase | None = None
_assembly_uc: AssemblyUseCase | None = None
_selection_uc: SelectionUseCase | None = None
_stl_uc: StlExportUseCase | None = None
_constraint_uc: ConstraintUseCase | None = None
_mleader_uc: MLeaderUseCase | None = None
_sheet_metal_uc: SheetMetalUseCase | None = None
_feature_uc: FeatureUseCase | None = None
_nurb_ifc_uc: NurbIfcUseCase | None = None
_multicad_uc: MultiCadUseCase | None = None


def _ensure_connected() -> None:
    global _repository, _entity_uc, _layer_uc, _block_uc, _document_uc, _system_uc, _routing_cache
    global _solid_uc, _symbol_uc, _table_uc, _hatch_uc, _dimension_uc, _measurement_uc
    global _transform_uc, _primitive_uc, _doc_mgmt_uc, _block_mgmt_uc, _teo_uc, _layer_mgmt_uc
    global _linear_dim_uc, _sweep_loft_uc, _edge_op_uc, _assembly_uc, _selection_uc, _stl_uc
    global _constraint_uc, _mleader_uc, _sheet_metal_uc, _feature_uc, _nurb_ifc_uc, _multicad_uc
    with _lock:
        if _repository is not None and _repository.is_available():
            return
        if _repository is None:
            _repository = CadRepository()
        if not _repository.connect():
            log.warning("CAD not available", mode=_repository.connection_mode)
        _entity_uc = EntityUseCase(_repository)
        _layer_uc = LayerUseCase(_repository)
        _block_uc = BlockUseCase(_repository)
        _document_uc = DocumentUseCase(_repository)
        _system_uc = SystemUseCase(_repository)
        _solid_uc = SolidUseCase(_repository)
        _symbol_uc = SymbolUseCase(_repository._http)
        _table_uc = TableUseCase(_repository._http)
        _hatch_uc = HatchUseCase(_repository._http)
        _dimension_uc = DimensionUseCase(_repository._http)
        _measurement_uc = MeasurementUseCase(_repository._http)
        _transform_uc = TransformationUseCase(_repository._http)
        _primitive_uc = PrimitiveUseCase(_repository._http)
        _doc_mgmt_uc = DocumentManagementUseCase(_repository._http)
        _block_mgmt_uc = BlockManagementUseCase(_repository._http)
        _teo_uc = TrimExtendOffsetUseCase(_repository._http)
        _layer_mgmt_uc = LayerManagementUseCase(_repository._http)
        _linear_dim_uc = LinearDimUseCase(_repository._http)
        _sweep_loft_uc = SweepLoftUseCase(_repository._http)
        _edge_op_uc = EdgeOpUseCase(_repository._http)
        _assembly_uc = AssemblyUseCase(_repository._http)
        _selection_uc = SelectionUseCase(_repository._http)
        _stl_uc = StlExportUseCase(_repository._http)
        _constraint_uc = ConstraintUseCase(_repository._http)
        _mleader_uc = MLeaderUseCase(_repository._http)
        _sheet_metal_uc = SheetMetalUseCase(_repository._http)
        _feature_uc = FeatureUseCase(_repository._http)
        _nurb_ifc_uc = NurbIfcUseCase(_repository._http)
        _multicad_uc = MultiCadUseCase(_repository._http)
        _routing_cache = None


# -- Tool Definitions ----------------------------------------------------------


def _get_tools() -> list[Tool]:
    """Return all 133 MCP tool definitions."""
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
    ]


# -- Routing -------------------------------------------------------------------


# Maps tool names to the use-case method attribute name on the global variable.
# Format: tool_name -> (global_var_name, method_name)
_TOOL_HANDLER_MAP: dict[str, tuple[str, str]] = {
    # Health & System
    "health_check": ("_system_uc", "is_available"),
    "get_system_fonts": ("_system_uc", "get_fonts"),
    "get_system_info": ("_system_uc", "get_info"),
    "execute_command": ("_system_uc", "execute_command"),
    "get_system_variable": ("_system_uc", "get_variable"),
    "set_system_variable": ("_system_uc", "set_variable"),
    # 2D Primitives
    "create_line": ("_entity_uc", "create_line"),
    "create_circle": ("_entity_uc", "create_circle"),
    "create_arc": ("_entity_uc", "create_arc"),
    "create_polyline": ("_entity_uc", "create_polyline"),
    "create_rectangle": ("_entity_uc", "create_rectangle"),
    "create_text": ("_entity_uc", "create_text"),
    "create_mtext": ("_entity_uc", "create_mtext"),
    "create_point": ("_entity_uc", "create_point"),
    "create_ellipse": ("_entity_uc", "create_ellipse"),
    "create_spline": ("_entity_uc", "create_spline"),
    "create_helix": ("_entity_uc", "create_helix"),
    "create_region": ("_entity_uc", "create_region"),
    "create_boundary": ("_entity_uc", "create_boundary"),
    "delete_entity": ("_entity_uc", "delete_entity"),
    "get_entity": ("_entity_uc", "get_entity"),
    # Entity Transformations
    "move_entity": ("_entity_uc", "move_entity"),
    "copy_entity": ("_entity_uc", "copy_entity"),
    "rotate_entity": ("_entity_uc", "rotate_entity"),
    "scale_entity": ("_entity_uc", "scale_entity"),
    "mirror_entity": ("_entity_uc", "mirror_entity"),
    "stretch_entity": ("_transform_uc", "stretch_entity"),
    "explode_entity": ("_transform_uc", "explode_entity"),
    "divide_entity": ("_transform_uc", "divide_entity"),
    "measure_entity": ("_transform_uc", "measure_entity"),
    "array_3d": ("_transform_uc", "array_3d"),
    "align_3d": ("_transform_uc", "align_3d"),
    "mirror_3d": ("_transform_uc", "mirror_3d"),
    # Layers
    "create_layer": ("_layer_uc", "create_layer"),
    "get_linetypes": ("_layer_uc", "get_linetypes"),
    "get_layers": ("_layer_uc", "get_layers"),
    "set_current_layer": ("_layer_uc", "set_current_layer"),
    "set_layer_state": ("_layer_uc", "set_layer_state"),
    "delete_layer": ("_layer_uc", "delete_layer"),
    "layer_isolate": ("_layer_mgmt_uc", "layer_isolate"),
    "layer_off": ("_layer_mgmt_uc", "layer_off"),
    "layer_freeze": ("_layer_mgmt_uc", "layer_freeze"),
    "layer_on_all": ("_layer_mgmt_uc", "layer_on_all"),
    "layer_thaw_all": ("_layer_mgmt_uc", "layer_thaw_all"),
    # Blocks
    "get_blocks": ("_block_uc", "get_blocks"),
    "insert_block": ("_block_uc", "insert_block"),
    "delete_block": ("_block_uc", "delete_block"),
    "get_block_entities": ("_block_uc", "get_block_entities"),
    "create_block": ("_block_mgmt_uc", "create_block"),
    "explode_block": ("_block_mgmt_uc", "explode_block"),
    # Document
    "get_document_info": ("_document_uc", "get_info"),
    "save_document": ("_document_uc", "save"),
    "export_pdf": ("_document_uc", "export_pdf"),
    "export_dwg": ("_document_uc", "export_dwg"),
    "export_dxf": ("_document_uc", "export_dxf"),
    "zoom_extents": ("_document_uc", "zoom_extents"),
    "new_document": ("_document_uc", "new_document"),
    "create_project": ("_document_uc", "create_project"),
    "save_project": ("_document_uc", "save_project"),
    "open_document": ("_document_uc", "open_document"),
    "close_document": ("_document_uc", "close_document"),
    # Document Management
    "undo": ("_doc_mgmt_uc", "undo"),
    "redo": ("_doc_mgmt_uc", "redo"),
    "purge": ("_doc_mgmt_uc", "purge"),
    "import_step": ("_doc_mgmt_uc", "import_step"),
    "export_step": ("_doc_mgmt_uc", "export_step"),
    "export_ifc": ("_document_uc", "export_ifc"),
    # 3D Solids
    "create_box": ("_solid_uc", "create_box"),
    "create_sphere": ("_solid_uc", "create_sphere"),
    "create_cylinder": ("_solid_uc", "create_cylinder"),
    "create_cone": ("_solid_uc", "create_cone"),
    "create_torus": ("_solid_uc", "create_torus"),
    "create_wedge": ("_solid_uc", "create_wedge"),
    "create_pyramid": ("_solid_uc", "create_pyramid"),
    "boolean_union": ("_solid_uc", "boolean_union"),
    "boolean_subtract": ("_solid_uc", "boolean_subtract"),
    "boolean_intersect": ("_solid_uc", "boolean_intersect"),
    "extrude_solid": ("_solid_uc", "extrude_solid"),
    "revolve_solid": ("_solid_uc", "revolve_solid"),
    "sweep_solid": ("_sweep_loft_uc", "sweep_solid"),
    "loft_solid": ("_sweep_loft_uc", "loft_solid"),
    "fillet_edge": ("_edge_op_uc", "fillet_edge"),
    "chamfer_edge": ("_edge_op_uc", "chamfer_edge"),
    "set_3d_view": ("_solid_uc", "set_3d_view"),
    "get_solid_properties": ("_solid_uc", "get_solid_properties"),
    "move_solid": ("_solid_uc", "move_solid"),
    # Symbols
    "create_roughness": ("_symbol_uc", "create_roughness"),
    "create_old_roughness": ("_symbol_uc", "create_old_roughness"),
    "create_tolerance": ("_symbol_uc", "create_tolerance"),
    "create_datum": ("_symbol_uc", "create_datum"),
    "create_weld": ("_symbol_uc", "create_weld"),
    "create_leader": ("_symbol_uc", "create_leader"),
    "create_note_comb": ("_symbol_uc", "create_note_comb"),
    "create_dim_number": ("_symbol_uc", "create_dim_number"),
    "create_mleader": ("_mleader_uc", "create_mleader"),
    # Tables
    "create_table": ("_table_uc", "create_table"),
    "edit_table_cell": ("_table_uc", "edit_table_cell"),
    "get_table_info": ("_table_uc", "get_table_info"),
    "delete_table": ("_table_uc", "delete_table"),
    # Hatch
    "create_hatch": ("_hatch_uc", "create_hatch"),
    "create_gradient": ("_hatch_uc", "create_gradient"),
    "get_hatch_info": ("_hatch_uc", "get_hatch_info"),
    "edit_hatch": ("_hatch_uc", "edit_hatch"),
    # Dimensions
    "create_aligned_dimension": ("_dimension_uc", "create_aligned_dimension"),
    "create_rotated_dimension": ("_dimension_uc", "create_rotated_dimension"),
    "create_radial_dimension": ("_dimension_uc", "create_radial_dimension"),
    "create_diametric_dimension": ("_dimension_uc", "create_diametric_dimension"),
    "create_angular_dimension": ("_dimension_uc", "create_angular_dimension"),
    "create_ordinate_dimension": ("_dimension_uc", "create_ordinate_dimension"),
    "create_arc_length_dimension": ("_dimension_uc", "create_arc_length_dimension"),
    "create_linear_dimension": ("_linear_dim_uc", "create_linear_dimension"),
    # Measurements
    "get_distance": ("_measurement_uc", "get_distance"),
    "get_angle": ("_measurement_uc", "get_angle"),
    "get_area": ("_measurement_uc", "get_area"),
    "get_entity_info": ("_measurement_uc", "get_entity_info"),
    "get_all_entities": ("_measurement_uc", "get_all_entities"),
    "get_entity_detail": ("_selection_uc", "get_entity_detail"),
    # Trim / Extend / Offset
    "trim_entity": ("_teo_uc", "trim_entity"),
    "extend_entity": ("_teo_uc", "extend_entity"),
    "offset_entity": ("_teo_uc", "offset_entity"),
    # Primitives
    "create_polygon": ("_primitive_uc", "create_polygon"),
    "create_donut": ("_primitive_uc", "create_donut"),
    "create_xline": ("_primitive_uc", "create_xline"),
    "create_ray": ("_primitive_uc", "create_ray"),
    # Selection
    "select_entities": ("_selection_uc", "select_entities"),
    "select_by_handles": ("_selection_uc", "select_by_handles"),
    # 2D Constraints
    "constraint_parallel": ("_constraint_uc", "constraint_parallel"),
    "constraint_coincident": ("_constraint_uc", "constraint_coincident"),
    "constraint_fix": ("_constraint_uc", "constraint_fix"),
    "constraint_horizontal": ("_constraint_uc", "constraint_horizontal"),
    "constraint_vertical": ("_constraint_uc", "constraint_vertical"),
    "constraint_tangent": ("_constraint_uc", "constraint_tangent"),
    "constraint_perpendicular": ("_constraint_uc", "constraint_perpendicular"),
    "constraint_collinear": ("_constraint_uc", "constraint_collinear"),
    "constraint_concentric": ("_constraint_uc", "constraint_concentric"),
    "constraint_equal": ("_constraint_uc", "constraint_equal"),
    "constraint_symmetric": ("_constraint_uc", "constraint_symmetric"),
    "constraint_distance": ("_constraint_uc", "constraint_distance"),
    # Assembly
    "insert_part": ("_assembly_uc", "insert_part"),
    "assembly_mate": ("_assembly_uc", "assembly_mate"),
    "assembly_angle": ("_assembly_uc", "assembly_angle"),
    "assembly_tangent": ("_assembly_uc", "assembly_tangent"),
    "assembly_symmetry": ("_assembly_uc", "assembly_symmetry"),
    # STL Export
    "export_stl": ("_stl_uc", "export_stl"),
    # Sheet Metal
    "create_base_flange": ("_sheet_metal_uc", "create_base_flange"),
    "create_edge_flange": ("_sheet_metal_uc", "create_edge_flange"),
    "create_bend": ("_sheet_metal_uc", "create_bend"),
    "unfold_sheet_metal": ("_sheet_metal_uc", "unfold_sheet_metal"),
    "create_base_plate": ("_sheet_metal_uc", "create_base_plate"),
    # 3D Features
    "create_simple_hole": ("_feature_uc", "create_simple_hole"),
    "create_threaded_hole": ("_feature_uc", "create_threaded_hole"),
    "create_standard_hole": ("_feature_uc", "create_standard_hole"),
    "create_shell": ("_feature_uc", "create_shell"),
    "create_mirror_feature": ("_feature_uc", "create_mirror_feature"),
    "create_circular_pattern": ("_feature_uc", "create_circular_pattern"),
    "create_rectangular_pattern": ("_feature_uc", "create_rectangular_pattern"),
    "create_sketch": ("_feature_uc", "create_sketch"),
    "add_sketch_circle": ("_feature_uc", "add_sketch_circle"),
    "add_sketch_line": ("_feature_uc", "add_sketch_line"),
    "create_profile": ("_feature_uc", "create_profile"),
    "create_extrude_feature": ("_feature_uc", "create_extrude_feature"),
    "create_revolve_feature": ("_feature_uc", "create_revolve_feature"),
    # Mesh / Viewport / Render
    "create_mesh": ("_entity_uc", "create_mesh"),
    "edit_mesh": ("_entity_uc", "edit_mesh"),
    "set_viewport": ("_entity_uc", "set_viewport"),
    "render": ("_entity_uc", "render"),
    # NURBS / IFC
    "create_nurb_curve": ("_nurb_ifc_uc", "create_nurb_curve"),
    "create_nurb_surface": ("_nurb_ifc_uc", "create_nurb_surface"),
    "modify_nurb": ("_nurb_ifc_uc", "modify_nurb"),
    "import_ifc": ("_nurb_ifc_uc", "import_ifc"),
    "get_ifc_entities": ("_nurb_ifc_uc", "get_ifc_entities"),
    # MultiCAD API
    "create_grid_axis": ("_multicad_uc", "create_grid_axis"),
    "create_grid_label": ("_multicad_uc", "create_grid_label"),
    "create_room": ("_multicad_uc", "create_room"),
    "get_room_properties": ("_multicad_uc", "get_room_properties"),
    "create_custom_object": ("_multicad_uc", "create_custom_object"),
    "create_parametric_object": ("_multicad_uc", "create_parametric_object"),
    "create_reactor": ("_multicad_uc", "create_reactor"),
    "create_2d_break": ("_multicad_uc", "create_2d_break"),
    "start_motion_preview": ("_multicad_uc", "start_motion_preview"),
    "stop_motion_preview": ("_multicad_uc", "stop_motion_preview"),
    "create_body_contour": ("_multicad_uc", "create_body_contour"),
    "check_3d_faces": ("_multicad_uc", "check_3d_faces"),
}


def _build_routing() -> dict[str, Callable[..., Any]]:
    """Build tool_name -> handler routing from the handler map."""
    global _routing_cache
    if _routing_cache is not None:
        return _routing_cache  # type: ignore[return-value]

    import src.presentation.server as _srv  # noqa: PLW0406

    routing: dict[str, Callable[..., Any]] = {}
    for tool_name, (var_name, method_name) in _TOOL_HANDLER_MAP.items():
        uc = getattr(_srv, var_name, None)
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
    as readable text with Russian labels.
    """
    if result is None:
        return "nil (нет результата)"
    if isinstance(result, dict):
        # If error field present, show it
        if result.get("success") is False:
            err = result.get("error") or "неизвестная ошибка"
            return f"ОШИБКА: {err}"
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
            return "(пусто)"
        lines = [f"  {i + 1}. {v}" for i, v in enumerate(result)]
        return "\n".join(lines)
    return str(result)


def _label(key: str) -> str:
    """Map English JSON keys to Russian labels for user-facing output."""
    labels: dict[str, str] = {
        "handle": "Идентификатор",
        "name": "Имя",
        "version": "Версия",
        "path": "Путь",
        "is_saved": "Сохранён",
        "entities_count": "Объектов",
        "layers_count": "Слоёв",
        "blocks_count": "Блоков",
        "active_documents": "Активных документов",
        "success": "Успех",
        "error": "Ошибка",
        "error_message": "Ошибка",
        "output": "Результат",
        "command": "Команда",
        "is_on": "Включён",
        "is_frozen": "Заморожен",
        "is_locked": "Заблокирован",
        "color": "Цвет",
        "value": "Значение",
        "type": "Тип",
    }
    return labels.get(key, key.capitalize())


# -- Server --------------------------------------------------------------------


def create_server() -> Server:
    server = Server("ncad-mcp-server")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return _get_tools()

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
                        "ОШИБКА: Не удалось подключиться к nanoCAD.\n"
                        "Проверьте:\n"
                        "  1. Запущен ли nanoCAD\n"
                        "  2. Загружен ли .NET плагин (CadEngine.Plugin)\n"
                        "  3. Не занят ли порт 5080\n"
                        "Выполните health_check для диагностики."
                    ),
                )
            ]

        # Allow health/system tools when CAD is offline; fail everything else early
        if name not in ("health_check", "get_system_info", "get_system_variable"):
            if _repository is None or not _repository.is_available():
                return [
                    TextContent(
                        type="text",
                        text=(
                            "ОШИБКА: nanoCAD недоступен.\n"
                            "Запустите nanoCAD с загруженным .NET плагином (CadEngine.Plugin)\n"
                            "и повторите попытку. Текущий режим: "
                            + (_repository.connection_mode if _repository else "none")
                        ),
                    )
                ]

        routing = _build_routing()
        handler = routing.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"ОШИБКА: Неизвестный инструмент: {name}")]

        try:
            validate_tool_input(name, args)
        except ToolValidationError as e:
            return [TextContent(type="text", text=f"ОШИБКА ВАЛИДАЦИИ: {e}")]

        try:
            result = handler(**args)
            log.info("Tool result", tool=name, result=result)
            return [TextContent(type="text", text=_format_result(result))]
        except NotImplementedError as e:
            msg = f"НЕ РЕАЛИЗОВАНО: {e}. Требуется .NET engine в nanoCAD."
            log.warning("Tool not implemented", tool=name, error=msg)
            return [TextContent(type="text", text=msg)]
        except Exception as e:
            log.exception("Tool error", tool=name)
            return [TextContent(type="text", text=f"ОШИБКА: {e}")]

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
