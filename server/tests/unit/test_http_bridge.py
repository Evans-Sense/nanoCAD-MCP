from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.infrastructure.http_bridge import HttpCadBridge


@pytest.fixture(autouse=True)
def _set_test_data_dir() -> None:
    r"""Set NANOCAD_MCP_DATA_DIR to C:\ so tests with C:/projects pass validation."""
    os.environ["NANOCAD_MCP_DATA_DIR"] = "C:\\"


@pytest.fixture
def bridge() -> HttpCadBridge:
    b = HttpCadBridge(port=9999)
    b._client = MagicMock()
    b._available = True
    return b


def _mock_response(data: dict | None = None, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data or {}
    return resp


# ── Health ─────────────────────────────────────────────────


class TestHealth:
    def test_check_health(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"status": "ok"})
        result = bridge.check_health()
        assert result == {"status": "ok"}
        bridge._client.request.assert_called_once_with(
            "GET", "/api/system/health", json=None, timeout=2.0
        )

    def test_check_health_none_on_error(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        result = bridge.check_health()
        assert result is None

    def test_connect_success(self) -> None:
        b = HttpCadBridge(port=9999)
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.get.return_value = _mock_response(
                {"status": "ok", "version": "26.0"}
            )
            assert b.connect() is True
            assert b.is_available is True

    def test_connect_failure(self) -> None:
        b = HttpCadBridge(port=9999)
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("refused")
            assert b.connect() is False
            assert b.is_available is False

    def test_close(self, bridge: HttpCadBridge) -> None:
        bridge.close()
        assert bridge._client is None
        assert bridge.is_available is False

    def test_connect_no_client_returns_false(self) -> None:
        b = HttpCadBridge(port=9999)
        assert b.connect() is False

    def test_connect_http_error(self) -> None:
        b = HttpCadBridge(port=9999)
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.get.return_value = _mock_response({}, status=500)
            assert b.connect() is False


# ── Generic Request ─────────────────────────────────────────


class TestRequest:
    def test_request_success(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"key": "val"})
        result = bridge._request("POST", "/api/test", json_body={"a": 1})
        assert result == {"key": "val"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/test", json={"a": 1}, timeout=30.0
        )

    def test_request_no_client(self) -> None:
        b = HttpCadBridge(port=9999)
        result = b._request("GET", "/api/test")
        assert result is None

    def test_request_http_error(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = __import__("httpx").HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        result = bridge._request("GET", "/api/test")
        assert result is None

    def test_request_connection_error_sets_available_false(
        self, bridge: HttpCadBridge
    ) -> None:
        bridge._client.request.side_effect = __import__("httpx").ConnectError(
            "connection refused"
        )
        result = bridge._request("GET", "/api/test")
        assert result is None
        assert bridge.is_available is False

    def test_request_timeout_does_not_mark_unavailable(
        self, bridge: HttpCadBridge
    ) -> None:
        bridge._client.request.side_effect = __import__("httpx").TimeoutException(
            "timed out"
        )
        # Bridge should remain available after timeout
        assert bridge.is_available is True
        result = bridge._request("GET", "/api/test")
        assert result is None
        assert bridge.is_available is True

    def test_request_generic_error_does_not_mark_unavailable(
        self, bridge: HttpCadBridge
    ) -> None:
        bridge._client.request.side_effect = __import__("httpx").RequestError(
            "some other error"
        )
        assert bridge.is_available is True
        result = bridge._request("GET", "/api/test")
        assert result is None
        assert bridge.is_available is True

    def test_request_json_decode_error(self, bridge: HttpCadBridge) -> None:
        import json

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
        bridge._client.request.return_value = mock_resp
        result = bridge._request("GET", "/api/test")
        assert result is None


# ── Entity operations ───────────────────────────────────────


class TestEntityOps:
    def test_create_entity_success(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "ABC"})
        result = bridge.create_entity("line", {"x1": 0, "y1": 0, "x2": 10, "y2": 10})
        assert result == "ABC"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/line", json={"x1": 0, "y1": 0, "x2": 10, "y2": 10}, timeout=30.0
        )

    def test_create_entity_no_handle(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"error": "fail"})
        result = bridge.create_entity("line", {})
        assert result is None

    def test_create_entity_none_result(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(None)
        result = bridge.create_entity("circle", {"cx": 0, "cy": 0, "radius": 5})
        assert result is None

    def test_delete_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.delete_entity("H1") is True
        bridge._client.request.assert_called_once_with(
            "DELETE", "/api/entity/H1", json=None, timeout=30.0
        )

    def test_delete_entity_fail(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.delete_entity("H1") is False

    def test_get_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "H1", "type": "LINE"})
        result = bridge.get_entity("H1")
        assert result == {"handle": "H1", "type": "LINE"}

    def test_move_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.move_entity("H1", 5.0, 10.0) is True

    def test_copy_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "H2"})
        result = bridge.copy_entity("H1")
        assert result == "H2"

    def test_copy_entity_fail(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.copy_entity("H1") is None

    def test_rotate_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.rotate_entity("H1", 45.0) is True

    def test_scale_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.scale_entity("H1", 2.0, 5, 5) is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/H1/scale", json={"factor": 2.0, "center_x": 5, "center_y": 5}, timeout=30.0
        )


# ── Layer operations ────────────────────────────────────────


