"""Unit tests for src.presentation.server.

Tests cover:
- setup_logging
- _ensure_connected (global state initialization)
- _get_tools (tool definitions, 133 tools)
- _build_routing (routing table)
- _has_kwargs utility
- create_server (MCP Server)
- main entry point
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import Tool

import src.presentation.server as srv


# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

_SERVER_GLOBALS = [
    "_repository", "_entity_uc", "_layer_uc", "_block_uc", "_document_uc",
    "_system_uc", "_solid_uc", "_symbol_uc", "_table_uc", "_hatch_uc",
    "_dimension_uc", "_measurement_uc", "_transform_uc", "_primitive_uc",
    "_doc_mgmt_uc", "_block_mgmt_uc", "_teo_uc", "_layer_mgmt_uc",
    "_linear_dim_uc", "_sweep_loft_uc", "_edge_op_uc", "_assembly_uc",
    "_selection_uc", "_stl_uc", "_constraint_uc", "_mleader_uc",
    "_sheet_metal_uc", "_feature_uc", "_nurb_ifc_uc", "_multicad_uc", "_routing_cache",
]

_USE_CASE_PATHS = [
    "src.presentation.server.EntityUseCase",
    "src.presentation.server.LayerUseCase",
    "src.presentation.server.BlockUseCase",
    "src.presentation.server.DocumentUseCase",
    "src.presentation.server.SystemUseCase",
    "src.presentation.server.SolidUseCase",
    "src.presentation.server.SymbolUseCase",
    "src.presentation.server.TableUseCase",
    "src.presentation.server.HatchUseCase",
    "src.presentation.server.DimensionUseCase",
    "src.presentation.server.MeasurementUseCase",
    "src.presentation.server.TransformationUseCase",
    "src.presentation.server.PrimitiveUseCase",
    "src.presentation.server.DocumentManagementUseCase",
    "src.presentation.server.BlockManagementUseCase",
    "src.presentation.server.TrimExtendOffsetUseCase",
    "src.presentation.server.LayerManagementUseCase",
    "src.presentation.server.LinearDimUseCase",
    "src.presentation.server.SweepLoftUseCase",
    "src.presentation.server.EdgeOpUseCase",
    "src.presentation.server.AssemblyUseCase",
    "src.presentation.server.SelectionUseCase",
    "src.presentation.server.StlExportUseCase",
    "src.presentation.server.ConstraintUseCase",
    "src.presentation.server.MLeaderUseCase",
    "src.presentation.server.SheetMetalUseCase",
    "src.presentation.server.FeatureUseCase",
    "src.presentation.server.NurbIfcUseCase",
    "src.presentation.server.MultiCadUseCase",
]


@pytest.fixture(autouse=True)
def _clean_globals() -> Any:
    """Reset module-level globals before each test."""
    import src.presentation.server as srv

    patchers = [patch.object(srv, g, None) for g in _SERVER_GLOBALS]
    for p in patchers:
        p.start()
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


def _patch_use_cases() -> ExitStack:
    """Patch all use case imports and return an ExitStack."""
    stack = ExitStack()
    for path in _USE_CASE_PATHS:
        stack.enter_context(patch(path))
    return stack


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_resolves_log_path(self) -> None:
        with patch("src.presentation.server.logging.basicConfig") as mock_bc, \
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
    def test_creates_repository(self, mock_repo: MagicMock) -> None:
        with patch("src.presentation.server.CadRepository", return_value=mock_repo):
            srv._ensure_connected()
            assert srv._repository is not None

    def test_connects_repository(self, mock_repo: MagicMock) -> None:
        with patch("src.presentation.server.CadRepository", return_value=mock_repo):
            srv._ensure_connected()
            mock_repo.connect.assert_called_once()

    def test_skips_if_already_connected(self, mock_repo: MagicMock) -> None:
        with patch("src.presentation.server.CadRepository", return_value=mock_repo):
            srv._ensure_connected()
            mock_repo.connect.reset_mock()
            srv._ensure_connected()
            mock_repo.connect.assert_not_called()

    def test_reconnects_if_unavailable(self, mock_repo: MagicMock) -> None:
        mock_repo.is_available.side_effect = [False, True]
        with patch("src.presentation.server.CadRepository", return_value=mock_repo):
            srv._ensure_connected()
            # connect is called; is_available was checked twice
            assert mock_repo.connect.called

    def test_warns_on_connect_failure(self, mock_repo: MagicMock) -> None:
        mock_repo.connect.return_value = False
        mock_repo.connection_mode = "offline"
        with patch("src.presentation.server.CadRepository", return_value=mock_repo), \
             patch("src.presentation.server.log.warning") as mock_warn:
            srv._ensure_connected()
            mock_warn.assert_called_once()

    def test_creates_all_use_cases(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            # Verify use cases are created
            assert srv._entity_uc is not None
            assert srv._layer_uc is not None
            assert srv._system_uc is not None
            assert srv._solid_uc is not None


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


class TestBuildRouting:
    def test_returns_empty_when_globals_are_none(self) -> None:
        """_build_routing should return empty dict if globals are None."""
        all_uc_names = [
            "_system_uc", "_entity_uc", "_layer_uc", "_block_uc", "_document_uc",
            "_solid_uc", "_symbol_uc", "_table_uc", "_hatch_uc", "_dimension_uc",
            "_measurement_uc", "_transform_uc", "_primitive_uc", "_doc_mgmt_uc",
            "_block_mgmt_uc", "_teo_uc", "_layer_mgmt_uc", "_linear_dim_uc",
            "_sweep_loft_uc", "_edge_op_uc", "_assembly_uc", "_selection_uc",
            "_stl_uc", "_constraint_uc", "_mleader_uc", "_sheet_metal_uc",
            "_feature_uc", "_nurb_ifc_uc", "_multicad_uc",
        ]
        stack = ExitStack()
        try:
            for name in all_uc_names:
                stack.enter_context(patch.object(srv, name, None))
            srv._routing_cache = None
            routing = srv._build_routing()
            assert isinstance(routing, dict)
            assert len(routing) == 0
        finally:
            stack.close()

    def test_returns_dict_with_all_tool_names(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._repository = None
            srv._routing_cache = None
            srv._ensure_connected()
            routing = srv._build_routing()
            tools = srv._get_tools()
            assert len(routing) == len(tools)
            for t in tools:
                assert t.name in routing

    def test_each_handler_is_callable(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            for name, handler in routing.items():
                assert callable(handler), f"{name} is not callable"

    def test_health_check_maps_to_is_available(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["health_check"] == srv._system_uc.is_available

    def test_get_system_fonts_maps_to_system_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["get_system_fonts"] == srv._system_uc.get_fonts

    def test_create_line_maps_to_entity_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["create_line"] == srv._entity_uc.create_line

    def test_get_layers_maps_to_layer_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["get_layers"] == srv._layer_uc.get_layers

    def test_get_linetypes_maps_to_layer_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["get_linetypes"] == srv._layer_uc.get_linetypes

    def test_create_mesh_maps_to_entity_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["create_mesh"] == srv._entity_uc.create_mesh

    def test_edit_mesh_maps_to_entity_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["edit_mesh"] == srv._entity_uc.edit_mesh

    def test_set_viewport_maps_to_entity_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["set_viewport"] == srv._entity_uc.set_viewport

    def test_render_maps_to_entity_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["render"] == srv._entity_uc.render

    def test_create_nurb_curve_maps_to_nurb_ifc_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["create_nurb_curve"] == srv._nurb_ifc_uc.create_nurb_curve

    def test_create_nurb_surface_maps_to_nurb_ifc_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["create_nurb_surface"] == srv._nurb_ifc_uc.create_nurb_surface

    def test_modify_nurb_maps_to_nurb_ifc_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["modify_nurb"] == srv._nurb_ifc_uc.modify_nurb

    def test_import_ifc_maps_to_nurb_ifc_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["import_ifc"] == srv._nurb_ifc_uc.import_ifc

    def test_get_ifc_entities_maps_to_nurb_ifc_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["get_ifc_entities"] == srv._nurb_ifc_uc.get_ifc_entities


class TestMultiCadTools:
    """Test that MultiCAD API tools are routed correctly."""

    @pytest.mark.parametrize("tool_name", [
        "create_grid_axis", "create_grid_label", "create_room",
        "get_room_properties", "create_custom_object", "create_parametric_object",
        "create_reactor", "create_2d_break", "start_motion_preview",
        "stop_motion_preview", "create_body_contour", "check_3d_faces",
    ])
    def test_multicad_tools_in_routing(self, tool_name: str, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert tool_name in routing

    def test_create_grid_axis_maps_to_multicad_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["create_grid_axis"] == srv._multicad_uc.create_grid_axis

    def test_create_room_maps_to_multicad_uc(self, mock_repo: MagicMock) -> None:
        with _patch_use_cases() as stack:
            stack.enter_context(patch("src.presentation.server.CadRepository", return_value=mock_repo))
            srv._ensure_connected()
            routing = srv._build_routing()
            assert routing["create_room"] == srv._multicad_uc.create_room


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
