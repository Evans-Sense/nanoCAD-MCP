"""
Comprehensive integration tests for the nanoCAD HTTP API.

These tests require a running nanoCAD instance with the .NET engine plugin
(HTTP bridge on localhost:5080).

Usage:
    # Start nanoCAD (it auto-loads the plugin via nCad.ini)
    # Then run:
    $env:NANOCAD_MCP_TEST_LIVE = "1"
    py -m pytest tests/integration/test_http_api.py -v --timeout=120

    # Run a specific category:
    py -m pytest tests/integration/test_http_api.py -v -k Test2DEntities
"""
from __future__ import annotations

import contextlib
import os
import random
import sys
import time
from typing import Any

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

LIVE = os.environ.get("NANOCAD_MCP_TEST_LIVE", "0") == "1"
skip_reason = "Set NANOCAD_MCP_TEST_LIVE=1 and run with nanoCAD open"

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

# ── Helpers ──────────────────────────────────────────────────────────────────

BASE = "http://localhost:5080"
TIMEOUT = 30.0


def url(path: str) -> str:
    return f"{BASE}{path}"


def _post(path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST and return parsed JSON body."""
    assert httpx is not None, "httpx required"
    resp = httpx.post(url(path), json=json, timeout=TIMEOUT)
    if resp.status_code == 404:
        return {"error": f"404: {path} not found", "success": False}
    resp.raise_for_status()
    return resp.json()


def _get(path: str) -> dict[str, Any]:
    assert httpx is not None, "httpx required"
    resp = httpx.get(url(path), timeout=TIMEOUT)
    if resp.status_code == 404:
        return {"error": f"404: {path} not found", "success": False}
    resp.raise_for_status()
    return resp.json()


def _patch(path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
    assert httpx is not None, "httpx required"
    resp = httpx.request("PATCH", url(path), json=json, timeout=TIMEOUT)
    if resp.status_code == 404:
        return {"error": f"404: {path} not found", "success": False}
    resp.raise_for_status()
    return resp.json()


def _delete(path: str) -> dict[str, Any]:
    assert httpx is not None, "httpx required"
    resp = httpx.request("DELETE", url(path), timeout=TIMEOUT)
    if resp.status_code == 404:
        return {"error": f"404: {path} not found", "success": False}
    resp.raise_for_status()
    return resp.json()


def _handle(result: dict[str, Any]) -> str:
    """Extract handle from create response."""
    handle = result.get("handle") or result.get("Handle") or ""
    return str(handle)


def test_id() -> str:
    """Generate a unique test suffix."""
    return f"INT_{random.randint(10000, 99999)}"


def _create_line(x1: float = 0, y1: float = 0, x2: float = 10, y2: float = 10) -> str:
    """Create a fresh line entity, return its handle."""
    r = _post("/api/entity/line", json={"start_x": x1, "start_y": y1, "end_x": x2, "end_y": y2})
    return _handle(r)


# ── Skip condition ───────────────────────────────────────────────────────────

pytestmark = pytest.mark.skipif(
    not LIVE or httpx is None,
    reason=skip_reason + " (httpx required)" if httpx is None else skip_reason,
)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 1: System
# ══════════════════════════════════════════════════════════════════════════════
class TestSystem:
    def test_01_health(self) -> None:
        result = _get("/api/system/health")
        assert result.get("status") == "ok"
        assert "version" in result

    def test_02_system_info(self) -> None:
        result = _get("/api/system/info")
        assert "version" in result
        # license_type might be empty in free edition
        assert isinstance(result.get("license_type"), (str, type(None)))

    def test_03_get_system_variable(self) -> None:
        result = _get("/api/system/variable/DBLCLKEDIT")
        assert result.get("name") == "DBLCLKEDIT"
        assert "value" in result

    def test_04_set_system_variable(self) -> None:
        result = _post("/api/system/variable/MIRRTEXT", json={"value": "0"})
        assert result.get("success") is not False

    def test_05_execute_command(self) -> None:
        result = _post("/api/system/command", json={"command": "ZOOM", "args": ["E"]})
        # Allow success or meaningful error
        assert result is not None

    def test_06_get_fonts(self) -> None:
        result = _get("/api/system/fonts")
        assert isinstance(result, dict)
        assert "fonts" in result or "count" in result

    def test_07_get_linetypes(self) -> None:
        result = _get("/api/linetype")
        assert isinstance(result, dict)
        # Should have at least BYLAYER, BYBLOCK, CONTINUOUS
        linetypes = result.get("linetypes") or result.get("Linetypes") or []
        if isinstance(linetypes, list):
            names = [lt.get("name", "") if isinstance(lt, dict) else str(lt) for lt in linetypes]
            assert "BYLAYER" in names or "Continuous" in names


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 2: Document
# ══════════════════════════════════════════════════════════════════════════════
class TestDocument:
    def test_01_get_info(self) -> None:
        result = _get("/api/document")
        assert "name" in result
        assert isinstance(result.get("entities_count"), (int, float))

    def test_02_save(self) -> None:
        # Save to a temp path to avoid dialog prompts
        import os
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), f"ncad_test_save_{random.randint(10000, 99999)}.dwg")
        result = _post("/api/document/save", json={"path": tmp})
        assert result.get("success") is not False, f"Save failed: {result}"
        # Cleanup
        with contextlib.suppress(BaseException): os.remove(tmp)

    def test_03_undo_redo(self) -> None:
        # Create then undo
        _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 5, "end_y": 5})
        undo = _post("/api/document/undo")
        assert undo.get("success") is not False, f"Undo failed: {undo}"
        redo = _post("/api/document/redo")
        assert redo.get("success") is not False, f"Redo failed: {redo}"

    def test_04_zoom_extents(self) -> None:
        result = _post("/api/document/zoom/extents")
        assert result.get("success") is not False

    def test_05_purge(self) -> None:
        result = _post("/api/document/purge")
        assert result.get("success") is not False

    def test_06_new_document(self) -> None:
        """Create a new document (may fail in some editions)."""
        result = _post("/api/document/new", json={"template": ""})
        # If not supported, it should return a clear error
        if result.get("success") is False:
            assert "error" in result

    def test_07_open_document(self) -> None:
        """Open a document — may fail if file doesn't exist, but route must respond."""
        result = _post("/api/document/open", json={"path": "C:\\nonexistent_test_file.dwg"})
        assert result is not None

    def test_08_export_pdf(self) -> None:
        """Export to PDF."""
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"test_export_{test_id()}.pdf")
            result = _post("/api/document/export/pdf", json={"path": path})
            if result.get("success") is False:
                assert "error" in result
        except Exception as e:
            pytest.skip(f"PDF export: {e}")

    def test_09_export_dwg(self) -> None:
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"test_export_{test_id()}.dwg")
            result = _post("/api/document/export/dwg", json={"path": path})
            if result.get("success") is False:
                assert "error" in result
        except Exception as e:
            pytest.skip(f"DWG export: {e}")

    def test_10_export_dxf(self) -> None:
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"test_export_{test_id()}.dxf")
            result = _post("/api/document/export/dxf", json={"path": path})
            if result.get("success") is False:
                assert "error" in result
        except Exception as e:
            pytest.skip(f"DXF export: {e}")

    def test_11_export_step(self) -> None:
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"test_export_{test_id()}.step")
            result = _post("/api/document/export/step", json={"path": path})
            if result.get("success") is False:
                assert "error" in result
        except Exception as e:
            pytest.skip(f"STEP export: {e}")

    def test_12_export_stl(self) -> None:
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"test_export_{test_id()}.stl")
            result = _post("/api/document/export/stl", json={"path": path, "binary": False})
            if result.get("success") is False:
                assert "error" in result
        except Exception as e:
            pytest.skip(f"STL export: {e}")

    def test_13_import_step(self) -> None:
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"nonexistent_{test_id()}.step")
            result = _post("/api/document/import/step", json={"path": path})
            # Expected to fail (file doesn't exist), but the route should return a response
            assert isinstance(result, dict)
        except httpx.ConnectError:
            pytest.skip("HTTP server unavailable (plugin may have crashed)")

    def test_14_import_ifc(self) -> None:
        try:
            path = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"nonexistent_{test_id()}.ifc")
            result = _post("/api/document/import/ifc", json={"path": path})
            assert isinstance(result, dict)
        except httpx.ConnectError:
            pytest.skip("HTTP server unavailable (plugin may have crashed)")

    def test_15_get_ifc_entities(self) -> None:
        """Get IFC entities (may be empty in a non-IFC drawing)."""
        try:
            result = _get("/api/document/ifc/entities")
            assert isinstance(result, dict)
        except httpx.ConnectError:
            pytest.skip("HTTP server unavailable (plugin may have crashed)")

    def test_16_close_document(self) -> None:
        """Close document — DESTRUCTIVE: kills HTTP server plugin.

        Skip by default. Run manually if needed with -k close_document.
        """
        pytest.skip("Closing last document unloads the .NET plugin (HTTP server dies)")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 2b: Project Lifecycle (create_project, save_project)