class TestLinetypeOps:
    def test_get_linetypes(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"linetypes": [{"name": "Continuous", "description": "Solid line"}]}
        )
        result = bridge.get_linetypes()
        assert result == [{"name": "Continuous", "description": "Solid line"}]
        bridge._client.request.assert_called_once_with(
            "GET", "/api/linetype", json=None, timeout=30.0
        )

    def test_get_linetypes_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.get_linetypes() == []

    def test_get_linetypes_none(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=_mock_response({}, status=404)
        )
        assert bridge.get_linetypes() == []


class TestLayerOps:
    def test_get_layers(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"layers": [{"name": "0", "is_on": True}]}
        )
        result = bridge.get_layers()
        assert result == [{"name": "0", "is_on": True}]

    def test_get_layers_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.get_layers() == []

    def test_get_layers_none(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=_mock_response({}, status=404)
        )
        assert bridge.get_layers() == []

    def test_create_layer(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_layer("Test") is True

    def test_create_layer_with_color(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_layer("Test", "red") is True

    def test_set_current_layer(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.set_current_layer("0") is True


# ── Document operations ─────────────────────────────────────


class TestDocumentOps:
    def test_get_document_info(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"name": "drawing.dwg"})
        result = bridge.get_document_info()
        assert result == {"name": "drawing.dwg"}

    def test_save_document(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.save_document("C:\\test.dwg") is True

    def test_save_document_no_path(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.save_document() is True

    def test_export_pdf(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.export_pdf("C:\\out.pdf") is True

    def test_export_dwg(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.export_dwg("C:/out.dwg") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/export/dwg",
            json={"path": "C:/out.dwg"}, timeout=30.0,
        )

    def test_export_dxf(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.export_dxf("C:/out.dxf") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/export/dxf",
            json={"path": "C:/out.dxf"}, timeout=30.0,
        )

    def test_zoom_extents(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.zoom_extents() is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/zoom/extents", json=None, timeout=30.0,
        )

    def test_get_document_info(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({
            "name": "test.dwg", "entities_count": 10,
        })
        result = bridge.get_document_info()
        assert result["name"] == "test.dwg"

    def test_get_system_info(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({
            "version": "26.0", "is_engine_available": True,
        })
        result = bridge.get_system_info()
        assert result["version"] == "26.0"

    def test_insert_block(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "INS_001"})
        result = bridge.insert_block("WASHER", x=10, y=20, scale=1.5, rotation=30)
        assert result == "INS_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/block/WASHER/insert",
            json={
                "x": 10, "y": 20,
                "scaleX": 1.5, "scaleY": 1.5, "scaleZ": 1.5,
                "rotation": 30,
            },
            timeout=30.0,
        )

    def test_insert_block_default_scale(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "INS_002"})
        bridge.insert_block("WASHER")
        body = bridge._client.request.call_args.kwargs["json"]
        assert body["scaleX"] == 1.0
        assert body["scaleY"] == 1.0
        assert body["scaleZ"] == 1.0

    def test_get_blocks(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({
            "blocks": [{"name": "WASHER"}, {"name": "SHAFT"}],
        })
        result = bridge.get_blocks()
        assert len(result) == 2
        assert result[0]["name"] == "WASHER"
        bridge._client.request.assert_called_once_with(
            "GET", "/api/block", json=None, timeout=30.0,
        )

    def test_get_blocks_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.get_blocks()
        assert result == []

    def test_open_document(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.open_document("C:\\drawing.dwg") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/open",
            json={"path": "C:/drawing.dwg"},
            timeout=30.0,
        )

    def test_close_document(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.close_document() is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/close",
            json=None,
            timeout=30.0,
        )


# ── System operations ───────────────────────────────────────


class TestSystemFontsOps:
    def test_get_system_fonts(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"fonts": [{"name": "Arial", "type": "truetype"}]}
        )
        result = bridge.get_system_fonts()
        assert result == [{"name": "Arial", "type": "truetype"}]
        bridge._client.request.assert_called_once_with(
            "GET", "/api/system/fonts", json=None, timeout=30.0
        )

    def test_get_system_fonts_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.get_system_fonts() == []

    def test_get_system_fonts_none(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=_mock_response({}, status=404)
        )
        assert bridge.get_system_fonts() == []


class TestSystemOps:
    def test_execute_command(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"output": "ok"})
        result = bridge.execute_command("_LINE")
        assert result == "ok"

    def test_execute_command_no_output(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.execute_command("_LINE") is None

    def test_get_system_variable(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"value": "1"})
        result = bridge.get_system_variable("CMDECHO")
        assert result == "1"

    def test_get_system_variable_no_value(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.get_system_variable("CMDECHO") is None

    def test_set_system_variable(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.set_system_variable("CMDECHO", "0") is True


# ── 3D Solid operations ─────────────────────────────────────


class TestSolidOps:
    def test_create_box(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "BOX_001"})
        result = bridge.create_box(100, 200, 50)
        assert result == "BOX_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/solid/box", json={"x": 100, "y": 200, "z": 50}, timeout=30.0
        )

    def test_create_box_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.create_box(10, 20, 30) is None

    def test_create_sphere(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "SPH_001"})
        assert bridge.create_sphere(50) == "SPH_001"

    def test_create_cylinder(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "CYL_001"})
        assert bridge.create_cylinder(25, 100) == "CYL_001"

    def test_create_cone(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "CONE_001"})
        assert bridge.create_cone(30, 80) == "CONE_001"

    def test_create_torus(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "TOR_001"})
        assert bridge.create_torus(50, 10) == "TOR_001"

    def test_create_wedge(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "WDG_001"})
        assert bridge.create_wedge(100, 50, 30) == "WDG_001"

    def test_create_pyramid(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "PYR_001"})
        assert bridge.create_pyramid(80, 6, 30) == "PYR_001"

    def test_boolean_union(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "RESULT"})
        result = bridge.boolean_union("A", "B")
        assert result == "RESULT"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/solid/A/union/B", json=None, timeout=30.0
        )

    def test_boolean_subtract(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "RESULT"})
        assert bridge.boolean_subtract("A", "B") == "RESULT"

    def test_boolean_intersect(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "RESULT"})
        assert bridge.boolean_intersect("A", "B") == "RESULT"

    def test_extrude_solid(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "EXT_001"})
        result = bridge.extrude_solid("H1", 50, 5)
        assert result == "EXT_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/solid/extrude",
            json={"handle": "H1", "height": 50, "taper_angle": 5},
            timeout=30.0,
        )

    def test_revolve_solid(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "REV_001"})
        result = bridge.revolve_solid("H1", 0, 0, 0, 0, 0, 1, 360)
        assert result == "REV_001"

    def test_move_solid(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.move_solid("H1", 10, 20, 5) is True

    def test_set_3d_view(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.set_3d_view("top", "wireframe") is True

    def test_get_solid_properties(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"handle": "H1", "volume": 100.0}
        )
        result = bridge.get_solid_properties("H1")
        assert result == {"handle": "H1", "volume": 100.0}


# ── Symbol operations ───────────────────────────────────────


class TestSymbolOps:
    def test_create_roughness(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "RGH_001"})
        result = bridge.create_roughness("Ra 6.3", 0, "", 1)
        assert result == {"handle": "RGH_001"}

    def test_create_old_roughness(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "OLD_001"})
        assert bridge.create_old_roughness("6.3", 0, "", False, 0) is not None

    def test_create_tolerance(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "TOL_001"})
        result = bridge.create_tolerance("1", "0.1", "A")
        assert result is not None

    def test_create_tolerance_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "TOL_001"})
        result = bridge.create_tolerance()
        assert result is not None
        # Should NOT include empty keys in body
        call_kwargs = bridge._client.request.call_args[1]
        json_body = call_kwargs["json"]
        assert "type1" not in json_body

    def test_create_datum(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "DAT_001"})
        assert bridge.create_datum("B") is not None

    def test_create_weld(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "WLD_001"})
        assert bridge.create_weld(False, False) is not None

    def test_create_leader(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "LDR_001"})
        result = bridge.create_leader(0, 0, 10, 10, 20, 10, "Note")
        assert result is not None

    def test_create_note_comb(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "NTC_001"})
        assert bridge.create_note_comb(45, 12, "A", "B") is not None

    def test_create_dim_number(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "DIM_001"})
        assert bridge.create_dim_number(0, 0, 10, 10, "1", 1, True) is not None

    def test_create_mleader(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "MLE_001"})
        result = bridge.create_mleader(0, 0, 10, 10, "Note", 3.5)
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "POST", "/api/symbol/mleader",
            json={"arrow_x": 0, "arrow_y": 0, "leader_x": 10, "leader_y": 10,
                  "text": "Note", "text_height": 3.5},
            timeout=30.0,
        )


