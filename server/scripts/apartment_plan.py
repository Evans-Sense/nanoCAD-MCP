"""Studio Apartment Floor Plan — First nanoCAD MCP project.

Layout (6000 × 4000 mm):
  +-------+-------+
  |       |       |
  | Living| Bed   |
  | Room  | Room  |
  |   +-door-+    |
  +---+-----+-----+

Layers: Walls, Doors, Windows, Furniture, Annotation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.cad_repository import CadRepository
from src.application.use_cases import EntityUseCase, LayerUseCase, DocumentUseCase


def main():
    repo = CadRepository()
    if not repo.connect():
        print("Cannot connect to nanoCAD")
        return
    mode = repo.connection_mode
    print(f"Connected in '{mode}' mode")

    entity = EntityUseCase(repo)
    layer = LayerUseCase(repo)
    doc = DocumentUseCase(repo)

    # ── Layers ────────────────────────────────────────────
    print("Creating layers...")
    layer.create_layer("Walls")
    layer.create_layer("Doors")
    layer.create_layer("Windows")
    layer.create_layer("Furniture")
    layer.create_layer("Annotation")

    # ── Outer walls (6000 × 4000) ─────────────────────────
    print("Drawing outer walls...")
    entity.create_rectangle(0, 0, 6000, 4000, layer="Walls")

    # ── Inner dividing wall (with door gap) ───────────────
    print("Drawing inner wall...")
    entity.create_line(3500, 0, 3500, 1800, layer="Walls")
    entity.create_line(3500, 2700, 3500, 4000, layer="Walls")

    # ── Door (arc + line) ─────────────────────────────────
    print("Adding door...")
    door_cx, door_cy = 3500, 2250
    door_radius = 900
    entity.create_arc(door_cx, door_cy, door_radius, -90, 0, layer="Doors")
    entity.create_line(door_cx, door_cy, door_cx, door_cy - door_radius, layer="Doors")

    # ── Window on top wall ────────────────────────────────
    print("Adding window...")
    entity.create_line(1500, 4000, 2500, 4000, layer="Windows")
    entity.create_line(1500, 4050, 2500, 4050, layer="Windows")
    entity.create_line(1500, 3970, 1500, 4080, layer="Windows")
    entity.create_line(2500, 3970, 2500, 4080, layer="Windows")

    # ── Furniture ─────────────────────────────────────────
    print("Adding furniture...")

    # Living room sofa
    entity.create_rectangle(200, 200, 1200, 800, layer="Furniture")
    # Coffee table
    entity.create_circle(1700, 500, 300, layer="Furniture")
    # TV unit
    entity.create_rectangle(100, 3200, 600, 3800, layer="Furniture")

    # Bedroom bed
    entity.create_rectangle(4000, 200, 5400, 1800, layer="Furniture")
    # Bedroom desk
    entity.create_rectangle(4000, 3200, 4800, 3600, layer="Furniture")
    # Chair
    entity.create_circle(5000, 3400, 150, layer="Furniture")

    # ── Labels ────────────────────────────────────────────
    print("Adding labels...")
    entity.create_text(1600, 2800, "Living Room", 200, layer="Annotation")
    entity.create_text(4400, 2800, "Bedroom", 200, layer="Annotation")
    entity.create_text(100, 4150, "6000 × 4000 mm", 150, layer="Annotation")

    # ── Finalize ──────────────────────────────────────────
    doc.zoom_extents()
    print("Done! Zooming to extents.")

    repo.close()
    print("Connection closed.")


if __name__ == "__main__":
    main()
