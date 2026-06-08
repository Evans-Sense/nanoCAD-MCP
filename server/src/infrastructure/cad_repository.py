from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

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
from src.domain.interfaces import ICadRepository
from src.infrastructure.com_bridge import NanoCadComBridge
from src.infrastructure.http_bridge import HttpCadBridge

logger = logging.getLogger(__name__)


class CadRepository(ICadRepository):
    """Repository implementation that tries HTTP (.NET engine) first,
    then falls back to COM Automation.

    This provides maximum API coverage:
    - .NET engine: full access to hostmgd/hostdbmgd
    - COM fallback: basic operations when .NET engine is not loaded
    """

    def __init__(self) -> None:
        self._http = HttpCadBridge()
        self._com = NanoCadComBridge()
        self._mode: str = "none"
        self._mode_emoji: str = "⛔"

    # ── Connection Management ──────────────────────────────────

    def connect(self) -> bool:
        """Try HTTP first, then COM. Returns True if any connection works."""
        # Try HTTP bridge (.NET engine)
        if self._http.connect():
            self._mode = "full"
            self._mode_emoji = "⚡"
            logger.info("CAD Repository: connected via HTTP (.NET engine) — full mode")
            return True

        # Fallback to COM
        if self._com.connect():
            self._mode = "com"
            self._mode_emoji = "🔧"
            logger.info("CAD Repository: connected via COM — limited mode")
            return True

        self._mode = "offline"
        self._mode_emoji = "⛔"
        logger.warning("CAD Repository: not connected (no .NET engine, no COM)")
        return False

    def close(self) -> None:
        self._http.close()
        self._com.disconnect()
        self._mode = "none"

    @property
    def connection_mode(self) -> str:
        """Returns 'full', 'com', or 'offline'."""
        return self._mode

    # ── Health ──────────────────────────────────────────────────

    def is_available(self) -> bool:
        if self._mode == "full":
            health = self._http.check_health()
            if health is None:
                self._mode = "offline"
                logger.warning("Engine health check failed, switching to offline")
            return health is not None
        if self._mode == "com":
            return self._com.is_connected
        return False

    def get_system_info(self) -> CadSystemInfo:
        if self._mode == "full":
            info = self._http.check_health()
            if info:
                return CadSystemInfo(
                    version=info.get("version", "unknown"),
                    is_com_available=True,
                    is_engine_available=True,
                    active_documents=info.get("active_documents", 0),
                )
        return CadSystemInfo(
            version="COM",
            is_com_available=self._com.is_connected,
            is_engine_available=False,
            active_documents=1 if self._com.is_connected else 0,
        )

    # ── Internal helpers ───────────────────────────────────────

    def _ensure_entity_params(
        self, layer: LayerName | None, color: Any, linetype: Any, lineweight: Any
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if layer:
            params["layer"] = str(layer)
        if color is not None:
            params["color"] = color
        if linetype is not None:
            params["linetype"] = linetype
        if lineweight is not None:
            params["lineweight"] = lineweight
        return params

    def _to_handle(self, raw: str | None) -> EntityHandle | None:
        if raw:
            return EntityHandle(value=raw)
        return None

    # ── Entity Creation ────────────────────────────────────────

    def create_line(self, entity: CadLine) -> EntityHandle:
        params = {
            "x1": entity.start.x,
            "y1": entity.start.y,
            "x2": entity.end.x,
            "y2": entity.end.y,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        if self._mode == "full":
            result = self._http.create_entity("line", params)
            if result:
                return EntityHandle(value=result)
        # COM fallback
        handle = self._com.com_add_line(
            entity.start.x,
            entity.start.y,
            entity.end.x,
            entity.end.y,
        )
        h = self._to_handle(handle)
        if h:
            return h
        msg = "Failed to create line via COM"
        raise RuntimeError(msg)

    def create_circle(self, entity: CadCircle) -> EntityHandle:
        params = {
            "cx": entity.center.x,
            "cy": entity.center.y,
            "radius": entity.radius,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        if self._mode == "full":
            result = self._http.create_entity("circle", params)
            if result:
                return EntityHandle(value=result)
        handle = self._com.com_add_circle(entity.center.x, entity.center.y, entity.radius)
        h = self._to_handle(handle)
        if h:
            return h
        msg = "Failed to create circle"
        raise RuntimeError(msg)

    def create_arc(self, entity: CadArc) -> EntityHandle:
        if self._mode == "full":
            params = {
                "cx": entity.center.x,
                "cy": entity.center.y,
                "radius": entity.radius,
                "start_angle": entity.start_angle,
                "end_angle": entity.end_angle,
                **self._ensure_entity_params(
                    entity.layer, entity.color, entity.linetype, entity.lineweight
                ),
            }
            result = self._http.create_entity("arc", params)
            if result:
                return EntityHandle(value=result)
        handle = self._com.com_add_arc(
            entity.center.x,
            entity.center.y,
            entity.radius,
            entity.start_angle,
            entity.end_angle,
        )
        h = self._to_handle(handle)
        if h:
            return h
        msg = "Failed to create arc"
        raise RuntimeError(msg)

    def create_polyline(self, entity: CadPolyline) -> EntityHandle:
        if self._mode == "full":
            params = {
                "vertices": [(v.x, v.y) for v in entity.vertices],
                "closed": entity.closed,
                **self._ensure_entity_params(
                    entity.layer, entity.color, entity.linetype, entity.lineweight
                ),
            }
            result = self._http.create_entity("polyline", params)
            if result:
                return EntityHandle(value=result)
        vertices = [(v.x, v.y) for v in entity.vertices]
        handle = self._com.com_add_polyline(vertices, entity.closed)
        h = self._to_handle(handle)
        if h:
            return h
        msg = "Failed to create polyline"
        raise RuntimeError(msg)

    def create_point(self, entity: CadPoint) -> EntityHandle:
        if self._mode == "full":
            params = {
                "x": entity.position.x,
                "y": entity.position.y,
                **self._ensure_entity_params(
                    entity.layer, entity.color, entity.linetype, entity.lineweight
                ),
            }
            result = self._http.create_entity("point", params)
            if result:
                return EntityHandle(value=result)
        handle = self._com.com_add_point(entity.position.x, entity.position.y)
        h = self._to_handle(handle)
        if h:
            return h
        msg = "Failed to create point"
        raise RuntimeError(msg)

    def create_text(self, entity: CadText) -> EntityHandle:
        if self._mode == "full":
            params = {
                "x": entity.insertion.x,
                "y": entity.insertion.y,
                "content": entity.content,
                "height": entity.height,
                "rotation": entity.rotation,
                **self._ensure_entity_params(
                    entity.layer, entity.color, entity.linetype, entity.lineweight
                ),
            }
            result = self._http.create_entity("text", params)
            if result:
                return EntityHandle(value=result)
        handle = self._com.com_add_text(
            entity.insertion.x, entity.insertion.y, entity.content, entity.height
        )
        h = self._to_handle(handle)
        if h:
            return h
        msg = "Failed to create text"
        raise RuntimeError(msg)

    def create_mtext(self, entity: CadMText) -> EntityHandle:
        if self._mode != "full":
            msg = "MText creation requires .NET engine (COM mode)"
            raise NotImplementedError(msg)
        params = {
            "top_left_x": entity.top_left.x,
            "top_left_y": entity.top_left.y,
            "bottom_right_x": entity.bottom_right.x,
            "bottom_right_y": entity.bottom_right.y,
            "content": entity.content,
            "height": entity.height,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("mtext", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create mtext"
        raise RuntimeError(msg)

    def create_ellipse(self, entity: CadEllipse) -> EntityHandle:
        if self._mode != "full":
            msg = "Ellipse creation requires .NET engine"
            raise NotImplementedError(msg)
        params = {
            "cx": entity.center.x,
            "cy": entity.center.y,
            "major_axis_x": entity.major_axis_end.x,
            "major_axis_y": entity.major_axis_end.y,
            "radius_ratio": entity.radius_ratio,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("ellipse", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create ellipse"
        raise RuntimeError(msg)

    def create_spline(self, entity: CadSpline) -> EntityHandle:
        if self._mode != "full":
            msg = "Spline creation requires .NET engine"
            raise NotImplementedError(msg)
        params = {
            "fit_points": [(p.x, p.y) for p in entity.fit_points],
            "degree": entity.degree,
            "closed": entity.closed,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("spline", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create spline"
        raise RuntimeError(msg)

    def create_ray(self, entity: CadRay) -> EntityHandle:
        if self._mode != "full":
            msg = "Ray creation requires .NET engine"
            raise NotImplementedError(msg)
        params = {
            "p1_x": entity.start.x,
            "p1_y": entity.start.y,
            "p2_x": entity.start.x + entity.direction.x,
            "p2_y": entity.start.y + entity.direction.y,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("ray", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create ray"
        raise RuntimeError(msg)

    def create_xline(self, entity: CadXLine) -> EntityHandle:
        if self._mode != "full":
            msg = "XLine creation requires .NET engine"
            raise NotImplementedError(msg)
        params = {
            "p1_x": entity.through.x,
            "p1_y": entity.through.y,
            "p2_x": entity.through.x + entity.direction.x,
            "p2_y": entity.through.y + entity.direction.y,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("xline", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create xline"
        raise RuntimeError(msg)

    def create_solid(self, entity: CadSolid) -> EntityHandle:
        if self._mode != "full":
            msg = "2D Solid creation requires .NET engine"
            raise NotImplementedError(msg)
        params = {
            "points": [(p.x, p.y) for p in entity.points],
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("solid", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create solid"
        raise RuntimeError(msg)

    def create_hatch(self, entity: CadHatch) -> EntityHandle:
        if self._mode != "full":
            msg = "Hatch creation requires .NET engine"
            raise NotImplementedError(msg)
        params = {
            "pattern_name": entity.pattern_name,
            "pattern_scale": entity.pattern_scale,
            "pattern_angle": entity.pattern_angle,
            "associative": entity.associative,
            **self._ensure_entity_params(
                entity.layer, entity.color, entity.linetype, entity.lineweight
            ),
        }
        result = self._http.create_entity("hatch", params)
        h = self._to_handle(result)
        if h:
            return h
        msg = "Failed to create hatch"
        raise RuntimeError(msg)

    # ── Entity Manipulation ────────────────────────────────────

    def get_entity(self, handle: EntityHandle) -> CadEntity | None:
        if self._mode == "full":
            data = self._http.get_entity(str(handle))
            if data:
                return CadEntity.model_validate(data)
        return None

    def delete_entity(self, handle: EntityHandle) -> bool:
        if self._mode == "full" and self._http.delete_entity(str(handle)):
            return True
        return self._com.com_delete_entity(str(handle))

    def move_entity(self, handle: EntityHandle, dx: float, dy: float) -> bool:
        if self._mode == "full" and self._http.move_entity(str(handle), dx, dy):
            return True
        msg = "Move via COM not implemented"
        raise NotImplementedError(msg)

    def copy_entity(self, handle: EntityHandle) -> EntityHandle | None:
        if self._mode == "full":
            result = self._http.copy_entity(str(handle))
            return self._to_handle(result)
        msg = "Copy via COM not implemented"
        raise NotImplementedError(msg)

    def rotate_entity(
        self, handle: EntityHandle, angle: float, center: Point2D | None = None
    ) -> bool:
        if self._mode == "full":
            cx = center.x if center else None
            cy = center.y if center else None
            if self._http.rotate_entity(str(handle), angle, cx, cy):
                return True
        msg = "Rotate via COM not implemented"
        raise NotImplementedError(msg)

    def scale_entity(
        self, handle: EntityHandle, factor: float, center: Point2D | None = None
    ) -> bool:
        if self._mode == "full":
            cx = center.x if center else None
            cy = center.y if center else None
            if self._http.scale_entity(str(handle), factor, cx, cy):
                return True
        msg = "Scale via COM not implemented"
        raise NotImplementedError(msg)

    def mirror_entity(self, handle: EntityHandle, p1: Point2D, p2: Point2D) -> bool:
        if self._mode != "full":
            msg = "Mirror requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http._request(
            "POST",
            f"/api/entity/{handle}/mirror",
            json_body={"p1_x": p1.x, "p1_y": p1.y, "p2_x": p2.x, "p2_y": p2.y},
        )
        return result is not None

    def set_entity_layer(self, handle: EntityHandle, layer: LayerName) -> bool:
        if self._mode == "full":
            result = self._http._request(
                "PATCH",
                f"/api/entity/{handle}/layer",
                json_body={"layer": str(layer)},
            )
            return result is not None
        msg = "Set layer via COM not implemented"
        raise NotImplementedError(msg)

    def get_entities_by_type(
        self, entity_type: str, layer: LayerName | None = None
    ) -> list[CadEntity]:
        if self._mode != "full":
            msg = "Query by type requires .NET engine"
            raise NotImplementedError(msg)
        params: dict[str, Any] = {"entity_type": entity_type}
        if layer:
            params["layer"] = str(layer)
        result = self._http._request("POST", "/api/entity/query/by-type", json_body=params)
        if result and "entities" in result:
            return [CadEntity.model_validate(e) for e in result["entities"]]
        return []

    # ── Layer Management ───────────────────────────────────────

    def create_layer(self, layer: CadLayer) -> None:
        if self._mode == "full":
            if self._http.create_layer(str(layer.name), str(layer.color)):
                return
        self._com.com_add_layer(str(layer.name))

    def get_linetypes(self) -> list[dict[str, Any]]:
        """Get all linetypes in the drawing."""
        if self._mode == "full":
            linetypes_data = self._http.get_linetypes()
            if linetypes_data:
                return linetypes_data
        # COM fallback — not available via COM, return empty list
        return []

    def get_layers(self) -> list[CadLayer]:
        if self._mode == "full":
            layers_data = self._http.get_layers()
            if layers_data:
                return [
                    CadLayer(
                        name=LayerName(value=l["name"]),
                        is_on=l.get("is_on", True),
                        is_frozen=l.get("is_frozen", False),
                        is_locked=l.get("is_locked", False),
                    )
                    for l in layers_data
                ]
        # COM fallback
        com_layers = self._com.com_get_layers()
        return [
            CadLayer(
                name=LayerName(value=l["name"]),
                is_on=l["is_on"],
                is_frozen=l["is_frozen"],
                is_locked=l["is_locked"],
            )
            for l in com_layers
        ]

    def set_current_layer(self, name: LayerName) -> None:
        if self._mode == "full" and self._http.set_current_layer(str(name)):
            return
        self._com.com_set_current_layer(str(name))

    def delete_layer(self, name: LayerName) -> bool:
        if self._mode == "full":
            result = self._http._request("DELETE", f"/api/layer/{name}")
            return result is not None
        msg = "Delete layer via COM not implemented"
        raise NotImplementedError(msg)

    def set_layer_state(
        self,
        name: LayerName,
        on: bool | None = None,
        frozen: bool | None = None,
        locked: bool | None = None,
    ) -> None:
        if self._mode != "full":
            msg = "Layer state change requires .NET engine"
            raise NotImplementedError(msg)
        body: dict[str, Any] = {}
        if on is not None:
            body["on"] = on
        if frozen is not None:
            body["frozen"] = frozen
        if locked is not None:
            body["locked"] = locked
        self._http._request("PATCH", f"/api/layer/{name}", json_body=body)

    # ── Block Operations ───────────────────────────────────────

    def create_block(self, block: CadBlock) -> None:
        if self._mode != "full":
            msg = "Block creation requires .NET engine"
            raise NotImplementedError(msg)
        self._http._request("POST", "/api/block", json_body=block.model_dump())

    def insert_block(self, block_ref: CadBlockRef) -> EntityHandle:
        if self._mode != "full":
            msg = "Block insertion requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http._request(
            "POST",
            f"/api/block/{block_ref.block_name}/insert",
            json_body=block_ref.model_dump(),
        )
        h = self._to_handle(result.get("handle") if isinstance(result, dict) else None)
        if h:
            return h
        msg = "Failed to insert block"
        raise RuntimeError(msg)

    def get_blocks(self) -> list[CadBlock]:
        if self._mode != "full":
            msg = "Block listing requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http._request("GET", "/api/block")
        if result and "blocks" in result:
            return [CadBlock.model_validate(b) for b in result["blocks"]]
        return []

    def delete_block(self, name: LayerName) -> bool:
        if self._mode != "full":
            msg = "Block deletion requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http._request("DELETE", f"/api/block/{name}")
        return result is not None

    # ── Document Operations ────────────────────────────────────

    def get_document_info(self) -> CadDocumentInfo:
        if self._mode == "full":
            info = self._http.get_document_info()
            if info:
                return CadDocumentInfo(
                    name=info.get("name", ""),
                    path=info.get("path", ""),
                    is_saved=info.get("is_saved", False),
                    entities_count=info.get("entities_count", 0),
                    layers_count=info.get("layers_count", 0),
                    blocks_count=info.get("blocks_count", 0),
                )
        # COM fallback
        com_info = self._com.com_get_document_info()
        return CadDocumentInfo(
            name=com_info.get("name", ""),
            path=com_info.get("path", ""),
            is_saved=com_info.get("is_saved", False),
            entities_count=com_info.get("entities_count", 0),
            layers_count=0,
            blocks_count=0,
        )

    def save_document(self, path: str | None = None) -> None:
        if self._mode == "full" and self._http.save_document(path):
            return
        self._com.com_save_document(path)

    def export_pdf(self, path: str) -> None:
        if self._mode == "full" and self._http.export_pdf(path):
            return
        self._com.com_export_pdf(path)

    def export_dwg(self, path: str) -> None:
        if self._mode != "full":
            msg = "DWG export requires .NET engine"
            raise NotImplementedError(msg)
        self._http._request("POST", "/api/document/export/dwg", json_body={"path": path})

    def export_dxf(self, path: str) -> None:
        if self._mode != "full":
            msg = "DXF export requires .NET engine"
            raise NotImplementedError(msg)
        self._http._request("POST", "/api/document/export/dxf", json_body={"path": path})

    def zoom_extents(self) -> None:
        if self._mode == "full":
            self._http._request("POST", "/api/document/zoom/extents")
            return
        self._com.com_zoom_extents()

    def new_document(self, template: str | None = None) -> None:
        if self._mode != "full":
            msg = "New document requires .NET engine"
            raise NotImplementedError(msg)
        body = {"template": template} if template else {}
        self._http._request("POST", "/api/document/new", json_body=body)

    def create_project(
        self,
        filename: str,
        directory: str,
        template: str | None = None,
    ) -> None:
        """Create a new project file at ``directory/filename``.

        Creates the directory if missing. Adds .dwg if no extension.
        Returns silently on success; raises on transport error.
        """
        if self._mode != "full":
            msg = "Create project requires .NET engine"
            raise NotImplementedError(msg)
        if not filename:
            msg = "filename is required"
            raise ValueError(msg)
        if not directory:
            msg = "directory is required"
            raise ValueError(msg)
        # Ensure the directory exists on the client side too (cheap safety).
        Path(directory).mkdir(parents=True, exist_ok=True)
        ok = self._http.create_project(filename=filename, directory=directory, template=template)
        if not ok:
            msg = f"create_project failed: {directory}/{filename}"
            raise RuntimeError(msg)

    def save_project(self, filename: str, directory: str) -> None:
        """Save current document to ``directory/filename`` (overwrites)."""
        if self._mode != "full":
            msg = "Save project requires .NET engine"
            raise NotImplementedError(msg)
        if not filename:
            msg = "filename is required"
            raise ValueError(msg)
        if not directory:
            msg = "directory is required"
            raise ValueError(msg)
        Path(directory).mkdir(parents=True, exist_ok=True)
        ok = self._http.save_project(filename=filename, directory=directory)
        if not ok:
            msg = f"save_project failed: {directory}/{filename}"
            raise RuntimeError(msg)

    def open_document(self, path: str) -> None:
        if self._mode != "full":
            msg = "Open document requires .NET engine"
            raise NotImplementedError(msg)
        self._http._request("POST", "/api/document/open", json_body={"path": path})

    def close_document(self) -> None:
        if self._mode != "full":
            msg = "Close document requires .NET engine"
            raise NotImplementedError(msg)
        self._http._request("POST", "/api/document/close")

    # ── System ─────────────────────────────────────────────────

    def get_system_fonts(self) -> list[dict[str, Any]]:
        if self._mode == "full":
            return self._http.get_system_fonts()
        return []

    def execute_command(self, command: str) -> str | None:
        if self._mode == "full":
            return self._http.execute_command(command)
        msg = "Command execution requires .NET engine"
        raise NotImplementedError(msg)

    def get_system_variable(self, name: str) -> str | None:
        if self._mode == "full":
            return self._http.get_system_variable(name)
        return self._com.com_get_system_variable(name)

    def set_system_variable(self, name: str, value: str) -> None:
        if self._mode == "full":
            self._http.set_system_variable(name, value)
        self._com.com_set_system_variable(name, value)

    # ── Extended HTTP-only operations ──────────────────────

    def create_helix(self, **kwargs: Any) -> Any:
        return self._http.create_helix(**kwargs) if self._http else None

    def create_region(self, **kwargs: Any) -> Any:
        return self._http.create_region(**kwargs) if self._http else None

    def create_boundary(self, **kwargs: Any) -> Any:
        return self._http.create_boundary(**kwargs) if self._http else None

    def create_gradient(self, **kwargs: Any) -> Any:
        return self._http.create_gradient(**kwargs) if self._http else None

    def create_arc_length_dimension(self, **kwargs: Any) -> Any:
        return self._http.create_arc_length_dimension(**kwargs) if self._http else None

    def export_ifc(self, **kwargs: Any) -> Any:
        return self._http.export_ifc(**kwargs) if self._http else None

    def create_mesh(self, **kwargs: Any) -> Any:
        return self._http.create_mesh(**kwargs) if self._http else None

    def edit_mesh(self, **kwargs: Any) -> Any:
        return self._http.edit_mesh(**kwargs) if self._http else None

    def set_viewport(self, **kwargs: Any) -> Any:
        return self._http.set_viewport(**kwargs) if self._http else None

    def render(self, **kwargs: Any) -> Any:
        return self._http.render(**kwargs) if self._http else None

    # ── NURBS / IFC ────────────────────────────────────────

    def create_nurb_curve(self, request: CreateNurbCurveRequest) -> EntityHandle | None:
        if self._mode != "full":
            msg = "NURBS curve creation requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http.create_nurb_curve(**request.model_dump())
        handle = result.get("handle") if result else None
        return EntityHandle(value=handle) if handle else None

    def create_nurb_surface(self, request: CreateNurbSurfaceRequest) -> EntityHandle | None:
        if self._mode != "full":
            msg = "NURBS surface creation requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http.create_nurb_surface(**request.model_dump())
        handle = result.get("handle") if result else None
        return EntityHandle(value=handle) if handle else None

    def modify_nurb(self, request: ModifyNurbRequest) -> bool:
        if self._mode != "full":
            msg = "NURBS modification requires .NET engine"
            raise NotImplementedError(msg)
        result = self._http.modify_nurb(**request.model_dump())
        return result is not None

    def import_ifc(self, path: str) -> bool:
        if self._mode != "full":
            msg = "IFC import requires .NET engine"
            raise NotImplementedError(msg)
        return self._http.import_ifc(path=path)

    def get_ifc_entities(self) -> list[dict[str, Any]] | None:
        if self._mode != "full":
            msg = "IFC query requires .NET engine"
            raise NotImplementedError(msg)
        return self._http.get_ifc_entities()

    # ── MultiCAD API ────────────────────────────────────────

    def create_grid_axis(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_grid_axis(
                grid_type=request.type,
                origin_x=request.origin_x,
                origin_y=request.origin_y,
                spacings_x=request.spacings_x,
                spacings_y=request.spacings_y,
                naming_x=request.naming_x,
                naming_y=request.naming_y,
            )
        return False

    def create_grid_label(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_grid_label(
                grid_handle=request.grid_handle,
                label=request.label,
                axis_index=request.axis_index,
                direction=request.direction,
            )
        return False

    def create_room(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_room(
                x=request.x,
                y=request.y,
                width=request.width,
                height=request.height,
                name=request.name,
            )
        return False

    def get_room_properties(self, handle: str) -> dict[str, Any] | None:
        if self._mode == "full":
            return self._http.get_room_properties(handle=handle)
        return None

    def create_custom_object(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_custom_object(
                class_name=request.class_name,
                properties=request.properties,
            )
        return False

    def create_parametric_object(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_parametric_object(
                object_type=request.type,
                parameters=request.parameters,
            )
        return False

    def create_reactor(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_reactor(
                entity_handle=request.entity_handle,
                event_type=request.event_type,
            )
        return False

    def create_2d_break(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_2d_break(
                view_handle=request.view_handle,
                x1=request.x1,
                y1=request.y1,
                x2=request.x2,
                y2=request.y2,
            )
        return False

    def start_motion_preview(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.start_motion_preview(handle=request.handle)
        return False

    def stop_motion_preview(self) -> bool:
        if self._mode == "full":
            return self._http.stop_motion_preview()
        return False

    def create_body_contour(self, request: Any) -> bool:
        if self._mode == "full":
            return self._http.create_body_contour(solid_handle=request.solid_handle)
        return False

    def check_3d_faces(self, handle: str) -> dict[str, Any] | None:
        if self._mode == "full":
            return self._http.check_3d_faces(handle=handle)
        return None