# ── Table / Hatch / Dimension operations ─────────────────────


class TestTableHatchDimOps:
    def test_create_table(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "TBL_001"})
        assert bridge.create_table(3, 4, 30, 100) is not None

    def test_edit_table_cell(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.edit_table_cell("TBL_001", 1, 2, "new value")
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "PATCH", "/api/table/TBL_001/cell",
            json={"row_index": 1, "column_index": 2, "value": "new value"},
            timeout=30.0,
        )

    def test_get_table_info(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "TBL_001", "row_count": 3})
        result = bridge.get_table_info("TBL_001")
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "GET", "/api/table/TBL_001",
            json=None, timeout=30.0,
        )

    def test_delete_table(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.delete_table("TBL_001")
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "DELETE", "/api/table/TBL_001",
            json=None, timeout=30.0,
        )

    def test_get_table_info_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.get_table_info("INVALID")
        assert result == {}

    def test_edit_table_cell_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("connection failed")
        result = bridge.edit_table_cell("TBL_001", 0, 0, "x")
        assert result is None

    def test_create_hatch(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "HTC_001"})
        assert bridge.create_hatch("ANSI31", 1.0) is not None

    def test_get_hatch_info(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"pattern": "ANSI31"})
        result = bridge.get_hatch_info("H1")
        assert result == {"pattern": "ANSI31"}

    def test_edit_hatch(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.edit_hatch("H1", "ANSI32", 2.0)
        assert result is not None

    def test_edit_hatch_no_scale(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.edit_hatch("H1", "ANSI32")
        assert result is not None

    def test_create_aligned_dimension(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "DIM_001"})
        result = bridge.create_aligned_dimension(0, 0, 10, 10, 5, -5)
        assert result is not None

    # ── New 6 tools ──────────────────────────────────────────

    def test_create_helix(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "HLX_001"})
        result = bridge.create_helix(0, 0, 0, 20, 10, 50, 3)
        assert result == "HLX_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/helix",
            json={"center_x": 0, "center_y": 0, "center_z": 0,
                  "start_radius": 20, "end_radius": 10, "height": 50, "turns": 3},
            timeout=30.0,
        )

    def test_create_helix_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.create_helix(0, 0, 0, 20, 10, 50, 3) is None

    def test_create_region(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "REG_001"})
        result = bridge.create_region(["C1", "C2"])
        assert result == {"handle": "REG_001"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/region",
            json={"curve_handles": ["C1", "C2"]},
            timeout=30.0,
        )

    def test_create_region_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        result = bridge.create_region(["C1"])
        assert result is None

    def test_create_boundary(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "BND_001"})
        result = bridge.create_boundary(50.0, 50.0)
        assert result == {"handle": "BND_001"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/boundary",
            json={"point_x": 50.0, "point_y": 50.0},
            timeout=30.0,
        )

    def test_create_boundary_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.create_boundary(0, 0)
        assert result == {}

    def test_create_gradient(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "GRD_001"})
        result = bridge.create_gradient("1,0,0", "0,0,1", 2.0, "radial")
        assert result == {"handle": "GRD_001"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/gradient",
            json={"color1": "1,0,0", "color2": "0,0,1", "scale": 2.0, "gradient_type": "radial"},
            timeout=30.0,
        )

    def test_create_gradient_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        result = bridge.create_gradient()
        assert result is None

    def test_create_arc_length_dimension(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "DIM_AL_001"})
        result = bridge.create_arc_length_dimension(0, 0, 50, 0, 90, 0, 0)
        assert result == {"handle": "DIM_AL_001"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/dimension/arc_length",
            json={"center_x": 0, "center_y": 0, "radius": 50,
                  "start_angle": 0, "end_angle": 90, "dim_x": 0, "dim_y": 0},
            timeout=30.0,
        )

    def test_create_arc_length_dimension_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.create_arc_length_dimension()
        assert result == {}

    def test_export_ifc(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.export_ifc("C:/model.ifc")
        assert result == {"success": True}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/export/ifc",
            json={"path": "C:/model.ifc"},
            timeout=30.0,
        )

    def test_export_ifc_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        result = bridge.export_ifc("C:/bad.ifc")
        assert result is None


