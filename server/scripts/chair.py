"""Modern Office Chair — 2D views + 3D solid model.

Design (mm):
  - 4 cylindrical legs (R15 × 450) on 460 × 460 grid
  - Horizontal cross-bars between legs
  - Seat cushion (480 × 460 × 40) at height 450
  - Backrest (480 × 30 × 350) behind seat
  - Two armrests (350 × 40 × 25) at sides

Layers: Legs, Frame, Seat, Backrest, Armrests, Dimensions
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.cad_repository import CadRepository
from src.application.use_cases import DocumentUseCase, EntityUseCase, LayerUseCase, SolidUseCase


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

    # ── New document (clears any previous drawing) ────────
    print("Creating new document...")
    doc.new_document()

    # ── Layers ────────────────────────────────────────────
    print("Creating layers...")
    for name in ("Legs", "Frame", "Seat", "Backrest", "Armrests", "Dimensions"):
        layer.create_layer(name)

    # ══════════════════════════════════════════════════════
    # 2D FRONT VIEW (at Y = -500, schematic)
    # ══════════════════════════════════════════════════════
    print("Drawing 2D front view...")

    fx, fy = 200.0, 300.0  # front view origin

    # Seat profile (front)
    entity.create_rectangle(fx - 240, fy - 20, fx + 240, fy + 20, layer="Seat")

    # Legs (front)
    leg_h = 430
    for lx in (-220, 220):
        entity.create_line(fx + lx, fy, fx + lx, fy + leg_h, layer="Legs")

    # Backrest (front)
    entity.create_rectangle(fx - 240, fy + 30, fx + 240, fy + 380, layer="Backrest")

    # Armrests (front)
    for ax in (-270, 270):
        entity.create_rectangle(fx + ax, fy - 50, fx + ax - 30, fy + 30, layer="Armrests")

    # Label
    entity.create_text(fx, fy - 80, "FRONT VIEW", 30, layer="Dimensions")

    # ══════════════════════════════════════════════════════
    # 2D SIDE VIEW (at X = -500)
    # ══════════════════════════════════════════════════════
    print("Drawing 2D side view...")

    sx, sy = -300.0, 200.0  # side view origin (shifted left)

    # Seat profile (side)
    entity.create_rectangle(sx - 20, sy, sx + 20, sy + 460, layer="Seat")

    # Legs (side)
    for lz in (-15, 15):
        entity.create_line(sx + lz, sy + 460, sx + lz, sy + 460 + 430, layer="Legs")

    # Backrest (side)
    entity.create_rectangle(sx - 15, sy + 460 + 30, sx + 15, sy + 460 + 380, layer="Backrest")

    # Label
    entity.create_text(sx, sy - 60, "SIDE VIEW", 30, layer="Dimensions")

    # ══════════════════════════════════════════════════════
    # 3D SOLID MODEL
    # ══════════════════════════════════════════════════════
    if solid:
        print("Creating 3D solid model...")

        # ── Helper to create a solid and verify result ────
        def make(label: str, method: str, *args: object, **kw: object) -> str | None:
            fn = getattr(solid, method)
            result = fn(*args, **kw)
            if isinstance(result, dict):
                if "error" in result:
                    print(f"  ERROR {label}: {result}")
                    return None
                h = result.get("handle")
                if h:
                    print(f"  {label}: {h}")
                    return h
            print(f"  {label}: unexpected result {result}")
            return None

        # ── Constants ─────────────────────────────────────
        leg_r = 15.0
        leg_h = 450.0
        leg_offset = 220.0  # half of 460 grid

        seat_w = 480.0
        seat_d = 460.0
        seat_th = 40.0
        seat_z = 450.0  # top of seat from floor

        back_w = 480.0
        back_th = 30.0
        back_h = 350.0

        arm_len = 350.0
        arm_w = 40.0
        arm_th = 25.0

        # ── 1. Four legs ──────────────────────────────────
        print("Creating legs...")
        leg_handles: list[str] = []
        for lx, ly in [
            (leg_offset, leg_offset),
            (-leg_offset, leg_offset),
            (-leg_offset, -leg_offset),
            (leg_offset, -leg_offset),
        ]:
            h = make(f"Leg ({lx:.0f}, {ly:.0f})", "create_cylinder", leg_r, leg_h)
            if h:
                leg_handles.append(h)
                # Move so bottom is at Z=0 and position in XY
                # Cylinder center was at origin, extends -225..+225 in Z
                # Move by (lx, ly, leg_h/2) → bottom at Z=0
                solid.move_solid(h, lx, ly, leg_h / 2)

        # ── 2. Cross-bars between legs ────────────────────
        print("Creating cross-bars...")
        bar_r = 6.0

        # Cross-bar 1: connects leg1-leg2 (along X)
        h = make("Cross-bar 1", "create_box", 2 * leg_offset, bar_r * 2, bar_r * 2)
        if h:
            solid.move_solid(h, 0, leg_offset, 200)

        # Cross-bar 2: connects leg3-leg4 (along X)
        h = make("Cross-bar 2", "create_box", 2 * leg_offset, bar_r * 2, bar_r * 2)
        if h:
            solid.move_solid(h, 0, -leg_offset, 200)

        # Cross-bar 3: connects leg1-leg3 (along Y)
        h = make("Cross-bar 3", "create_box", bar_r * 2, 2 * leg_offset, bar_r * 2)
        if h:
            solid.move_solid(h, leg_offset, 0, 200)

        # Cross-bar 4: connects leg2-leg4 (along Y)
        h = make("Cross-bar 4", "create_box", bar_r * 2, 2 * leg_offset, bar_r * 2)
        if h:
            solid.move_solid(h, -leg_offset, 0, 200)

        # ── 3. Seat ───────────────────────────────────────
        print("Creating seat...")
        h = make("Seat", "create_box", seat_w, seat_d, seat_th)
        if h:
            # Box center at origin, extends -240..240, -230..230, -20..20
            # Move so bottom of seat = seat_z - seat_th = 410, top = 450
            solid.move_solid(h, 0, 0, seat_z - seat_th / 2)
            seat_handle = h

        # ── 4. Backrest ───────────────────────────────────
        print("Creating backrest...")
        h = make("Backrest", "create_box", back_w, back_th, back_h)
        if h:
            # Box center at origin
            # Position behind seat: Y = -(seat_d/2 + back_th/2)
            # Z: bottom at seat_z (=450), center at seat_z + back_h/2
            back_y = -(seat_d / 2 + back_th / 2)
            back_z = seat_z + back_h / 2
            solid.move_solid(h, 0, back_y, back_z)

        # ── 5. Armrests ───────────────────────────────────
        print("Creating armrests...")
        # Armrest: narrow left-right (arm_w=40), long front-back (arm_len=350), thin vertical (arm_th=25)
        # box(X, Y, Z) → X=arm_w=40, Y=arm_len=350, Z=arm_th=25
        # Top of armrest should be slightly above seat surface
        armrest_above_seat = 20  # mm above seat top
        arm_z = seat_z + armrest_above_seat - arm_th / 2  # = 450 + 20 - 12.5 = 457.5

        arm_gap = 10  # gap between seat edge and armrest (mm)
        arm_x_offset = seat_w / 2 + arm_w / 2 + arm_gap  # = 240 + 20 + 10 = 270

        for side, sign in [("L", -1), ("R", 1)]:
            h = make(f"Armrest {side}", "create_box", arm_w, arm_len, arm_th)
            if h:
                solid.move_solid(h, sign * arm_x_offset, -40, arm_z)

        # Armrest supports (vertical posts near front of armrest)
        support_r = 10
        armrest_bottom_z = arm_z - arm_th / 2  # Z of armrest bottom = 425
        support_h = armrest_bottom_z  # from floor (0) to armrest bottom
        support_y = 80  # near front of armrest
        for side_x in (-arm_x_offset, arm_x_offset):
            h = make(f"Armrest support ({side_x:.0f})", "create_cylinder", support_r, support_h)
            if h:
                solid.move_solid(h, side_x, support_y, support_h / 2)

        # ── 6. View ───────────────────────────────────────
        print("Setting view...")
        solid.set_3d_view("swiso", "realistic")

    # ── Finalize ──────────────────────────────────────────
    print("Zooming to extents...")
    doc.zoom_extents()

    print("\n" + "=" * 50)
    print("Office Chair design complete!")
    print("  • 2D views: Front, Side")
    print("  • 3D model: 4 legs, cross-bars, seat, backrest, armrests")
    print("=" * 50)

    repo.close()
    print("Connection closed.")


if __name__ == "__main__":
    main()