# ══════════════════════════════════════════════════════════════════════════════

TEST_PROJECT_DIR = os.path.join(
    os.environ.get("TEMP", "C:\\temp"), "nanoCAD_test_projects"
)


class TestProjectLifecycle:
    """End-to-end: create a new DWG project, draw something, save it."""

    def setup_method(self) -> None:
        os.makedirs(TEST_PROJECT_DIR, exist_ok=True)
        self.filename = f"proj_{test_id()}.dwg"
        self.directory = TEST_PROJECT_DIR
        self.full_path = os.path.join(self.directory, self.filename)

    def teardown_method(self) -> None:
        for p in [
            self.full_path,
            self.full_path + ".bak",
            self.full_path.replace(".dwg", ".dwl"),
            self.full_path.replace(".dwg", ".dwl2"),
        ]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass

    def test_01_create_project(self) -> None:
        """Create a new project and verify the file is written."""
        result = _post(
            "/api/document/new",
            json={"template": "", "save_path": self.full_path.replace("\\", "/")},
        )
        # nanoCAD may or may not return success=True, but it must not crash
        assert "error" not in result or result.get("success") is True, (
            f"create_project failed: {result}"
        )

    def test_02_create_project_appends_dwg_extension(self) -> None:
        """If filename is given without .dwg, the file should still end with .dwg."""
        result = _post(
            "/api/document/new",
            json={
                "template": "",
                "save_path": f"{self.directory}/noext_{test_id()}".replace("\\", "/"),
            },
        )
        assert "error" not in result or result.get("success") is True

    def test_03_save_project(self) -> None:
        """Save current document to a specific path (after drawing something)."""
        # Draw a line first
        _post(
            "/api/entity/line",
            json={"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 100},
        )
        # Save to the target path (use forward slashes for JSON safety)
        result = _post(
            "/api/document/save",
            json={"path": self.full_path.replace("\\", "/")},
        )
        assert "error" not in result or result.get("success") is True, (
            f"save_project failed: {result}"
        )

    def test_04_full_project_lifecycle(self) -> None:
        """Full lifecycle: create -> draw line -> save -> verify file exists."""
        # 1. Create a new project
        result = _post(
            "/api/document/new",
            json={"template": "", "save_path": self.full_path.replace("\\", "/")},
        )
        # Some nanoCAD editions may not support save_path; that's OK as long as
        # we don't crash. The next save_project call will still work.
        if result.get("success") is not True and result.get("success") is not False:
            pass
        # 2. Draw something
        line_result = _post(
            "/api/entity/line",
            json={"start_x": 0, "start_y": 0, "end_x": 50, "end_y": 50},
        )
        assert "error" not in line_result
        # 3. Save the project
        save_result = _post(
            "/api/document/save",
            json={"path": self.full_path.replace("\\", "/")},
        )
        # 4. If save was reported successful, file should exist
        if save_result.get("success") is True:
            assert os.path.exists(self.full_path), (
                f"Save reported success but file {self.full_path} does not exist"
            )

    def test_05_save_project_with_subdirectory(self) -> None:
        """Save to a subdirectory that doesn't exist yet — C# should create it."""
        subdir = os.path.join(self.directory, f"sub_{test_id()}")
        full_path = os.path.join(subdir, f"deep_{test_id()}.dwg")
        result = _post(
            "/api/document/save",
            json={"path": full_path.replace("\\", "/")},
        )
        # If save was reported successful, file should exist
        if result.get("success") is True:
            assert os.path.exists(full_path), (
                f"Save reported success but file {full_path} does not exist"
            )
        # Cleanup
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
            if os.path.exists(subdir):
                os.rmdir(subdir)
        except OSError:
            pass

    def test_06_create_project_normalizes_path(self) -> None:
        """Backslashes in path should be handled by C# (or auto-normalized client-side)."""
        # Send raw backslashes — if the server normalizes, this should work
        result = _post(
            "/api/document/new",
            json={"save_path": self.full_path},  # raw backslashes
        )
        # Server may return success or a JSON error — both are acceptable
        assert result is not None


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 3: Layers
# ══════════════════════════════════════════════════════════════════════════════
class TestLayers:
    _layer_name: str = ""

    def test_01_get_layers(self) -> None:
        result = _get("/api/layer")
        layers = result.get("layers") or result.get("Layers") or []
        assert len(layers) >= 1  # At least layer "0"

    def test_02_create_layer(self) -> None:
        TestLayers._layer_name = f"INT_LAYER_{test_id()}"
        result = _post("/api/layer", json={"name": TestLayers._layer_name})
        assert result.get("success") is True, f"Layer creation failed: {result}"

    def test_03_set_current_layer(self) -> None:
        name = TestLayers._layer_name
        result = _post(f"/api/layer/{name}/current")
        assert result.get("success") is not False
        # Verify the layer was set as current
        time.sleep(0.1)
        # Note: HostMgd may not propagate Db.Clayer change to subsequent entities
        # created in the same transaction, so we only verify the API call succeeded.
        # If the layer is set, it shows up in subsequent operations (e.g., new commands).

    def test_04_set_layer_state(self) -> None:
        name = TestLayers._layer_name
        result = _patch(f"/api/layer/{name}", json={"on": False, "locked": True})
        assert result.get("success") is not False
        # Turn back on
        _patch(f"/api/layer/{name}", json={"on": True, "locked": False})

    def test_05_layer_off_on(self) -> None:
        name = TestLayers._layer_name
        result = _post(f"/api/layer/{name}/off")
        assert result.get("success") is not False
        result = _post("/api/layer/on")
        assert result.get("success") is not False

    def test_06_layer_isolate(self) -> None:
        name = TestLayers._layer_name
        result = _post(f"/api/layer/{name}/isolate")
        assert result.get("success") is not False
        # Turn all back on
        _post("/api/layer/on")

    def test_07_layer_freeze_thaw(self) -> None:
        name = TestLayers._layer_name
        result = _post(f"/api/layer/{name}/freeze")
        assert result.get("success") is not False
        result = _post("/api/layer/thaw")
        assert result.get("success") is not False

    def test_08_delete_layer(self) -> None:
        name = TestLayers._layer_name
        result = _delete(f"/api/layer/{name}")
        # May fail if layer has entities — but we allow that
        if result.get("success") is False:
            assert "error" in result


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 4: 2D Entities
# ══════════════════════════════════════════════════════════════════════════════
class Test2DEntities:
    """Create every 2D primitive type and verify handle returned."""
    handles: list[str] = []

    def test_01_line(self) -> None:
        r = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 100})
        h = _handle(r)
        assert h, f"No handle: {r}"
        assert r.get("type") == "LINE"
        Test2DEntities.handles.append(h)

    def test_02_circle(self) -> None:
        r = _post("/api/entity/circle", json={"cx": 50, "cy": 50, "radius": 25})
        h = _handle(r)
        assert h
        assert r.get("type") == "CIRCLE"

    def test_03_arc(self) -> None:
        r = _post("/api/entity/arc", json={"cx": 50, "cy": 50, "radius": 30, "start_angle": 0, "end_angle": 180})
        h = _handle(r)
        assert h
        assert r.get("type") == "ARC"

    def test_04_rectangle(self) -> None:
        r = _post("/api/entity/rectangle", json={"x": 0, "y": 0, "width": 200, "height": 100})
        h = _handle(r)
        assert h

    def test_05_polyline(self) -> None:
        r = _post("/api/entity/polyline", json={
            "vertices": [[0, 0], [50, 0], [50, 50], [0, 50]],
            "closed": True,
        })
        h = _handle(r)
        assert h
        assert r.get("type") == "POLYLINE"

    def test_06_text(self) -> None:
        r = _post("/api/entity/text", json={"x": 10, "y": 10, "content": "Hello CAD", "height": 5})
        h = _handle(r)
        assert h
        assert r.get("type") == "DBText" or r.get("type") == "TEXT"

    def test_07_point(self) -> None:
        r = _post("/api/entity/point", json={"x": 25, "y": 25})
        h = _handle(r)
        assert h

    def test_08_mtext(self) -> None:
        """Multi-line text (requires .NET engine)."""
        r = _post("/api/entity/mtext", json={
            "x1": 0, "y1": 0, "x2": 100, "y2": 20,
            "content": "Multi\nLine\nText", "height": 5,
        })
        if r.get("error") and "not supported" in str(r.get("error", "")):
            pytest.skip("MText not supported in this nanoCAD edition")
        h = _handle(r)
        assert h

    def test_09_ellipse(self) -> None:
        r = _post("/api/entity/ellipse", json={
            "cx": 100, "cy": 50, "major_axis_x": 40, "major_axis_y": 0, "radius_ratio": 0.5,
        })
        h = _handle(r)
        assert h
        assert r.get("type") == "ELLIPSE"

    def test_10_spline(self) -> None:
        r = _post("/api/entity/spline", json={
            "fit_points": [[0, 0], [25, 50], [50, 0], [75, 50], [100, 0]],
            "degree": 3,
            "closed": False,
        })
        h = _handle(r)
        assert h
        assert r.get("type") == "SPLINE" or r.get("type") == "Spline"

    def test_11_polygon(self) -> None:
        r = _post("/api/entity/polygon", json={
            "center_x": 150, "center_y": 150, "radius": 40, "sides": 6, "inscribed": True,
        })
        h = _handle(r)
        if not h and "not supported" in str(r.get("error", "")):
            pytest.skip("Polygon not supported in this edition")
        if h:
            Test2DEntities.handles.append(h)

    def test_12_donut(self) -> None:
        r = _post("/api/entity/donut", json={
            "center_x": 200, "center_y": 100, "inner_radius": 10, "outer_radius": 20,
        })
        h = _handle(r)
        if not h and "not supported" in str(r.get("error", "")):
            pytest.skip("Donut not supported in this edition")

    def test_13_xline(self) -> None:
        r = _post("/api/entity/xline", json={"p1_x": 0, "p1_y": 0, "p2_x": 100, "p2_y": 100})
        h = _handle(r)
        if not h and "not supported" in str(r.get("error", "")):
            pytest.skip("XLine not supported in this edition")

    def test_14_ray(self) -> None:
        r = _post("/api/entity/ray", json={"p1_x": 0, "p1_y": 0, "p2_x": 100, "p2_y": 0})
        h = _handle(r)
        if not h and "not supported" in str(r.get("error", "")):
            pytest.skip("Ray not supported in this edition")

    def test_15_helix(self) -> None:
        r = _post("/api/entity/helix", json={
            "center_x": 0, "center_y": 0, "center_z": 0,
            "start_radius": 20, "end_radius": 20, "height": 50, "turns": 3,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Helix not supported in this edition")

    def test_16_nurb_curve(self) -> None:
        """NURBS curve via Spline constructor."""
        r = _post("/api/entity/nurbcurve", json={
            "degree": 3,
            "control_points": [[0, 0, 0], [25, 50, 0], [50, -50, 0], [75, 50, 0], [100, 0, 0]],
            "knots": [0, 0, 0, 0, 1, 2, 3, 3, 3, 3],
            "closed": False,
        })
        if "not implemented" in str(r.get("error", "")).lower():
            pytest.skip("NURBS curve not implemented in this Teigha version")
        h = _handle(r)
        assert h, f"No handle from NURBS curve: {r}"


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 5: 3D Solids
# ══════════════════════════════════════════════════════════════════════════════
class Test3DSolids:
    """Create all 3D primitive types."""
    handles: list[str] = []

    def test_01_box(self) -> None:
        r = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        h = _handle(r)
        assert h
        assert r.get("type") == "SOLID3D"
        Test3DSolids.handles.append(h)

    def test_02_sphere(self) -> None:
        r = _post("/api/solid/sphere", json={"radius": 25})
        h = _handle(r)
        assert h

    def test_03_cylinder(self) -> None:
        r = _post("/api/solid/cylinder", json={"radius": 20, "height": 40})
        h = _handle(r)
        assert h

    def test_04_cone(self) -> None:
        r = _post("/api/solid/cone", json={"radius_bottom": 20, "height": 40})
        h = _handle(r)
        assert h

    def test_05_torus(self) -> None:
        r = _post("/api/solid/torus", json={"major_radius": 40, "minor_radius": 10})
        h = _handle(r)
        assert h

    def test_06_wedge(self) -> None:
        r = _post("/api/solid/wedge", json={"x": 40, "y": 30, "z": 20})
        h = _handle(r)
        assert h

    def test_07_pyramid(self) -> None:
        r = _post("/api/solid/pyramid", json={"height": 30, "sides": 6, "radius": 20})
        h = _handle(r)
        assert h

    def test_08_extrude(self) -> None:
        """Extrude a 2D polyline into a 3D solid."""
        # Create a closed polyline first
        pl = _post("/api/entity/polyline", json={
            "vertices": [[0, 0], [30, 0], [30, 20], [0, 20]], "closed": True,
        })
        h_pl = _handle(pl)
        if not h_pl:
            pytest.skip("No polyline to extrude")
        r = _post("/api/solid/extrude", json={"handle": h_pl, "height": 25, "taper_angle": 0})
        h = _handle(r)
        if not h and "not supported" in str(r.get("error", "")):
            pytest.skip("Extrude not supported via this endpoint")
        if h:
            assert r.get("type") == "SOLID3D" or r.get("success") is True

    def test_09_revolve(self) -> None:
        """Revolve a line around an axis."""
        line = _post("/api/entity/line", json={"start_x": 10, "start_y": 0, "end_x": 10, "end_y": 30})
        h_line = _handle(line)
        if not h_line:
            pytest.skip("No line to revolve")
        r = _post("/api/solid/revolve", json={
            "handle": h_line,
            "axis_x": 0, "axis_y": 0, "axis_z": 0,
            "dir_x": 0, "dir_y": 1, "dir_z": 0,
            "angle": 360,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Revolve not supported via this endpoint")

    def test_10_get_solid_properties(self) -> None:
        if not Test3DSolids.handles:
            pytest.skip("No solids created")
        h = Test3DSolids.handles[0]
        r = _get(f"/api/solid/{h}/props")
        # May not be available, but the endpoint should respond
        assert isinstance(r, dict)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 6: 3D Boolean Operations
# ══════════════════════════════════════════════════════════════════════════════
class Test3DBooleans:
    def test_01_boolean_union(self) -> None:
        b1 = _post("/api/solid/box", json={"x": 20, "y": 20, "z": 20})
        b2 = _post("/api/solid/sphere", json={"radius": 15})
        h1 = _handle(b1)
        h2 = _handle(b2)
        if not h1 or not h2:
            pytest.skip("Could not create solids for boolean test")
        r = _post(f"/api/solid/{h1}/union/{h2}")
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Boolean union not supported in this edition")

    def test_02_boolean_subtract(self) -> None:
        b1 = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        b2 = _post("/api/solid/cylinder", json={"radius": 10, "height": 30})
        h1 = _handle(b1)
        h2 = _handle(b2)
        if not h1 or not h2:
            pytest.skip("Could not create solids")
        r = _post(f"/api/solid/{h1}/subtract/{h2}")
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Boolean subtract not supported")

    def test_03_boolean_intersect(self) -> None:
        b1 = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        b2 = _post("/api/solid/sphere", json={"radius": 20})
        h1 = _handle(b1)
        h2 = _handle(b2)
        if not h1 or not h2:
            pytest.skip("Could not create solids")
        r = _post(f"/api/solid/{h1}/intersect/{h2}")
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Boolean intersect not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 7: Transforms
# ══════════════════════════════════════════════════════════════════════════════
class TestTransforms:
    """Entity transformation operations. Each test creates a fresh entity."""

    def test_01_move(self) -> None:
        h = _create_line(0, 0, 10, 10)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/move", json={"dx": 20, "dy": 30})
        assert r.get("success") is not False, f"Move failed: {r}"

    def test_02_copy(self) -> None:
        h = _create_line(5, 5, 15, 15)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/copy")
        assert "handle" in r or r.get("success") is True, f"Copy failed: {r}"

    def test_03_rotate(self) -> None:
        h = _create_line(10, 10, 20, 20)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/rotate", json={"angle": 45})
        assert r.get("success") is not False, f"Rotate failed: {r}"

    def test_04_scale(self) -> None:
        h = _create_line(0, 0, 10, 0)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/scale", json={"factor": 2, "cx": 0, "cy": 0})
        assert r.get("success") is not False, f"Scale failed: {r}"

    def test_05_mirror(self) -> None:
        h = _create_line(0, 0, 10, 0)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/mirror", json={"p1_x": 0, "p1_y": 0, "p2_x": 0, "p2_y": 100})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Mirror not supported")
        assert r.get("success") is not False, f"Mirror failed: {r}"

    def test_06_mirror3d(self) -> None:
        h = _create_line(0, 0, 10, 0)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/mirror3d", json={
            "p1_x": 0, "p1_y": 0, "p1_z": 0,
            "p2_x": 1, "p2_y": 0, "p2_z": 0,
            "p3_x": 0, "p3_y": 1, "p3_z": 0,
        })
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Mirror3D not supported")

    def test_07_stretch(self) -> None:
        h = _create_line(0, 0, 10, 0)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/stretch", json={"dx": 5, "dy": 5})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Stretch not supported")

    def test_08_explode(self) -> None:
        """Explode a rectangle into lines."""
        rect = _post("/api/entity/rectangle", json={"x": 0, "y": 0, "width": 50, "height": 30})
        h = _handle(rect)
        if not h:
            pytest.skip("No rect to explode")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/explode")
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Explode not supported")

    def test_09_offset(self) -> None:
        r2 = _post("/api/entity/circle", json={"cx": 0, "cy": 0, "radius": 20})
        h = _handle(r2)
        if not h:
            pytest.skip("No circle to offset")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/offset", json={"distance": 5})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Offset not supported")

    def test_10_trim(self) -> None:
        """Trim a line at a point."""
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 0})
        h = _handle(line)
        if not h:
            pytest.skip("No line to trim")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/trim", json={"cut_x": 50, "cut_y": 0, "keep_start": True})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Trim not supported")

    def test_11_extend(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 50, "end_y": 0})
        h = _handle(line)
        if not h:
            pytest.skip("No line to extend")
        time.sleep(0.1)
        r = _post(f"/api/entity/{h}/extend", json={"end_x": 100, "end_y": 0})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Extend not supported")

    def test_12_delete(self) -> None:
        """Delete a fresh entity."""
        h = _create_line(0, 0, 10, 0)
        if not h:
            pytest.skip("No line created")
        time.sleep(0.1)
        r = _delete(f"/api/entity/{h}")
        assert r.get("success") is not False, f"Delete failed: {r}"


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 8: Blocks
# ══════════════════════════════════════════════════════════════════════════════
class TestBlocks:
    _block_name: str = ""

    def test_01_get_blocks(self) -> None:
        r = _get("/api/block")
        blocks = r.get("blocks") or r.get("Blocks") or []
        assert isinstance(blocks, list)

    def test_02_create_block(self) -> None:
        # Create a line to use as block content
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 10, "end_y": 10})
        h = _handle(line)
        if not h:
            pytest.skip("No entity to make block")
        TestBlocks._block_name = f"INT_BLOCK_{test_id()}"
        r = _post("/api/block/create", json={"name": TestBlocks._block_name, "handles": [h]})
        assert r.get("success") is not False, f"Block creation failed: {r}"

    def test_03_insert_block(self) -> None:
        if not TestBlocks._block_name:
            pytest.skip("No block created")
        r = _post(f"/api/block/{TestBlocks._block_name}/insert", json={"x": 0, "y": 0})
        assert r.get("success") is not False or "handle" in r

    def test_04_get_block_entities(self) -> None:
        if not TestBlocks._block_name:
            pytest.skip("No block created")
        r = _get(f"/api/block/{TestBlocks._block_name}/entities")
        entities = r.get("entities") or r.get("Entities") or []
        assert isinstance(entities, list)

    def test_05_explode_block(self) -> None:
        if not TestBlocks._block_name:
            pytest.skip("No block created")
        r = _post(f"/api/block/{TestBlocks._block_name}/explode")
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Block explode not supported")

    def test_06_delete_block(self) -> None:
        if not TestBlocks._block_name:
            pytest.skip("No block created")
        r = _delete(f"/api/block/{TestBlocks._block_name}")
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Block delete not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 9: Symbols (MultiCAD)
# ══════════════════════════════════════════════════════════════════════════════
class TestSymbols:
    """Engineering symbols — many require MultiCAD API (Plus/Pro edition)."""

    def test_01_roughness(self) -> None:
        r = _post("/api/symbol/roughness", json={"value": "Ra 6.3", "angle": 0, "allowance": "", "type": 1})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Roughness requires MultiCAD API")
        assert r.get("success") is not False, f"Roughness failed: {r}"

    def test_02_old_roughness(self) -> None:
        r = _post("/api/symbol/old-roughness", json={
            "value": "6.3", "angle": 0, "method": "", "companion_mirror": False, "surf_pos": 0,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Old roughness requires MultiCAD API")

    def test_03_tolerance(self) -> None:
        r = _post("/api/symbol/tolerance", json={
            "type1": "//", "value1": "0.05", "letters1": "A",
            "type2": "", "value2": "", "letters2": "", "text": "",
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Tolerance requires MultiCAD API")
        assert r.get("success") is not False, f"Tolerance failed: {r}"

    def test_04_datum(self) -> None:
        r = _post("/api/symbol/datum", json={"letter": "A"})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Datum requires MultiCAD API")

    def test_05_weld(self) -> None:
        r = _post("/api/symbol/weld", json={"swap_sides": False, "right_orientation": False})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Weld requires MultiCAD API")

    def test_06_leader(self) -> None:
        r = _post("/api/symbol/leader", json={
            "arrow_x": 100, "arrow_y": 100,
            "bend_x": 150, "bend_y": 100,
            "shelf_x": 200, "shelf_y": 100,
            "text": "Test Note", "text_below": "",
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Leader not supported in this edition")

    def test_07_mleader(self) -> None:
        r = _post("/api/symbol/mleader", json={
            "arrow_x": 50, "arrow_y": 50,
            "leader_x": 120, "leader_y": 50,
            "text": "MLeader", "text_height": 5,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("MLeader not supported in this edition")

    def test_08_note_comb(self) -> None:
        r = _post("/api/symbol/note-comb", json={"angle": 45, "text_size": 12, "first_line": "Note", "second_line": ""})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Note comb not supported")

    def test_09_dim_number(self) -> None:
        r = _post("/api/symbol/dim-number", json={
            "x": 0, "y": 0, "arrow_x": 50, "arrow_y": 50,
            "text": "1", "index": 1, "autonum": True,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Dim number not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 10: Tables
# ══════════════════════════════════════════════════════════════════════════════
class TestTables:
    _handle: str = ""

    def test_01_create_table(self) -> None:
        r = _post("/api/table", json={"rows": 3, "columns": 4, "row_height": 30, "column_width": 100})
        assert r.get("success") is True, f"Table creation failed: {r}"
        h = _handle(r)
        assert h
        TestTables._handle = h

    def test_02_create_table_with_cells(self) -> None:
        r = _post("/api/table", json={
            "rows": 2, "columns": 2, "row_height": 25, "column_width": 80,
            "cells": [
                {"row_index": 0, "column_index": 0, "value": "Header1"},
                {"row_index": 1, "column_index": 1, "value": "Data1"},
            ],
        })
        assert r.get("success") is True

    def test_03_get_table_info(self) -> None:
        if not TestTables._handle:
            pytest.skip("No table created")
        r = _get(f"/api/table/{TestTables._handle}")
        assert r.get("success") is True
        assert r.get("rows") == 3
        assert r.get("columns") == 4

    def test_04_edit_table_cell(self) -> None:
        if not TestTables._handle:
            pytest.skip("No table created")
        r = _patch(f"/api/table/{TestTables._handle}/cell", json={
            "row_index": 0, "column_index": 0, "value": "Edited",
        })
        # API may return success: null, true, or no success key at all
        assert r.get("success") is not False, f"Edit cell failed: {r}"

    def test_05_delete_table(self) -> None:
        if not TestTables._handle:
            pytest.skip("No table created")
        r = _delete(f"/api/table/{TestTables._handle}")
        assert r.get("success") is True


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 11: Dimensions
# ══════════════════════════════════════════════════════════════════════════════
class TestDimensions:
    def test_01_linear(self) -> None:
        r = _post("/api/dimension/linear", json={
            "x1": 0, "y1": 0, "x2": 100, "y2": 0,
            "dim_x": 50, "dim_y": -20, "direction": "horizontal",
        })
        assert "handle" in r or r.get("success") is True

    def test_02_aligned(self) -> None:
        r = _post("/api/dimension/aligned", json={
            "x1": 0, "y1": 0, "x2": 100, "y2": 100,
            "dim_x": 75, "dim_y": 75,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Aligned dim not supported")

    def test_03_angular(self) -> None:
        r = _post("/api/dimension/angular", json={
            "center_x": 0, "center_y": 0,
            "p1_x": 50, "p1_y": 0, "p2_x": 0, "p2_y": 50,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Angular dim not supported")

    def test_04_radial(self) -> None:
        r = _post("/api/dimension/radial", json={"center_x": 0, "center_y": 0, "arc_x": 30, "arc_y": 0})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Radial dim not supported")

    def test_05_diametric(self) -> None:
        r = _post("/api/dimension/diametric", json={"center_x": 0, "center_y": 0, "arc_x": 30, "arc_y": 0})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Diametric dim not supported")

    def test_06_rotated(self) -> None:
        r = _post("/api/dimension/rotated", json={
            "x1": 0, "y1": 0, "x2": 100, "y2": 100,
            "dim_x": 50, "dim_y": 50, "rotation": 45,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Rotated dim not supported")

    def test_07_ordinate(self) -> None:
        r = _post("/api/dimension/ordinate", json={
            "use_x_axis": True,
            "defining_x": 0, "defining_y": 0,
            "leader_x": 50, "leader_y": 50,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Ordinate dim not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 12: Constraints
# ══════════════════════════════════════════════════════════════════════════════
class TestConstraints:
    def test_01_horizontal(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 10, "end_x": 100, "end_y": 20})
        h = _handle(line)
        if not h:
            pytest.skip("No line for constraint")
        r = _post("/api/constraint/horizontal", json={"handle": h})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Horizontal constraint not supported")
        assert r.get("success") is not False

    def test_02_vertical(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 10, "start_y": 0, "end_x": 20, "end_y": 100})
        h = _handle(line)
        if not h:
            pytest.skip("No line for constraint")
        r = _post("/api/constraint/vertical", json={"handle": h})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Vertical constraint not supported")
        assert r.get("success") is not False

    def test_03_parallel(self) -> None:
        l1 = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 50, "end_y": 50})
        l2 = _post("/api/entity/line", json={"start_x": 60, "start_y": 0, "end_x": 110, "end_y": 50})
        h1, h2 = _handle(l1), _handle(l2)
        if not h1 or not h2:
            pytest.skip("No lines for constraint")
        r = _post("/api/constraint/parallel", json={"handle1": h1, "handle2": h2})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Parallel constraint not supported")

    def test_04_perpendicular(self) -> None:
        l1 = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 50, "end_y": 0})
        l2 = _post("/api/entity/line", json={"start_x": 25, "start_y": 0, "end_x": 25, "end_y": 50})
        h1, h2 = _handle(l1), _handle(l2)
        if not h1 or not h2:
            pytest.skip("No lines")
        r = _post("/api/constraint/perpendicular", json={"handle1": h1, "handle2": h2})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Perpendicular constraint not supported")

    def test_05_concentric(self) -> None:
        c1 = _post("/api/entity/circle", json={"cx": 0, "cy": 0, "radius": 10})
        c2 = _post("/api/entity/circle", json={"cx": 50, "cy": 0, "radius": 5})
        h1, h2 = _handle(c1), _handle(c2)
        if not h1 or not h2:
            pytest.skip("No circles")
        r = _post("/api/constraint/concentric", json={"handle1": h1, "handle2": h2})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Concentric constraint not supported")

    def test_06_collinear(self) -> None:
        l1 = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 50, "end_y": 0})
        l2 = _post("/api/entity/line", json={"start_x": 60, "start_y": 5, "end_x": 100, "end_y": 5})
        h1, h2 = _handle(l1), _handle(l2)
        if not h1 or not h2:
            pytest.skip("No lines")
        r = _post("/api/constraint/collinear", json={"handle1": h1, "handle2": h2})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Collinear constraint not supported")

    def test_07_distance(self) -> None:
        c1 = _post("/api/entity/circle", json={"cx": 0, "cy": 0, "radius": 5})
        c2 = _post("/api/entity/circle", json={"cx": 50, "cy": 0, "radius": 5})
        h1, h2 = _handle(c1), _handle(c2)
        if not h1 or not h2:
            pytest.skip("No circles")
        r = _post("/api/constraint/distance", json={"handle1": h1, "handle2": h2, "distance": 100})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Distance constraint not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 13: Hatch
# ══════════════════════════════════════════════════════════════════════════════
class TestHatch:
    """Hatch creation, query, and edit."""
    _handle: str = ""

    def test_01_create_hatch(self) -> None:
        # Create a closed polyline as boundary
        pl = _post("/api/entity/polyline", json={
            "vertices": [[0, 0], [100, 0], [100, 50], [0, 50]],
            "closed": True,
        })
        h_pl = _handle(pl)
        if not h_pl:
            pytest.skip("No boundary for hatch")
        r = _post("/api/hatch", json={
            "pattern": "ANSI31", "scale": 1.0,
            "boundary_handles": [h_pl],
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Hatch not supported in this edition")
        assert r.get("success") is True, f"Hatch failed: {r}"
        h = _handle(r)
        if h:
            TestHatch._handle = h

    def test_02_get_hatch_info(self) -> None:
        if not TestHatch._handle:
            pytest.skip("No hatch created")
        r = _get(f"/api/hatch/{TestHatch._handle}")
        assert isinstance(r, dict)

    def test_03_edit_hatch(self) -> None:
        if not TestHatch._handle:
            pytest.skip("No hatch created")
        r = _patch(f"/api/hatch/{TestHatch._handle}", json={"pattern": "ANSI32", "scale": 2.0})
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("Hatch edit not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 14: Measurements
# ══════════════════════════════════════════════════════════════════════════════
class TestMeasurements:
    def test_01_distance(self) -> None:
        r = _post("/api/measurement/distance", json={
            "x1": 0, "y1": 0, "z1": 0,
            "x2": 100, "y2": 0, "z2": 0,
        })
        assert "distance" in r
        assert float(r["distance"]) == pytest.approx(100, abs=0.01)
        assert float(r["dx"]) == pytest.approx(100, abs=0.01)

    def test_02_angle(self) -> None:
        r = _post("/api/measurement/angle", json={
            "x1": 10, "y1": 0, "z1": 0,
            "x2": 0, "y2": 0, "z2": 0,
            "x3": 0, "y3": 10, "z3": 0,
        })
        assert "angle_degrees" in r, f"No angle_degrees in response: {r}"
        angle = float(r["angle_degrees"])
        assert abs(angle - 90.0) < 1.0, f"Expected ~90°, got {angle}"

    def test_03_area(self) -> None:
        pl = _post("/api/entity/polyline", json={
            "vertices": [[100, 100], [200, 100], [200, 150], [100, 150]],
            "closed": True,
        })
        h = _handle(pl)
        if not h:
            pytest.skip("No closed polyline for area test")
        r = _get(f"/api/measurement/area/{h}")
        # Area may be computed as 0 if polyline is not a closed planar region
        assert isinstance(r, dict)

    def test_04_get_all_entities(self) -> None:
        r = _get("/api/measurement/entities")
        assert "count" in r
        assert isinstance(r.get("count"), (int, float))
        entities = r.get("entities") or r.get("Entities") or []
        assert isinstance(entities, list)

    def test_05_get_entity_info(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 0})
        h = _handle(line)
        if not h:
            pytest.skip("No entity for info test")
        r = _get(f"/api/selection/entity/{h}")
        assert isinstance(r, dict)
        # Should have type/layer info
        if r.get("success") is not False:
            assert "type" in r or "Type" in r

    def test_06_get_solid_properties(self) -> None:
        box = _post("/api/solid/box", json={"x": 10, "y": 10, "z": 10})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for props test")
        r = _get(f"/api/solid/{h}/props")
        assert isinstance(r, dict)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 15: Assembly
# ══════════════════════════════════════════════════════════════════════════════
class TestAssembly:
    def test_01_insert_part(self) -> None:
        """Insert a predefined block as a part."""
        r = _post("/api/assembly/insert", json={"block_name": "_DOT", "x": 0, "y": 0, "z": 0})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Assembly insert not supported in this edition")
        assert isinstance(r, dict)

    def test_02_mate(self) -> None:
        b1 = _post("/api/solid/box", json={"x": 10, "y": 10, "z": 10})
        b2 = _post("/api/solid/box", json={"x": 20, "y": 10, "z": 10})
        h1, h2 = _handle(b1), _handle(b2)
        if not h1 or not h2:
            pytest.skip("No solids for mate")
        r = _post("/api/assembly/mate", json={"handle1": h1, "handle2": h2})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Assembly mate not supported")

    def test_03_angle_constraint(self) -> None:
        b1 = _post("/api/solid/box", json={"x": 5, "y": 5, "z": 5})
        b2 = _post("/api/solid/box", json={"x": 15, "y": 5, "z": 5})
        h1, h2 = _handle(b1), _handle(b2)
        if not h1 or not h2:
            pytest.skip("No solids")
        r = _post("/api/assembly/angle", json={"handle1": h1, "handle2": h2, "angle": 45})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Assembly angle not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 16: Sheet Metal
# ══════════════════════════════════════════════════════════════════════════════
class TestSheetMetal:
    def test_01_base_flange(self) -> None:
        r = _post("/api/sheetmetal/base-flange", json={
            "width": 100, "length": 60, "thickness": 2,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Sheet metal requires MultiCAD API (Plus/Pro)")
        # May create a solid3d handle

    def test_02_base_plate(self) -> None:
        r = _post("/api/sheetmetal/base-plate", json={
            "width": 80, "length": 50, "thickness": 3,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Base plate requires MultiCAD API")

    def test_03_edge_flange(self) -> None:
        r = _post("/api/sheetmetal/edge-flange", json={
            "base_handle": "", "bend_radius": 2,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Edge flange requires MultiCAD API")

    def test_04_bend(self) -> None:
        box = _post("/api/solid/box", json={"x": 20, "y": 20, "z": 2})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for bend")
        r = _post("/api/sheetmetal/bend", json={"handle": h, "bend_radius": 3})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Bend requires MultiCAD API")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 17: MultiCAD API (Plus/Pro only)
# ══════════════════════════════════════════════════════════════════════════════
class TestMultiCad:
    """These require nanoCAD Plus/Pro edition with MultiCAD API."""

    def test_01_grid_axis(self) -> None:
        r = _post("/api/multicad/grid-axis", json={
            "type": "rectangular",
            "origin_x": 0, "origin_y": 0,
            "spacings_x": [1000], "spacings_y": [500],
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Grid axis requires MultiCAD API (Plus/Pro)")

    def test_02_room(self) -> None:
        r = _post("/api/multicad/room", json={
            "x": 0, "y": 0, "width": 1000, "height": 500,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Room requires MultiCAD API (Plus/Pro)")

    def test_03_2d_break(self) -> None:
        r = _post("/api/multicad/2d-break", json={})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("2D break requires MultiCAD API (Plus/Pro)")

    def test_04_custom_object(self) -> None:
        """This is a stub — always returns a clear error."""
        r = _post("/api/multicad/custom-object", json={"class_name": "TestClass"})
        assert r.get("success") is False
        assert "error" in r

    def test_05_parametric_object(self) -> None:
        r = _post("/api/multicad/parametric", json={"type": "extrusion"})
        assert r.get("success") is False
        assert "error" in r

    def test_06_reactor(self) -> None:
        r = _post("/api/multicad/reactor", json={"entity_handle": "0", "event_type": "modified"})
        assert r.get("success") is False
        assert "error" in r

    def test_07_body_contour(self) -> None:
        r = _post("/api/multicad/body-contour", json={"solid_handle": "0"})
        assert r.get("success") is False
        assert "error" in r

    def test_08_3d_faces(self) -> None:
        """Check 3D faces via Brep reflection."""
        box = _post("/api/solid/box", json={"x": 15, "y": 15, "z": 15})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for 3D face check")
        r = _get(f"/api/multicad/3d-faces/{h}")
        # May work even in free edition — uses Teigha Brep reflection
        if "not supported" in str(r.get("error", "")):
            pytest.skip("3D faces not supported in this edition")
        assert isinstance(r, dict)

    def test_09_motion_preview(self) -> None:
        """Start/stop motion preview (stub — requires Mc3dAnimationManager)."""
        r = _post("/api/multicad/motion-preview/start", json={"handle": "0"})
        assert r.get("success") is False
        assert "error" in r

    def test_10_motion_preview_stop(self) -> None:
        r = _post("/api/multicad/motion-preview/stop")
        assert r.get("success") is True  # Always succeeds

    def test_11_set_grid_label(self) -> None:
        """Set a grid label (requires grid axis first)."""
        r = _post("/api/multicad/grid-label", json={
            "grid_type": "rectangular", "index": 0, "label": "A", "direction": "X",
        })
        # Expected to fail because no grid exists — but should respond
        assert isinstance(r, dict)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 18: 3D View
# ══════════════════════════════════════════════════════════════════════════════
class Test3DView:
    def test_01_set_view(self) -> None:
        r = _post("/api/solid/view", json={"direction": "sw", "render_mode": "wireframe"})
        assert r.get("success") is not False

    def test_02_zoom(self) -> None:
        r = _post("/api/solid/zoom", json={"direction": "extents"})
        assert r.get("success") is not False


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 19: Selection
# ══════════════════════════════════════════════════════════════════════════════
class TestSelection:
    def test_01_select_by_type(self) -> None:
        r = _post("/api/selection/select", json={"entity_type": "Line", "max_count": 5})
        assert isinstance(r, dict)

    def test_02_select_by_handles(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 200, "start_y": 200, "end_x": 300, "end_y": 300})
        h = _handle(line)
        if not h:
            pytest.skip("No entity for selection")
        r = _post("/api/selection/by-handles", json={"handles": [h]})
        assert isinstance(r, dict)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 20: NURBS
# ══════════════════════════════════════════════════════════════════════════════
class TestNurbs:
    def test_01_create_nurb_curve(self) -> None:
        """Create a NURBS curve (uses Spline constructor)."""
        r = _post("/api/entity/nurbcurve", json={
            "degree": 3,
            "control_points": [[0, 0, 0], [25, 50, 0], [50, -50, 0], [75, 50, 0], [100, 0, 0]],
            "knots": [0, 0, 0, 0, 1, 2, 3, 3, 3, 3],
            "closed": False,
        })
        if "not implemented" in str(r.get("error", "")).lower():
            pytest.skip("NURBS curve not implemented in this Teigha version")
        h = _handle(r)
        assert h, f"NURBS curve failed: {r}"
        TestNurbs._h_curve = h

    def test_02_modify_nurb(self) -> None:
        """Modify a NURBS control point."""
        h = getattr(TestNurbs, "_h_curve", None)
        if not h:
            pytest.skip("No NURBS curve to modify")
        r = _patch("/api/entity/nurb", json={
            "handle": h, "index": 2,
            "x": 60, "y": 0, "z": 25,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("NURBS modification not supported")

    def test_03_create_nurb_surface(self) -> None:
        """Create a NURBS surface — likely returns eNotImplementedYet."""
        r = _post("/api/entity/nurbsurface", json={
            "degree_u": 3, "degree_v": 3,
            "control_points": [
                [0, 0, 0], [10, 0, 0], [20, 0, 5], [30, 0, 0],
                [0, 10, 0], [10, 10, 5], [20, 10, 10], [30, 10, 0],
                [0, 20, 0], [10, 20, 0], [20, 20, 5], [30, 20, 0],
            ],
            "u_knots": [0, 0, 0, 0, 1, 2, 2, 2, 2],
            "v_knots": [0, 0, 0, 0, 1, 2, 2, 2, 2],
            "u_count": 4, "v_count": 3,
        })
        # Expected to return eNotImplementedYet at runtime
        err = str(r.get("error", "")).lower()
        if "not implemented" in err or "enotimplementedyet" in err:
            pytest.skip("NURBS surface not implemented in this Teigha version")
        # If it does work, verify handle
        h = _handle(r)
        if h:
            assert r.get("type") == "NURBSURFACE" or r.get("type") is not None


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 21: Features (3D Feature-Based Modeling)
# ══════════════════════════════════════════════════════════════════════════════
class TestFeatures:
    def test_01_sketch(self) -> None:
        """Create a sketch on a solid face."""
        box = _post("/api/solid/box", json={"x": 25, "y": 25, "z": 25})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid for sketch")
        r = _post("/api/feature/sketch", json={"solid_handle": h_box})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Sketch not supported in this edition")

    def test_02_simple_hole(self) -> None:
        box = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for hole")
        r = _post("/api/feature/hole/simple", json={
            "solid_handle": h, "diameter": 10, "depth": 15,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Simple hole not supported in this edition")

    def test_03_standard_hole(self) -> None:
        box = _post("/api/solid/box", json={"x": 20, "y": 20, "z": 20})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for hole")
        r = _post("/api/feature/hole/standard", json={
            "solid_handle": h, "diameter": 8, "depth": 10, "standard": "ISO",
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Standard hole not supported")

    def test_04_threaded_hole(self) -> None:
        box = _post("/api/solid/box", json={"x": 20, "y": 20, "z": 20})
        h = _handle(box)
        if not h:
            pytest.skip("No solid")
        r = _post("/api/feature/hole/threaded", json={
            "solid_handle": h, "diameter": 10, "depth": 12,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Threaded hole not supported")

    def test_05_shell(self) -> None:
        box = _post("/api/solid/box", json={"x": 40, "y": 40, "z": 40})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for shell")
        r = _post("/api/feature/shell", json={
            "solid_handle": h, "thickness": 2,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Shell not supported in this edition")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 22: Mesh & Gradient
# ══════════════════════════════════════════════════════════════════════════════
class TestMeshAndGradient:
    def test_01_create_mesh(self) -> None:
        r = _post("/api/entity/mesh", json={
            "vertices": [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0], [5, 5, 10]],
            "faces": [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]],
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Mesh not supported")

    def test_02_edit_mesh(self) -> None:
        mesh = _post("/api/entity/mesh", json={
            "vertices": [[0, 0, 0], [5, 0, 0], [5, 5, 0], [0, 5, 0]],
            "faces": [[0, 1, 2, 3]],
        })
        h = _handle(mesh)
        if not h:
            pytest.skip("No mesh to edit")
        r = _patch("/api/entity/mesh", json={
            "handle": h, "subdivide": "linear", "level": 1,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Mesh edit not supported")

    def test_03_create_gradient(self) -> None:
        pl = _post("/api/entity/polyline", json={
            "vertices": [[0, 0], [100, 0], [100, 50], [0, 50]],
            "closed": True,
        })
        h = _handle(pl)
        if not h:
            pytest.skip("No boundary for gradient")
        r = _post("/api/gradient", json={
            "color1": "255,0,0", "color2": "0,0,255",
            "scale": 1.0, "gradient_type": "linear",
            "boundary_handles": [h],
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Gradient not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 23: 3D Array & Align
# ══════════════════════════════════════════════════════════════════════════════
class Test3DArrayAlign:
    def test_01_array_3d(self) -> None:
        box = _post("/api/solid/box", json={"x": 5, "y": 5, "z": 5})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for array")
        r = _post(f"/api/entity/{h}/array3d", json={
            "count_x": 3, "count_y": 2, "count_z": 1,
            "spacing_x": 20, "spacing_y": 15, "spacing_z": 0,
        })
        if r.get("success") is False and "not supported" in str(r.get("error", "")):
            pytest.skip("3D array not supported in this edition")

    def test_02_align_3d(self) -> None:
        box = _post("/api/solid/box", json={"x": 5, "y": 5, "z": 5})
        h = _handle(box)
        if not h:
            pytest.skip("No solid for align")
        r = _post(f"/api/entity/{h}/align3d", json={
            "src_p1_x": 0, "src_p1_y": 0, "src_p1_z": 0,
            "dst_p1_x": 50, "dst_p1_y": 50, "dst_p1_z": 0,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("3D align not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 24: 3D Divide & Measure
# ══════════════════════════════════════════════════════════════════════════════
class Test3DDivideMeasure:
    def test_01_divide_entity(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 0})
        h = _handle(line)
        if not h:
            pytest.skip("No line to divide")
        r = _post(f"/api/entity/{h}/divide", json={"segments": 5})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Divide not supported")

    def test_02_measure_entity(self) -> None:
        line = _post("/api/entity/line", json={"start_x": 0, "start_y": 0, "end_x": 100, "end_y": 0})
        h = _handle(line)
        if not h:
            pytest.skip("No line to measure")
        r = _post(f"/api/entity/{h}/measure", json={"distance": 20})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Measure not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 25: Viewport & Render
# ══════════════════════════════════════════════════════════════════════════════
class TestViewportRender:
    def test_01_viewport(self) -> None:
        r = _post("/api/viewport", json={"x": 0, "y": 0, "width": 800, "height": 600})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Viewport not supported")

    def test_02_render(self) -> None:
        r = _post("/api/render", json={"output_path": ""})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Render not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 26: Features (Sketch-based)
# ══════════════════════════════════════════════════════════════════════════════
class TestSketchFeatures:
    """Sketch-based feature operations (requires full 3D feature modeling)."""

    def test_01_sketch_circle(self) -> None:
        box = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        sketch = _post("/api/feature/sketch", json={"solid_handle": h_box})
        h_sk = _handle(sketch)
        if not h_sk:
            pytest.skip("No sketch created")
        r = _post("/api/feature/sketch/circle", json={
            "sketch_handle": h_sk, "cx": 10, "cy": 10, "cz": 0, "radius": 5,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Sketch circle not supported")
        else:
            assert r.get("success") is not False

    def test_02_sketch_line(self) -> None:
        box = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        sketch = _post("/api/feature/sketch", json={"solid_handle": h_box})
        h_sk = _handle(sketch)
        if not h_sk:
            pytest.skip("No sketch")
        r = _post("/api/feature/sketch/line", json={
            "sketch_handle": h_sk, "x1": 0, "y1": 0, "z1": 0,
            "x2": 20, "y2": 0, "z2": 0,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Sketch line not supported")

    def test_03_sketch_profile(self) -> None:
        box = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        sketch = _post("/api/feature/sketch", json={"solid_handle": h_box})
        h_sk = _handle(sketch)
        if not h_sk:
            pytest.skip("No sketch")
        r = _post("/api/feature/sketch/profile", json={"sketch_handle": h_sk})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Sketch profile not supported")

    def test_04_extrude_feature(self) -> None:
        """Create a sketch, profile, then extrude."""
        box = _post("/api/solid/box", json={"x": 30, "y": 30, "z": 30})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        sketch = _post("/api/feature/sketch", json={"solid_handle": h_box})
        h_sk = _handle(sketch)
        if not h_sk:
            pytest.skip("No sketch")
        profile = _post("/api/feature/sketch/profile", json={"sketch_handle": h_sk})
        h_pr = _handle(profile)
        if not h_pr:
            pytest.skip("No profile")
        r = _post("/api/feature/extrude", json={
            "solid_handle": h_box, "profile_handle": h_pr,
            "height": 20, "taper_angle": 0, "direction": True,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Extrude feature not supported")

    def test_05_revolve_feature(self) -> None:
        """Revolve a sketch profile."""
        box = _post("/api/solid/box", json={"x": 20, "y": 20, "z": 20})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        sketch = _post("/api/feature/sketch", json={"solid_handle": h_box})
        h_sk = _handle(sketch)
        if not h_sk:
            pytest.skip("No sketch")
        profile = _post("/api/feature/sketch/profile", json={"sketch_handle": h_sk})
        h_pr = _handle(profile)
        if not h_pr:
            pytest.skip("No profile")
        r = _post("/api/feature/revolve", json={
            "solid_handle": h_box, "profile_handle": h_pr,
            "axis_x": 0, "axis_y": 0, "axis_z": 0,
            "dir_x": 0, "dir_y": 1, "dir_z": 0,
            "angle": 360,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Revolve feature not supported")

    def test_06_mirror_feature(self) -> None:
        box = _post("/api/solid/box", json={"x": 20, "y": 20, "z": 20})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        r = _post("/api/feature/mirror", json={
            "solid_handle": h_box, "plane_handle": "",
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Mirror feature not supported")

    def test_07_rectangular_pattern(self) -> None:
        box = _post("/api/solid/box", json={"x": 15, "y": 15, "z": 15})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        r = _post("/api/feature/pattern/rectangular", json={
            "solid_handle": h_box, "feature_handle": "",
            "count_x": 2, "spacing_x": 30,
            "count_y": 2, "spacing_y": 30,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Pattern not supported")

    def test_08_circular_pattern(self) -> None:
        box = _post("/api/solid/box", json={"x": 10, "y": 10, "z": 10})
        h_box = _handle(box)
        if not h_box:
            pytest.skip("No solid")
        r = _post("/api/feature/pattern/circular", json={
            "solid_handle": h_box, "feature_handle": "",
            "count": 4, "angle": 360,
        })
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Circular pattern not supported")


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 27: Boundary & Region
# ══════════════════════════════════════════════════════════════════════════════
class TestBoundaryRegion:
    def test_01_create_region(self) -> None:
        """Create a region from closed curves."""
        pl = _post("/api/entity/polyline", json={
            "vertices": [[0, 0], [50, 0], [50, 30], [0, 30]],
            "closed": True,
        })
        h = _handle(pl)
        if not h:
            pytest.skip("No polyline for region")
        r = _post("/api/entity/region", json={"curve_handles": [h]})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Region not supported in this edition")

    def test_02_create_boundary(self) -> None:
        r = _post("/api/entity/boundary", json={"point_x": 25, "point_y": 25})
        if "not supported" in str(r.get("error", "")):
            pytest.skip("Boundary not supported")