# ── Measurement operations ───────────────────────────────────


class TestMeasurementOps:
    def test_get_distance(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"distance": 10.0})
        result = bridge.get_distance(0, 0, 0, 10, 0, 0)
        assert result == {"distance": 10.0}

    def test_get_angle(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"angle_degrees": 90.0})
        result = bridge.get_angle(0, 0, 0, 0, 0, 0, 10, 0, 0)
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "POST", "/api/measurement/angle",
            json={
                "x1": 0, "y1": 0, "z1": 0,
                "x2": 0, "y2": 0, "z2": 0,
                "x3": 10, "y3": 0, "z3": 0,
            },
            timeout=30.0,
        )

    def test_get_angle_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"error": "Zero-length vectors"})
        result = bridge.get_angle(0, 0, 0, 0, 0, 0, 0, 0, 0)
        assert "error" in result

    def test_get_area(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"area": 100.0})
        assert bridge.get_area("H1") == {"area": 100.0}

    def test_get_entity_info(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"type": "LINE"})
        assert bridge.get_entity_info("H1") == {"type": "LINE"}

    def test_get_all_entities(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "H1"}]}
        )
        result = bridge.get_all_entities()
        assert result == {"entities": [{"handle": "H1"}]}


# ── Transformation operations ────────────────────────────────


class TestTransformationOps:
    def test_mirror_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.mirror_entity("H1", 0, 0, 10, 0) is True

    def test_stretch_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.stretch_entity("H1", 5, 5) is True

    def test_explode_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "E1"}]}
        )
        result = bridge.explode_entity("H1")
        assert result is not None

    def test_divide_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "P1"}, {"handle": "P2"}]}
        )
        result = bridge.divide_entity("H1", 3)
        assert result is not None

    def test_measure_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.measure_entity("H1", 10.0)
        assert result is not None

    def test_array_3d(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "C1"}, {"handle": "C2"}]}
        )
        result = bridge.array_3d("H1", 2, 2, 1, 50, 50, 0)
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/H1/array3d",
            json={"handle": "H1", "count_x": 2, "count_y": 2, "count_z": 1,
                  "spacing_x": 50, "spacing_y": 50, "spacing_z": 0},
            timeout=30.0,
        )

    def test_align_3d(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.align_3d(
            "H1",
            (0, 0, 0), (1, 0, 0), (0, 1, 0),
            (10, 10, 0), (11, 10, 0), (10, 11, 0),
        )
        assert result is True

    def test_mirror_3d(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.mirror_3d(
            "H1", (0, 0, 0), (10, 0, 0), (0, 10, 0)
        )
        assert result is True


# ── Primitive operations ─────────────────────────────────────


class TestPrimitiveOps:
    def test_create_polygon(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "POL_001"})
        result = bridge.create_polygon(0, 0, 10, 6, True)
        assert result == "POL_001"

    def test_create_polygon_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.create_polygon(0, 0, 10, 6, True) is None

    def test_create_donut(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "DON_001"})
        assert bridge.create_donut(0, 0, 5, 10) == "DON_001"

    def test_create_xline(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "XLN_001"})
        result = bridge.create_xline(0, 0, 10, 10)
        assert result == "XLN_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/xline",
            json={"p1_x": 0, "p1_y": 0, "p2_x": 10, "p2_y": 10},
            timeout=30.0,
        )

    def test_create_ray(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "RAY_001"})
        result = bridge.create_ray(0, 0, 10, 10)
        assert result == "RAY_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/ray",
            json={"p1_x": 0, "p1_y": 0, "p2_x": 10, "p2_y": 10},
            timeout=30.0,
        )


