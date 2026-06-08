"""
nanoCAD Lighthouse Generator
=============================
Creates all plywood lighthouse parts in the current nanoCAD drawing
via the HTTP API (.NET engine plugin on port 5080).

Usage:
    py F:\\nanoCAD\\server\\scripts\\create_lighthouse.py

Requirements:
    - nanoCAD 26 running with CadEngine.Plugin loaded
    - Port 5080 listening (HTTP API)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

SERVER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_ROOT))

from src.infrastructure.http_bridge import HttpCadBridge


# ── Geometry Helpers ───────────────────────────────────────────

def hexagon_vertices(cx: float, cy: float, r: float) -> list[list[float]]:
    """Return [[x,y],...] vertices for a regular hexagon, flat-top orientation."""
    verts = []
    for i in range(6):
        a = math.radians(90 + i * 60)
        verts.append([round(cx + r * math.cos(a), 2), round(cy + r * math.sin(a), 2)])
    return verts


def trapezoid_vertices(bottom_r: float, top_r: float, height: float,
                       cx: float = 0.0, cy: float = 0.0) -> list[list[float]]:
    """Return [[x,y],...] for a symmetric trapezoid (y=0 at bottom)."""
    return [
        [cx - bottom_r, cy],
        [cx + bottom_r, cy],
        [cx + top_r, cy + height],
        [cx - top_r, cy + height],
    ]


def polyline_vertices(vertices: list[list[float]]) -> list[list[float]]:
    """Round and close a polyline vertex list."""
    result = [[round(v[0], 2), round(v[1], 2)] for v in vertices]
    if result[0] != result[-1]:
        result.append(result[0])
    return result


def arc_points(cx: float, cy: float, r: float,
               start_deg: float, end_deg: float,
               steps: int = 12) -> list[list[float]]:
    """Approximate an arc as a polyline vertex list."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts.append([round(cx + r * math.cos(a), 2), round(cy + r * math.sin(a), 2)])
    return pts


# ── Main Drawing Function ──────────────────────────────────────

