"""Flange Coupling — 2D orthographic views + 3D solid model.

Design:
  - Flange Ø200 mm outer, Ø80 mm bore, 20 mm thick
  - 6 × Ø12 mm bolt holes on PCD Ø160 mm
  - Front view (2D) + Isometric 3D solid with bore and bolt holes

Layers: Construction, Outline, Holes, Dimensions, 3D_Solid
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.cad_repository import CadRepository
from src.application.use_cases import (
    DocumentUseCase,
    EntityUseCase,
    LayerUseCase,
    SolidUseCase,
)


def main() -> None:
    repo = CadRepository()
    if not repo.connect():
        print("Cannot connect to nanoCAD")
        return
    mode = repo.connection_mode
    print(f"Connected in '{mode}' mode")

    entity = EntityUseCase(repo)
    layer = LayerUseCase(repo)
    doc = DocumentUseCase(repo)
    solid = SolidUseCase(repo) if mode == "full" else None

    # ── Layers ────────────────────────────────────────────
    print("Creating layers...")
    for name in ("Construction", "Outline", "Holes", "Dimensions", "3D_Solid"):
        layer.create_layer(name)

    # ── Constants ─────────────────────────────────────────
    flange_od = 200.0       # outer diameter (mm)
    bore_d = 80.0           # inner bore diameter
    pcd = 160.0             # pitch circle diameter
    bolt_d = 12.0           # bolt hole diameter
    bolt_count = 6
    flange_thickness = 20.0

    cx, cy = 300.0, 250.0   # center of 2D front view

    # ══════════════════════════════════════════════════════
    # 2D FRONT VIEW
    # ══════════════════════════════════════════════════════

    print("Drawing 2D front view...")

    # ── Outer flange circle ──────────────────────────────
    entity.create_circle(cx, cy, flange_od / 2, layer="Outline")

    # ── Inner bore circle ────────────────────────────────
    entity.create_circle(cx, cy, bore_d / 2, layer="Outline")

    # ── Construction circle (PCD) ────────────────────────
    entity.create_circle(cx, cy, pcd / 2, layer="Construction")

    # ── Bolt holes ───────────────────────────────────────
    print("Adding bolt holes...")
    for i in range(bolt_count):
        angle = 2 * math.pi * i / bolt_count
        bx = cx + (pcd / 2) * math.cos(angle)
        by = cy + (pcd / 2) * math.sin(angle)
        entity.create_circle(bx, by, bolt_d / 2, layer="Holes")

    # ── Center lines ─────────────────────────────────────
    print("Adding center lines...")
    cl_ext = flange_od / 2 + 30
    entity.create_line(cx - cl_ext, cy, cx + cl_ext, cy, layer="Construction")
    entity.create_line(cx, cy - cl_ext, cx, cy + cl_ext, layer="Construction")

    # ── Dimensions ───────────────────────────────────────
    print("Adding dimensions...")
    entity.create_text(cx, cy - flange_od / 2 - 40, f"Ø{flange_od:.0f}", 30, layer="Dimensions")
    entity.create_text(cx, cy + flange_od / 2 + 20, f"Ø{bore_d:.0f} bore", 25, layer="Dimensions")
    entity.create_text(cx + pcd / 2 + 20, cy + 60, f"{bolt_count}×Ø{bolt_d:.0f}", 25, layer="Dimensions")
    entity.create_text(cx, cy - 10, "FRONT VIEW", 35, layer="Dimensions")

    # ══════════════════════════════════════════════════════
    # 3D SOLID MODEL
    # ══════════════════════════════════════════════════════

    if solid:
        print("Creating 3D solid model...")

        # 1. Main flange cylinder at origin (R=100, H=20)
        result = solid.create_cylinder(flange_od / 2, flange_thickness)
        if "error" in result:
            print(f"  ERROR creating flange body: {result}")
            repo.close()
            return
        flange_handle = result["handle"]
        print(f"  Flange body created: {flange_handle}")

        # 2. Bore cylinder (R=40, H=20) at origin → subtract
        result2 = solid.create_cylinder(bore_d / 2, flange_thickness)
        if "error" in result2:
            print(f"  ERROR creating bore: {result2}")
            repo.close()
            return
        bore_handle = result2["handle"]
        print(f"  Bore body created: {bore_handle}")

        # 3. Subtract bore from flange
        result3 = solid.boolean_subtract(flange_handle, bore_handle)
        if "error" in result3:
            print(f"  ERROR subtracting bore: {result3}")
            repo.close()
            return
        main_handle = result3["handle"]
        print(f"  Bore subtracted: {main_handle}")

        # 4. Create bolt holes
        for i in range(bolt_count):
            angle = 2 * math.pi * i / bolt_count
            # Each bolt hole is created at origin, then moved to PCD position
            r = solid.create_cylinder(bolt_d / 2, flange_thickness)
            if "error" in r:
                print(f"  ERROR creating bolt hole {i}: {r}")
                continue
            bh_handle = r["handle"]

            # Move bolt hole to PCD position
            bx = (pcd / 2) * math.cos(angle)
            by = (pcd / 2) * math.sin(angle)
            solid.move_solid(bh_handle, bx, by, 0)

            # Subtract bolt hole from main flange
            r2 = solid.boolean_subtract(main_handle, bh_handle)
            if "error" in r2:
                print(f"  ERROR subtracting bolt hole {i}: {r2}")
                continue
            main_handle = r2["handle"]
            print(f"  Bolt hole {i+1}/{bolt_count} subtracted")

        # 5. Set isometric view
        solid.set_3d_view("swiso", "realistic")

        # 6. Get final solid properties
        props = solid.get_solid_properties(main_handle)
        if props:
            print(f"  Final solid properties: {props}")

    # ── Finalize ──────────────────────────────────────────
    doc.zoom_extents()
    print("\nDone! Flange coupling created successfully.")
    print("  • 2D front view with center lines, bolt holes, and dimensions")
    print("  • 3D solid with bore and 6 bolt holes")

    repo.close()
    print("Connection closed.")


if __name__ == "__main__":
    main()
