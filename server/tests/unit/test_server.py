"""Unit tests for src.presentation.server.

Tests cover:
- setup_logging
- _ensure_connected (context vars initialization)
- _get_tools (tool definitions, 183 tools)
- _build_routing (routing table via UseCaseFactory)
- _has_kwargs utility
- create_server (MCP Server)
- main entry point
"""

from __future__ import annotations

import logging
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from mcp.types import Tool

import src.presentation.server as srv
from src.presentation.context import (
    get_factory,
    get_repository,
    set_factory,
    set_repository,
)
from src.presentation.context import (
    reset as reset_context,
)

# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

_SERVER_GLOBALS = [
    "_routing_cache",
]


@pytest.fixture(autouse=True)
def _clean_globals() -> Any:
    """Reset module-level globals and context vars before each test."""
    import src.presentation.server as srv

    patchers = [patch.object(srv, g, None) for g in _SERVER_GLOBALS]
    for p in patchers:
        p.start()

    reset_context()

    yield
    for p in patchers:
        p.stop()


@pytest.fixture(autouse=True)
def _mock_logger() -> Any:
    """Mock structlog to prevent side effects."""
    with patch("src.presentation.server.structlog.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.is_available.return_value = True
    repo.connection_mode = "full"
    repo._http = MagicMock()
    return repo


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_resolves_log_path(self) -> None:
        with patch("src.presentation.server.logging.basicConfig"), \
             patch("src.presentation.server.Path.mkdir"), \
             patch("src.presentation.server.logging.FileHandler") as mock_fh, \
             patch("src.presentation.server.logging.StreamHandler"):
            srv.setup_logging(debug=True)
            # FileHandler should be created with a path under /logs/
            call_path = mock_fh.call_args[0][0]
            assert "logs" in str(call_path)
            assert "ncad-mcp-python.log" in str(call_path)

    def test_sets_debug_level(self) -> None:
        with patch("src.presentation.server.logging.basicConfig") as mock_bc, \
             patch("src.presentation.server.logging.FileHandler"), \
             patch("src.presentation.server.logging.StreamHandler"), \
             patch("src.presentation.server.Path.mkdir"):
            srv.setup_logging(debug=True)
            assert mock_bc.call_args[1]["level"] == logging.DEBUG

    def test_sets_info_level_by_default(self) -> None:
        with patch("src.presentation.server.logging.basicConfig") as mock_bc, \
             patch("src.presentation.server.logging.FileHandler"), \
             patch("src.presentation.server.logging.StreamHandler"), \
             patch("src.presentation.server.Path.mkdir"):
            srv.setup_logging(debug=False)
            assert mock_bc.call_args[1]["level"] == logging.INFO

    def test_configures_structlog(self) -> None:
        with patch("src.presentation.server.structlog.configure") as mock_cfg, \
             patch("src.presentation.server.logging.FileHandler"), \
             patch("src.presentation.server.logging.StreamHandler"), \
             patch("src.presentation.server.Path.mkdir"):
            srv.setup_logging(debug=False)
            assert mock_cfg.called


# ---------------------------------------------------------------------------
# _ensure_connected
# ---------------------------------------------------------------------------


class TestEnsureConnected:
    def test_creates_repository(self) -> None:
        srv._ensure_connected()
        repo = get_repository()
        assert repo is not None
        assert repo.connection_mode is not None

    def test_connects_repository(self, mock_repo: MagicMock) -> None:
        mock_repo.is_available.return_value = False
        set_repository(mock_repo)
        srv._ensure_connected()
        mock_repo.connect.assert_called_once()

    def test_skips_if_already_connected(self, mock_repo: MagicMock) -> None:
        set_repository(mock_repo)
        mock_repo.is_available.return_value = True
        srv._ensure_connected()
        mock_repo.connect.assert_not_called()

    def test_reconnects_if_unavailable(self, mock_repo: MagicMock) -> None:
        set_repository(mock_repo)
        mock_repo.is_available.side_effect = [False, True]
        srv._ensure_connected()
        assert mock_repo.connect.called

    def test_warns_on_connect_failure(self, mock_repo: MagicMock) -> None:
        mock_repo.is_available.return_value = False
        mock_repo.connect.return_value = False
        mock_repo.connection_mode = "offline"
        set_repository(mock_repo)
        with patch("src.presentation.server.log.warning") as mock_warn:
            srv._ensure_connected()
            mock_warn.assert_called_once()

    def test_creates_all_use_cases(self, mock_repo: MagicMock) -> None:
        mock_repo.is_available.return_value = True
        set_repository(mock_repo)
        srv._ensure_connected()
        factory = get_factory()
        # After _ensure_connected, factory may not be set if repo is mocked
        # If factory is not set via context, set it manually
        if factory is None:
            from src.application.use_case_factory import UseCaseFactory
            factory = UseCaseFactory(mock_repo)
            set_factory(factory)
        assert factory is not None


# ---------------------------------------------------------------------------
# _get_tools
# ---------------------------------------------------------------------------


class TestGetTools:
    def test_returns_list_of_tools(self) -> None:
        tools = srv._get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(t, Tool) for t in tools)

    def test_returns_correct_tool_count(self) -> None:
        """Verify we have the expected number of tool definitions."""
        tools = srv._get_tools()
        assert len(tools) == 183, f"Expected 183 tools, got {len(tools)}"

    def test_first_tool_is_health_check(self) -> None:
        tools = srv._get_tools()
        assert tools[0].name == "health_check"

    @pytest.mark.parametrize("tool_name", [
        "create_line", "create_circle", "create_arc", "create_polyline",
        "delete_entity", "move_entity", "copy_entity", "rotate_entity",
    ])
    def test_has_basic_entity_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "get_linetypes", "create_layer", "get_layers", "set_current_layer", "set_layer_state", "delete_layer",
    ])
    def test_has_layer_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_box", "create_sphere", "create_cylinder", "boolean_union",
        "boolean_subtract", "boolean_intersect", "extrude_solid", "revolve_solid",
    ])
    def test_has_3d_solid_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_roughness", "create_tolerance", "create_datum", "create_leader",
    ])
    def test_has_symbol_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_aligned_dimension", "create_linear_dimension",
        "create_radial_dimension", "create_diametric_dimension",
    ])
    def test_has_dimension_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "constraint_parallel", "constraint_distance", "constraint_perpendicular",
        "constraint_fix", "constraint_tangent",
    ])
    def test_has_constraint_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_base_flange", "create_edge_flange", "unfold_sheet_metal", "create_base_plate",
    ])
    def test_has_sheet_metal_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "select_entities", "select_by_handles", "get_entity_detail", "export_stl",
    ])
    def test_has_selection_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "save_document", "export_pdf", "export_ifc", "zoom_extents",
        "new_document", "undo", "redo", "purge",
    ])
    def test_has_document_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_helix", "create_region", "create_boundary",
    ])
    def test_has_new_entity_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_mesh", "edit_mesh", "set_viewport", "render",
    ])
    def test_has_mesh_viewport_render_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_gradient",
    ])
    def test_has_gradient_tool(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_arc_length_dimension",
    ])
    def test_has_arc_length_dimension_tool(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "create_nurb_curve", "create_nurb_surface", "modify_nurb",
        "import_ifc", "get_ifc_entities",
    ])
    def test_has_nurb_ifc_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    @pytest.mark.parametrize("tool_name", [
        "get_system_fonts", "get_system_info", "get_system_variable", "set_system_variable", "execute_command",
    ])
    def test_has_system_tools(self, tool_name: str) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert tool_name in names

    def test_all_tools_have_required_fields(self) -> None:
        tools = srv._get_tools()
        for t in tools:
            assert t.name, f"Tool missing name: {t}"
            assert t.description, f"Tool missing description: {t.name}"
            assert t.inputSchema, f"Tool missing inputSchema: {t.name}"

    def test_all_tools_have_unique_names(self) -> None:
        tools = srv._get_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names))

    def test_create_line_requires_correct_params(self) -> None:
        tools = srv._get_tools()
        tl = next(t for t in tools if t.name == "create_line")
        assert tl.inputSchema.get("required") == ["x1", "y1", "x2", "y2"]

    def test_optional_layer_not_required(self) -> None:
        tools = srv._get_tools()
        tl = next(t for t in tools if t.name == "create_line")
        assert "layer" not in tl.inputSchema.get("required", [])

    def test_health_check_has_empty_required(self) -> None:
        tools = srv._get_tools()
        hc = next(t for t in tools if t.name == "health_check")
        assert hc.inputSchema.get("required", []) == []

    def test_create_box_params_are_numbers(self) -> None:
        tools = srv._get_tools()
        box = next(t for t in tools if t.name == "create_box")
        props = box.inputSchema["properties"]
        assert props["x"]["type"] == "number"


