from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ── Value Objects ──────────────────────────────────────────────


class Point2D(BaseModel, frozen=True):
    x: float
    y: float

    def __iter__(self) -> Any:
        yield self.x
        yield self.y

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class Point3D(BaseModel, frozen=True):
    x: float
    y: float
    z: float = 0.0

    def __iter__(self) -> Any:
        yield self.x
        yield self.y
        yield self.z

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


class CadColor(BaseModel, frozen=True):
    """AutoCAD Color — either color index (0..256) or true color (RGB)."""

    red: int = 0
    green: int = 0
    blue: int = 0
    color_index: int | None = None

    @field_validator("red", "green", "blue")
    @classmethod
    def _check_rgb(cls, v: int) -> int:
        if not 0 <= v <= 255:
            msg = f"RGB value must be 0..255, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("color_index")
    @classmethod
    def _check_index(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 256:
            msg = f"Color index must be 0..256, got {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def by_index(cls, index: int) -> CadColor:
        return CadColor(color_index=index, red=0, green=0, blue=0)

    @classmethod
    def by_rgb(cls, r: int, g: int, b: int) -> CadColor:
        return CadColor(red=r, green=g, blue=b)

    @classmethod
    def by_layer(cls) -> CadColor:
        return CadColor(color_index=256)


class LayerName(BaseModel, frozen=True):
    value: str = Field(min_length=1, max_length=256)

    def __str__(self) -> str:
        return self.value


class EntityHandle(BaseModel, frozen=True):
    value: str

    def __str__(self) -> str:
        return self.value


class LineType(BaseModel, frozen=True):
    name: str = "Continuous"

    def __str__(self) -> str:
        return self.name


class LineWeight(IntEnum):
    """AutoCAD lineweight enum (in mm/100)."""

    DEFAULT = -1
    BYLAYER = -2
    BYBLOCK = -3
    LW_000 = 0
    LW_005 = 5
    LW_009 = 9
    LW_013 = 13
    LW_015 = 15
    LW_018 = 18
    LW_020 = 20
    LW_025 = 25
    LW_030 = 30
    LW_035 = 35
    LW_040 = 40
    LW_050 = 50
    LW_053 = 53
    LW_060 = 60
    LW_070 = 70
    LW_080 = 80
    LW_090 = 90
    LW_100 = 100
    LW_106 = 106
    LW_120 = 120
    LW_130 = 130
    LW_140 = 140
    LW_150 = 150
    LW_160 = 160
    LW_170 = 170
    LW_180 = 180
    LW_190 = 190
    LW_200 = 200
    LW_210 = 210
    LW_211 = 211


# ── Base Entity ────────────────────────────────────────────────


class CadEntity(BaseModel):
    """Base for all CAD entities."""

    handle: EntityHandle | None = None
    layer: LayerName = LayerName(value="0")
    color: CadColor | None = None
    linetype: LineType | None = None
    lineweight: LineWeight | None = None

    model_config = {"extra": "ignore"}


# ── Concrete Entities ──────────────────────────────────────────


class CadLine(CadEntity):
    entity_type: Literal["LINE"] = "LINE"
    start: Point2D
    end: Point2D


class CadCircle(CadEntity):
    entity_type: Literal["CIRCLE"] = "CIRCLE"
    center: Point2D
    radius: float = Field(gt=0)


class CadArc(CadEntity):
    entity_type: Literal["ARC"] = "ARC"
    center: Point2D
    radius: float = Field(gt=0)
    start_angle: float  # degrees
    end_angle: float  # degrees


class CadPolyline(CadEntity):
    entity_type: Literal["POLYLINE"] = "POLYLINE"
    vertices: list[Point2D] = Field(min_length=2)
    closed: bool = False
    constant_width: float = 0.0


class CadPoint(CadEntity):
    entity_type: Literal["POINT"] = "POINT"
    position: Point2D


class CadText(CadEntity):
    entity_type: Literal["TEXT"] = "TEXT"
    insertion: Point2D
    content: str = Field(min_length=1)
    height: float = Field(gt=0)
    rotation: float = 0.0  # degrees


class CadMText(CadEntity):
    entity_type: Literal["MTEXT"] = "MTEXT"
    top_left: Point2D
    bottom_right: Point2D
    content: str = Field(min_length=1)
    height: float = Field(gt=0)


class CadEllipse(CadEntity):
    entity_type: Literal["ELLIPSE"] = "ELLIPSE"
    center: Point2D
    major_axis_end: Point2D  # vector from center
    radius_ratio: float = Field(gt=0, le=1)


class CadSpline(CadEntity):
    entity_type: Literal["SPLINE"] = "SPLINE"
    fit_points: list[Point2D] = Field(min_length=2)
    degree: int = Field(default=3, ge=1, le=10)
    closed: bool = False


class CadRay(CadEntity):
    entity_type: Literal["RAY"] = "RAY"
    start: Point2D
    direction: Point2D  # unit vector


class CadXLine(CadEntity):
    entity_type: Literal["XLINE"] = "XLINE"
    through: Point2D
    direction: Point2D  # unit vector


class CadSolid(CadEntity):
    entity_type: Literal["SOLID"] = "SOLID"
    points: list[Point2D] = Field(min_length=3, max_length=4)  # 3 or 4 points


class CadHatchBoundary(BaseModel, frozen=True):
    """A single boundary loop for a hatch."""

    type: Literal["closed_polyline", "circle", "ellipse"]
    points: list[Point2D]  # for polyline
    center: Point2D | None = None  # for circle/ellipse
    radius: float | None = None
    major_axis: Point2D | None = None
    radius_ratio: float | None = None


class CadHatch(CadEntity):
    entity_type: Literal["HATCH"] = "HATCH"
    boundaries: list[CadHatchBoundary] = Field(min_length=1)
    pattern_name: str = "SOLID"
    pattern_scale: float = 1.0
    pattern_angle: float = 0.0  # degrees
    associative: bool = True


class CadDimension(CadEntity):
    entity_type: Literal["DIMENSION"] = "DIMENSION"
    dim_type: Literal["aligned", "linear", "angular", "radial", "diameter"]
    points: list[Point2D]  # type-dependent points
    text: str | None = None


CadEntityType = (
    CadLine
    | CadCircle
    | CadArc
    | CadPolyline
    | CadPoint
    | CadText
    | CadMText
    | CadEllipse
    | CadSpline
    | CadRay
    | CadXLine
    | CadSolid
    | CadHatch
    | CadDimension
)


# ── Layer ───────────────────────────────────────────────────────


class CadLayer(BaseModel):
    name: LayerName
    color: CadColor = CadColor.by_index(7)  # white/black
    linetype: LineType = LineType(name="Continuous")
    lineweight: LineWeight = LineWeight.DEFAULT
    is_on: bool = True
    is_frozen: bool = False
    is_locked: bool = False
    description: str = ""


# ── Block ───────────────────────────────────────────────────────


class CadBlock(BaseModel):
    name: LayerName
    base_point: Point2D
    entities: list[CadEntity] = Field(default_factory=list)


class CadBlockRef(CadEntity):
    entity_type: Literal["BLOCK_REF"] = "BLOCK_REF"
    block_name: LayerName
    insertion: Point2D
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0
    rotation: float = 0.0  # degrees


# ── Document Info ──────────────────────────────────────────────


class CadDocumentInfo(BaseModel):
    name: str
    path: str
    is_saved: bool
    entities_count: int
    layers_count: int
    blocks_count: int
    extents_min: Point2D | None = None
    extents_max: Point2D | None = None


# ── System Info ────────────────────────────────────────────────


class CadSystemInfo(BaseModel):
    version: str
    is_com_available: bool
    is_engine_available: bool
    active_documents: int


# ── NURBS / IFC models ──────────────────────────────────────


class CreateNurbCurveRequest(BaseModel):
    degree: int = 3
    periodic: bool = False
    control_points: list[list[float]]
    knots: list[float]
    weights: list[float] | None = None
    layer: str | None = None


class CreateNurbSurfaceRequest(BaseModel):
    degree_u: int = 3
    degree_v: int = 3
    rational: bool = False
    control_points: list[list[float]]
    u_knots: list[float]
    v_knots: list[float]
    weights: list[float] | None = None
    num_control_u: int
    num_control_v: int
    layer: str | None = None


class ModifyNurbRequest(BaseModel):
    handle: str
    control_points: list[list[float]] | None = None
    knots: list[float] | None = None


class ImportIfcRequest(BaseModel):
    path: str


class GetIfcEntitiesResponse(BaseModel):
    entities: list[dict[str, Any]]
    count: int


# ── MultiCAD API models ──────────────────────────────────────


class GridAxisRequest(BaseModel):
    type: str = "rect"
    origin_x: float = 0
    origin_y: float = 0
    spacings_x: list[float] = Field(default_factory=lambda: [1000.0])
    spacings_y: list[float] = Field(default_factory=lambda: [1000.0])
    naming_x: str = "1,2,3..."
    naming_y: str = "A,B,C..."


class GridLabelRequest(BaseModel):
    grid_handle: str
    label: str
    axis_index: int = 0
    direction: str = "x"


class CreateRoomRequest(BaseModel):
    x: float = 0
    y: float = 0
    width: float = 1000
    height: float = 1000
    name: str | None = None


class CustomObjectRequest(BaseModel):
    class_name: str
    properties: dict[str, Any] | None = None


class ParametricObjectRequest(BaseModel):
    type: str
    parameters: dict[str, Any] | None = None


class ReactorRequest(BaseModel):
    entity_handle: str
    event_type: str = "modified"


class Break2dRequest(BaseModel):
    view_handle: str
    x1: float = 0
    y1: float = 0
    x2: float = 0
    y2: float = 0


class MotionPreviewRequest(BaseModel):
    handle: str


class BodyContourRequest(BaseModel):
    solid_handle: str
