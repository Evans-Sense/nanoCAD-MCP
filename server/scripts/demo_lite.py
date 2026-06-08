"""
nanoCAD MCP Demo: Engineering Project (LITE)
=============================================
A focused walkthrough of the most important MCP tool categories. Builds
a smaller but representative engineering drawing.

This is the LITE version — covers the core categories but stops short
of assemblies, sheet metal and exports to minimize server load.

Usage:
    py F:\\nanoCAD\\server\\scripts\\demo_lite.py

By default the project is created in %TEMP%/nanoCAD_demo/.
"""
from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path
from typing import Any

SERVER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_ROOT))

from src.infrastructure import HttpCadBridge, SafeBridge

DEMO_DIR = Path(os.environ.get("TEMP", "C:\\temp")) / "nanoCAD_demo"
PROJECT_NAME = "engineering_project_lite"
CALL_DELAY = 0.1  # seconds between calls to avoid MainThreadExecutor overload


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def step(msg: str) -> None:
    print(f"  -> {msg}")


def ok(label: str, val: Any) -> None:
    if val:
        print(f"     [OK] {label}: {val}")
    else:
        print(f"     [skip] {label} returned empty")


def run() -> None:
    http = HttpCadBridge(port=5080)
    http.connect()
    if not http.is_available:
        print("ERROR: nanoCAD HTTP API not available on port 5080")
        sys.exit(1)

    print("Connected to nanoCAD MCP server")
    print(f"Project output directory: {DEMO_DIR}")
    safe: Any = SafeBridge(http, call_delay=CALL_DELAY)

    # ────────────────────────────────────────────────────────────
    section("0. Project lifecycle: create + (later) save")
    # ────────────────────────────────────────────────────────────
    step(f"create_project: {PROJECT_NAME}.dwg in {DEMO_DIR}")
    safe.create_project(filename=PROJECT_NAME + ".dwg", directory=str(DEMO_DIR))
    time.sleep(1.0)

    # ────────────────────────────────────────────────────────────
    section("1. System & document")
    # ────────────────────────────────────────────────────────────
    step("health_check + get_system_info + get_document_info")
    ok("health", http.check_health())
    ok("system_info", http.get_system_info())
    ok("doc_info", http.get_document_info())
    ok("get_layers", http.get_layers())

    # ────────────────────────────────────────────────────────────
    section("2. System variables & 3D view")
    # ────────────────────────────────────────────────────────────
    step("set_system_variable LTSCALE = 10")
    safe.set_system_variable("LTSCALE", "10")

    step("set_3d_view -> SE Isometric, wireframe")
    safe.set_3d_view("SE Isometric", "wireframe")

    # ────────────────────────────────────────────────────────────
    section("3. Layers — structured layer scheme")
    # ────────────────────────────────────────────────────────────
    layers = [
        ("FRAME", "7"),
        ("DIMENSIONS", "3"),
        ("TEXT", "2"),
        ("CONSTRUCTION", "6"),
        ("BLOCKS", "4"),
    ]
    step("create 5 layers")
    for name, color in layers:
        safe.create_layer(name, color=color)
    safe.set_current_layer("FRAME")

    # ────────────────────────────────────────────────────────────
    section("4. 2D primitives — every shape type")
    # ────────────────────────────────────────────────────────────
    step("frame outline: 2 line segments")
    safe.create_entity("Line", {"x1": 0, "y1": 0, "x2": 200, "y2": 0, "layer": "FRAME"})
    safe.create_entity("Line", {"x1": 200, "y1": 0, "x2": 200, "y2": 150, "layer": "FRAME"})

    step("create_rectangle 100x80")
    rect_h = safe.create_entity("Rectangle", {
        "x": 50, "y": 40, "width": 100, "height": 80, "layer": "FRAME"
    })

    step("create_circle r=15 at (100, 80)")
    circ_h = safe.create_entity("Circle", {
        "cx": 100, "cy": 80, "radius": 15, "layer": "FRAME"
    })

    step("create_arc 90 deg, r=30")
    safe.create_entity("Arc", {
        "cx": 100, "cy": 80, "radius": 30,
        "start_angle": 0, "end_angle": 90, "layer": "FRAME"
    })

    step("create_ellipse major=40, minor=20")
    safe.create_entity("Ellipse", {
        "cx": 100, "cy": 80, "major_axis": 40, "minor_axis": 20, "layer": "FRAME"
    })

    step("create_polyline: closed pentagon")
    verts = []
    for i in range(5):
        ang = math.radians(90 + i * 72)
        verts.append([100 + 50 * math.cos(ang), 80 + 50 * math.sin(ang)])
    safe.create_entity("Polyline", {
        "vertices": verts, "closed": True, "layer": "FRAME"
    })

    step("create_polygon: hexagon r=12")
    safe.create_entity("Polygon", {
        "cx": 160, "cy": 30, "sides": 6, "radius": 12, "layer": "FRAME"
    })

    step("create_donut: r1=8, r2=4")
    safe.create_entity("Donut", {
        "cx": 30, "cy": 130, "inner_radius": 4, "outer_radius": 8, "layer": "FRAME"
    })

    step("create_spline: cubic through 4 points")
    safe.create_entity("Spline", {
        "points": [[20, 20], [60, 80], [120, 60], [180, 100]],
        "degree": 3, "layer": "FRAME"
    })

    step("create_point: at 4 corners")
    for px, py in [(0, 0), (200, 0), (200, 150), (0, 150)]:
        safe.create_entity("Point", {"x": px, "y": py, "layer": "FRAME"})

    step("create_xline + create_ray")
    safe.create_entity("XLine", {
        "base_x": 0, "base_y": 75, "dir_x": 1, "dir_y": 0, "layer": "CONSTRUCTION"
    })
    safe.create_entity("Ray", {
        "base_x": 100, "base_y": 80, "dir_x": math.cos(math.radians(30)),
        "dir_y": math.sin(math.radians(30)), "layer": "CONSTRUCTION"
    })

    step("create_text + create_mtext")
    safe.create_entity("Text", {
        "x": 5, "y": 145, "text": "Frame label", "height": 3, "layer": "TEXT"
    })
    safe.create_entity("MText", {
        "x": 50, "y": 130, "text": "Multi-line\\nannotation", "height": 2.5,
        "width": 40, "layer": "TEXT"
    })

    # ────────────────────────────────────────────────────────────
    section("5. 2D transformations")
    # ────────────────────────────────────────────────────────────
    step("copy_entity, move, rotate, scale, mirror, offset")
    copy_h = safe.copy_entity(rect_h) if rect_h else None
    if copy_h:
        safe.move_entity(copy_h, dx=150, dy=0)
        safe.rotate_entity(copy_h, cx=250, cy=80, angle=45)
        safe.scale_entity(copy_h, cx=250, cy=80, factor=1.5)
        safe.mirror_entity(copy_h, p1_x=0, p1_y=0, p2_x=300, p2_y=0)
    if circ_h:
        safe.offset_entity(circ_h, distance=5)

    # ────────────────────────────────────────────────────────────
    section("6. Hatch")
    # ────────────────────────────────────────────────────────────
    step("create_hatch SOLID on rectangle")
    if rect_h:
        safe.create_hatch(pattern="SOLID", boundary_handles=[rect_h])

    # ────────────────────────────────────────────────────────────
    section("7. 2D Constraints")
    # ────────────────────────────────────────────────────────────
    step("create two lines, apply horizontal/vertical/coincident/distance")
    h_line = safe.create_entity("Line", {
        "x1": 250, "y1": 200, "x2": 350, "y2": 200, "layer": "CONSTRUCTION"
    })
    v_line = safe.create_entity("Line", {
        "x1": 250, "y1": 200, "x2": 250, "y2": 300, "layer": "CONSTRUCTION"
    })
    if h_line:
        safe.constraint_horizontal(h_line)
    if v_line:
        safe.constraint_vertical(v_line)
    if h_line and v_line:
        safe.constraint_coincident(h_line, v_line)

    a_pt = safe.create_entity("Point", {"x": 0, "y": 200, "layer": "CONSTRUCTION"})
    b_pt = safe.create_entity("Point", {"x": 100, "y": 200, "layer": "CONSTRUCTION"})
    if a_pt and b_pt:
        safe.constraint_distance(a_pt, b_pt, distance=100)

    # ────────────────────────────────────────────────────────────
    section("8. Dimensions")
    # ────────────────────────────────────────────────────────────
    step("linear + aligned + angular + radial + diametric + ordinate")
    safe.create_linear_dimension(
        x1=0, y1=0, x2=200, y2=0, dim_x=100, dim_y=15, direction="horizontal"
    )
    safe.create_aligned_dimension(
        x1=0, y1=150, x2=200, y2=150, dim_x=100, dim_y=165
    )
    safe.create_angular_dimension(
        center_x=0, center_y=0,
        p1_x=200, p1_y=0, p2_x=0, p2_y=150,
    )
    if circ_h:
        # NOTE: create_dim_number triggers a UI dialog and hangs the HTTP server.
        # safe.create_dim_number(x=100, y=80, arrow_x=120, arrow_y=85, text="1", index=1)
        pass
        safe.create_diametric_dimension(
            center_x=100, center_y=80, arc_x=85, arc_y=80
        )
    safe.create_ordinate_dimension(
        use_x_axis=True, defining_x=100, defining_y=80,
        leader_x=100, leader_y=110
    )

    # ────────────────────────────────────────────────────────────
    section("9. Engineering symbols")
    # ────────────────────────────────────────────────────────────
    step("roughness, tolerance, datum, weld, leader")
    # NOTE: create_note_comb and create_mleader are skipped because they
    # trigger interactive UI dialogs in nanoCAD and hang the HTTP server.
    # They should only be used from the interactive CAD UI, not via API.
    safe.create_roughness(value="Ra 1.6")
    safe.create_tolerance(type1="○", value1="0.05", letters1="A,B")
    safe.create_datum(letter="A")
    safe.create_weld(length_above="6", length_below="6")
    safe.create_leader(
        arrow_x=180, arrow_y=120, bend_x=190, bend_y=125,
        shelf_x=200, shelf_y=125, text="DETAIL A"
    )

    # ────────────────────────────────────────────────────────────
    section("10. Table")
    # ────────────────────────────────────────────────────────────
    step("create_table 3x3 + edit_table_cell")
    table_h = safe.create_table(rows=3, columns=3, row_height=8, column_width=40)
    if table_h:
        safe.edit_table_cell(handle=table_h, row_index=0, column_index=0, value="Drawn")
        safe.edit_table_cell(handle=table_h, row_index=1, column_index=0, value="DEMO")

    # ────────────────────────────────────────────────────────────
    section("11. Block definition + insertion")
    # ────────────────────────────────────────────────────────────
    step("create_block WASHER + insert + explode + get_blocks")
    washer_circle = safe.create_entity("Circle", {
        "cx": 0, "cy": 0, "radius": 10, "layer": "BLOCKS"
    })
    block_h = safe.create_block(
        name="WASHER",
        handles=[washer_circle] if washer_circle else [],
        base_x=0, base_y=0,
    )
    if block_h:
        safe.insert_block(name="WASHER", x=300, y=80, scale=1.0)
        safe.insert_block(name="WASHER", x=320, y=80, scale=1.5)
        safe.explode_block(name="WASHER")
    blocks = safe.get_blocks() or []
    step(f"   {len(blocks)} block(s) in drawing")

    # ────────────────────────────────────────────────────────────
    section("12. 3D primitives")
    # ────────────────────────────────────────────────────────────
    step("create_box, sphere, cylinder, cone, torus, wedge, pyramid")
    base_box = safe.create_box(x=200, y=150, z=10)
    sph = safe.create_sphere(radius=15)
    cyl = safe.create_cylinder(radius=20, height=80)
    cone = safe.create_cone(radius_bottom=25, height=40)
    torus = safe.create_torus(major_radius=30, minor_radius=8)
    wedge = safe.create_wedge(x=30, y=30, z=30)
    safe.create_pyramid(height=40, sides=4, radius=15)

    if sph:
        safe.move_solid(sph, dx=100, dy=75, dz=30)
    if cyl:
        safe.move_solid(cyl, dx=60, dy=60, dz=0)
    if cone:
        safe.move_solid(cone, dx=140, dy=60, dz=0)
    if torus:
        safe.move_solid(torus, dx=100, dy=75, dz=100)

    # ────────────────────────────────────────────────────────────
    section("13. 3D operations + booleans + edges")
    # ────────────────────────────────────────────────────────────
    step("extrude, revolve, fillet, chamfer, boolean ops")
    prof = safe.create_entity("Rectangle", {
        "x": 250, "y": 200, "width": 10, "height": 10, "layer": "CONSTRUCTION"
    })
    if prof:
        safe.extrude_solid(prof, height=50)

    if base_box:
        safe.fillet_edge(base_box, radius=2.0)
    if base_box and cyl:
        safe.boolean_subtract(base_box, cyl)
    if cone and sph:
        safe.boolean_union(cone, sph)
    if torus and wedge:
        safe.boolean_intersect(torus, wedge)

    # ────────────────────────────────────────────────────────────
    section("14. Document housekeeping + save")
    # ────────────────────────────────────────────────────────────
    step("zoom_extents, undo/redo, purge, save_project")
    safe.zoom_extents()
    safe.undo()
    safe.redo()
    safe.purge()

    doc_info2 = safe.get_document_info()
    if doc_info2:
        step(f"   entities={doc_info2.get('entities_count', '?')}, "
             f"layers={doc_info2.get('layers_count', '?')}")

    safe.save_project(filename=PROJECT_NAME + ".dwg", directory=str(DEMO_DIR))

    # ────────────────────────────────────────────────────────────
    section("DONE")
    # ────────────────────────────────────────────────────────────
    print(f"Project files written to: {DEMO_DIR}")
    if DEMO_DIR.exists():
        print()
        print("Files produced:")
        for f in sorted(DEMO_DIR.iterdir()):
            if f.is_file():
                size_kb = f.stat().st_size / 1024
                print(f"  {f.name:40s} {size_kb:8.1f} KB")


if __name__ == "__main__":
    run()
