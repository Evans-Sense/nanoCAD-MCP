from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_ENGINE_PORT = 5080
HEALTH_CHECK_TIMEOUT = 2.0  # seconds
REQUEST_TIMEOUT = 30.0  # seconds for long operations


def _read_port_file() -> int | None:
    """Read the engine port from a well-known temp file.

    The .NET plugin writes its listening port to %TEMP%\\ncad-mcp-port.txt
    for auto-discovery.
    """
    port_file = Path.home() / "AppData" / "Local" / "Temp" / "ncad-mcp-port.txt"
    try:
        if port_file.exists():
            text = port_file.read_text().strip()
            return int(text)
    except (ValueError, OSError) as e:
        logger.warning("Cannot read port file %s: %s", port_file, e)
    return None


class HttpCadBridge:
    """HTTP client to the .NET plugin running inside nanoCAD.

    Communicates via REST JSON API on localhost.
    """

    def __init__(self, port: int | None = None) -> None:
        self._port = port or _read_port_file() or DEFAULT_ENGINE_PORT
        self._base_url = f"http://localhost:{self._port}"
        self._client: httpx.Client | None = None
        self._available: bool = False

    # ── Lifecycle ──────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect to the engine. Returns True if engine is reachable."""
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=HEALTH_CHECK_TIMEOUT,
        )
        try:
            resp = self._client.get("/api/system/health")
            if resp.status_code == 200:
                self._available = True
                logger.info(
                    "Connected to .NET engine at %s — version: %s",
                    self._base_url,
                    resp.json().get("version", "unknown"),
                )
                return True
        except httpx.ConnectError:
            logger.info(
                "Engine not reachable at %s — will use COM fallback",
                self._base_url,
            )
        except Exception as e:
            logger.warning("Engine health check failed: %s", e)
        self._available = False
        return False

    def close(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
        self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    # ── Generic Request ────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        timeout: float = REQUEST_TIMEOUT,
    ) -> dict[str, Any] | None:
        if not self._client:
            return None
        try:
            resp = self._client.request(method, path, json=json_body, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            logger.warning("Connection refused %s %s: %s", method, path, e)
            self._available = False
            return None
        except httpx.TimeoutException as e:
            logger.warning("Timeout %s %s after %.1fs: %s", method, path, timeout, e)
            # Don't mark unavailable — timeout is per-request, next may succeed
            return None
        except httpx.HTTPStatusError as e:
            body = e.response.text if e.response else ""
            logger.error(
                "HTTP %s %s -> %s: %s",
                method,
                path,
                e.response.status_code if e.response else "?",
                body,
            )
            return None
        except httpx.RequestError as e:
            logger.warning("HTTP request failed %s %s: %s", method, path, e)
            return None
        except json.JSONDecodeError as e:
            logger.exception("Invalid JSON response %s %s: %s", method, path, e)
            return None

    # ── Health ─────────────────────────────────────────────────

    def check_health(self) -> dict[str, Any] | None:
        return self._request("GET", "/api/system/health", timeout=HEALTH_CHECK_TIMEOUT)

    # ── Entity operations ──────────────────────────────────────

    def create_entity(self, entity_type: str, params: dict[str, Any]) -> str | None:
        result = self._request("POST", f"/api/entity/{entity_type.lower()}", json_body=params)
        if result and "handle" in result:
            return str(result["handle"])
        logger.error("create_entity(%s) failed: %s", entity_type, result)
        return None

    def delete_entity(self, handle: str) -> bool:
        result = self._request("DELETE", f"/api/entity/{handle}")
        return result is not None

    def get_entity(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/entity/{handle}")

    def move_entity(self, handle: str, dx: float, dy: float) -> bool:
        result = self._request(
            "POST",
            f"/api/entity/{handle}/move",
            json_body={"dx": dx, "dy": dy},
        )
        return result is not None

    def copy_entity(self, handle: str) -> str | None:
        result = self._request("POST", f"/api/entity/{handle}/copy")
        if result and "handle" in result:
            return str(result["handle"])
        return None

    def rotate_entity(
        self, handle: str, angle: float, cx: float | None = None, cy: float | None = None
    ) -> bool:
        body: dict[str, Any] = {"angle": angle}
        if cx is not None and cy is not None:
            body["center_x"] = cx
            body["center_y"] = cy
        result = self._request("POST", f"/api/entity/{handle}/rotate", json_body=body)
        return result is not None

    def scale_entity(
        self, handle: str, factor: float, cx: float | None = None, cy: float | None = None
    ) -> bool:
        body: dict[str, Any] = {"factor": factor}
        if cx is not None and cy is not None:
            body["center_x"] = cx
            body["center_y"] = cy
        result = self._request("POST", f"/api/entity/{handle}/scale", json_body=body)
        return result is not None

    # ── Layer operations ───────────────────────────────────────

    def get_linetypes(self) -> list[dict[str, Any]]:
        """Get all linetypes in the drawing."""
        result = self._request("GET", "/api/linetype")
        if result and "linetypes" in result:
            return result["linetypes"]
        return []

    def get_layers(self) -> list[dict[str, Any]]:
        result = self._request("GET", "/api/layer")
        if result and "layers" in result:
            return result["layers"]
        return []

    def create_layer(self, name: str, color: str | None = None) -> bool:
        body: dict[str, Any] = {"name": name}
        if color:
            body["color"] = color
        result = self._request("POST", "/api/layer", json_body=body)
        return result is not None

    def set_current_layer(self, name: str) -> bool:
        result = self._request("POST", f"/api/layer/{name}/current")
        return result is not None

    # ── Document operations ────────────────────────────────────

    def get_document_info(self) -> dict[str, Any] | None:
        return self._request("GET", "/api/document")

    def save_document(self, path: str | None = None) -> bool:
        body = {"path": path} if path else {}
        result = self._request("POST", "/api/document/save", json_body=body)
        return result is not None

    def save_project(self, filename: str, directory: str) -> bool:
        """Save the current document to ``directory/filename``.

        Args:
            filename: Project filename (with or without .dwg extension).
            directory: Target directory (absolute path). Auto-normalized to
                forward slashes.
        """
        if not filename.lower().endswith(".dwg"):
            filename = f"{filename}.dwg"
        full_path = f"{directory.rstrip('/').rstrip(chr(92))}/{filename}"
        full_path = full_path.replace(chr(92), "/")
        return self.save_document(full_path)

    def export_pdf(self, path: str) -> bool:
        result = self._request("POST", "/api/document/export/pdf", json_body={"path": path})
        return result is not None

    def export_dwg(self, path: str) -> bool:
        result = self._request("POST", "/api/document/export/dwg", json_body={"path": path})
        return result is not None

    def export_dxf(self, path: str) -> bool:
        result = self._request("POST", "/api/document/export/dxf", json_body={"path": path})
        return result is not None

    def zoom_extents(self) -> bool:
        result = self._request("POST", "/api/document/zoom/extents")
        return result is not None

    def get_system_info(self) -> dict[str, Any] | None:
        return self._request("GET", "/api/system/info")

    # ── System ─────────────────────────────────────────────────

    def execute_command(self, command: str) -> str | None:
        result = self._request("POST", "/api/system/command", json_body={"command": command})
        if result and "output" in result:
            return str(result["output"])
        return None

    def get_system_variable(self, name: str) -> str | None:
        result = self._request("GET", f"/api/system/variable/{name}")
        if result and "value" in result:
            return str(result["value"])
        return None

    def set_system_variable(self, name: str, value: str) -> bool:
        result = self._request("POST", f"/api/system/variable/{name}", json_body={"value": value})
        return result is not None

    def get_system_fonts(self) -> list[dict[str, Any]]:
        """Get all available fonts in the system."""
        result = self._request("GET", "/api/system/fonts")
        if result and "fonts" in result:
            return result["fonts"]
        return []

    # -- 3D Operations --

    def create_box(self, x: float, y: float, z: float) -> str | None:
        result = self._request("POST", "/api/solid/box", json_body={"x": x, "y": y, "z": z})
        return str(result["handle"]) if result and "handle" in result else None

    def create_sphere(self, radius: float) -> str | None:
        result = self._request("POST", "/api/solid/sphere", json_body={"radius": radius})
        return str(result["handle"]) if result and "handle" in result else None

    def create_cylinder(self, radius: float, height: float) -> str | None:
        result = self._request(
            "POST", "/api/solid/cylinder", json_body={"radius": radius, "height": height}
        )
        return str(result["handle"]) if result and "handle" in result else None

    def create_cone(self, radius_bottom: float, height: float) -> str | None:
        result = self._request(
            "POST", "/api/solid/cone", json_body={"radius_bottom": radius_bottom, "height": height}
        )
        return str(result["handle"]) if result and "handle" in result else None

    def create_torus(self, major_radius: float, minor_radius: float) -> str | None:
        result = self._request(
            "POST",
            "/api/solid/torus",
            json_body={"major_radius": major_radius, "minor_radius": minor_radius},
        )
        return str(result["handle"]) if result and "handle" in result else None

    def create_wedge(self, x: float, y: float, z: float) -> str | None:
        result = self._request("POST", "/api/solid/wedge", json_body={"x": x, "y": y, "z": z})
        return str(result["handle"]) if result and "handle" in result else None

    def create_pyramid(self, height: float, sides: int, radius: float) -> str | None:
        result = self._request(
            "POST",
            "/api/solid/pyramid",
            json_body={"height": height, "sides": sides, "radius": radius},
        )
        return str(result["handle"]) if result and "handle" in result else None

    def create_helix(
        self,
        center_x: float = 0,
        center_y: float = 0,
        center_z: float = 0,
        start_radius: float = 20,
        end_radius: float = 20,
        height: float = 50,
        turns: float = 3,
        layer: str | None = None,
    ) -> str | None:
        body: dict[str, Any] = {
            "center_x": center_x,
            "center_y": center_y,
            "center_z": center_z,
            "start_radius": start_radius,
            "end_radius": end_radius,
            "height": height,
            "turns": turns,
        }
        if layer:
            body["layer"] = layer
        result = self._request("POST", "/api/entity/helix", json_body=body)
        return str(result["handle"]) if result and "handle" in result else None

    def create_region(self, curve_handles: list[str]) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/entity/region",
            json_body={"curve_handles": curve_handles},
        )

    def create_boundary(
        self,
        point_x: float,
        point_y: float,
        layer: str | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {"point_x": point_x, "point_y": point_y}
        if layer:
            body["layer"] = layer
        return self._request("POST", "/api/entity/boundary", json_body=body)

    def create_mesh(
        self,
        vertices: list[list[float]],
        face_indices: list[int],
        smooth_level: int = 0,
        layer: str | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {
            "vertices": vertices,
            "face_indices": face_indices,
            "smooth_level": smooth_level,
        }
        if layer:
            body["layer"] = layer
        return self._request("POST", "/api/entity/mesh", json_body=body)

    def edit_mesh(
        self,
        handle: str,
        vertices: list[list[float]] | None = None,
        subdivide: int | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {"handle": handle}
        if vertices is not None:
            body["vertices"] = vertices
        if subdivide is not None:
            body["subdivide"] = subdivide
        return self._request("PATCH", "/api/entity/mesh", json_body=body)

    def set_viewport(self, name: str = "*Active", vp_type: str = "single") -> bool:
        result = self._request(
            "POST",
            "/api/viewport",
            json_body={"name": name, "type": vp_type},
        )
        return result is not None

    def render(self, output_file: str | None = None) -> bool:
        body: dict[str, Any] = {}
        if output_file:
            body["output_file"] = output_file
        result = self._request("POST", "/api/render", json_body=body)
        return result is not None

    def create_gradient(
        self,
        color1: str = "1,1,1",
        color2: str = "0,0,0",
        scale: float = 1.0,
        gradient_type: str = "linear",
        boundary_handles: list[str] | None = None,
        point_xs: list[float] | None = None,
        point_ys: list[float] | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {
            "color1": color1,
            "color2": color2,
            "scale": scale,
            "gradient_type": gradient_type,
        }
        if boundary_handles:
            body["boundary_handles"] = boundary_handles
        if point_xs:
            body["point_xs"] = point_xs
        if point_ys:
            body["point_ys"] = point_ys
        return self._request("POST", "/api/gradient", json_body=body)

    def create_arc_length_dimension(
        self,
        center_x: float = 0,
        center_y: float = 0,
        radius: float = 50,
        start_angle: float = 0,
        end_angle: float = 90,
        dim_x: float = 0,
        dim_y: float = 0,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/arc_length",
            json_body={
                "center_x": center_x,
                "center_y": center_y,
                "radius": radius,
                "start_angle": start_angle,
                "end_angle": end_angle,
                "dim_x": dim_x,
                "dim_y": dim_y,
            },
        )

    def export_ifc(self, path: str) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/document/export/ifc",
            json_body={"path": path},
        )

    def boolean_union(self, h1: str, h2: str) -> str | None:
        result = self._request("POST", f"/api/solid/{h1}/union/{h2}")
        return str(result["handle"]) if result and "handle" in result else None

    def boolean_subtract(self, h1: str, h2: str) -> str | None:
        result = self._request("POST", f"/api/solid/{h1}/subtract/{h2}")
        return str(result["handle"]) if result and "handle" in result else None

    def boolean_intersect(self, h1: str, h2: str) -> str | None:
        result = self._request("POST", f"/api/solid/{h1}/intersect/{h2}")
        return str(result["handle"]) if result and "handle" in result else None

    def extrude_solid(self, handle: str, height: float, taper_angle: float = 0) -> str | None:
        result = self._request(
            "POST",
            "/api/solid/extrude",
            json_body={"handle": handle, "height": height, "taper_angle": taper_angle},
        )
        return str(result["handle"]) if result and "handle" in result else None

    def revolve_solid(
        self,
        handle: str,
        ax: float,
        ay: float,
        az: float,
        dx: float,
        dy: float,
        dz: float,
        angle: float,
    ) -> str | None:
        result = self._request(
            "POST",
            "/api/solid/revolve",
            json_body={
                "handle": handle,
                "axis_x": ax,
                "axis_y": ay,
                "axis_z": az,
                "dir_x": dx,
                "dir_y": dy,
                "dir_z": dz,
                "angle": angle,
            },
        )
        return str(result["handle"]) if result and "handle" in result else None

    def move_solid(self, handle: str, dx: float, dy: float, dz: float = 0) -> bool:
        result = self._request(
            "POST", f"/api/solid/{handle}/move3d", json_body={"dx": dx, "dy": dy, "dz": dz}
        )
        return result is not None

    def set_3d_view(self, direction: str, render_mode: str = "wireframe") -> bool:
        result = self._request(
            "POST",
            "/api/solid/view",
            json_body={"direction": direction, "render_mode": render_mode},
        )
        return result is not None

    def get_solid_properties(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/solid/{handle}/props")

    # -- Symbol operations (MultiCAD) --

    def create_roughness(
        self, value: str = "Ra 6.3", angle: float = 0, allowance: str = "", symbol_type: int = 1
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/symbol/roughness",
            json_body={"value": value, "angle": angle, "allowance": allowance, "type": symbol_type},
        )

    def create_old_roughness(
        self,
        value: str = "6.3",
        angle: float = 0,
        method: str = "",
        companion_mirror: bool = False,
        surf_pos: float = 0,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/symbol/old-roughness",
            json_body={
                "value": value,
                "angle": angle,
                "method": method,
                "companion_mirror": companion_mirror,
                "surf_pos": surf_pos,
            },
        )

    def create_tolerance(
        self,
        type1: str | None = None,
        value1: str | None = None,
        letters1: str | None = None,
        type2: str | None = None,
        value2: str | None = None,
        letters2: str | None = None,
        text: str | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {}
        if type1:
            body["type1"] = type1
        if value1:
            body["value1"] = value1
        if letters1:
            body["letters1"] = letters1
        if type2:
            body["type2"] = type2
        if value2:
            body["value2"] = value2
        if letters2:
            body["letters2"] = letters2
        if text:
            body["text"] = text
        return self._request("POST", "/api/symbol/tolerance", json_body=body)

    def create_datum(self, letter: str = "A") -> dict[str, Any] | None:
        return self._request("POST", "/api/symbol/datum", json_body={"letter": letter})

    def create_weld(
        self,
        swap_sides: bool = False,
        right_orientation: bool = False,
        length_above: str | None = None,
        length_below: str | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {"swap_sides": swap_sides, "right_orientation": right_orientation}
        if length_above:
            body["length_above"] = length_above
        if length_below:
            body["length_below"] = length_below
        return self._request("POST", "/api/symbol/weld", json_body=body)

    def create_leader(
        self,
        arrow_x: float,
        arrow_y: float,
        bend_x: float,
        bend_y: float,
        shelf_x: float,
        shelf_y: float,
        text: str,
        text_below: str | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {
            "arrow_x": arrow_x,
            "arrow_y": arrow_y,
            "bend_x": bend_x,
            "bend_y": bend_y,
            "shelf_x": shelf_x,
            "shelf_y": shelf_y,
            "text": text,
        }
        if text_below:
            body["text_below"] = text_below
        return self._request("POST", "/api/symbol/leader", json_body=body)

    def create_note_comb(
        self, angle: float = 45, text_size: float = 12, first_line: str = "", second_line: str = ""
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/symbol/note-comb",
            json_body={
                "angle": angle,
                "text_size": text_size,
                "first_line": first_line,
                "second_line": second_line,
            },
        )

    def create_dim_number(
        self,
        x: float,
        y: float,
        arrow_x: float,
        arrow_y: float,
        text: str = "",
        index: int = 1,
        autonum: bool = True,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/symbol/dim-number",
            json_body={
                "x": x,
                "y": y,
                "arrow_x": arrow_x,
                "arrow_y": arrow_y,
                "text": text,
                "index": index,
                "autonum": autonum,
            },
        )

    # -- Table operations (MultiCAD) --

    def create_table(
        self,
        rows: int = 3,
        columns: int = 3,
        row_height: float = 30,
        column_width: float = 100,
        cells: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {
            "rows": rows,
            "columns": columns,
            "row_height": row_height,
            "column_width": column_width,
        }
        if cells:
            body["cells"] = cells
        return self._request("POST", "/api/table", json_body=body)

    def edit_table_cell(
        self,
        handle: str,
        row_index: int,
        column_index: int,
        value: str,
    ) -> dict[str, Any] | None:
        return self._request(
            "PATCH",
            f"/api/table/{handle}/cell",
            json_body={"row_index": row_index, "column_index": column_index, "value": value},
        )

    def get_table_info(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/table/{handle}")

    def delete_table(self, handle: str) -> dict[str, Any] | None:
        return self._request("DELETE", f"/api/table/{handle}")

    # -- Hatch operations --

    def create_hatch(
        self,
        pattern: str = "ANSI31",
        scale: float = 1.0,
        boundary_handles: list[str] | None = None,
        boundary_points: list[dict[str, float]] | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {"pattern": pattern, "scale": scale}
        if boundary_handles:
            body["boundary_handles"] = boundary_handles
        if boundary_points:
            body["boundary_points"] = boundary_points
        return self._request("POST", "/api/hatch", json_body=body)

    def get_hatch_info(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/hatch/{handle}")

    def edit_hatch(
        self, handle: str, pattern: str | None = None, scale: float | None = None
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {}
        if pattern:
            body["pattern"] = pattern
        if scale is not None:
            body["scale"] = scale
        return self._request("PATCH", f"/api/hatch/{handle}", json_body=body)

    # -- Dimension operations --

    def create_aligned_dimension(
        self, x1: float, y1: float, x2: float, y2: float, dim_x: float, dim_y: float
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/aligned",
            json_body={"x1": x1, "y1": y1, "x2": x2, "y2": y2, "dim_x": dim_x, "dim_y": dim_y},
        )

    def create_rotated_dimension(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        dim_x: float,
        dim_y: float,
        rotation: float,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/rotated",
            json_body={
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "dim_x": dim_x,
                "dim_y": dim_y,
                "rotation": rotation,
            },
        )

    def create_radial_dimension(
        self, center_x: float, center_y: float, arc_x: float, arc_y: float
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/radial",
            json_body={"center_x": center_x, "center_y": center_y, "arc_x": arc_x, "arc_y": arc_y},
        )

    def create_diametric_dimension(
        self, center_x: float, center_y: float, arc_x: float, arc_y: float
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/diametric",
            json_body={"center_x": center_x, "center_y": center_y, "arc_x": arc_x, "arc_y": arc_y},
        )

    def create_angular_dimension(
        self, center_x: float, center_y: float, p1_x: float, p1_y: float, p2_x: float, p2_y: float
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/angular",
            json_body={
                "center_x": center_x,
                "center_y": center_y,
                "p1_x": p1_x,
                "p1_y": p1_y,
                "p2_x": p2_x,
                "p2_y": p2_y,
            },
        )

    def create_ordinate_dimension(
        self,
        use_x_axis: bool,
        defining_x: float,
        defining_y: float,
        leader_x: float,
        leader_y: float,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/ordinate",
            json_body={
                "use_x_axis": use_x_axis,
                "defining_x": defining_x,
                "defining_y": defining_y,
                "leader_x": leader_x,
                "leader_y": leader_y,
            },
        )

    # -- Measurement operations --

    def get_distance(
        self, x1: float, y1: float, z1: float, x2: float, y2: float, z2: float
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/measurement/distance",
            json_body={"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2},
        )

    def get_angle(
        self,
        x1: float,
        y1: float,
        z1: float,
        x2: float,
        y2: float,
        z2: float,
        x3: float,
        y3: float,
        z3: float,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/measurement/angle",
            json_body={
                "x1": x1,
                "y1": y1,
                "z1": z1,
                "x2": x2,
                "y2": y2,
                "z2": z2,
                "x3": x3,
                "y3": y3,
                "z3": z3,
            },
        )

    def get_area(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/measurement/area/{handle}")

    def get_entity_info(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/entity/{handle}/info")

    def get_all_entities(self) -> dict[str, Any] | None:
        return self._request("GET", "/api/measurement/entities")

    # -- Mirror entity --

    def mirror_entity(
        self, handle: str, p1_x: float, p1_y: float, p2_x: float, p2_y: float
    ) -> bool:
        result = self._request(
            "POST",
            f"/api/entity/{handle}/mirror",
            json_body={"p1_x": p1_x, "p1_y": p1_y, "p2_x": p2_x, "p2_y": p2_y},
        )
        return result is not None

    # -- Transformation operations --

    def stretch_entity(self, handle: str, dx: float, dy: float) -> bool:
        result = self._request(
            "POST",
            f"/api/entity/{handle}/stretch",
            json_body={"handle": handle, "points": [], "dx": dx, "dy": dy},
        )
        return result is not None

    def explode_entity(self, handle: str) -> dict[str, Any] | None:
        return self._request("POST", f"/api/entity/{handle}/explode")

    def divide_entity(self, handle: str, segments: int) -> dict[str, Any] | None:
        return self._request(
            "POST",
            f"/api/entity/{handle}/divide",
            json_body={"handle": handle, "segments": segments},
        )

    def measure_entity(self, handle: str, distance: float) -> dict[str, Any] | None:
        return self._request(
            "POST",
            f"/api/entity/{handle}/measure",
            json_body={"handle": handle, "distance": distance},
        )

    def array_3d(
        self,
        handle: str,
        count_x: int = 2,
        count_y: int = 1,
        count_z: int = 1,
        spacing_x: float = 10,
        spacing_y: float = 10,
        spacing_z: float = 10,
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            f"/api/entity/{handle}/array3d",
            json_body={
                "handle": handle,
                "count_x": count_x,
                "count_y": count_y,
                "count_z": count_z,
                "spacing_x": spacing_x,
                "spacing_y": spacing_y,
                "spacing_z": spacing_z,
            },
        )

    def align_3d(
        self,
        handle: str,
        src_p1: tuple[float, float, float],
        src_p2: tuple[float, float, float],
        src_p3: tuple[float, float, float],
        dst_p1: tuple[float, float, float],
        dst_p2: tuple[float, float, float],
        dst_p3: tuple[float, float, float],
    ) -> bool:
        result = self._request(
            "POST",
            f"/api/entity/{handle}/align3d",
            json_body={
                "handle": handle,
                "src_p1_x": src_p1[0],
                "src_p1_y": src_p1[1],
                "src_p1_z": src_p1[2],
                "src_p2_x": src_p2[0],
                "src_p2_y": src_p2[1],
                "src_p2_z": src_p2[2],
                "src_p3_x": src_p3[0],
                "src_p3_y": src_p3[1],
                "src_p3_z": src_p3[2],
                "dst_p1_x": dst_p1[0],
                "dst_p1_y": dst_p1[1],
                "dst_p1_z": dst_p1[2],
                "dst_p2_x": dst_p2[0],
                "dst_p2_y": dst_p2[1],
                "dst_p2_z": dst_p2[2],
                "dst_p3_x": dst_p3[0],
                "dst_p3_y": dst_p3[1],
                "dst_p3_z": dst_p3[2],
            },
        )
        return result is not None

    def mirror_3d(
        self,
        handle: str,
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        p3: tuple[float, float, float],
    ) -> bool:
        result = self._request(
            "POST",
            f"/api/entity/{handle}/mirror3d",
            json_body={
                "handle": handle,
                "p1_x": p1[0],
                "p1_y": p1[1],
                "p1_z": p1[2],
                "p2_x": p2[0],
                "p2_y": p2[1],
                "p2_z": p2[2],
                "p3_x": p3[0],
                "p3_y": p3[1],
                "p3_z": p3[2],
            },
        )
        return result is not None

    # -- New Primitive operations --

    def create_polygon(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        sides: int = 6,
        inscribed: bool = True,
        layer: str | None = None,
    ) -> str | None:
        body: dict[str, Any] = {
            "center_x": center_x,
            "center_y": center_y,
            "radius": radius,
            "sides": sides,
            "inscribed": inscribed,
        }
        if layer:
            body["layer"] = layer
        result = self._request("POST", "/api/entity/polygon", json_body=body)
        return str(result["handle"]) if result and "handle" in result else None

    def create_donut(
        self,
        center_x: float,
        center_y: float,
        inner_radius: float,
        outer_radius: float,
        layer: str | None = None,
    ) -> str | None:
        body: dict[str, Any] = {
            "center_x": center_x,
            "center_y": center_y,
            "inner_radius": inner_radius,
            "outer_radius": outer_radius,
        }
        if layer:
            body["layer"] = layer
        result = self._request("POST", "/api/entity/donut", json_body=body)
        return str(result["handle"]) if result and "handle" in result else None

    def create_xline(
        self, p1_x: float, p1_y: float, p2_x: float, p2_y: float, layer: str | None = None
    ) -> str | None:
        body: dict[str, Any] = {"p1_x": p1_x, "p1_y": p1_y, "p2_x": p2_x, "p2_y": p2_y}
        if layer:
            body["layer"] = layer
        result = self._request("POST", "/api/entity/xline", json_body=body)
        return str(result["handle"]) if result and "handle" in result else None

    def create_ray(
        self, p1_x: float, p1_y: float, p2_x: float, p2_y: float, layer: str | None = None
    ) -> str | None:
        body: dict[str, Any] = {"p1_x": p1_x, "p1_y": p1_y, "p2_x": p2_x, "p2_y": p2_y}
        if layer:
            body["layer"] = layer
        result = self._request("POST", "/api/entity/ray", json_body=body)
        return str(result["handle"]) if result and "handle" in result else None

    # -- Document Management --

    def undo(self) -> bool:
        result = self._request("POST", "/api/document/undo")
        return result is not None

    def redo(self) -> bool:
        result = self._request("POST", "/api/document/redo")
        return result is not None

    def purge(self) -> bool:
        result = self._request("POST", "/api/document/purge")
        return result is not None

    def import_step(self, path: str) -> bool:
        result = self._request("POST", "/api/document/import/step", json_body={"path": path})
        return result is not None

    def export_step(self, path: str) -> bool:
        result = self._request("POST", "/api/document/export/step", json_body={"path": path})
        return result is not None

    # -- Block Create/Explode --

    def create_block(
        self, name: str, handles: list[str], base_x: float = 0, base_y: float = 0
    ) -> str | None:
        result = self._request(
            "POST",
            "/api/block/create",
            json_body={"name": name, "handles": handles, "base_x": base_x, "base_y": base_y},
        )
        return str(result["handle"]) if result and "handle" in result else None

    def insert_block(
        self,
        name: str,
        x: float = 0,
        y: float = 0,
        scale: float = 1.0,
        rotation: float = 0,
    ) -> str | None:
        """Insert a previously defined block at the given position."""
        result = self._request(
            "POST",
            f"/api/block/{name}/insert",
            json_body={
                "x": x,
                "y": y,
                "scaleX": scale,
                "scaleY": scale,
                "scaleZ": scale,
                "rotation": rotation,
            },
        )
        return str(result["handle"]) if result and "handle" in result else None

    def get_blocks(self) -> list[dict[str, Any]]:
        """List all block definitions in the current drawing."""
        result = self._request("GET", "/api/block")
        if result and "blocks" in result:
            return result["blocks"]
        return []

    def explode_block(self, name: str) -> bool:
        result = self._request("POST", f"/api/block/{name}/explode")
        return result is not None

    # -- Quick Wins --
    def new_document(
        self,
        template: str | None = None,
        save_path: str | None = None,
    ) -> bool:
        """Create a new document.

        Args:
            template: Optional .dwt template path.
            save_path: Optional full file path (e.g. ``C:/Projects/foo.dwg``) to
                save the new document to immediately after creation.
        """
        body: dict[str, Any] = {}
        if template:
            body["template"] = template
        if save_path:
            body["save_path"] = save_path
        result = self._request("POST", "/api/document/new", json_body=body)
        return result is not None

    def create_project(
        self,
        filename: str,
        directory: str,
        template: str | None = None,
    ) -> bool:
        """Create a new project file at ``directory/filename``.

        Args:
            filename: Project filename (with or without .dwg extension).
            directory: Target directory (absolute path). Auto-normalized to
                forward slashes (avoids JSON escape issues).
            template: Optional .dwt template path.

        Returns True if the project was created and saved.
        """
        if not filename.lower().endswith(".dwg"):
            filename = f"{filename}.dwg"
        # Normalize: use forward slashes to avoid JSON escaping issues
        full_path = f"{directory.rstrip('/').rstrip(chr(92))}/{filename}"
        full_path = full_path.replace(chr(92), "/")
        return self.new_document(template=template, save_path=full_path)

    def open_document(self, path: str) -> bool:
        result = self._request("POST", "/api/document/open", json_body={"path": path})
        return result is not None

    def close_document(self) -> bool:
        result = self._request("POST", "/api/document/close")
        return result is not None

    def delete_block(self, name: str) -> bool:
        result = self._request("DELETE", f"/api/block/{name}")
        return result is not None

    def get_block_entities(self, name: str) -> list[dict[str, Any]]:
        result = self._request("GET", f"/api/block/{name}/entities")
        if result and "entities" in result:
            return result["entities"]
        return []

    # -- Trim / Extend / Offset --
    def trim_entity(
        self, handle: str, cut_x: float, cut_y: float, keep_start: bool = True
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            f"/api/entity/{handle}/trim",
            json_body={"handle": handle, "cut_x": cut_x, "cut_y": cut_y, "keep_start": keep_start},
        )

    def extend_entity(self, handle: str, end_x: float, end_y: float) -> bool:
        result = self._request(
            "POST",
            f"/api/entity/{handle}/extend",
            json_body={"handle": handle, "end_x": end_x, "end_y": end_y},
        )
        return result is not None

    def offset_entity(self, handle: str, distance: float) -> dict[str, Any] | None:
        return self._request(
            "POST",
            f"/api/entity/{handle}/offset",
            json_body={"handle": handle, "distance": distance},
        )

    # -- Layer Management --
    def layer_isolate(self, name: str) -> bool:
        result = self._request("POST", f"/api/layer/{name}/isolate")
        return result is not None

    def layer_off(self, name: str) -> bool:
        result = self._request("POST", f"/api/layer/{name}/off")
        return result is not None

    def layer_freeze(self, name: str) -> bool:
        result = self._request("POST", f"/api/layer/{name}/freeze")
        return result is not None

    def layer_on_all(self) -> bool:
        result = self._request("POST", "/api/layer/on")
        return result is not None

    def layer_thaw_all(self) -> bool:
        result = self._request("POST", "/api/layer/thaw")
        return result is not None

    # -- DIMLINEAR --
    def create_linear_dimension(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        dim_x: float,
        dim_y: float,
        direction: str = "horizontal",
    ) -> dict[str, Any] | None:
        return self._request(
            "POST",
            "/api/dimension/linear",
            json_body={
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "dim_x": dim_x,
                "dim_y": dim_y,
                "direction": direction,
            },
        )

    # -- SWEEP / LOFT / FILLETEDGE / CHAMFEREDGE --
    def sweep_solid(self, profile_handle: str, path_handle: str) -> bool:
        result = self._request(
            "POST",
            "/api/solid/sweep",
            json_body={"profile_handle": profile_handle, "path_handle": path_handle},
        )
        return result is not None

    def loft_solid(self, section_handles: list[str]) -> bool:
        result = self._request(
            "POST", "/api/solid/loft", json_body={"section_handles": section_handles}
        )
        return result is not None

    def fillet_edge(self, handle: str, radius: float = 5.0) -> bool:
        result = self._request(
            "POST", "/api/solid/filletedge", json_body={"handle": handle, "radius": radius}
        )
        return result is not None

    def chamfer_edge(self, handle: str, dist1: float = 5.0, dist2: float = 5.0) -> bool:
        result = self._request(
            "POST",
            "/api/solid/chamferedge",
            json_body={"handle": handle, "dist1": dist1, "dist2": dist2},
        )
        return result is not None

    # -- Assembly --
    def insert_part(self, block_name: str, x: float, y: float, z: float) -> bool:
        result = self._request(
            "POST",
            "/api/assembly/insert",
            json_body={"block_name": block_name, "x": x, "y": y, "z": z},
        )
        return result is not None

    def assembly_mate(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/assembly/mate", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def assembly_angle(self, handle1: str, handle2: str, angle: float) -> bool:
        result = self._request(
            "POST",
            "/api/assembly/angle",
            json_body={"handle1": handle1, "handle2": handle2, "angle": angle},
        )
        return result is not None

    def assembly_tangent(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/assembly/tangent", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def assembly_symmetry(self, handle1: str, handle2: str, plane_handle: str) -> bool:
        result = self._request(
            "POST",
            "/api/assembly/symmetry",
            json_body={"handle1": handle1, "handle2": handle2, "plane_handle": plane_handle},
        )
        return result is not None

    # -- 3D Features --
    def create_simple_hole(self, solid_handle: str, diameter: float, depth: float) -> bool:
        result = self._request(
            "POST",
            "/api/feature/hole/simple",
            json_body={"solid_handle": solid_handle, "diameter": diameter, "depth": depth},
        )
        return result is not None

    def create_threaded_hole(self, solid_handle: str, diameter: float, depth: float) -> bool:
        result = self._request(
            "POST",
            "/api/feature/hole/threaded",
            json_body={"solid_handle": solid_handle, "diameter": diameter, "depth": depth},
        )
        return result is not None

    def create_standard_hole(
        self, solid_handle: str, diameter: float, depth: float, standard: str = "ISO"
    ) -> bool:
        result = self._request(
            "POST",
            "/api/feature/hole/standard",
            json_body={
                "solid_handle": solid_handle,
                "diameter": diameter,
                "depth": depth,
                "standard": standard,
            },
        )
        return result is not None

    def create_shell(self, solid_handle: str, thickness: float, outward: bool = False) -> bool:
        result = self._request(
            "POST",
            "/api/feature/shell",
            json_body={"solid_handle": solid_handle, "thickness": thickness, "outward": outward},
        )
        return result is not None

    def create_mirror_feature(self, solid_handle: str, plane_handle: str) -> bool:
        result = self._request(
            "POST",
            "/api/feature/mirror",
            json_body={"solid_handle": solid_handle, "plane_handle": plane_handle},
        )
        return result is not None

    def create_circular_pattern(
        self, solid_handle: str, feature_handle: str, count: int, angle: float
    ) -> bool:
        result = self._request(
            "POST",
            "/api/feature/pattern/circular",
            json_body={
                "solid_handle": solid_handle,
                "feature_handle": feature_handle,
                "count": count,
                "angle": angle,
            },
        )
        return result is not None

    def create_rectangular_pattern(
        self,
        solid_handle: str,
        feature_handle: str,
        count_x: int,
        spacing_x: float,
        count_y: int,
        spacing_y: float,
    ) -> bool:
        result = self._request(
            "POST",
            "/api/feature/pattern/rectangular",
            json_body={
                "solid_handle": solid_handle,
                "feature_handle": feature_handle,
                "count_x": count_x,
                "spacing_x": spacing_x,
                "count_y": count_y,
                "spacing_y": spacing_y,
            },
        )
        return result is not None

    def create_sketch(self, solid_handle: str) -> str | None:
        result = self._request(
            "POST",
            "/api/feature/sketch",
            json_body={"solid_handle": solid_handle},
        )
        return str(result.get("handle")) if result and "handle" in result else None

    def add_sketch_circle(
        self, sketch_handle: str, cx: float, cy: float, cz: float, radius: float
    ) -> bool:
        result = self._request(
            "POST",
            "/api/feature/sketch/circle",
            json_body={
                "sketch_handle": sketch_handle,
                "cx": cx,
                "cy": cy,
                "cz": cz,
                "radius": radius,
            },
        )
        return result is not None

    def add_sketch_line(
        self,
        sketch_handle: str,
        x1: float,
        y1: float,
        z1: float,
        x2: float,
        y2: float,
        z2: float,
    ) -> bool:
        result = self._request(
            "POST",
            "/api/feature/sketch/line",
            json_body={
                "sketch_handle": sketch_handle,
                "x1": x1,
                "y1": y1,
                "z1": z1,
                "x2": x2,
                "y2": y2,
                "z2": z2,
            },
        )
        return result is not None

    def create_profile(self, sketch_handle: str) -> str | None:
        result = self._request(
            "POST",
            "/api/feature/sketch/profile",
            json_body={"sketch_handle": sketch_handle},
        )
        return str(result.get("handle")) if result and "handle" in result else None

    def create_extrude_feature(
        self,
        solid_handle: str,
        profile_handle: str,
        height: float,
        taper_angle: float = 0,
        direction: bool = True,
    ) -> str | None:
        result = self._request(
            "POST",
            "/api/feature/extrude",
            json_body={
                "solid_handle": solid_handle,
                "profile_handle": profile_handle,
                "height": height,
                "taper_angle": taper_angle,
                "direction": direction,
            },
        )
        return str(result.get("handle")) if result and "handle" in result else None

    def create_revolve_feature(
        self,
        solid_handle: str,
        profile_handle: str,
        axis_x: float,
        axis_y: float,
        axis_z: float,
        dir_x: float,
        dir_y: float,
        dir_z: float,
        angle: float,
    ) -> str | None:
        result = self._request(
            "POST",
            "/api/feature/revolve",
            json_body={
                "solid_handle": solid_handle,
                "profile_handle": profile_handle,
                "axis_x": axis_x,
                "axis_y": axis_y,
                "axis_z": axis_z,
                "dir_x": dir_x,
                "dir_y": dir_y,
                "dir_z": dir_z,
                "angle": angle,
            },
        )
        return str(result.get("handle")) if result and "handle" in result else None

    # -- Selection / QSELECT --
    def select_entities(
        self,
        entity_type: str | None = None,
        layer: str | None = None,
        color: int | None = None,
        max_count: int = 1000,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {"max_count": max_count}
        if entity_type:
            body["entity_type"] = entity_type
        if layer:
            body["layer"] = layer
        if color is not None:
            body["color"] = color
        return self._request("POST", "/api/selection/select", json_body=body)

    def select_by_handles(self, handles: list[str]) -> dict[str, Any] | None:
        return self._request("POST", "/api/selection/by-handles", json_body={"handles": handles})

    def get_entity_detail(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/selection/entity/{handle}")

    # -- MultiCAD API --
    def create_grid_axis(
        self,
        grid_type: str = "rect",
        origin_x: float = 0,
        origin_y: float = 0,
        spacings_x: list[float] | None = None,
        spacings_y: list[float] | None = None,
        naming_x: str = "1,2,3...",
        naming_y: str = "A,B,C...",
    ) -> bool:
        body: dict[str, Any] = {
            "type": grid_type,
            "origin_x": origin_x,
            "origin_y": origin_y,
            "spacings_x": spacings_x or [1000],
            "spacings_y": spacings_y or [1000],
            "naming_x": naming_x,
            "naming_y": naming_y,
        }
        result = self._request("POST", "/api/multicad/grid-axis", json_body=body)
        return result is not None

    def create_grid_label(
        self,
        grid_handle: str,
        label: str,
        axis_index: int = 0,
        direction: str = "x",
    ) -> bool:
        body: dict[str, Any] = {
            "grid_handle": grid_handle,
            "label": label,
            "axis_index": axis_index,
            "direction": direction,
        }
        result = self._request("POST", "/api/multicad/grid-label", json_body=body)
        return result is not None

    def create_room(
        self,
        x: float = 0,
        y: float = 0,
        width: float = 1000,
        height: float = 1000,
        name: str | None = None,
    ) -> bool:
        body: dict[str, Any] = {"x": x, "y": y, "width": width, "height": height}
        if name:
            body["name"] = name
        result = self._request("POST", "/api/multicad/room", json_body=body)
        return result is not None

    def get_room_properties(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/multicad/room/{handle}")

    def create_custom_object(
        self, class_name: str, properties: dict[str, Any] | None = None
    ) -> bool:
        body: dict[str, Any] = {"class_name": class_name}
        if properties:
            body["properties"] = properties
        result = self._request("POST", "/api/multicad/custom-object", json_body=body)
        return result is not None

    def create_parametric_object(
        self, object_type: str, parameters: dict[str, Any] | None = None
    ) -> bool:
        body: dict[str, Any] = {"type": object_type}
        if parameters:
            body["parameters"] = parameters
        result = self._request("POST", "/api/multicad/parametric", json_body=body)
        return result is not None

    def create_reactor(self, entity_handle: str, event_type: str = "modified") -> bool:
        result = self._request(
            "POST",
            "/api/multicad/reactor",
            json_body={"entity_handle": entity_handle, "event_type": event_type},
        )
        return result is not None

    def create_2d_break(
        self,
        view_handle: str,
        x1: float = 0,
        y1: float = 0,
        x2: float = 0,
        y2: float = 0,
    ) -> bool:
        result = self._request(
            "POST",
            "/api/multicad/2d-break",
            json_body={"view_handle": view_handle, "x1": x1, "y1": y1, "x2": x2, "y2": y2},
        )
        return result is not None

    def start_motion_preview(self, handle: str) -> bool:
        result = self._request(
            "POST",
            "/api/multicad/motion-preview/start",
            json_body={"handle": handle},
        )
        return result is not None

    def stop_motion_preview(self) -> bool:
        result = self._request("POST", "/api/multicad/motion-preview/stop")
        return result is not None

    def create_body_contour(self, solid_handle: str) -> bool:
        result = self._request(
            "POST",
            "/api/multicad/body-contour",
            json_body={"solid_handle": solid_handle},
        )
        return result is not None

    def check_3d_faces(self, handle: str) -> dict[str, Any] | None:
        return self._request("GET", f"/api/multicad/3d-faces/{handle}")

    # -- STL Export --
    def export_stl(self, path: str, binary: bool = True) -> bool:
        result = self._request(
            "POST", "/api/document/export/stl", json_body={"path": path, "binary": binary}
        )
        return result is not None

    # -- 2D Constraints --
    def constraint_parallel(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/constraint/parallel", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def constraint_coincident(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/constraint/coincident", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def constraint_fix(self, handle: str) -> bool:
        result = self._request("POST", "/api/constraint/fix", json_body={"handle": handle})
        return result is not None

    def constraint_horizontal(self, handle: str) -> bool:
        result = self._request("POST", "/api/constraint/horizontal", json_body={"handle": handle})
        return result is not None

    def constraint_vertical(self, handle: str) -> bool:
        result = self._request("POST", "/api/constraint/vertical", json_body={"handle": handle})
        return result is not None

    def constraint_tangent(self, handle_line: str, handle_curve: str) -> bool:
        result = self._request(
            "POST",
            "/api/constraint/tangent",
            json_body={"handle_line": handle_line, "handle_curve": handle_curve},
        )
        return result is not None

    def constraint_perpendicular(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST",
            "/api/constraint/perpendicular",
            json_body={"handle1": handle1, "handle2": handle2},
        )
        return result is not None

    def constraint_collinear(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/constraint/collinear", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def constraint_concentric(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/constraint/concentric", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def constraint_equal(self, handle1: str, handle2: str) -> bool:
        result = self._request(
            "POST", "/api/constraint/equal", json_body={"handle1": handle1, "handle2": handle2}
        )
        return result is not None

    def constraint_symmetric(self, handle1: str, handle2: str, plane_handle: str) -> bool:
        result = self._request(
            "POST",
            "/api/constraint/symmetric",
            json_body={"handle1": handle1, "handle2": handle2, "plane_handle": plane_handle},
        )
        return result is not None

    def constraint_distance(self, handle1: str, handle2: str, distance: float) -> bool:
        result = self._request(
            "POST",
            "/api/constraint/distance",
            json_body={"handle1": handle1, "handle2": handle2, "distance": distance},
        )
        return result is not None

    # ── Sheet Metal ────────────────────────────────────────────

    def create_base_flange(
        self, x: float, y: float, width: float, length: float, thickness: float
    ) -> bool:
        result = self._request(
            "POST",
            "/api/sheetmetal/base-flange",
            json_body={"x": x, "y": y, "width": width, "length": length, "thickness": thickness},
        )
        return result is not None

    def create_edge_flange(self, base_handle: str, bend_radius: float = 5.0) -> bool:
        result = self._request(
            "POST",
            "/api/sheetmetal/edge-flange",
            json_body={"base_handle": base_handle, "bend_radius": bend_radius},
        )
        return result is not None

    def create_bend(self, handle: str, bend_radius: float = 5.0) -> bool:
        result = self._request(
            "POST", "/api/sheetmetal/bend", json_body={"handle": handle, "bend_radius": bend_radius}
        )
        return result is not None

    def unfold_sheet_metal(self, handle: str, x: float = 0, y: float = 0) -> bool:
        result = self._request(
            "POST", "/api/sheetmetal/unfold", json_body={"handle": handle, "x": x, "y": y}
        )
        return result is not None

    def create_base_plate(
        self, x: float, y: float, width: float, length: float, thickness: float
    ) -> bool:
        result = self._request(
            "POST",
            "/api/sheetmetal/base-plate",
            json_body={"x": x, "y": y, "width": width, "length": length, "thickness": thickness},
        )
        return result is not None

    # -- MLEADER --
    def create_mleader(
        self,
        arrow_x: float,
        arrow_y: float,
        leader_x: float,
        leader_y: float,
        text: str,
        text_height: float = 3.5,
        layer: str | None = None,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {
            "arrow_x": arrow_x,
            "arrow_y": arrow_y,
            "leader_x": leader_x,
            "leader_y": leader_y,
            "text": text,
            "text_height": text_height,
        }
        if layer:
            body["layer"] = layer
        return self._request("POST", "/api/symbol/mleader", json_body=body)

    # ── NURBS / IFC ────────────────────────────────────────────

    def create_nurb_curve(self, **kwargs: Any) -> dict[str, Any] | None:
        return self._request("POST", "/api/entity/nurbcurve", json_body=kwargs)

    def create_nurb_surface(self, **kwargs: Any) -> dict[str, Any] | None:
        return self._request("POST", "/api/entity/nurbsurface", json_body=kwargs)

    def modify_nurb(self, **kwargs: Any) -> dict[str, Any] | None:
        return self._request("PATCH", "/api/entity/nurb", json_body=kwargs)

    def import_ifc(self, path: str) -> bool:
        result = self._request("POST", "/api/document/import/ifc", json_body={"path": path})
        return result is not None

    def get_ifc_entities(self) -> list[dict[str, Any]] | None:
        result = self._request("GET", "/api/document/ifc/entities")
        if result and "entities" in result:
            return result["entities"]
        return None
