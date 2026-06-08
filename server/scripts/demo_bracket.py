"""
nanoCAD Demo: Mechanical Part Generator
========================================
Creates a simple mechanical bracket:
- Base plate (polyline)
- Holes (circles)
- Proper layer assignment

Usage:
    py F:\\nanoCAD\\server\\scripts\\demo_bracket.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_ROOT))

from src.infrastructure.http_bridge import HttpCadBridge


def create_bracket() -> None:
    http = HttpCadBridge(port=5080)
    http.connect()
    if not http.is_available:
        print("nanoCAD HTTP API not available on port 5080")
        print("Start nanoCAD with CadEngine.Plugin loaded")
        return

    print("Connected to nanoCAD")

    # Create layers
    http.create_layer("BASE", color="1")
    http.create_layer("HOLES", color="3")
    http.create_layer("DIMENSIONS", color="5")
    print("Layers created: BASE, HOLES, DIMENSIONS")

    # Base plate: 200x100 rectangle
    # C# model: PolylineRequest { Vertices = double[][], Closed, Layer }
    h = http.create_entity("Polyline", {
        "vertices": [[0, 0], [200, 0], [200, 100], [0, 100]],
        "closed": True,
        "layer": "BASE",
    })
    print(f"Base plate created (handle={h})")

    # Mounting holes at corners
    # C# model: CircleRequest { Cx, Cy, Radius, Layer }
    for x, y in [(20, 20), (180, 20), (20, 80), (180, 80)]:
        hc = http.create_entity("Circle", {
            "cx": x, "cy": y, "radius": 5,
            "layer": "HOLES",
        })
        print(f"  Hole at ({x},{y}) handle={hc}")

    # Center hole
    http.create_entity("Circle", {
        "cx": 100, "cy": 50, "radius": 15,
        "layer": "HOLES",
    })
    print("Center hole created")

    # Dimension lines on DIMENSIONS layer
    # C# model: LineRequest { X1, Y1, X2, Y2, Layer }
    http.create_entity("Line", {
        "x1": -10, "y1": -10, "x2": 210, "y2": -10,
        "layer": "DIMENSIONS",
    })
    http.create_entity("Line", {
        "x1": 210, "y1": -10, "x2": 210, "y2": 110,
        "layer": "DIMENSIONS",
    })
    print("Dimension lines created")

    print("")
    print("Bracket created successfully!")
    print("  200x100 base plate [BASE]")
    print("  4x mounting holes r=5 [HOLES]")
    print("  1x center hole r=15 [HOLES]")
    print("  2x dimension lines [DIMENSIONS]")


if __name__ == "__main__":
    create_bracket()
