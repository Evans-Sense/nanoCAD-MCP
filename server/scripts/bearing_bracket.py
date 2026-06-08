"""Bearing Bracket — Classic 3D Modeling Exercise.

Source: Standard AutoCAD 3D beginner exercise (stepped bracket).
All dimensions in mm.

Design:
  - Base plate: 120 × 80 × 15
  - Vertical column: 40 × 80 × 50 (centered on base, rear edge)
  - Cylindrical boss: R25, H50 (on top of column)
  - Through-bore: R12, H=115 (through boss + column + base)
  - 4 mounting holes: R6, H15 (corners of base)
  - 2 stiffening ribs: 10 × 50 × 15

Layers: Base, Column, Boss, Hole, Mount, Rib
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

    if not solid:
        print("ERROR: 3D operations require .NET engine (full mode)")
        repo.close()
        return

    # ── Layers ────────────────────────────────────────────
    print("Creating layers...")
    for name in ("Base", "Column", "Boss", "Hole", "Mount", "Rib", "Dims"):
        layer.create_layer(name)

    # ══════════════════════════════════════════════════════
    # Constants
    # ══════════════════════════════════════════════════════
    # Base
    base_w = 120.0   # X (width)
    base_d = 80.0    # Y (depth)
    base_th = 15.0   # Z (thickness)

    # Column
    col_w = 40.0     # X
    col_d = base_d   # Y (same as base depth)
    col_h = 50.0     # Z (height above base)

    # Boss (cylindrical, on top of column)
    boss_r = 25.0    # radius
    boss_h = 50.0    # Z height

    # Through-bore
    bore_r = 12.0

    # Mount holes
    mount_r = 6.0
    mount_margin = 15.0  # from edge of base

    # Ribs
    rib_th = 10.0    # X thickness
    rib_h = 50.0     # Z height (same as column)
    rib_d = 30.0     # Y length (from column rear toward center)

    # ══════════════════════════════════════════════════════
    # Helper
    # ══════════════════════════════════════════════════════
    def make(label: str, method: str, *args: object) -> str | None:
        fn = getattr(solid, method)
        result = fn(*args)
        if isinstance(result, dict):
            if "error" in result:
                print(f"  ERROR {label}: {result}")
                return None
            h = result.get("handle")
            if h:
                print(f"  {label}: {h}")
                return h
        print(f"  {label}: unexpected {result}")
        return None

    # ══════════════════════════════════════════════════════
    # 2D DRAWING (orthographic views)
    # ══════════════════════════════════════════════════════
    print("Drawing 2D views...")

    # Front view (XY plane, schematic)
    fx, fy = 300.0, 200.0
    # Base rectangle
    entity.create_rectangle(fx - base_w / 2, fy, fx + base_w / 2, fy + base_th, layer="Base")
    # Column
    entity.create_rectangle(fx - col_w / 2, fy + base_th, fx + col_w / 2, fy + base_th + col_h, layer="Column")
    # Boss outline
    boss_cx = fx
    boss_cy = fy + base_th + col_h + boss_h / 2
    entity.create_circle(boss_cx, boss_cy, boss_r, layer="Boss")
    # Bore
    entity.create_circle(boss_cx, boss_cy, bore_r, layer="Hole")
    # Mount holes
    for mx in (-(base_w / 2 - mount_margin), (base_w / 2 - mount_margin)):
        entity.create_circle(fx + mx, fy - 10, mount_r, layer="Mount")
    entity.create_text(fx, fy - 50, "FRONT VIEW", 25, layer="Dims")

    # Side view (YZ plane, schematic)
    sx, sy = -100.0, 150.0
    # Base
    entity.create_rectangle(sx, sy, sx + base_d, sy + base_th, layer="Base")
    # Column
    entity.create_rectangle(sx, sy + base_th, sx + col_d, sy + base_th + col_h, layer="Column")
    # Boss
    boss_cy_s = sy + base_th + col_h + boss_h / 2
    entity.create_circle(sx + base_d / 2, boss_cy_s, boss_r, layer="Boss")
    entity.create_text(sx + base_d / 2, sy - 50, "SIDE VIEW", 25, layer="Dims")

    # ══════════════════════════════════════════════════════
    # 3D SOLID MODEL
    # ══════════════════════════════════════════════════════
    print("Creating 3D solid model...")

    # ── 1. Base plate ─────────────────────────────────────
    print("Step 1: Base plate...")
    h = make("Base", "create_box", base_w, base_d, base_th)
    if not h:
        repo.close()
        return
    # Box at origin: Z from -base_th/2 to +base_th/2
    # Move so bottom is at Z=0
    solid.move_solid(h, 0, 0, base_th / 2)
    base_handle = h

    # ── 2. Vertical column ────────────────────────────────
    print("Step 2: Vertical column...")
    h = make("Column", "create_box", col_w, col_d, col_h)
    if h:
        # Column bottom at base_th, top at base_th + col_h
        # Center at Z = base_th + col_h/2
        solid.move_solid(h, 0, 0, base_th + col_h / 2)
        # Union column with base
        r = solid.boolean_union(base_handle, h)
        if "error" not in r:
            base_handle = r["handle"]
            print(f"  Union base+column: {base_handle}")

    # ── 3. Cylindrical boss ───────────────────────────────
    print("Step 3: Cylindrical boss...")
    h = make("Boss", "create_cylinder", boss_r, boss_h)
    if h:
        # Boss bottom at base_th + col_h, top at base_th + col_h + boss_h
        solid.move_solid(h, 0, 0, base_th + col_h + boss_h / 2)
        # Union boss with base_handle
        r = solid.boolean_union(base_handle, h)
        if "error" not in r:
            base_handle = r["handle"]
            print(f"  Union +boss: {base_handle}")

    # ── 4. Through-bore ───────────────────────────────────
    print("Step 4: Through-bore...")
    total_h = base_th + col_h + boss_h
    h = make("Bore", "create_cylinder", bore_r, total_h)
    if h:
        solid.move_solid(h, 0, 0, total_h / 2)
        r = solid.boolean_subtract(base_handle, h)
        if "error" not in r:
            base_handle = r["handle"]
            print(f"  Subtract bore: {base_handle}")

    # ── 5. Mount holes (×4) ───────────────────────────────
    print("Step 5: Mount holes...")
    hole_positions = [
        (-(base_w / 2 - mount_margin), -(base_d / 2 - mount_margin)),
        ( (base_w / 2 - mount_margin), -(base_d / 2 - mount_margin)),
        (-(base_w / 2 - mount_margin),  (base_d / 2 - mount_margin)),
        ( (base_w / 2 - mount_margin),  (base_d / 2 - mount_margin)),
    ]
    for i, (hx, hy) in enumerate(hole_positions, 1):
        h = make(f"Mount hole {i}", "create_cylinder", mount_r, base_th)
        if h:
            solid.move_solid(h, hx, hy, base_th / 2)
            r = solid.boolean_subtract(base_handle, h)
            if "error" not in r:
                base_handle = r["handle"]
                print(f"  Subtract mount {i}: {base_handle}")

    # ── 6. Stiffening ribs (×2) ───────────────────────────
    print("Step 6: Stiffening ribs...")
    # Ribs are triangular-ish. We'll approximate with thin boxes
    # placed at the junction of base and column, extending along Y.
    rib_x = rib_th / 2
    for rib_y_sign in (-1, 1):
        rib_y = rib_y_sign * (col_d / 2 - rib_d / 2)
        h = make(f"Rib {'F' if rib_y_sign < 0 else 'R'}", "create_box", rib_th, rib_d, rib_h)
        if h:
            # Rib sits on base, extends up col_h
            solid.move_solid(h, rib_x, rib_y, base_th + rib_h / 2)
            # Union rib with body
            r = solid.boolean_union(base_handle, h)
            if "error" not in r:
                base_handle = r["handle"]
                print(f"  Union rib: {base_handle}")

    # ── 7. Final view ─────────────────────────────────────
    print("Setting view...")
    solid.set_3d_view("swiso", "realistic")

    # ── 8. Properties ─────────────────────────────────────
    props = solid.get_solid_properties(base_handle)
    if props:
        area = props.get("area", 0)
        print(f"  Final area: {area:.1f} mm^2")

    # ── Finalize ──────────────────────────────────────────
    doc.zoom_extents()

    print("\n" + "=" * 55)
    print("Bearing Bracket - 3D exercise complete!")
    print("  1. Base plate:   120 x 80 x 15")
    print("  2. Column:        40 x 80 x 50")
    print("  3. Boss:          R25 x H50")
    print("  4. Through-bore:  R12 (full height)")
    print("  5. Mount holes:   4 x R6 (corners)")
    print("  6. Stiffeners:    2 x ribs")
    print("=" * 55)

    repo.close()
    print("Connection closed.")


if __name__ == "__main__":
    main()