def create_lighthouse(bridge: HttpCadBridge) -> None:
    """Create all lighthouse parts. Exits on critical failure."""

    def log(msg: str) -> None:
        print(f"  {msg}")

    # ── Helper wrappers that raise on failure ─────────────────

    def mk_layer(name: str) -> bool:
        return bridge.create_layer(name)

    def set_layer(name: str) -> bool:
        return bridge.set_current_layer(name)

    def mk_polyline(verts: list[list[float]], layer: str | None = None) -> str:
        params: dict[str, Any] = {"vertices": verts, "closed": True}
        if layer:
            params["layer"] = layer
        h = bridge.create_entity("polyline", params)
        if not h:
            raise RuntimeError(f"Failed to create polyline on layer {layer}")
        return h

    def mk_rect(x1: float, y1: float, x2: float, y2: float, layer: str | None = None) -> str:
        params: dict[str, Any] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        if layer:
            params["layer"] = layer
        h = bridge.create_entity("rectangle", params)
        if not h:
            raise RuntimeError(f"Failed to create rectangle on layer {layer}")
        return h

    def mk_circle(cx: float, cy: float, r: float, layer: str | None = None) -> str:
        params: dict[str, Any] = {"cx": cx, "cy": cy, "radius": r}
        if layer:
            params["layer"] = layer
        h = bridge.create_entity("circle", params)
        if not h:
            raise RuntimeError(f"Failed to create circle on layer {layer}")
        return h

    def mk_text(x: float, y: float, text: str, height: float = 4) -> str:
        h = bridge.create_entity("text", {"x": x, "y": y, "content": text, "height": height, "layer": "LABELS"})
        if not h:
            raise RuntimeError(f"Failed to create text: {text}")
        return h

    # ── Step 1: Layers ───────────────────────────────────────

    log("Creating layers...")
    for name in ["BASE", "WALLS", "SHELVES", "DOME", "FINIAL", "CUTOUTS", "LABELS"]:
        mk_layer(name)
    set_layer("BASE")
    log("Layers ready.")

    # ══════════════════════════════════════════════════════════
    # 2. BASE PLATE — hexagon R=82
    # ══════════════════════════════════════════════════════════

    log("Base plate (hexagon R=82)...")
    set_layer("BASE")
    bv = hexagon_vertices(0, 0, 82.0)
    mk_polyline(bv, "BASE")
    mk_text(0, -95, "BASE PLATE (R=82)")

    # ══════════════════════════════════════════════════════════
    # 3. TOP PLATFORM — hexagon R=52
    # ══════════════════════════════════════════════════════════

    log("Top platform (hexagon R=52)...")
    set_layer("BASE")
    tv = hexagon_vertices(0, 160, 52.0)
    mk_polyline(tv, "BASE")
    mk_text(0, 100, "TOP PLATFORM (R=52)")

    # ══════════════════════════════════════════════════════════
    # 4. SIDE PANELS — 5 with window + 1 with door
    # ══════════════════════════════════════════════════════════

    BW, TW, PH = 82.0, 52.0, 202.0  # bottom half-width, top half-width, panel height
    SX = BW * 2 + 20  # spacing between panels

    log("Side panels (5 + 1 door)...")
    set_layer("WALLS")

    for i in range(5):
        px = -2 * SX + i * SX
        py = -300.0

        # Outline
        ov = trapezoid_vertices(BW, TW, PH, px, py)
        mk_polyline(polyline_vertices(ov), "WALLS")

        # Window cutout (rectangle)
        mk_rect(px - 7, py + 131, px + 7, py + 149, "CUTOUTS")

        # Lantern opening
        mk_rect(px - 12, py + 164, px + 12, py + 197, "CUTOUTS")

        mk_text(px, py - 18, f"PANEL {i+1}")

    # Door panel
    dx, dy = 3 * SX, -300.0
    odv = trapezoid_vertices(BW, TW, PH, dx, dy)
    mk_polyline(polyline_vertices(odv), "WALLS")

    # Door arch: rectangle + semicircle
    dw, drh, dah = 24, 30, 12
    mk_rect(dx - dw / 2, dy + 2, dx + dw / 2, dy + 2 + drh, "CUTOUTS")
    # Door arch (semicircle)
    cap = arc_points(dx, dy + 2 + drh, dw / 2, 0, 180, 10)
    bridge.create_entity("polyline", {"vertices": cap, "closed": False, "layer": "CUTOUTS"})

    # Door window
    mk_circle(dx, dy + 28, 4, "CUTOUTS")

    # Lantern opening (narrower for door panel)
    mk_rect(dx - 8, dy + 164, dx + 8, dy + 197, "CUTOUTS")

    mk_text(dx, dy - 18, "DOOR PANEL")

    # ══════════════════════════════════════════════════════════
    # 5. SHELVES
    # ══════════════════════════════════════════════════════════

    log("Shelves...")
    set_layer("SHELVES")

    for i, (r, label) in enumerate([(72, "LOWER SHELF R=72"), (62, "UPPER SHELF R=62")]):
        sy = 200 + i * 120
        mk_polyline(hexagon_vertices(0, sy, r), "SHELVES")
        mk_text(0, sy - r - 15, label)

    # ══════════════════════════════════════════════════════════
    # 6. DOME PETALS
    # ══════════════════════════════════════════════════════════

    log("Dome petals (6)...")
    set_layer("DOME")

    dome_y = 480.0
    left_profile = [(-26, 0), (-28, 10), (-29, 22), (-28.5, 35),
                    (-26, 48), (-22, 60), (-17, 72), (-10, 84), (0, 95)]
    right_profile = [(10, 84), (17, 72), (22, 60), (26, 48),
                     (28.5, 35), (29, 22), (28, 10), (26, 0)]

    for i in range(6):
        px = -2.5 * 55 + i * 55
        pts = []
        for lx, ly in left_profile:
            pts.append([px + lx, dome_y + ly])
        for rx, ry in right_profile:
            pts.append([px + rx, dome_y + ry])
        mk_polyline(polyline_vertices(pts), "DOME")
        mk_text(px, dome_y - 10, f"PETAL {i+1}")

    # ══════════════════════════════════════════════════════════
    # 7. LED shelf
    # ══════════════════════════════════════════════════════════

    log("LED shelf...")
    set_layer("SHELVES")
    mk_polyline(hexagon_vertices(-150, 550, 42), "SHELVES")
    mk_circle(-150, 550, 6, "CUTOUTS")
    mk_text(-150, 498, "LED SHELF (R=42)")

    # ══════════════════════════════════════════════════════════
    # 8. FINIAL
    # ══════════════════════════════════════════════════════════

    log("Finial...")
    set_layer("FINIAL")
    finial_shape: list[list[float]] = [[-6.0, 0.0], [6.0, 0.0], [6.0, 5.0], [3.0, 5.0], [3.0, 32.0],
                    [1.0, 40.0], [0.0, 42.0], [-1.0, 40.0], [-3.0, 32.0],
                    [-3.0, 5.0], [-6.0, 5.0], [-6.0, 0.0]]
    fpts = [[-150 + fx, 620 + fy] for fx, fy in finial_shape]
    mk_polyline(polyline_vertices(fpts), "FINIAL")
    mk_text(-150, 605, "FINIAL")

    # ══════════════════════════════════════════════════════════
    # 9. Finalize
    # ══════════════════════════════════════════════════════════

    bridge._request("POST", "/api/document/zoom/extents")
    log("Zoomed to extents.")
    print("\nAll parts created successfully!")


# ── Main ───────────────────────────────────────────────────────

def main() -> None:
    print("=" * 56)
    print("  nanoCAD LIGHTHOUSE GENERATOR")
    print("  Checking nanoCAD HTTP API...")
    print("=" * 56)

    bridge = HttpCadBridge()

    if not bridge.connect():
        print("\n  ERROR: Cannot connect to nanoCAD HTTP API.")
        print("  Ensure nanoCAD is running with CadEngine.Plugin.")
        print("  Check port 5080 is listening.")
        bridge.close()
        sys.exit(1)

    print(f"  Connected! nanoCAD HTTP API available.\n")

    try:
        create_lighthouse(bridge)
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bridge.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
