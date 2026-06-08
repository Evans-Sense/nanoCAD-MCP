"""2-Furrow Moldboard Plow for 30 HP Tractor.

Based on standard agricultural engineering specifications:
  - Tractor power: 30 HP (22 kW)
  - Number of furrows: 2
  - Furrow width: 300 mm (12")
  - Working depth: 200-250 mm
  - Total working width: 600 mm

Components:
  1. Frame: main beam + cross beam + braces
  2. Plow bodies (x2): share + moldboard + shank
  3. Hitch: 3-point linkage bracket
  4. Depth wheel

Layers: Frame, Body, Hitch, Wheel, Dims
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
        print("ERROR: 3D requires .NET engine")
        repo.close()
        return

    # ── Layers ────────────────────────────────────────────
    print("Creating layers...")
    for name in ("Frame", "Body", "Hitch", "Wheel", "Dims"):
        layer.create_layer(name)

    def make(label: str, method: str, *args: object) -> str | None:
        fn = getattr(solid, method)
        result = fn(*args)
        if isinstance(result, dict) and "handle" in result:
            h = result["handle"]
            if h:
                print(f"  {label}: {h}")
                return h
        print(f"  {label}: FAILED ({result})")
        return None

    # ══════════════════════════════════════════════════════
    # DIMENSIONS (mm)
    # ══════════════════════════════════════════════════════

    # Frame
    beam_l = 1500.0     # main beam length (Y axis)
    beam_sec = 60.0     # square tube section
    cross_l = 800.0     # cross beam length (X axis)
    cross_sec = 50.0    # cross beam section

    # Plow body
    furrow_w = 300.0    # furrow width
    share_l = 350.0     # share length (Y)
    share_w = 300.0     # share width (X)
    share_th = 14.0     # share thickness
    mold_l = 550.0      # moldboard length (Y)
    mold_w = 350.0      # moldboard width
    mold_th = 8.0       # moldboard thickness
    shank_h = 400.0     # shank height (Z)
    shank_w = 40.0      # shank width (X)
    shank_d = 25.0      # shank depth (Y)

    # Hitch
    hitch_w = 50.0      # bracket width
    hitch_h = 200.0     # bracket height
    hitch_d = 30.0      # bracket depth
    pin_r = 12.0        # hitch pin radius
    pin_l = 80.0        # pin length

    # Depth wheel
    wheel_r = 100.0     # wheel radius
    wheel_w = 30.0      # wheel width

    # ══════════════════════════════════════════════════════
    # 2D VIEWS
    # ══════════════════════════════════════════════════════
    print("Drawing 2D views...")

    # Top view (XY plane)
    tx, ty = 200.0, 100.0

    # Frame beam
    entity.create_rectangle(tx - beam_sec / 2, ty, tx + beam_sec / 2, ty + beam_l, layer="Frame")
    # Cross beam
    entity.create_rectangle(tx - cross_l / 2, ty + 400, tx + cross_l / 2, ty + 400 + cross_sec, layer="Frame")
    # Plow bodies
    for bx in (-furrow_w / 2, furrow_w / 2):
        entity.create_rectangle(tx + bx - share_w / 2, ty + 500, tx + bx + share_w / 2, ty + 500 + share_l, layer="Body")
    # Hitch bracket
    entity.create_rectangle(tx - hitch_w / 2, ty - hitch_h, tx + hitch_w / 2, ty, layer="Hitch")

    entity.create_text(tx, ty - 150, "TOP VIEW", 25, layer="Dims")

    # Side view (YZ plane)
    sx, sy = -200.0, 100.0
    # Main beam
    entity.create_rectangle(sx, sy, sx + beam_l, sy + beam_sec, layer="Frame")
    # Shank
    for sh_x in (400, 750):
        entity.create_rectangle(sx + sh_x, sy - shank_h, sx + sh_x + shank_d, sy, layer="Body")
    # Hitch bracket
    entity.create_rectangle(sx - hitch_d, sy - hitch_h, sx, sy + hitch_w, layer="Hitch")

    entity.create_text(sx + beam_l / 2, sy - shank_h - 80, "SIDE VIEW", 25, layer="Dims")

    # ══════════════════════════════════════════════════════
    # 3D SOLID MODEL
    # ══════════════════════════════════════════════════════
    print("Creating 3D solid model...")

    body = None  # will hold current boolean result

    # ── 1. Main frame beam ────────────────────────────────
    print("Step 1: Frame...")
    h = make("Main beam", "create_box", beam_sec, beam_l, beam_sec)
    if h:
        solid.move_solid(h, 0, beam_l / 2, beam_sec / 2)
        body = h

    # Cross beam
    h = make("Cross beam", "create_box", cross_l, cross_sec, cross_sec)
    if h and body:
        solid.move_solid(h, 0, 500, beam_sec / 2)
        r = solid.boolean_union(body, h)
        if "handle" in r:
            body = r["handle"]

    # Diagonal braces
    for sign in (-1, 1):
        h = make(f"Brace {sign}", "create_box", 30, 200, 30)
        if h and body:
            solid.move_solid(h, sign * 250, 400, beam_sec / 2)
            r = solid.boolean_union(body, h)
            if "handle" in r:
                body = r["handle"]

    # ── 2. Hitch (3-point linkage bracket) ────────────────
    print("Step 2: Hitch...")
    h = make("Hitch plate", "create_box", hitch_w, hitch_d, hitch_h)
    if h and body:
        solid.move_solid(h, 0, -hitch_d / 2, hitch_h / 2)
        r = solid.boolean_union(body, h)
        if "handle" in r:
            body = r["handle"]

    # Top link pin
    h = make("Top pin", "create_cylinder", pin_r, pin_l)
    if h and body:
        solid.move_solid(h, 0, 0, hitch_h - 30)
        r = solid.boolean_union(body, h)
        if "handle" in r:
            body = r["handle"]

    # Lower link pins (x2)
    for sign in (-1, 1):
        h = make(f"Lower pin {sign}", "create_cylinder", pin_r, pin_l)
        if h and body:
            solid.move_solid(h, sign * 200, 0, 50)
            r = solid.boolean_union(body, h)
            if "handle" in r:
                body = r["handle"]

    # ── 3. Plow bodies (x2) ──────────────────────────────
    print("Step 3: Plow bodies...")

    for i, (bx, by_off) in enumerate([(0, 0), (-furrow_w, 300)], 1):
        print(f"  Plow body {i}...")

        # Shank (vertical support)
        h = make(f"  Shank {i}", "create_box", shank_w, shank_d, shank_h)
        if h and body:
            solid.move_solid(h, bx, 500 + by_off, -shank_h + beam_sec / 2)
            r = solid.boolean_union(body, h)
            if "handle" in r:
                body = r["handle"]

        # Share (cutting edge - wedge shape approximated as thin box)
        h = make(f"  Share {i}", "create_box", share_w, share_l, share_th)
        if h and body:
            # Share hangs below shank, angled forward
            solid.move_solid(h, bx, 500 + by_off + share_l / 2, -shank_h + beam_sec / 2 - share_th / 2)
            r = solid.boolean_union(body, h)
            if "handle" in r:
                body = r["handle"]

        # Moldboard (soil-turning plate)
        h = make(f"  Moldboard {i}", "create_box", mold_w, mold_l, mold_th)
        if h and body:
            # Moldboard is behind and above share, angled
            solid.move_solid(h, bx, 500 + by_off + 100, -shank_h + beam_sec / 2 + 50)
            r = solid.boolean_union(body, h)
            if "handle" in r:
                body = r["handle"]

        # Skim (small share below main share)
        h = make(f"  Skim {i}", "create_box", 150, 200, 10)
        if h and body:
            solid.move_solid(h, bx + 75, 500 + by_off + 50, -shank_h + beam_sec / 2 - share_th - 15)
            r = solid.boolean_union(body, h)
            if "handle" in r:
                body = r["handle"]

    # ── 4. Depth wheel ────────────────────────────────────
    print("Step 4: Depth wheel...")
    h = make("Wheel", "create_cylinder", wheel_r, wheel_w)
    if h and body:
        # Wheel at rear of frame
        solid.move_solid(h, 300, beam_l - 100, wheel_r)
        r = solid.boolean_union(body, h)
        if "handle" in r:
            body = r["handle"]

    # Wheel bracket
    h = make("Wheel bracket", "create_box", 30, 30, wheel_r)
    if h and body:
        solid.move_solid(h, 300, beam_l - 100, wheel_r / 2)
        r = solid.boolean_union(body, h)
        if "handle" in r:
            body = r["handle"]

    # ── 5. View ───────────────────────────────────────────
    print("Setting view...")
    solid.set_3d_view("swiso", "realistic")

    props = solid.get_solid_properties(body) if body else {}
    if props:
        area = props.get("area", 0)
        print(f"  Surface area: {area:.0f} mm^2")

    doc.zoom_extents()

    print("\n" + "=" * 55)
    print("2-Furrow Moldboard Plow - 30 HP Tractor")
    print("=" * 55)
    print("  Frame:")
    print("    Main beam:    60x60x1500 mm (square tube)")
    print("    Cross beam:   50x50x800 mm")
    print("    Braces:       2x diagonal")
    print("  Hitch: 3-point linkage")
    print("    Top link pin:  R12x80 mm")
    print("    Lower pins:    2x R12x80 mm")
    print("  Plow bodies (x2):")
    print("    Share:        300x350x14 mm")
    print("    Moldboard:    350x550x8 mm")
    print("    Shank:        40x25x400 mm")
    print("    Skim:         150x200x10 mm")
    print("  Depth wheel: R100x30 mm")
    print("  Working width:  600 mm (2 x 300 mm)")
    print("  Working depth:  200-250 mm")
    print("=" * 55)

    repo.close()
    print("Connection closed.")


if __name__ == "__main__":
    main()
