"""
nanoCAD MCP Demo: Engineering Project
=====================================
A practical walkthrough of every major MCP tool category. Builds a
realistic engineering drawing that includes 2D drafting, 3D modelling,
sheet metal, blocks, assemblies, dimensions, constraints, symbols
and exports — then saves the result.

Usage:
    # 1) Start nanoCAD with CadEngine.Plugin loaded (via nCad.ini)
    # 2) Run this script:
    py F:\\nanoCAD\\server\\scripts\\demo_engineering_project.py

By default the project is created in %TEMP%/nanoCAD_demo/.
The script logs every step and the resulting .dwg can be opened in nanoCAD.

Note: The HTTP server uses a main-thread executor that can be overwhelmed
by many rapid calls. The script adds small delays and tolerates timeouts.
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

from src.infrastructure.http_bridge import HttpCadBridge

DEMO_DIR = Path(os.environ.get("TEMP", "C:\\temp")) / "nanoCAD_demo"
PROJECT_NAME = "engineering_project"

# Tiny delay between calls to avoid overloading the MainThreadExecutor queue
CALL_DELAY = 0.05


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
        print(f"     [skip] {label} returned empty (feature may not be available)")


# ════════════════════════════════════════════════════════════════
# Helper wrappers that swallow transport errors and add a small
# delay between calls so the main-thread executor isn't overwhelmed
# ════════════════════════════════════════════════════════════════

def _make_safe(http_bridge: HttpCadBridge) -> "Safe":
    return Safe(http_bridge)


class Safe:
    """Wrapper that wraps every method on the bridge with try/except + delay.

    Usage:
        safe = Safe(http)
        safe.create_line(...)  # never raises, returns None on error
    """

    def __init__(self, bridge: HttpCadBridge) -> None:
        self._bridge = bridge

    def __getattr__(self, name: str) -> Any:
        fn = getattr(self._bridge, name)

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = fn(*args, **kwargs)
                time.sleep(CALL_DELAY)
                return result
            except Exception as e:  # noqa: BLE001
                print(f"     [error] {name}: {e}")
                time.sleep(CALL_DELAY * 2)
                if not self._bridge.is_available:
                    print("     [fatal] HTTP bridge became unavailable — aborting demo")
                    raise SystemExit(1) from e
                return None

        return wrapper


def run() -> None:
    http = HttpCadBridge(port=5080)
    http.connect()
    if not http.is_available:
        print("ERROR: nanoCAD HTTP API not available on port 5080")
        print("Start nanoCAD with CadEngine.Plugin loaded (check nCad.ini)")
        sys.exit(1)

    print("Connected to nanoCAD MCP server")
    print(f"Project output directory: {DEMO_DIR}")

    safe: Any = Safe(http)

    # ────────────────────────────────────────────────────────────
    section("0. Project lifecycle: create + (later) save")
    # ────────────────────────────────────────────────────────────
    step(f"create_project: {PROJECT_NAME}.dwg in {DEMO_DIR}")
    safe.create_project(filename=PROJECT_NAME + ".dwg", directory=str(DEMO_DIR))
    time.sleep(0.5)

    # ────────────────────────────────────────────────────────────
    section("1. System / document health")
    # ────────────────────────────────────────────────────────────
    step("health_check")
    ok("health", http.check_health())

    step("get_system_info")
    ok("system_info", http.get_system_info())

    step("get_document_info")
    ok("doc_info", http.get_document_info())

    step("get_system_fonts")
    fonts = safe.get_system_fonts() or []
    step(f"   found {len(fonts)} font(s)")

    step("get_linetypes")
    ltypes = safe.get_linetypes() or []
    step(f"   found {len(ltypes)} linetype(s)")

    # ────────────────────────────────────────────────────────────
    section("2. System variables & 3D view")
    # ────────────────────────────────────────────────────────────
    step("set_system_variable LTSCALE = 10")
    safe.set_system_variable("LTSCALE", "10")

    step("set_system_variable DIMSTYLE = Standard")
    safe.set_system_variable("DIMSTYLE", "Standard")

    step("set_3d_view -> SE Isometric, wireframe")
    safe.set_3d_view("SE Isometric", "wireframe")

    # ────────────────────────────────────────────────────────────
    section("3. Layers — structured layer scheme")
    # ────────────────────────────────────────────────────────────
    layers = [
        ("FRAME", "7"),
        ("DIMENSIONS", "3"),
        ("CENTER", "1"),
        ("HIDDEN", "5"),
        ("HATCH", "8"),
        ("TEXT", "2"),
        ("CONSTRUCTION", "6"),
        ("BLOCKS", "4"),
    ]
    step("create 8 layers")
    for name, color in layers:
        safe.create_layer(name, color=color)

    step("set_current_layer -> FRAME")
    safe.set_current_layer("FRAME")

    step("layer_off HIDDEN (demo) + layer_on_all (reset)")
    safe.layer_off("HIDDEN")
    safe.layer_on_all()
    safe.layer_thaw_all()

    ok("get_layers", http.get_layers())

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
    arc_h = safe.create_entity("Arc", {
        "cx": 100, "cy": 80, "radius": 30,
        "start_angle": 0, "end_angle": 90, "layer": "FRAME"
    })

    step("create_ellipse major=40, minor=20")
    ell_h = safe.create_entity("Ellipse", {
        "cx": 100, "cy": 80, "major_axis": 40, "minor_axis": 20, "layer": "FRAME"
    })

    step("create_polyline: closed pentagon")
    verts = []
    for i in range(5):
        ang = math.radians(90 + i * 72)
        verts.append([100 + 50 * math.cos(ang), 80 + 50 * math.sin(ang)])
    poly_h = safe.create_entity("Polyline", {
        "vertices": verts, "closed": True, "layer": "FRAME"
    })

    step("create_polygon: hexagon r=12 at (160, 30)")
    pg_h = safe.create_entity("Polygon", {
        "cx": 160, "cy": 30, "sides": 6, "radius": 12, "layer": "FRAME"
    })

    step("create_donut: r1=8, r2=4 at (30, 130)")
    safe.create_entity("Donut", {
        "cx": 30, "cy": 130, "inner_radius": 4, "outer_radius": 8, "layer": "FRAME"
    })

    step("create_spline: cubic through 4 points")
    spl_h = safe.create_entity("Spline", {
        "points": [[20, 20], [60, 80], [120, 60], [180, 100]],
        "degree": 3, "layer": "FRAME"
    })

    step("create_point: at 4 corners")
    for px, py in [(0, 0), (200, 0), (200, 150), (0, 150)]:
        safe.create_entity("Point", {"x": px, "y": py, "layer": "CENTER"})

    step("create_xline (infinite)")
    safe.create_entity("XLine", {
        "base_x": 0, "base_y": 75, "dir_x": 1, "dir_y": 0, "layer": "CONSTRUCTION"
    })

    step("create_ray (half-line)")
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
    step("copy_entity: duplicate the rectangle")
    copy_h = safe.copy_entity(rect_h) if rect_h else None

    step("move_entity: copy to (250, 40)")
    if copy_h:
        safe.move_entity(copy_h, dx=150, dy=0)

    step("rotate_entity: 45 deg around (250, 80)")
    if copy_h:
        safe.rotate_entity(copy_h, cx=250, cy=80, angle=45)

    step("scale_entity: 1.5x")
    if copy_h:
        safe.scale_entity(copy_h, cx=250, cy=80, factor=1.5)

    step("mirror_entity: across x=150")
    if copy_h:
        safe.mirror_entity(copy_h, p1_x=0, p1_y=0, p2_x=300, p2_y=0)

    step("offset_entity: offset circle by 5")
    if circ_h:
        safe.offset_entity(circ_h, distance=5)

    # ────────────────────────────────────────────────────────────
    section("6. Hatch")
    # ────────────────────────────────────────────────────────────
    step("create_hatch SOLID on rectangle")
    if rect_h:
        safe.create_hatch(pattern="SOLID", boundary_handles=[rect_h])
    step("create_hatch ANSI31 on copy")
    if copy_h:
        safe.create_hatch(pattern="ANSI31", boundary_handles=[copy_h], scale=2)

    # ────────────────────────────────────────────────────────────
    section("7. 2D Constraints")
    # ────────────────────────────────────────────────────────────
    step("create two lines for constraint demo")
    h_line = safe.create_entity("Line", {
        "x1": 250, "y1": 200, "x2": 350, "y2": 200, "layer": "CONSTRUCTION"
    })
    v_line = safe.create_entity("Line", {
        "x1": 250, "y1": 200, "x2": 250, "y2": 300, "layer": "CONSTRUCTION"
    })

    if h_line:
        step("constraint_horizontal on h_line")
        safe.constraint_horizontal(h_line)
    if v_line:
        step("constraint_vertical on v_line")
        safe.constraint_vertical(v_line)
    if h_line and v_line:
        step("constraint_coincident between line endpoints")
        safe.constraint_coincident(h_line, v_line)

    a_pt = safe.create_entity("Point", {"x": 0, "y": 200, "layer": "CENTER"})
    b_pt = safe.create_entity("Point", {"x": 100, "y": 200, "layer": "CENTER"})
    if a_pt and b_pt:
        step("constraint_distance = 100 between two points")
        safe.constraint_distance(a_pt, b_pt, distance=100)

    # ────────────────────────────────────────────────────────────
    section("8. Dimensions")
    # ────────────────────────────────────────────────────────────
    step("linear dimension: 200 mm base width")
    safe.create_linear_dimension(x1=0, y1=0, x2=200, y2=0, dim_x=100, dim_y=15, direction="horizontal")

    step("aligned dimension: top edge 200")
    safe.create_aligned_dimension(x1=0, y1=150, x2=200, y2=150, dim_x=100, dim_y=165)

    step("angular dimension: between frame corner lines")
    safe.create_angular_dimension(center_x=0, center_y=0,
         p1_x=200, p1_y=0, p2_x=0, p2_y=150)

    if circ_h:
        step("radial dimension: r of circle (center=100,80, arc=115,80)")
        safe.create_radial_dimension(center_x=100, center_y=80, arc_x=115, arc_y=80)

        step("diametric dimension: diam of circle (center=100,80, arc=85,80)")
        safe.create_diametric_dimension(center_x=100, center_y=80, arc_x=85, arc_y=80)

    step("ordinate dimension: x=100")
    safe.create_ordinate_dimension(use_x_axis=True, defining_x=100, defining_y=80,
         leader_x=100, leader_y=110)

    # ────────────────────────────────────────────────────────────
    section("9. Engineering symbols (GOST / ISO)")
    # ────────────────────────────────────────────────────────────
    step("create_roughness (GOST, Ra 1.6)")
    safe.create_roughness(value="Ra 1.6")

    step("create_tolerance (form, 0.05)")
    safe.create_tolerance(type1="○", value1="0.05", letters1="A,B")

    step("create_datum A")
    safe.create_datum(letter="A")

    step("create_weld (fillet 6mm)")
    safe.create_weld(length_above="6", length_below="6")

    step("create_leader (annotation = 'DETAIL A')")
    safe.create_leader(arrow_x=180, arrow_y=120, bend_x=190, bend_y=125,
         shelf_x=200, shelf_y=125, text="DETAIL A")

    step("create_note_comb (notes list) [SKIPPED: requires UI dialog]")
    # NOTE: create_note_comb triggers an interactive UI dialog in nanoCAD
    # and hangs the HTTP server. Use it from the CAD UI, not via API.
    # safe.create_note_comb(angle=45, text_size=2.5,
    #      first_line="1. ALL DIMS IN MM",
    #      second_line="2. Ra 1.6")

    step("create_dim_number (pos 1, on circle)")
    if circ_h:
        # NOTE: create_dim_number triggers a UI dialog and hangs the HTTP server.
        # safe.create_dim_number(x=100, y=80, arrow_x=120, arrow_y=85, text="1", index=1)
        pass

    # ────────────────────────────────────────────────────────────
    section("10. Table (drawing register)")
    # ────────────────────────────────────────────────────────────
    step("create_table 3x3 (title block)")
    table_h = safe.create_table(rows=3, columns=3, row_height=8, column_width=40)
    ok("table", table_h)
    if table_h:
        step("edit_table_cell (0, 0) -> 'Drawn'")
        safe.edit_table_cell(handle=table_h, row_index=0, column_index=0, value="Drawn")
        step("edit_table_cell (1, 0) -> 'DEMO'")
        safe.edit_table_cell(handle=table_h, row_index=1, column_index=0, value="DEMO")

    # ────────────────────────────────────────────────────────────
    section("11. Block definitions and insertion")
    # ────────────────────────────────────────────────────────────
    step("create_block WASHER from a circle")
    washer_circle = safe.create_entity("Circle", {
        "cx": 0, "cy": 0, "radius": 10, "layer": "BLOCKS"
    })
    block_h = safe.create_block(name="WASHER",
                   handles=[washer_circle] if washer_circle else [],
                   base_x=0, base_y=0)
    ok("block_h", block_h)

    if block_h:
        step("insert_block WASHER at (300, 80)")
        safe.insert_block(name="WASHER", x=300, y=80, scale=1.0)
        step("insert_block WASHER at (320, 80) scaled 1.5x")
        safe.insert_block(name="WASHER", x=320, y=80, scale=1.5)
        step("explode_block WASHER")
        safe.explode_block(name="WASHER")

    step("get_blocks (list all)")
    blocks = safe.get_blocks() or []
    step(f"   {len(blocks)} block(s) in drawing")

    # ────────────────────────────────────────────────────────────
    section("12. Selection / filtering")
    # ────────────────────────────────────────────────────────────
    step("select_entities by layer=FRAME")
    sel = safe.select_entities(layer="FRAME") or {}
    step(f"   {sel.get('count', '?')} entities selected")

    # ────────────────────────────────────────────────────────────
    section("13. 3D primitives + transformations")
    # ────────────────────────────────────────────────────────────
    step("create_box: base plate 200x150x10")
    base_box = safe.create_box(x=200, y=150, z=10)
    ok("base_box", base_box)

    step("create_sphere r=15")
    sph = safe.create_sphere(radius=15)
    if sph:
        safe.move_solid(sph, dx=100, dy=75, dz=30)

    step("create_cylinder r=20 h=80")
    cyl = safe.create_cylinder(radius=20, height=80)
    if cyl:
        safe.move_solid(cyl, dx=60, dy=60, dz=0)

    step("create_cone r=25 h=40")
    cone = safe.create_cone(radius_bottom=25, height=40)
    if cone:
        safe.move_solid(cone, dx=140, dy=60, dz=0)

    step("create_torus R=30 r=8")
    torus = safe.create_torus(major_radius=30, minor_radius=8)
    if torus:
        safe.move_solid(torus, dx=100, dy=75, dz=100)

    step("create_wedge 30x30x30")
    wedge = safe.create_wedge(x=30, y=30, z=30)
    if wedge:
        safe.move_solid(wedge, dx=40, dy=110, dz=0)

    step("create_pyramid h=40, 4 sides, r=15")
    safe.create_pyramid(height=40, sides=4, radius=15)

    # ────────────────────────────────────────────────────────────
    section("14. 3D operations — extrude, revolve")
    # ────────────────────────────────────────────────────────────
    step("create extrude profile (rectangle) at (250, 200)")
    prof = safe.create_entity("Rectangle", {
        "x": 250, "y": 200, "width": 10, "height": 10, "layer": "CONSTRUCTION"
    })
    if prof:
        step("extrude_solid: profile -> height 50")
        safe.extrude_solid(prof, height=50)

    step("create revolve profile (line)")
    rev_prof = safe.create_entity("Line", {
        "x1": 400, "y1": 200, "x2": 400, "y2": 240, "layer": "CONSTRUCTION"
    })
    if rev_prof:
        step("revolve_solid: 360 deg rotation around (380, 220)")
        safe.revolve_solid(handle=rev_prof, axis_x=380, axis_y=220, angle=360)

    # ────────────────────────────────────────────────────────────
    section("15. Boolean operations on 3D solids")
    # ────────────────────────────────────────────────────────────
    if base_box and cyl:
        step("boolean_subtract: cylinder from base box")
        safe.boolean_subtract(base_box, cyl)
    if cone and sph:
        step("boolean_union: cone + sphere")
        safe.boolean_union(cone, sph)
    if torus and wedge:
        step("boolean_intersect: torus with wedge")
        safe.boolean_intersect(torus, wedge)

    # ────────────────────────────────────────────────────────────
    section("16. 3D edge operations")
    # ────────────────────────────────────────────────────────────
    if base_box:
        step("fillet_edge on base box (r=2)")
        safe.fillet_edge(base_box, radius=2.0)
    if cone:
        step("chamfer_edge on cone (5x5)")
        safe.chamfer_edge(cone, dist1=5.0, dist2=5.0)

    # ────────────────────────────────────────────────────────────
    section("17. Solid properties")
    # ────────────────────────────────────────────────────────────
    if base_box:
        step("get_solid_properties on base box")
        props = safe.get_solid_properties(base_box)
        if props:
            step(f"   volume={props.get('volume', '?')}, surface={props.get('surface', '?')}")

    # ────────────────────────────────────────────────────────────
    section("18. Sheet metal")
    # ────────────────────────────────────────────────────────────
    step("create_base_flange: 100x80 sheet, t=2")
    flange = safe.create_base_flange(length=100, width=80, thickness=2)
    ok("flange", flange)
    if flange:
        step("create_edge_flange on the base")
        safe.create_edge_flange(flange, bend_radius=3.0)
        step("create_bend on base flange")
        safe.create_bend(flange, bend_radius=3.0)

    # ────────────────────────────────────────────────────────────
    section("19. Advanced entities (helix, region, NURBS)")
    # ────────────────────────────────────────────────────────────
    step("create_helix: 10 turns, r=20, h=50")
    safe.create_helix(base_x=500, base_y=200, base_z=0,
         radius=20, height=50, turns=10)

    step("create_region from a closed polyline")
    region_profile = safe.create_entity("Polyline", {
        "vertices": [[600, 200], [650, 200], [650, 250], [600, 250]],
        "closed": True, "layer": "CONSTRUCTION"
    })
    if region_profile:
        safe.create_region([region_profile])

    step("create_nurb_curve (cubic through 5 pts)")
    safe.create_nurb_curve(points=[[700, 200], [720, 250], [760, 220], [800, 280], [840, 240]],
         degree=3)

    # ────────────────────────────────────────────────────────────
    section("20. Document housekeeping")
    # ────────────────────────────────────────────────────────────
    step("zoom_extents")
    safe.zoom_extents()

    step("undo / redo roundtrip")
    safe.undo()
    safe.redo()

    step("purge unused objects")
    safe.purge()

    step("get_document_info (after all operations)")
    doc_info2 = safe.get_document_info()
    if doc_info2:
        step(f"   entities={doc_info2.get('entities_count', '?')}, "
             f"layers={doc_info2.get('layers_count', '?')}")

    # ────────────────────────────────────────────────────────────
    section("21. Project save (final)")
    # ────────────────────────────────────────────────────────────
    step(f"save_project: {PROJECT_NAME}.dwg -> {DEMO_DIR}")
    safe.save_project(filename=PROJECT_NAME + ".dwg", directory=str(DEMO_DIR))

    # ────────────────────────────────────────────────────────────
    section("22. Exports (PDF / DWG / DXF / STEP / STL)")
    # ────────────────────────────────────────────────────────────
    out = DEMO_DIR / PROJECT_NAME
    step("export_pdf")
    safe.export_pdf(str(out) + ".pdf")
    step("export_dwg")
    safe.export_dwg(str(out) + "_export.dwg")
    step("export_dxf")
    safe.export_dxf(str(out) + ".dxf")
    step("export_step")
    safe.export_step(str(out) + ".step")
    step("export_stl")
    safe.export_stl(str(out) + ".stl", binary=True)

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