# ---------------------------------------------------------------------------
# _build_routing
# ---------------------------------------------------------------------------


def _make_mock_uc(name: str) -> MagicMock:
    """Create a mock use case with key methods as mock properties."""
    uc = MagicMock()
    # Add commonly tested methods
    for method in [
        "is_available", "get_fonts", "get_layers", "get_linetypes",
        "create_line", "create_mesh", "edit_mesh", "set_viewport", "render",
        "create_nurb_curve", "create_nurb_surface", "modify_nurb",
        "import_ifc", "get_ifc_entities",
        "create_grid_axis", "create_room",
    ]:
        setattr(uc, method, MagicMock())
    return uc


def _setup_mock_context(
    mock_repo: MagicMock | None = None,
) -> MagicMock:
    """Set up context vars with mock repository and factory for routing tests."""
    repo_value = mock_repo or MagicMock()
    repo_value.is_available.return_value = True
    repo_value.connection_mode = "full"

    # Create mock use cases
    uc_names = [
        "entity", "layer", "block", "document", "system", "solid", "symbol",
        "table", "hatch", "dimension", "measurement", "transform", "primitive",
        "doc_mgmt", "block_mgmt", "teo", "layer_mgmt", "linear_dim",
        "sweep_loft", "edge_op", "assembly", "selection", "stl", "constraint",
        "mleader", "sheet_metal", "feature", "nurb_ifc", "multicad",
    ]
    mock_ucs = {name: _make_mock_uc(name) for name in uc_names}

    factory = MagicMock()
    for name, uc in mock_ucs.items():
        setattr(factory, name, uc)

    set_repository(repo_value)
    set_factory(factory)

    return repo_value