# ── Document Management ──────────────────────────────────────


class TestDocManagementOps:
    def test_undo(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.undo() is True

    def test_redo(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.redo() is True

    def test_purge(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.purge() is True

    def test_import_step(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.import_step("C:\\model.step") is True

    def test_export_step(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.export_step("C:\\model.step") is True

    def test_export_stl(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.export_stl("C:\\model.stl", True) is True

    def test_new_document(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.new_document() is True

    def test_new_document_with_template(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.new_document("template.dwt") is True

    def test_create_project(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_project("model.dwg", "C:/projects") is True
        # Routes to /api/document/new with save_path = dir/filename.dwg
        bridge._client.request.assert_called_once_with(
            "POST",
            "/api/document/new",
            json={"save_path": "C:/projects/model.dwg"},
            timeout=30.0,
        )

    def test_create_project_with_template(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert (
            bridge.create_project("model.dwg", "C:/projects", "C:/templates/ansi.dwt") is True
        )
        body = bridge._client.request.call_args.kwargs["json"]
        assert body["template"] == "C:/templates/ansi.dwt"
        assert body["save_path"] == "C:/projects/model.dwg"

    def test_create_project_appends_dwg_extension(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        bridge.create_project("model", "C:/projects")
        body = bridge._client.request.call_args.kwargs["json"]
        assert body["save_path"] == "C:/projects/model.dwg"

    def test_create_project_normalizes_backslashes(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        bridge.create_project("model.dwg", "C:\\projects\\sub")
        body = bridge._client.request.call_args.kwargs["json"]
        # backslashes must be replaced with forward slashes for JSON safety
        assert "\\" not in body["save_path"]
        assert body["save_path"] == "C:/projects/sub/model.dwg"

    def test_create_project_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("connection failed")
        assert bridge.create_project("model.dwg", "C:/projects") is False

    def test_save_project(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.save_project("out.dwg", "C:/projects") is True
        # Routes to /api/document/save with path = dir/filename.dwg
        bridge._client.request.assert_called_once_with(
            "POST",
            "/api/document/save",
            json={"path": "C:/projects/out.dwg"},
            timeout=30.0,
        )

    def test_save_project_appends_dwg_extension(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        bridge.save_project("out", "C:/projects")
        body = bridge._client.request.call_args.kwargs["json"]
        assert body["path"] == "C:/projects/out.dwg"

    def test_save_project_normalizes_backslashes(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        bridge.save_project("out.dwg", "C:\\projects\\sub")
        body = bridge._client.request.call_args.kwargs["json"]
        assert "\\" not in body["path"]
        assert body["path"] == "C:/projects/sub/out.dwg"

    def test_save_project_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("connection failed")
        assert bridge.save_project("out.dwg", "C:/projects") is False


# ── Block operations ────────────────────────────────────────


class TestBlockOps:
    def test_create_block(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "BLK_001"})
        result = bridge.create_block("MyBlock", ["H1", "H2"], 0, 0)
        assert result == "BLK_001"
        bridge._client.request.assert_called_once_with(
            "POST", "/api/block/create",
            json={"name": "MyBlock", "handles": ["H1", "H2"], "base_x": 0, "base_y": 0},
            timeout=30.0,
        )

    def test_create_block_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.create_block("B", ["H1"]) is None

    def test_explode_block(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.explode_block("MyBlock") is True

    def test_delete_block(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.delete_block("BadBlock") is True

    def test_get_block_entities(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "E1"}]}
        )
        result = bridge.get_block_entities("MyBlock")
        assert result == [{"handle": "E1"}]

    def test_get_block_entities_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        assert bridge.get_block_entities("X") == []


# ── Trim / Extend / Offset ──────────────────────────────────


class TestTrimExtendOffsetOps:
    def test_trim_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "H2"}]}
        )
        result = bridge.trim_entity("H1", 5, 0, True)
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/H1/trim",
            json={"handle": "H1", "cut_x": 5, "cut_y": 0, "keep_start": True},
            timeout=30.0,
        )

    def test_extend_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.extend_entity("H1", 20, 0) is True

    def test_offset_entity(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "OFF_001"}]}
        )
        result = bridge.offset_entity("H1", 5.0)
        assert result is not None


# ── Layer Management ────────────────────────────────────────


class TestLayerMgmtOps:
    def test_layer_isolate(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.layer_isolate("Layer1") is True

    def test_layer_off(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.layer_off("Layer1") is True

    def test_layer_freeze(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.layer_freeze("Layer1") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/layer/Layer1/freeze", json=None, timeout=30.0
        )

    def test_layer_on_all(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.layer_on_all() is True

    def test_layer_thaw_all(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.layer_thaw_all() is True


# ── DIMLINEAR / SWEEP / LOFT / FILLETEDGE / CHAMFEREDGE ─────


class TestAdvancedOps:
    def test_create_linear_dimension(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "DIM_001"})
        result = bridge.create_linear_dimension(0, 0, 10, 0, 5, -5, "horizontal")
        assert result is not None

    def test_sweep_solid(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.sweep_solid("PROF", "PATH") is True

    def test_loft_solid(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.loft_solid(["S1", "S2"]) is True

    def test_fillet_edge(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "handle": "1F5"})
        assert bridge.fillet_edge("H1", 5.0) == "1F5"

    def test_chamfer_edge(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "handle": "2A0"})
        assert bridge.chamfer_edge("H1", 5.0, 5.0) == "2A0"

    def test_fillet_edge_error_response(self, bridge: HttpCadBridge) -> None:
        """Error JSON should return None, not a handle."""
        bridge._client.request.return_value = _mock_response({"success": False, "error": "Not supported"})
        assert bridge.fillet_edge("H1") is None

    def test_chamfer_edge_error_response(self, bridge: HttpCadBridge) -> None:
        """Error JSON should return None, not a handle."""
        bridge._client.request.return_value = _mock_response({"success": False, "error": "Not supported"})
        assert bridge.chamfer_edge("H1") is None

    def test_fillet_edge_connect_error(self, bridge: HttpCadBridge) -> None:
        """Network error should return None."""
        import httpx
        bridge._client.request.side_effect = httpx.ConnectError("connection refused")
        assert bridge.fillet_edge("H1") is None

    def test_chamfer_edge_connect_error(self, bridge: HttpCadBridge) -> None:
        """Network error should return None."""
        import httpx
        bridge._client.request.side_effect = httpx.ConnectError("connection refused")
        assert bridge.chamfer_edge("H1") is None


# ── Assembly operations ──────────────────────────────────────


class TestAssemblyOps:
    def test_insert_part(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.insert_part("Part1", 0, 0, 0) is True

    def test_assembly_mate(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.assembly_mate("H1", "H2") is True

    def test_assembly_angle(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.assembly_angle("H1", "H2", 45) is True

    def test_assembly_tangent(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.assembly_tangent("H1", "H2") is True

    def test_assembly_symmetry(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.assembly_symmetry("H1", "H2", "PLANE") is True


# ── Selection operations ─────────────────────────────────────


class TestSelectionOps:
    def test_select_entities(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "H1"}]}
        )
        result = bridge.select_entities("LINE", "0", 7, 100)
        assert result is not None
        bridge._client.request.assert_called_once_with(
            "POST", "/api/selection/select",
            json={"max_count": 100, "entity_type": "LINE", "layer": "0", "color": 7},
            timeout=30.0,
        )

    def test_select_entities_no_filters(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "H1"}]}
        )
        result = bridge.select_entities()
        assert result is not None

    def test_select_by_handles(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "H1"}]}
        )
        result = bridge.select_by_handles(["H1", "H2"])
        assert result is not None

    def test_get_entity_detail(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"handle": "H1", "type": "LINE", "length": 10.0}
        )
        result = bridge.get_entity_detail("H1")
        assert result == {"handle": "H1", "type": "LINE", "length": 10.0}


# ── 2D Constraints ───────────────────────────────────────────


class TestConstraintOps:
    def test_constraint_parallel(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_parallel("H1", "H2") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/constraint/parallel",
            json={"handle1": "H1", "handle2": "H2"}, timeout=30.0
        )

    def test_constraint_coincident(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_coincident("H1", "H2") is True

    def test_constraint_fix(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_fix("H1") is True

    def test_constraint_horizontal(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_horizontal("H1") is True

    def test_constraint_vertical(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_vertical("H1") is True

    def test_constraint_tangent(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_tangent("LINE1", "ARC1") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/constraint/tangent",
            json={"handle_line": "LINE1", "handle_curve": "ARC1"}, timeout=30.0
        )

    def test_constraint_perpendicular(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_perpendicular("H1", "H2") is True

    def test_constraint_collinear(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_collinear("H1", "H2") is True

    def test_constraint_concentric(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_concentric("H1", "H2") is True

    def test_constraint_equal(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.constraint_equal("H1", "H2") is True

    def test_constraint_symmetric(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.constraint_symmetric("H1", "H2", "PLANE")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/constraint/symmetric",
            json={"handle1": "H1", "handle2": "H2", "plane_handle": "PLANE"},
            timeout=30.0,
        )

    def test_constraint_distance(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.constraint_distance("H1", "H2", 50.0)
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/constraint/distance",
            json={"handle1": "H1", "handle2": "H2", "distance": 50.0},
            timeout=30.0,
        )


# ── Sheet Metal ───────────────────────────────────────────────


class TestSheetMetalOps:
    def test_create_base_flange(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_base_flange(0, 0, 100, 200, 2) is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/sheetmetal/base-flange",
            json={"x": 0, "y": 0, "width": 100, "length": 200, "thickness": 2},
            timeout=30.0,
        )

    def test_create_edge_flange(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_edge_flange("BASE_H", 5.0) is True

    def test_create_bend(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_bend("H1", 5.0) is True

    def test_unfold_sheet_metal(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.unfold_sheet_metal("H1", 0, 0) is True

    def test_create_base_plate(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_base_plate(0, 0, 100, 200, 2) is True


# ── Mesh / Viewport / Render ────────────────────────────────


class TestSubMeshOps:
    def test_create_mesh(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "M001"})
        result = bridge.create_mesh(
            [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0], [0, 0, 5], [10, 0, 5], [10, 10, 5], [0, 10, 5]],
            [3, 2, 1, 0, 4, 5, 6, 7, 0, 1, 5, 4, 1, 2, 6, 5, 2, 3, 7, 6, 3, 0, 4, 7],
            0,
        )
        assert result is not None
        assert result["handle"] == "M001"

    def test_create_mesh_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        result = bridge.create_mesh([[0, 0, 0], [10, 0, 0]], [0, 1])
        assert result is None

    def test_edit_mesh(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.edit_mesh("M001", vertices=[[1, 1, 1], [2, 2, 2]], subdivide=1)
        assert result is not None

    def test_edit_mesh_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.edit_mesh("INVALID")
        assert result == {}

    def test_set_viewport(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.set_viewport("test", "2vert") is True

    def test_set_viewport_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        assert bridge.set_viewport("bad") is False

    def test_render(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.render() is True

    def test_render_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.render("out.png")
        assert result is not None


# ── Port file ──────────────────────────────────────────────────


class TestPortFile:
    def test_read_port_file_exists(self) -> None:
        import tempfile

        tmp = tempfile.gettempdir()
        tmp + "/ncad-mcp-port-test.txt"

        # Temporarily mock Path.home() to point to temp
        with patch("src.infrastructure.http_bridge.Path.home") as mock_home:
            mock_home.return_value = __import__("pathlib").Path(tmp)
            with patch("src.infrastructure.http_bridge.Path.exists", return_value=True):
                with patch("src.infrastructure.http_bridge.Path.read_text", return_value="5080"):
                    result = __import__("src.infrastructure.http_bridge", fromlist=["_read_port_file"])._read_port_file()
                    assert result == 5080

    def test_read_port_file_missing(self) -> None:
        with patch("src.infrastructure.http_bridge.Path.exists", return_value=False):
            result = __import__("src.infrastructure.http_bridge", fromlist=["_read_port_file"])._read_port_file()
            assert result is None


# ── NURBS / IFC ─────────────────────────────────────────────


class TestNurbIfcOps:
    def test_create_nurb_curve(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "NC_001", "type": "NurbCurve"})
        result = bridge.create_nurb_curve(
            degree=3, periodic=False,
            control_points=[[0, 0], [5, 10], [10, 0]],
            knots=[0, 0, 0, 1, 1, 1],
        )
        assert result == {"handle": "NC_001", "type": "NurbCurve"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/nurbcurve",
            json={
                "degree": 3, "periodic": False,
                "control_points": [[0, 0], [5, 10], [10, 0]],
                "knots": [0, 0, 0, 1, 1, 1],
            },
            timeout=30.0,
        )

    def test_create_nurb_curve_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.create_nurb_curve(degree=3, control_points=[[0, 0]], knots=[0, 1])
        assert result == {}

    def test_create_nurb_surface(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"handle": "NS_001", "type": "NurbSurface"})
        result = bridge.create_nurb_surface(
            degree_u=3, degree_v=2, rational=False,
            control_points=[[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
            u_knots=[0, 0, 0, 1, 1, 1],
            v_knots=[0, 0, 1, 1],
            num_control_u=2, num_control_v=2,
        )
        assert result == {"handle": "NS_001", "type": "NurbSurface"}
        bridge._client.request.assert_called_once_with(
            "POST", "/api/entity/nurbsurface",
            json={
                "degree_u": 3, "degree_v": 2,
                "rational": False,
                "control_points": [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
                "u_knots": [0, 0, 0, 1, 1, 1],
                "v_knots": [0, 0, 1, 1],
                "num_control_u": 2, "num_control_v": 2,
            },
            timeout=30.0,
        )

    def test_create_nurb_surface_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.create_nurb_surface(
            control_points=[[0, 0]], u_knots=[0, 1], v_knots=[0, 1],
            num_control_u=1, num_control_v=1,
        )
        assert result == {}

    def test_modify_nurb(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.modify_nurb(handle="NC_001", control_points=[[0, 0], [5, 5], [10, 0]])
        assert result == {"success": True}
        bridge._client.request.assert_called_once_with(
            "PATCH", "/api/entity/nurb",
            json={"handle": "NC_001", "control_points": [[0, 0], [5, 5], [10, 0]]},
            timeout=30.0,
        )

    def test_modify_nurb_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.modify_nurb(handle="BAD") is None

    def test_import_ifc(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.import_ifc("C:/model.ifc") is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/document/import/ifc",
            json={"path": "C:/model.ifc"},
            timeout=30.0,
        )

    def test_import_ifc_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.import_ifc("C:/bad.ifc") is False

    def test_get_ifc_entities(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"entities": [{"handle": "I1", "type": "IfcWall", "layer": "0", "visible": True}], "count": 1}
        )
        result = bridge.get_ifc_entities()
        assert result == [{"handle": "I1", "type": "IfcWall", "layer": "0", "visible": True}]
        bridge._client.request.assert_called_once_with(
            "GET", "/api/document/ifc/entities",
            json=None, timeout=30.0,
        )

    def test_get_ifc_entities_empty(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({})
        result = bridge.get_ifc_entities()
        assert result is None

    def test_get_ifc_entities_no_entities_key(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"count": 0})
        result = bridge.get_ifc_entities()
        assert result is None


# ── MultiCAD API ─────────────────────────────────────────────


class TestMultiCadTools:
    def test_create_grid_axis(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "message": "ok"})
        result = bridge.create_grid_axis("rect", 0, 0, [1000], [1000], "1,2,3", "A,B,C")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/grid-axis",
            json={"type": "rect", "origin_x": 0, "origin_y": 0,
                  "spacings_x": [1000], "spacings_y": [1000],
                  "naming_x": "1,2,3", "naming_y": "A,B,C"},
            timeout=30.0,
        )

    def test_create_grid_axis_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        assert bridge.create_grid_axis() is False

    def test_create_grid_label(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.create_grid_label("GH1", "A", 0, "x")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/grid-label",
            json={"grid_handle": "GH1", "label": "A", "axis_index": 0, "direction": "x"},
            timeout=30.0,
        )

    def test_create_grid_label_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_grid_label("GH1", "A") is False

    def test_create_room(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "message": "ok"})
        result = bridge.create_room(0, 0, 5000, 4000, "Hall")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/room",
            json={"x": 0, "y": 0, "width": 5000, "height": 4000, "name": "Hall"},
            timeout=30.0,
        )

    def test_create_room_without_name(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        result = bridge.create_room(0, 0, 1000, 1000)
        assert result is True
        call_kwargs = bridge._client.request.call_args[1]
        assert "name" not in call_kwargs["json"]

    def test_create_room_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_room(0, 0, 100, 100) is False

    def test_get_room_properties(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"success": True, "room": {"name": "Room1", "area": 25.0}}
        )
        result = bridge.get_room_properties("RM1")
        assert result == {"success": True, "room": {"name": "Room1", "area": 25.0}}
        bridge._client.request.assert_called_once_with(
            "GET", "/api/multicad/room/RM1", json=None, timeout=30.0,
        )

    def test_get_room_properties_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        result = bridge.get_room_properties("BAD")
        assert result is None

    def test_create_custom_object(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "error": None})
        result = bridge.create_custom_object("Wall", {"height": 3000})
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/custom-object",
            json={"class_name": "Wall", "properties": {"height": 3000}},
            timeout=30.0,
        )

    def test_create_custom_object_without_properties(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True})
        assert bridge.create_custom_object("Wall") is True

    def test_create_custom_object_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_custom_object("Wall") is False

    def test_create_parametric_object(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "error": None})
        result = bridge.create_parametric_object("Column", {"width": 400, "depth": 400})
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/parametric",
            json={"type": "Column", "parameters": {"width": 400, "depth": 400}},
            timeout=30.0,
        )

    def test_create_parametric_object_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_parametric_object("Beam") is False

    def test_create_reactor(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "error": None})
        result = bridge.create_reactor("H1", "modified")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/reactor",
            json={"entity_handle": "H1", "event_type": "modified"},
            timeout=30.0,
        )

    def test_create_reactor_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_reactor("H1") is False

    def test_create_2d_break(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "message": "ok"})
        result = bridge.create_2d_break("V1", 100, 200, 300, 400)
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/2d-break",
            json={"view_handle": "V1", "x1": 100, "y1": 200, "x2": 300, "y2": 400},
            timeout=30.0,
        )

    def test_create_2d_break_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_2d_break("V1") is False

    def test_start_motion_preview(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "error": None})
        result = bridge.start_motion_preview("H1")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/motion-preview/start",
            json={"handle": "H1"},
            timeout=30.0,
        )

    def test_start_motion_preview_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        assert bridge.start_motion_preview("H1") is False

    def test_stop_motion_preview(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "message": "ok"})
        result = bridge.stop_motion_preview()
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/motion-preview/stop", json=None, timeout=30.0,
        )

    def test_stop_motion_preview_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.stop_motion_preview() is False

    def test_create_body_contour(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response({"success": True, "error": None})
        result = bridge.create_body_contour("H1")
        assert result is True
        bridge._client.request.assert_called_once_with(
            "POST", "/api/multicad/body-contour",
            json={"solid_handle": "H1"},
            timeout=30.0,
        )

    def test_create_body_contour_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=_mock_response({}, status=400)
        )
        assert bridge.create_body_contour("H1") is False

    def test_check_3d_faces(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.return_value = _mock_response(
            {"success": True, "faces": [{"id": 1, "normal": [0, 0, 1]}], "count": 1}
        )
        result = bridge.check_3d_faces("H1")
        assert result == {"success": True, "faces": [{"id": 1, "normal": [0, 0, 1]}], "count": 1}
        bridge._client.request.assert_called_once_with(
            "GET", "/api/multicad/3d-faces/H1", json=None, timeout=30.0,
        )

    def test_check_3d_faces_failure(self, bridge: HttpCadBridge) -> None:
        bridge._client.request.side_effect = httpx.RequestError("fail")
        result = bridge.check_3d_faces("BAD")
        assert result is None
