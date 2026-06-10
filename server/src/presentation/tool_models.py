"""Pydantic models for MCP tool input validation.

Each model corresponds to a tool in TOOL_DEFS. Tools without a model
fall back to JSON Schema validation in tool_validation.py.

Models enforce:
- Type correctness (float, int, string, bool)
- Positive values for dimensions (radius, height, width, length, thickness)
- Required fields
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

# ── Positive numeric helpers ───────────────────────────────────────────

PositiveFloat = Annotated[float, Field(gt=0, description="Must be > 0")]
NonNegativeFloat = Annotated[float, Field(ge=0, description="Must be >= 0")]

# ── 2D Primitives ──────────────────────────────────────────────────────


class CreateLineInput(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    layer: str = "0"


class CreateCircleInput(BaseModel):
    cx: float
    cy: float
    radius: PositiveFloat
    layer: str = "0"


class CreateArcInput(BaseModel):
    cx: float
    cy: float
    radius: PositiveFloat
    start_angle: float
    end_angle: float
    layer: str = "0"


class CreatePolylineInput(BaseModel):
    vertices: list[list[float]]
    closed: bool = False
    layer: str = "0"


# ── Text ───────────────────────────────────────────────────────────────


class CreateTextInput(BaseModel):
    x: float
    y: float
    content: str
    height: PositiveFloat
    rotation: float = 0
    layer: str = "0"


class CreateMTextInput(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    content: str
    height: PositiveFloat
    layer: str = "0"


# ── 3D Solids ─────────────────────────────────────────────────────────


class CreateBoxInput(BaseModel):
    x: float
    y: float
    z: float
    width: PositiveFloat
    length: PositiveFloat
    thickness: PositiveFloat


class CreateSphereInput(BaseModel):
    cx: float
    cy: float
    cz: float
    radius: PositiveFloat


class CreateCylinderInput(BaseModel):
    cx: float
    cy: float
    cz: float
    radius: PositiveFloat
    height: PositiveFloat


class CreateConeInput(BaseModel):
    cx: float
    cy: float
    cz: float
    radius_bottom: PositiveFloat
    height: PositiveFloat


class CreateWedgeInput(BaseModel):
    cx: float
    cy: float
    cz: float
    width: PositiveFloat
    length: PositiveFloat
    height: PositiveFloat


class CreateTorusInput(BaseModel):
    cx: float
    cy: float
    cz: float
    major_radius: PositiveFloat
    minor_radius: PositiveFloat


# ── Hatch ──────────────────────────────────────────────────────────────


class CreateHatchInput(BaseModel):
    handle: str
    pattern: str = "SOLID"
    scale: PositiveFloat = 1.0
    angle: float = 0


# ── Dimension ──────────────────────────────────────────────────────────


class CreateAlignedDimensionInput(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    dim_x: float
    dim_y: float
    layer: str = "0"


class CreateLinearDimensionInput(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    dim_x: float
    dim_y: float
    layer: str = "0"


# ── Model lookup ───────────────────────────────────────────────────────

# Map tool name → Pydantic model for O(1) lookup
INPUT_MODELS: dict[str, type[BaseModel]] = {
    "create_line": CreateLineInput,
    "create_circle": CreateCircleInput,
    "create_arc": CreateArcInput,
    "create_polyline": CreatePolylineInput,
    "create_text": CreateTextInput,
    "create_mtext": CreateMTextInput,
    "create_box": CreateBoxInput,
    "create_sphere": CreateSphereInput,
    "create_cylinder": CreateCylinderInput,
    "create_cone": CreateConeInput,
    "create_wedge": CreateWedgeInput,
    "create_torus": CreateTorusInput,
    "create_hatch": CreateHatchInput,
    "create_aligned_dimension": CreateAlignedDimensionInput,
    "create_linear_dimension": CreateLinearDimensionInput,
}


def get_model(tool_name: str) -> type[BaseModel] | None:
    """Return the Pydantic model for *tool_name*, or None."""
    return INPUT_MODELS.get(tool_name)
