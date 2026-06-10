from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.domain.entities import (
    CadArc,
    CadBlockRef,
    CadCircle,
    CadColor,
    CadEllipse,
    CadLayer,
    CadLine,
    CadMText,
    CadPoint,
    CadPolyline,
    CadSpline,
    CadText,
    EntityHandle,
    LayerName,
    Point2D,
)

if TYPE_CHECKING:
    from src.domain.interfaces import ICadRepository

logger = logging.getLogger(__name__)


def _join_project_path(directory: str, filename: str) -> str:
    """Join ``directory`` and ``filename`` and normalize to forward slashes."""
    dir_part = directory.rstrip("/").rstrip("\\")
    file_part = filename.lstrip("/").lstrip("\\")
    return f"{dir_part}/{file_part}".replace("\\", "/")


class EntityUseCase:
    def __init__(self, repo: ICadRepository) -> None:
        self._repo = repo

    def create_line(
        self, x1: float, y1: float, x2: float, y2: float, layer: str = "0"
    ) -> dict[str, Any]:
        entity = CadLine(
            start=Point2D(x=x1, y=y1),
            end=Point2D(x=x2, y=y2),
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_line(entity)
        return {"handle": str(handle), "type": "LINE"}

    def create_circle(
        self, cx: float, cy: float, radius: float, layer: str = "0"
    ) -> dict[str, Any]:
        entity = CadCircle(
            center=Point2D(x=cx, y=cy),
            radius=radius,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_circle(entity)
        return {"handle": str(handle), "type": "CIRCLE", "center": (cx, cy), "radius": radius}

    def create_arc(
        self,
        cx: float,
        cy: float,
        radius: float,
        start_angle: float,
        end_angle: float,
        layer: str = "0",
    ) -> dict[str, Any]:
        entity = CadArc(
            center=Point2D(x=cx, y=cy),
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_arc(entity)
        return {"handle": str(handle), "type": "ARC"}

    def create_polyline(
        self, vertices: list[tuple[float, float]], closed: bool = False, layer: str = "0"
    ) -> dict[str, Any]:
        entity = CadPolyline(
            vertices=[Point2D(x=v[0], y=v[1]) for v in vertices],
            closed=closed,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_polyline(entity)
        return {"handle": str(handle), "type": "POLYLINE", "vertices_count": len(vertices)}

    def create_text(
        self, x: float, y: float, content: str, height: float, layer: str = "0"
    ) -> dict[str, Any]:
        entity = CadText(
            insertion=Point2D(x=x, y=y),
            content=content,
            height=height,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_text(entity)
        return {"handle": str(handle), "type": "TEXT", "content": content}

    def create_mtext(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        content: str,
        height: float,
        layer: str = "0",
    ) -> dict[str, Any]:
        entity = CadMText(
            top_left=Point2D(x=x1, y=y1),
            bottom_right=Point2D(x=x2, y=y2),
            content=content,
            height=height,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_mtext(entity)
        return {"handle": str(handle), "type": "MTEXT"}

    def create_point(self, x: float, y: float, layer: str = "0") -> dict[str, Any]:
        entity = CadPoint(
            position=Point2D(x=x, y=y),
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_point(entity)
        return {"handle": str(handle), "type": "POINT"}

    def create_ellipse(
        self,
        cx: float,
        cy: float,
        major_axis_x: float,
        major_axis_y: float,
        radius_ratio: float = 0.5,
        layer: str = "0",
    ) -> dict[str, Any]:
        entity = CadEllipse(
            center=Point2D(x=cx, y=cy),
            major_axis_end=Point2D(x=major_axis_x, y=major_axis_y),
            radius_ratio=radius_ratio,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_ellipse(entity)
        return {"handle": str(handle), "type": "ELLIPSE"}

    def create_rectangle(
        self, x1: float, y1: float, x2: float, y2: float, layer: str = "0"
    ) -> dict[str, Any]:
        """Create a rectangle as a closed polyline."""
        return self.create_polyline(
            vertices=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
            closed=True,
            layer=layer,
        )

    def delete_entity(self, handle: str) -> dict[str, Any]:
        h = EntityHandle(value=handle)
        success = self._repo.delete_entity(h)
        return {"success": success, "handle": handle}

    def move_entity(self, handle: str, dx: float, dy: float) -> dict[str, Any]:
        h = EntityHandle(value=handle)
        success = self._repo.move_entity(h, dx, dy)
        return {"success": success, "handle": handle, "delta": (dx, dy)}

    def copy_entity(self, handle: str) -> dict[str, Any]:
        h = EntityHandle(value=handle)
        new_handle = self._repo.copy_entity(h)
        if new_handle:
            return {"success": True, "source_handle": handle, "new_handle": str(new_handle)}
        return {"success": False, "source_handle": handle}

    def rotate_entity(
        self, handle: str, angle: float, cx: float | None = None, cy: float | None = None
    ) -> dict[str, Any]:
        if (cx is None) != (cy is None):
            msg = "Both cx and cy must be provided together"
            raise ValueError(msg)
        h = EntityHandle(value=handle)
        center = Point2D(x=cx, y=cy) if cx is not None and cy is not None else None
        success = self._repo.rotate_entity(h, angle, center)
        return {"success": success, "handle": handle, "angle": angle}

    def scale_entity(
        self, handle: str, factor: float, cx: float | None = None, cy: float | None = None
    ) -> dict[str, Any]:
        h = EntityHandle(value=handle)
        center = Point2D(x=cx, y=cy) if cx is not None and cy is not None else None
        success = self._repo.scale_entity(h, factor, center)
        return {"success": success, "handle": handle, "factor": factor}

    def mirror_entity(
        self, handle: str, p1_x: float, p1_y: float, p2_x: float, p2_y: float
    ) -> dict[str, Any]:
        h = EntityHandle(value=handle)
        p1 = Point2D(x=p1_x, y=p1_y)
        p2 = Point2D(x=p2_x, y=p2_y)
        success = self._repo.mirror_entity(h, p1, p2)
        return {"success": success, "handle": handle}

    def get_entity(self, handle: str) -> dict[str, Any]:
        h = EntityHandle(value=handle)
        entity = self._repo.get_entity(h)
        if entity:
            return dict(entity.model_dump())
        return {"error": f"Entity {handle} not found"}

    def create_spline(
        self,
        fit_points: list[tuple[float, float]],
        degree: int = 3,
        closed: bool = False,
        layer: str = "0",
    ) -> dict[str, Any]:
        """Create a spline from fit points."""
        entity = CadSpline(
            fit_points=[Point2D(x=p[0], y=p[1]) for p in fit_points],
            degree=degree,
            closed=closed,
            layer=LayerName(value=layer),
        )
        handle = self._repo.create_spline(entity)
        return {"handle": str(handle), "type": "SPLINE", "fit_points_count": len(fit_points)}

    def create_helix(self, **kwargs: Any) -> Any:
        return self._repo.create_helix(
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            center_z=kwargs.get("center_z", 0),
            start_radius=kwargs.get("start_radius", 20),
            end_radius=kwargs.get("end_radius", 20),
            height=kwargs.get("height", 50),
            turns=kwargs.get("turns", 3),
            layer=kwargs.get("layer"),
        )

    def create_region(self, **kwargs: Any) -> Any:
        return self._repo.create_region(curve_handles=kwargs["curve_handles"])

    def create_boundary(self, **kwargs: Any) -> Any:
        return self._repo.create_boundary(
            point_x=kwargs["point_x"],
            point_y=kwargs["point_y"],
            layer=kwargs.get("layer"),
        )

    def create_mesh(self, **kwargs: Any) -> Any:
        return self._repo.create_mesh(
            vertices=kwargs["vertices"],
            face_indices=kwargs["face_indices"],
            smooth_level=kwargs.get("smooth_level", 0),
            layer=kwargs.get("layer"),
        )

    def edit_mesh(self, **kwargs: Any) -> Any:
        return self._repo.edit_mesh(
            handle=kwargs["handle"],
            vertices=kwargs.get("vertices"),
            subdivide=kwargs.get("subdivide"),
        )

    def set_viewport(self, **kwargs: Any) -> Any:
        return self._repo.set_viewport(
            name=kwargs.get("name", "*Active"),
            vp_type=kwargs.get("vp_type", "single"),
        )

    def render(self, **kwargs: Any) -> Any:
        return self._repo.render(
            output_file=kwargs.get("output_file"),
        )


class LayerUseCase:
    """Use cases for layer management."""

    def __init__(self, repo: ICadRepository) -> None:
        self._repo = repo

    def get_linetypes(self) -> list[dict[str, Any]]:
        """Get all linetypes in the drawing."""
        return self._repo.get_linetypes()

    def create_layer(self, name: str, color: str | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"name": LayerName(value=name)}
        if color is not None:
            kwargs["color"] = CadColor.by_index(int(color))
        layer = CadLayer(**kwargs)
        self._repo.create_layer(layer)
        return {"success": True, "name": name}

    def get_layers(self) -> list[dict[str, Any]]:
        layers = self._repo.get_layers()
        return [
            {
                "name": str(l.name),
                "is_on": l.is_on,
                "is_frozen": l.is_frozen,
                "is_locked": l.is_locked,
            }
            for l in layers
        ]

    def set_current_layer(self, name: str) -> dict[str, Any]:
        self._repo.set_current_layer(LayerName(value=name))
        return {"success": True, "name": name}

    def delete_layer(self, name: str) -> dict[str, Any]:
        success = self._repo.delete_layer(LayerName(value=name))
        return {"success": success, "name": name}

    def set_layer_state(
        self,
        name: str,
        on: bool | None = None,
        frozen: bool | None = None,
        locked: bool | None = None,
    ) -> dict[str, Any]:
        self._repo.set_layer_state(LayerName(value=name), on=on, frozen=frozen, locked=locked)
        return {"success": True, "name": name}


class BlockUseCase:
    """Use cases for block operations."""

    def __init__(self, repo: ICadRepository) -> None:
        self._repo = repo

    def get_blocks(self) -> list[dict[str, Any]]:
        blocks = self._repo.get_blocks()
        return [{"name": str(b.name)} for b in blocks]

    def insert_block(
        self, name: str, x: float, y: float, scale: float = 1.0, rotation: float = 0.0
    ) -> dict[str, Any]:
        ref = CadBlockRef(
            block_name=LayerName(value=name),
            insertion=Point2D(x=x, y=y),
            scale_x=scale,
            scale_y=scale,
            rotation=rotation,
        )
        handle = self._repo.insert_block(ref)
        return {"handle": str(handle), "block_name": name, "insertion": (x, y)}

    def delete_block(self, name: str) -> dict[str, Any]:
        success = self._repo.delete_block(LayerName(value=name))
        return {"success": success, "name": name}

    def get_block_entities(self, name: str) -> list[dict[str, Any]]:
        return self._repo.get_block_entities(name)


class DocumentUseCase:
    """Use cases for document operations."""

    def __init__(self, repo: ICadRepository) -> None:
        self._repo = repo

    def get_info(self) -> dict[str, Any]:
        info = self._repo.get_document_info()
        return info.model_dump()

    def save(self, path: str | None = None) -> dict[str, Any]:
        self._repo.save_document(path)
        return {"success": True, "path": path or "current file"}

    def export_pdf(self, path: str) -> dict[str, Any]:
        self._repo.export_pdf(path)
        return {"success": True, "path": path}

    def export_dwg(self, path: str) -> dict[str, Any]:
        self._repo.export_dwg(path)
        return {"success": True, "path": path}

    def export_dxf(self, path: str) -> dict[str, Any]:
        self._repo.export_dxf(path)
        return {"success": True, "path": path}

    def zoom_extents(self) -> dict[str, Any]:
        self._repo.zoom_extents()
        return {"success": True}

    def new_document(self, template: str | None = None) -> dict[str, Any]:
        self._repo.new_document(template)
        return {"success": True, "template": template}

    def create_project(
        self,
        filename: str,
        directory: str,
        template: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project file and save it to directory/filename."""
        self._repo.create_project(filename=filename, directory=directory, template=template)
        return {
            "success": True,
            "filename": filename,
            "directory": directory,
            "path": _join_project_path(directory, filename),
        }

    def save_project(self, filename: str, directory: str) -> dict[str, Any]:
        """Save the current document to directory/filename."""
        self._repo.save_project(filename=filename, directory=directory)
        return {
            "success": True,
            "filename": filename,
            "directory": directory,
            "path": _join_project_path(directory, filename),
        }

    def open_document(self, path: str) -> dict[str, Any]:
        self._repo.open_document(path)
        return {"success": True, "path": path}

    def close_document(self) -> dict[str, Any]:
        self._repo.close_document()
        return {"success": True}

    def export_ifc(self, **kwargs: Any) -> Any:
        return self._repo.export_ifc(path=kwargs["path"])


class SystemUseCase:
    """Use cases for system operations."""

    def __init__(self, repo: ICadRepository) -> None:
        self._repo = repo

    def get_fonts(self) -> list[dict[str, Any]]:
        """Get all available fonts."""
        return self._repo.get_system_fonts()

    def get_info(self) -> dict[str, Any]:
        info = self._repo.get_system_info()
        return info.model_dump()

    def is_available(self) -> dict[str, Any]:
        available = self._repo.is_available()
        info = self._repo.get_system_info()
        return {
            "available": available,
            "mode": "full"
            if info.is_engine_available
            else "com"
            if info.is_com_available
            else "offline",
            "version": info.version,
        }

    def execute_command(self, command: str) -> dict[str, Any]:
        output = self._repo.execute_command(command)
        return {"command": command, "output": output}

    def get_variable(self, name: str) -> dict[str, Any]:
        value = self._repo.get_system_variable(name)
        return {"name": name, "value": value}

    def set_variable(self, name: str, value: str) -> dict[str, Any]:
        self._repo.set_system_variable(name, value)
        return {"success": True, "name": name, "value": value}


class SolidUseCase:
    """Use cases for 3D solid operations.

    Requires a repository backed by the .NET HTTP engine.
    """

    def __init__(self, repo: ICadRepository) -> None:
        self._repo = repo

    def create_box(self, x: float, y: float, z: float) -> dict[str, Any]:
        handle = self._repo.create_box(x, y, z)
        return {"handle": handle, "type": "BOX"} if handle else {"error": "Failed to create box"}

    def create_sphere(self, radius: float) -> dict[str, Any]:
        handle = self._repo.create_sphere(radius)
        return (
            {"handle": handle, "type": "SPHERE"} if handle else {"error": "Failed to create sphere"}
        )

    def create_cylinder(self, radius: float, height: float) -> dict[str, Any]:
        handle = self._repo.create_cylinder(radius, height)
        return (
            {"handle": handle, "type": "CYLINDER"}
            if handle
            else {"error": "Failed to create cylinder"}
        )

    def create_cone(self, radius_bottom: float, height: float) -> dict[str, Any]:
        handle = self._repo.create_cone(radius_bottom, height)
        return {"handle": handle, "type": "CONE"} if handle else {"error": "Failed to create cone"}

    def create_torus(self, major_radius: float, minor_radius: float) -> dict[str, Any]:
        handle = self._repo.create_torus(major_radius, minor_radius)
        return (
            {"handle": handle, "type": "TORUS"} if handle else {"error": "Failed to create torus"}
        )

    def create_wedge(self, x: float, y: float, z: float) -> dict[str, Any]:
        handle = self._repo.create_wedge(x, y, z)
        return (
            {"handle": handle, "type": "WEDGE"} if handle else {"error": "Failed to create wedge"}
        )

    def create_pyramid(self, height: float, sides: int, radius: float) -> dict[str, Any]:
        handle = self._repo.create_pyramid(height, sides, radius)
        return (
            {"handle": handle, "type": "PYRAMID"}
            if handle
            else {"error": "Failed to create pyramid"}
        )

    def boolean_union(self, handle1: str, handle2: str) -> dict[str, Any]:
        handle = self._repo.boolean_union(handle1, handle2)
        return (
            {"handle": handle, "type": "SOLID3D"} if handle else {"error": "Boolean union failed"}
        )

    def boolean_subtract(self, handle1: str, handle2: str) -> dict[str, Any]:
        handle = self._repo.boolean_subtract(handle1, handle2)
        return (
            {"handle": handle, "type": "SOLID3D"}
            if handle
            else {"error": "Boolean subtract failed"}
        )

    def boolean_intersect(self, handle1: str, handle2: str) -> dict[str, Any]:
        handle = self._repo.boolean_intersect(handle1, handle2)
        return (
            {"handle": handle, "type": "SOLID3D"}
            if handle
            else {"error": "Boolean intersect failed"}
        )

    def extrude_solid(self, handle: str, height: float, taper_angle: float = 0) -> dict[str, Any]:
        new_handle = self._repo.extrude_solid(handle, height, taper_angle)
        return (
            {"handle": new_handle, "type": "SOLID3D"} if new_handle else {"error": "Extrude failed"}
        )

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
    ) -> dict[str, Any]:
        new_handle = self._repo.revolve_solid(
            handle, axis_x, axis_y, axis_z, dir_x, dir_y, dir_z, angle
        )
        return (
            {"handle": new_handle, "type": "SOLID3D"} if new_handle else {"error": "Revolve failed"}
        )

    def move_solid(self, handle: str, dx: float, dy: float, dz: float = 0) -> dict[str, Any]:
        success = self._repo.move_solid(handle, dx, dy, dz)
        return {"success": success, "handle": handle, "dx": dx, "dy": dy, "dz": dz}

    def set_3d_view(self, direction: str, render_mode: str = "wireframe") -> dict[str, Any]:
        success = self._repo.set_3d_view(direction, render_mode)
        return {"success": success, "direction": direction, "render_mode": render_mode}

    def get_solid_properties(self, handle: str) -> dict[str, Any]:
        props = self._repo.get_solid_properties(handle)
        return props or {}