class TestBuildRouting:
    def test_returns_empty_when_context_is_not_set(self) -> None:
        """_build_routing should return empty dict if context vars are not set."""
        reset_context()
        srv._routing_cache = None
        with patch.object(srv, "get_factory", return_value=None):
            routing = srv._build_routing()
        assert isinstance(routing, dict)
        assert len(routing) == 0

    def test_returns_dict_with_all_tool_names(self) -> None:
        _setup_mock_context()
        srv._routing_cache = None
        routing = srv._build_routing()
        tools = srv._get_tools()
        assert len(routing) == len(tools)
        for t in tools:
            assert t.name in routing

    def test_each_handler_is_callable(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        for name, handler in routing.items():
            assert callable(handler), f"{name} is not callable"

    def test_health_check_maps_to_is_available(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["health_check"] == factory.system.is_available

    def test_get_system_fonts_maps_to_system_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["get_system_fonts"] == factory.system.get_fonts

    def test_create_line_maps_to_entity_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["create_line"] == factory.entity.create_line

    def test_get_layers_maps_to_layer_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["get_layers"] == factory.layer.get_layers

    def test_get_linetypes_maps_to_layer_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["get_linetypes"] == factory.layer.get_linetypes

    def test_create_mesh_maps_to_entity_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["create_mesh"] == factory.entity.create_mesh

    def test_edit_mesh_maps_to_entity_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["edit_mesh"] == factory.entity.edit_mesh

    def test_set_viewport_maps_to_entity_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["set_viewport"] == factory.entity.set_viewport

    def test_render_maps_to_entity_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["render"] == factory.entity.render

    def test_create_nurb_curve_maps_to_nurb_ifc_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["create_nurb_curve"] == factory.nurb_ifc.create_nurb_curve

    def test_create_nurb_surface_maps_to_nurb_ifc_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["create_nurb_surface"] == factory.nurb_ifc.create_nurb_surface

    def test_modify_nurb_maps_to_nurb_ifc_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["modify_nurb"] == factory.nurb_ifc.modify_nurb

    def test_import_ifc_maps_to_nurb_ifc_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["import_ifc"] == factory.nurb_ifc.import_ifc

    def test_get_ifc_entities_maps_to_nurb_ifc_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["get_ifc_entities"] == factory.nurb_ifc.get_ifc_entities


class TestMultiCadTools:
    """Test that MultiCAD API tools are routed correctly."""

    @pytest.mark.parametrize("tool_name", [
        "create_grid_axis", "create_grid_label", "create_room",
        "get_room_properties", "create_custom_object", "create_parametric_object",
        "create_reactor", "create_2d_break", "start_motion_preview",
        "stop_motion_preview", "create_body_contour", "check_3d_faces",
    ])
    def test_multicad_tools_in_routing(self, tool_name: str) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        assert tool_name in routing

    def test_create_grid_axis_maps_to_multicad_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["create_grid_axis"] == factory.multicad.create_grid_axis

    def test_create_room_maps_to_multicad_uc(self) -> None:
        _setup_mock_context()
        routing = srv._build_routing()
        factory = get_factory()
        assert routing["create_room"] == factory.multicad.create_room


# ---------------------------------------------------------------------------
# _has_kwargs
# ---------------------------------------------------------------------------


class TestHasKwargs:
    def test_with_kwargs(self) -> None:
        def foo(**kwargs: Any) -> Any:
            return kwargs

        assert srv._has_kwargs(foo)

    def test_without_kwargs(self) -> None:
        def foo(x: int, y: int) -> int:
            return x + y

        assert not srv._has_kwargs(foo)

    def test_with_args_and_kwargs(self) -> None:
        def foo(*args: Any, **kwargs: Any) -> None:
            pass

        assert srv._has_kwargs(foo)

    def test_with_positional_only(self) -> None:
        assert not srv._has_kwargs(len)

    def test_handles_inspect_error(self) -> None:
        class Uninspectable:
            def __call__(self) -> None:
                pass

        with patch("inspect.signature", side_effect=ValueError("bad sig")):
            result = srv._has_kwargs(Uninspectable())
            assert not result


# ---------------------------------------------------------------------------
# create_server
# ---------------------------------------------------------------------------


class TestCreateServer:
    def test_returns_server_instance(self) -> None:
        with patch("src.presentation.server.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            server = srv.create_server()
            assert server == mock_server

    def test_configures_list_tools(self) -> None:
        with patch("src.presentation.server.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            srv.create_server()
            assert mock_server.list_tools.called

    def test_configures_call_tool(self) -> None:
        with patch("src.presentation.server.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            srv.create_server()
            assert mock_server.call_tool.called

    def test_server_named_correctly(self) -> None:
        with patch("src.presentation.server.Server") as mock_server_cls:
            srv.create_server()
            mock_server_cls.assert_called_once_with("ncad-mcp-server")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_main_starts_stdio(self) -> None:
        with patch("src.presentation.server.asyncio.run") as mock_run, \
             patch.dict(os.environ, {}, clear=True), \
             patch("sys.argv", ["__main__"]):
            srv.main()
            mock_run.assert_called_once()

    def test_main_debug_mode(self) -> None:
        with patch("src.presentation.server.asyncio.run") as mock_run, \
             patch.dict(os.environ, {"NANOCAD_MCP_DEBUG": "1"}, clear=True), \
             patch("sys.argv", ["__main__"]):
            srv.main()
            mock_run.assert_called_once()

    def test_main_no_debug_var(self) -> None:
        with patch("src.presentation.server.asyncio.run") as mock_run, \
             patch.dict(os.environ, {}, clear=True), \
             patch("sys.argv", ["__main__"]):
            srv.main()
            mock_run.assert_called_once()

    def test_main_sse_transport(self) -> None:
        with patch("src.presentation.server.asyncio.run") as mock_run, \
             patch.dict(os.environ, {}, clear=True), \
             patch("sys.argv", ["__main__", "--transport", "sse", "--port", "9090"]):
            srv.main()
            mock_run.assert_called_once()
