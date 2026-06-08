from __future__ import annotations

import logging
from typing import Any

import pywintypes

logger = logging.getLogger(__name__)

try:
    import win32com.client
except ImportError:
    win32com_client_available = False
    logger.warning("pywin32 not installed — COM bridge unavailable")
else:
    win32com_client_available = True


CAD_PROG_ID = "nanoCAD.Application"


def _to_safe_array(nc_util: Any, points: list[float]) -> Any:
    """Convert a flat list of floats to a COM safe array."""
    return nc_util.CreateSafeArrayFromVector(points)


def _from_safe_array(sa: Any) -> list[float]:
    """Convert a COM safe array to a flat list of floats."""
    win32com.client.CastTo(sa, "IUnknown")
    # pywin32 doesn't have a direct safe array reader; use VBArray
    # For 2D points, the safe array is typically a variant array
    try:
        # Try the VBArray approach
        lower = sa.LBound(1)
        upper = sa.UBound(1)
        result = []
        for i in range(lower, upper + 1):
            result.append(sa.GetValue(i))
        return result
    except Exception:
        return []


class NanoCadComBridge:
    """Low-level COM bridge to nanoCAD process.

    Uses pywin32 to connect to a running nanoCAD instance via COM Automation.
    Provides raw access to the nanoCAD COM object model.
    """

    def __init__(self) -> None:
        self._app: Any = None
        self._doc: Any = None
        self._ms: Any = None
        self._util: Any = None
        self._connected: bool = False

    # ── Connection Management ──────────────────────────────────

    def connect(self) -> bool:
        """Connect to a running nanoCAD instance.

        Tries GetObject first (running instance), then Dispatch (create new).
        """
        if not win32com_client_available:
            logger.error("pywin32 not available, cannot connect via COM")
            return False

        try:
            self._app = win32com.client.GetObject(None, CAD_PROG_ID)
            logger.info("Connected to running nanoCAD instance via GetObject")
        except pywintypes.com_error:
            try:
                self._app = win32com.client.Dispatch(CAD_PROG_ID)
                self._app.Visible = True
                logger.info("Started new nanoCAD instance via Dispatch")
            except pywintypes.com_error as e:
                logger.exception("Cannot connect or start nanoCAD: %s", e)
                return False

        try:
            self._doc = self._app.ActiveDocument
            self._ms = self._doc.ModelSpace
            self._util = self._doc.Utility
            self._connected = True
            logger.info(
                "Connected to nanoCAD — document: %s",
                getattr(self._doc, "Name", "<unknown>"),
            )
            return True
        except AttributeError as e:
            logger.exception("Connected to nanoCAD but cannot access document: %s", e)
            return False

    def disconnect(self) -> None:
        """Release COM references."""
        self._util = None
        self._ms = None
        self._doc = None
        self._app = None
        self._connected = False
        logger.info("Disconnected from nanoCAD")

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── Raw COM Accessors ──────────────────────────────────────

    @property
    def application(self) -> Any:
        return self._app

    @property
    def document(self) -> Any:
        return self._doc

    @property
    def model_space(self) -> Any:
        return self._ms

    @property
    def utility(self) -> Any:
        return self._util

    # ── Ensure Active Document ─────────────────────────────────

    def refresh_document(self) -> bool:
        """Re-acquire the active document (in case it changed)."""
        try:
            self._doc = self._app.ActiveDocument
            self._ms = self._doc.ModelSpace
            self._util = self._doc.Utility
            return True
        except Exception:
            self._connected = False
            return False

    # ── COM Entity Creation Wrappers ───────────────────────────

    def com_add_line(self, x1: float, y1: float, x2: float, y2: float) -> str:
        """Add a line via COM. Returns handle string."""
        pt1 = _to_safe_array(self._util, [x1, y1, 0.0])
        pt2 = _to_safe_array(self._util, [x2, y2, 0.0])
        ent = self._ms.AddLine(pt1, pt2)
        return str(ent.Handle)

    def com_add_circle(self, cx: float, cy: float, radius: float) -> str:
        """Add a circle via COM. Returns handle string."""
        center = _to_safe_array(self._util, [cx, cy, 0.0])
        ent = self._ms.AddCircle(center, radius)
        return str(ent.Handle)

    def com_add_arc(
        self,
        cx: float,
        cy: float,
        radius: float,
        start_angle: float,
        end_angle: float,
    ) -> str:
        """Add an arc via COM. Returns handle string."""
        center = _to_safe_array(self._util, [cx, cy, 0.0])
        # COM API uses radians
        import math

        sa = math.radians(start_angle)
        ea = math.radians(end_angle)
        ent = self._ms.AddArc(center, radius, sa, ea)
        return str(ent.Handle)

    def com_add_polyline(self, vertices: list[tuple[float, float]], closed: bool = False) -> str:
        """Add a lightweight polyline via COM. Returns handle string."""
        flat = []
        for vx, vy in vertices:
            flat.extend([vx, vy, 0.0])
        pts = _to_safe_array(self._util, flat)
        ent = self._ms.AddLightWeightPolyline(pts)
        if closed:
            ent.Closed = True
        return str(ent.Handle)

    def com_add_text(
        self,
        x: float,
        y: float,
        content: str,
        height: float,
    ) -> str:
        """Add a single-line text via COM. Returns handle string."""
        ins = _to_safe_array(self._util, [x, y, 0.0])
        ent = self._ms.AddText(content, ins, height)
        return str(ent.Handle)

    def com_add_point(self, x: float, y: float) -> str:
        """Add a point via COM. Returns handle string."""
        pt = _to_safe_array(self._util, [x, y, 0.0])
        ent = self._ms.AddPoint(pt)
        return str(ent.Handle)

    def com_delete_entity(self, handle: str) -> bool:
        """Delete an entity by handle via COM."""
        try:
            ent = self._doc.HandleToObject(handle)
            ent.Delete()
            return True
        except Exception as e:
            logger.warning("com_delete_entity(%s) failed: %s", handle, e)
            return False

    def com_get_layers(self) -> list[dict[str, Any]]:
        """Get all layers via COM."""
        layers = []
        try:
            lt = self._doc.Layers
            for l_obj in lt:
                layers.append(
                    {
                        "name": l_obj.Name,
                        "color": l_obj.Color,
                        "is_on": l_obj.LayerOn,
                        "is_frozen": l_obj.Freeze,
                        "is_locked": l_obj.Lock,
                        "linetype": str(l_obj.Linetype),
                    }
                )
        except Exception as e:
            logger.warning("com_get_layers failed: %s", e)
        return layers

    def com_add_layer(self, name: str) -> bool:
        """Add a layer via COM."""
        try:
            self._doc.Layers.Add(name)
            return True
        except Exception as e:
            logger.warning("com_add_layer(%s) failed: %s", name, e)
            return False

    def com_set_current_layer(self, name: str) -> bool:
        """Set the current layer via COM."""
        try:
            self._doc.ActiveLayer = self._doc.Layers.Item(name)
            return True
        except Exception as e:
            logger.warning("com_set_current_layer(%s) failed: %s", name, e)
            return False

    def com_save_document(self, path: str | None = None) -> bool:
        """Save the current document via COM."""
        try:
            if path:
                self._doc.SaveAs(path)
            else:
                self._doc.Save()
            return True
        except Exception as e:
            logger.warning("com_save_document failed: %s", e)
            return False

    def com_export_pdf(self, path: str) -> bool:
        """Export current document to PDF via COM."""
        try:
            # Use the Export method or PlotToDevice
            # COM API: doc.Plot.PlotToDevice or doc.Export
            self._doc.Export(path, "PDF")
            return True
        except Exception as e:
            logger.warning("com_export_pdf failed: %s", e)
            return False

    def com_get_system_variable(self, name: str) -> str | None:
        """Get a system variable via COM."""
        try:
            return str(self._doc.GetVariable(name))
        except Exception as e:
            logger.warning("com_get_system_variable(%s) failed: %s", name, e)
            return None

    def com_set_system_variable(self, name: str, value: str) -> bool:
        """Set a system variable via COM."""
        try:
            self._doc.SetVariable(name, value)
            return True
        except Exception as e:
            logger.warning("com_set_system_variable(%s) failed: %s", name, e)
            return False

    def com_zoom_extents(self) -> bool:
        """Zoom to drawing extents via COM."""
        try:
            self._doc.Application.ZoomExtents()
            return True
        except Exception as e:
            logger.warning("com_zoom_extents failed: %s", e)
            return False

    def com_get_document_info(self) -> dict[str, Any]:
        """Get document info via COM."""
        info: dict[str, Any] = {
            "name": "<unknown>",
            "path": "",
            "is_saved": False,
            "entities_count": 0,
        }
        try:
            info["name"] = str(self._doc.Name)
            info["path"] = str(self._doc.FullName) if self._doc.FullName else ""
            info["is_saved"] = not self._doc.Saved
            info["entities_count"] = self._ms.Count
        except Exception as e:
            logger.warning("com_get_document_info failed: %s", e)
        return info
