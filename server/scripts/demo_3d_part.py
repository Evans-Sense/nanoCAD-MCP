"""
nanoCAD Demo: 3D Mechanical Part
=================================
Creates a 3D model in a new document:
- Base plate (box 100x100x20)
- Mounting holes (cylinders for boolean subtract)
- Central bore

Usage:
    py F:\\nanoCAD\\server\\scripts\\demo_3d_part.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_ROOT))

from src.infrastructure.http_bridge import HttpCadBridge


def create_3d_part() -> None:
    http = HttpCadBridge(port=5080)
    http.connect()
    if not http.is_available:
        print("nanoCAD HTTP API not available")
        return

    print("Connected to nanoCAD")

    # Step 1: New document
    print("\n--- Step 1: New document ---")
    http.new_document()
    time.sleep(1)

    # Step 2: Set 3D view
    print("--- Step 2: Set 3D view ---")
    http.set_3d_view("SE Isometric", "wireframe")

    # Step 3: Create base plate (box 100x100x20)
    print("\n--- Step 3: Base plate ---")
    base = http.create_box(x=100, y=100, z=20)
    print(f"Base box (100x100x20): {base}")

    # Step 4: Create cylinders for holes
    print("\n--- Step 4: Mounting holes ---")
    cyl1 = http.create_cylinder(radius=5, height=25)
    print(f"Hole cylinder r=5: {cyl1}")

    cyl2 = http.create_cylinder(radius=5, height=25)
    print(f"Hole cylinder r=5: {cyl2}")

    # Move cylinders to corner positions
    if cyl1:
        http.move_solid(cyl1, dx=15, dy=15, dz=-2)
        print("  Moved to (15,15)")
    if cyl2:
        http.move_solid(cyl2, dx=85, dy=85, dz=-2)
        print("  Moved to (85,85)")

    # Step 5: Central bore
    print("\n--- Step 5: Central bore ---")
    cyl_c = http.create_cylinder(radius=12, height=25)
    print(f"Central bore r=12: {cyl_c}")
    if cyl_c:
        http.move_solid(cyl_c, dx=50, dy=50, dz=-2)
        print("  Moved to (50,50)")

    # Step 6: Boolean subtract - cut holes from base
    print("\n--- Step 6: Cut holes ---")
    if base and cyl1:
        r1 = http.boolean_subtract(base, cyl1)
        print(f"Subtract hole 1: {r1}")
    if base and cyl2:
        r2 = http.boolean_subtract(base, cyl2)
        print(f"Subtract hole 2: {r2}")
    if base and cyl_c:
        r3 = http.boolean_subtract(base, cyl_c)
        print(f"Subtract center bore: {r3}")

    # Step 7: Get properties
    print("\n--- Step 7: Properties ---")
    if base:
        props = http.get_solid_properties(base)
        if props:
            v = props.get("volume", "?")
            print(f"Final volume: {v}")

    # Step 8: Realistic view
    print("\n--- Step 8: Final view ---")
    http.set_3d_view("SE Isometric", "realistic")
    http.execute_command("_ZOOM _E")

    print("\n=== 3D Part created ===")
    print("  Base plate: 100x100x20")
    print("  2x mounting holes r=5 (cut)")
    print("  1x central bore r=12 (cut)")


if __name__ == "__main__":
    create_3d_part()
