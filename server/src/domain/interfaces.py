from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.entities import (
        CadArc,
        CadBlock,
        CadBlockRef,
        CadCircle,
        CadDocumentInfo,
        CadEllipse,
        CadEntity,
        CadHatch,
        CadLayer,
        CadLine,
        CadMText,
        CadPoint,
        CadPolyline,
        CadRay,
        CadSolid,
        CadSpline,
        CadSystemInfo,
        CadText,
        CadXLine,
        CreateNurbCurveRequest,
        CreateNurbSurfaceRequest,
        EntityHandle,
        LayerName,
        ModifyNurbRequest,
        Point2D,
    )


class ICadRepository(ABC):
    """Port interface for CAD operations."""

    # ── Health ──────────────────────────────────────────────

    @abstractmethod
    def is_available(self) -> bool:
        """Check if CAD is connected and responsive."""
        ...

    @abstractmethod
    def get_system_info(self) -> CadSystemInfo:
        """Get CAD system information."""
        ...

    # ── Entity Creation ─────────────────────────────────────

    @abstractmethod
    def create_line(self, entity: CadLine) -> EntityHandle: ...

    @abstractmethod
    def create_circle(self, entity: CadCircle) -> EntityHandle: ...

    @abstractmethod
    def create_arc(self, entity: CadArc) -> EntityHandle: ...

    @abstractmethod
    def create_polyline(self, entity: CadPolyline) -> EntityHandle: ...

    @abstractmethod
    def create_point(self, entity: CadPoint) -> EntityHandle: ...

    @abstractmethod
    def create_text(self, entity: CadText) -> EntityHandle: ...

    @abstractmethod
    def create_mtext(self, entity: CadMText) -> EntityHandle: ...

    @abstractmethod
    def create_ellipse(self, entity: CadEllipse) -> EntityHandle: ...

    @abstractmethod
    def create_spline(self, entity: CadSpline) -> EntityHandle: ...

    @abstractmethod
    def create_ray(self, entity: CadRay) -> EntityHandle: ...

    @abstractmethod
    def create_xline(self, entity: CadXLine) -> EntityHandle: ...

    @abstractmethod
    def create_solid(self, entity: CadSolid) -> EntityHandle: ...

    @abstractmethod
    def create_hatch(self, entity: CadHatch) -> EntityHandle: ...

    # ── Entity Manipulation ────────────────────────────────

    @abstractmethod
    def get_entity(self, handle: EntityHandle) -> CadEntity | None: ...

    @abstractmethod
    def delete_entity(self, handle: EntityHandle) -> bool: ...

    @abstractmethod
    def move_entity(self, handle: EntityHandle, dx: float, dy: float) -> bool: ...

    @abstractmethod
    def copy_entity(self, handle: EntityHandle) -> EntityHandle | None: ...

    @abstractmethod
    def rotate_entity(
        self, handle: EntityHandle, angle: float, center: Point2D | None = None
    ) -> bool: ...

    @abstractmethod
    def scale_entity(
        self, handle: EntityHandle, factor: float, center: Point2D | None = None
    ) -> bool: ...

    @abstractmethod
    def mirror_entity(self, handle: EntityHandle, p1: Point2D, p2: Point2D) -> bool: ...

    @abstractmethod
    def set_entity_layer(self, handle: EntityHandle, layer: LayerName) -> bool: ...

    @abstractmethod
    def get_entities_by_type(
        self, entity_type: str, layer: LayerName | None = None
    ) -> list[CadEntity]: ...

    # ── Layer Management ───────────────────────────────────

    @abstractmethod
    def get_linetypes(self) -> list[dict[str, Any]]:
        """Get all linetypes in the drawing."""
        ...

    @abstractmethod
    def create_layer(self, layer: CadLayer) -> None: ...

    @abstractmethod
    def get_layers(self) -> list[CadLayer]: ...

    @abstractmethod
    def set_current_layer(self, name: LayerName) -> None: ...

    @abstractmethod
    def delete_layer(self, name: LayerName) -> bool: ...

    @abstractmethod
    def set_layer_state(
        self,
        name: LayerName,
        on: bool | None = None,
        frozen: bool | None = None,
        locked: bool | None = None,
    ) -> None: ...

    # ── Block Operations ───────────────────────────────────

    @abstractmethod
    def create_block(self, block: CadBlock) -> None: ...

    @abstractmethod
    def insert_block(self, block_ref: CadBlockRef) -> EntityHandle: ...

    @abstractmethod
    def get_blocks(self) -> list[CadBlock]: ...

    @abstractmethod
    def delete_block(self, name: LayerName) -> bool: ...

    @abstractmethod
    def get_block_entities(self, name: str) -> list[dict[str, Any]]:
        """Get all entities within a block definition (requires .NET engine)."""
        ...

    # ── Document Operations ────────────────────────────────

    @abstractmethod
    def get_document_info(self) -> CadDocumentInfo: ...

    @abstractmethod
    def save_document(self, path: str | None = None) -> None: ...

    @abstractmethod
    def export_pdf(self, path: str) -> None: ...

    @abstractmethod
    def export_dwg(self, path: str) -> None: ...

    @abstractmethod
    def export_dxf(self, path: str) -> None: ...

    @abstractmethod
    def zoom_extents(self) -> None: ...

    @abstractmethod
    def new_document(self, template: str | None = None) -> None: ...

    @abstractmethod
    def create_project(
        self,
        filename: str,
        directory: str,
        template: str | None = None,
    ) -> None:
        """Create a new project file at directory/filename and save it.

        The directory is auto-created if it does not exist.
        """
        ...

    @abstractmethod
    def save_project(self, filename: str, directory: str) -> None:
        """Save current document to directory/filename (overwrites if exists)."""
        ...

    @abstractmethod
    def open_document(self, path: str) -> None: ...

    @abstractmethod
    def close_document(self) -> None: ...

    # ── System ─────────────────────────────────────────────

    @abstractmethod
    def get_system_fonts(self) -> list[dict[str, Any]]:
        """Get all available fonts in the system."""
        ...

    @abstractmethod
    def execute_command(self, command: str) -> str | None:
        """Execute a raw CAD command. Returns command output if available."""
        ...

    @abstractmethod
    def get_system_variable(self, name: str) -> str | None: ...

    @abstractmethod
    def set_system_variable(self, name: str, value: str) -> None: ...

    # ── Extended HTTP-only operations ──────────────────────

    @abstractmethod
    def create_helix(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def create_region(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def create_boundary(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def create_gradient(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def create_arc_length_dimension(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def export_ifc(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def create_mesh(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def edit_mesh(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def set_viewport(self, **kwargs: Any) -> Any: ...

    @abstractmethod
    def render(self, **kwargs: Any) -> Any: ...

    # ── 3D Solids ─────────────────────────────────────────────

    @abstractmethod
    def create_box(self, x: float, y: float, z: float) -> str | None: ...

    @abstractmethod
    def create_sphere(self, radius: float) -> str | None: ...

    @abstractmethod
    def create_cylinder(self, radius: float, height: float) -> str | None: ...

    @abstractmethod
    def create_cone(self, radius_bottom: float, height: float) -> str | None: ...

    @abstractmethod
    def create_torus(self, major_radius: float, minor_radius: float) -> str | None: ...

    @abstractmethod
    def create_wedge(self, x: float, y: float, z: float) -> str | None: ...

    @abstractmethod
    def create_pyramid(self, height: float, sides: int, radius: float) -> str | None: ...

    @abstractmethod
    def boolean_union(self, h1: str, h2: str) -> str | None: ...

    @abstractmethod
    def boolean_subtract(self, h1: str, h2: str) -> str | None: ...

    @abstractmethod
    def boolean_intersect(self, h1: str, h2: str) -> str | None: ...

    @abstractmethod
    def extrude_solid(
        self, handle: str, height: float, taper_angle: float = 0
    ) -> str | None: ...

    @abstractmethod
    def revolve_solid(
        self,
        handle: str,
        axis_x: float = 0,
        axis_y: float = 0,
        axis_z: float = 0,
        dir_x: float = 0,
        dir_y: float = 0,
        dir_z: float = 1,
        angle: float = 360,
    ) -> str | None: ...

    @abstractmethod
    def move_solid(
        self, handle: str, dx: float, dy: float, dz: float = 0
    ) -> bool: ...

    @abstractmethod
    def set_3d_view(
        self, direction: str, render_mode: str = "wireframe"
    ) -> bool: ...

    @abstractmethod
    def get_solid_properties(self, handle: str) -> dict[str, Any] | None: ...

    # ── NURBS / IFC ────────────────────────────────────────

    @abstractmethod
    def create_nurb_curve(self, request: CreateNurbCurveRequest) -> EntityHandle | None: ...

    @abstractmethod
    def create_nurb_surface(self, request: CreateNurbSurfaceRequest) -> EntityHandle | None: ...

    @abstractmethod
    def modify_nurb(self, request: ModifyNurbRequest) -> bool: ...

    @abstractmethod
    def import_ifc(self, path: str) -> bool: ...

    @abstractmethod
    def get_ifc_entities(self) -> list[dict[str, Any]] | None: ...

    # ── MultiCAD API ───────────────────────────────────────

    @abstractmethod
    def create_grid_axis(self, request: Any) -> bool: ...

    @abstractmethod
    def create_grid_label(self, request: Any) -> bool: ...

    @abstractmethod
    def create_room(self, request: Any) -> bool: ...

    @abstractmethod
    def get_room_properties(self, handle: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def create_custom_object(self, request: Any) -> bool: ...

    @abstractmethod
    def create_parametric_object(self, request: Any) -> bool: ...

    @abstractmethod
    def create_reactor(self, request: Any) -> bool: ...

    @abstractmethod
    def create_2d_break(self, request: Any) -> bool: ...

    @abstractmethod
    def start_motion_preview(self, request: Any) -> bool: ...

    @abstractmethod
    def stop_motion_preview(self) -> bool: ...

    @abstractmethod
    def create_body_contour(self, request: Any) -> bool: ...

    @abstractmethod
    def check_3d_faces(self, handle: str) -> dict[str, Any] | None: ...
