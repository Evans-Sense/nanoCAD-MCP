from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.domain.entities import (
    BodyContourRequest,
    Break2dRequest,
    CadArc,
    CadBlockRef,
    CadCircle,
    CadEllipse,
    CadHatch,
    CadLayer,
    CadLine,
    CadMText,
    CadPoint,
    CadPolyline,
    CadRay,
    CadSolid,
    CadSpline,
    CadText,
    CadXLine,
    CreateRoomRequest,
    CustomObjectRequest,
    EntityHandle,
    GridAxisRequest,
    GridLabelRequest,
    LayerName,
    MotionPreviewRequest,
    ParametricObjectRequest,
    Point2D,
    ReactorRequest,
)
from src.domain.exceptions import NotSupportedError
from src.infrastructure.cad_repository import CadRepository


@pytest.fixture
def repo() -> CadRepository:
    r = CadRepository()
    r._http = MagicMock()
    r._com = MagicMock()
    r._mode = "full"
    r._http.is_available = True
    return r


# ── Connection ──────────────────────────────────────────────────


class TestConnection:
    def test_connect_http_success(self) -> None:
        r = CadRepository()
        with patch.object(r, "_http") as mock_http:
            mock_http.connect.return_value = True
            assert r.connect() is True
            assert r.connection_mode == "full"

    def test_connect_com_fallback(self) -> None:
        r = CadRepository()
        with patch.object(r, "_http") as mock_http, patch.object(r, "_com") as mock_com:
            mock_http.connect.return_value = False
            mock_com.connect.return_value = True
            assert r.connect() is True
            assert r.connection_mode == "com"

    def test_connect_offline(self) -> None:
        r = CadRepository()
        with patch.object(r, "_http") as mock_http, patch.object(r, "_com") as mock_com:
            mock_http.connect.return_value = False
            mock_com.connect.return_value = False
            assert r.connect() is False
            assert r.connection_mode == "offline"

    def test_close(self) -> None:
        r = CadRepository()
        with patch.object(r, "_http") as mock_http, patch.object(r, "_com") as mock_com:
            r._mode = "full"
            r.close()
            mock_http.close.assert_called_once()
            mock_com.disconnect.assert_called_once()
            assert r.connection_mode == "none"

    def test_is_available_full(self, repo: CadRepository) -> None:
        repo._http.check_health.return_value = {"status": "ok"}
        assert repo.is_available() is True

    def test_is_available_full_offline(self, repo: CadRepository) -> None:
        repo._http.check_health.return_value = None
        assert repo.is_available() is False
        assert repo.connection_mode == "offline"

    def test_is_available_com(self) -> None:
        r = CadRepository()
        r._mode = "com"
        with patch.object(r, "_com", is_connected=True):
            r._com.is_connected = True  # type: ignore[attr-defined]
            assert r.is_available() is True

    def test_is_available_offline(self) -> None:
        r = CadRepository()
        r._mode = "offline"
        assert r.is_available() is False

    def test_get_system_info_full(self, repo: CadRepository) -> None:
        repo._http.check_health.return_value = {
            "version": "26.0", "active_documents": 1
        }
        info = repo.get_system_info()
        assert info.version == "26.0"
        assert info.is_engine_available is True

    def test_get_system_info_offline(self) -> None:
        r = CadRepository()
        r._mode = "offline"
        info = r.get_system_info()
        assert info.is_engine_available is False


# ── Entity Creation ─────────────────────────────────────────────


class TestEntityCreation:
    def _setup_http_create(self, repo: CadRepository, handle: str = "H_001") -> None:
        repo._http.create_entity.return_value = handle

    def _setup_com_fallback(self, repo: CadRepository) -> None:
        repo._http.create_entity.return_value = None

    def test_create_line(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadLine(start=Point2D(x=0, y=0), end=Point2D(x=10, y=10))
        result = repo.create_line(entity)
        assert str(result) == "H_001"
        repo._http.create_entity.assert_called_once()

    def test_create_line_com_fallback(self, repo: CadRepository) -> None:
        self._setup_com_fallback(repo)
        repo._com.com_add_line.return_value = "COM_001"
        entity = CadLine(start=Point2D(x=0, y=0), end=Point2D(x=10, y=10))
        result = repo.create_line(entity)
        assert str(result) == "COM_001"

    def test_create_line_fails(self, repo: CadRepository) -> None:
        self._setup_com_fallback(repo)
        repo._com.com_add_line.return_value = None
        entity = CadLine(start=Point2D(x=0, y=0), end=Point2D(x=10, y=10))
        with pytest.raises(RuntimeError, match="Failed to create line"):
            repo.create_line(entity)

    def test_create_circle(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadCircle(center=Point2D(x=0, y=0), radius=5)
        result = repo.create_circle(entity)
        assert str(result) == "H_001"

    def test_create_arc(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadArc(
            center=Point2D(x=0, y=0), radius=5, start_angle=0, end_angle=180
        )
        result = repo.create_arc(entity)
        assert str(result) == "H_001"

    def test_create_polyline(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadPolyline(
            vertices=[Point2D(x=0, y=0), Point2D(x=10, y=0), Point2D(x=10, y=10)],
            closed=True,
        )
        result = repo.create_polyline(entity)
        assert str(result) == "H_001"

    def test_create_point(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadPoint(position=Point2D(x=5, y=5))
        result = repo.create_point(entity)
        assert str(result) == "H_001"

    def test_create_text(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadText(insertion=Point2D(x=0, y=0), content="Hello", height=2.5)
        result = repo.create_text(entity)
        assert str(result) == "H_001"

    def test_create_text_com_fallback(self, repo: CadRepository) -> None:
        self._setup_com_fallback(repo)
        repo._com.com_add_text.return_value = "COM_TXT"
        entity = CadText(insertion=Point2D(x=0, y=0), content="Hi", height=1)
        result = repo.create_text(entity)
        assert str(result) == "COM_TXT"

    def test_create_mtext(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadMText(
            top_left=Point2D(x=0, y=0),
            bottom_right=Point2D(x=10, y=10),
            content="Multi",
            height=2.5,
        )
        result = repo.create_mtext(entity)
        assert str(result) == "H_001"
        # Verify params include top_left_x etc
        call_body = repo._http.create_entity.call_args[0][1]
        assert call_body["top_left_x"] == 0
        assert call_body["height"] == 2.5

    def test_create_mtext_fails(self, repo: CadRepository) -> None:
        repo._http.create_entity.return_value = None
        entity = CadMText(
            top_left=Point2D(x=0, y=0),
            bottom_right=Point2D(x=10, y=10),
            content="Multi",
            height=2.5,
        )
        with pytest.raises(RuntimeError):
            repo.create_mtext(entity)

    def test_create_ellipse(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadEllipse(
            center=Point2D(x=0, y=0),
            major_axis_end=Point2D(x=10, y=0),
            radius_ratio=0.5,
        )
        result = repo.create_ellipse(entity)
        assert str(result) == "H_001"

    def test_create_spline(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadSpline(
            fit_points=[Point2D(x=0, y=0), Point2D(x=5, y=10), Point2D(x=10, y=0)],
            degree=3,
        )
        result = repo.create_spline(entity)
        assert str(result) == "H_001"

    def test_create_ray(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadRay(start=Point2D(x=0, y=0), direction=Point2D(x=1, y=0))
        result = repo.create_ray(entity)
        assert str(result) == "H_001"
        call_body = repo._http.create_entity.call_args[0][1]
        assert call_body["p1_x"] == 0
        assert call_body["p1_y"] == 0
        assert call_body["p2_x"] == 1  # start.x + direction.x
        assert call_body["p2_y"] == 0  # start.y + direction.y

    def test_create_ray_fails(self, repo: CadRepository) -> None:
        repo._http.create_entity.return_value = None
        entity = CadRay(start=Point2D(x=0, y=0), direction=Point2D(x=1, y=0))
        with pytest.raises(RuntimeError):
            repo.create_ray(entity)

    def test_create_xline(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadXLine(through=Point2D(x=5, y=5), direction=Point2D(x=0, y=1))
        result = repo.create_xline(entity)
        assert str(result) == "H_001"
        call_body = repo._http.create_entity.call_args[0][1]
        assert call_body["p1_x"] == 5
        assert call_body["p1_y"] == 5
        assert call_body["p2_x"] == 5  # through.x + direction.x
        assert call_body["p2_y"] == 6  # through.y + direction.y

    def test_create_xline_fails(self, repo: CadRepository) -> None:
        repo._http.create_entity.return_value = None
        entity = CadXLine(through=Point2D(x=5, y=5), direction=Point2D(x=0, y=1))
        with pytest.raises(RuntimeError):
            repo.create_xline(entity)

    def test_create_solid_2d(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        entity = CadSolid(
            points=[
                Point2D(x=0, y=0),
                Point2D(x=10, y=0),
                Point2D(x=5, y=10),
            ]
        )
        result = repo.create_solid(entity)
        assert str(result) == "H_001"

    def test_create_hatch(self, repo: CadRepository) -> None:
        self._setup_http_create(repo)
        from src.domain.entities import CadHatchBoundary
        entity = CadHatch(
            boundaries=[
                CadHatchBoundary(
                    type="closed_polyline",
                    points=[Point2D(x=0, y=0), Point2D(x=10, y=0), Point2D(x=10, y=10), Point2D(x=0, y=10)],
                )
            ],
            pattern_name="ANSI31",
        )
        result = repo.create_hatch(entity)
        assert str(result) == "H_001"
        call_body = repo._http.create_entity.call_args[0][1]
        assert call_body["pattern_name"] == "ANSI31"

    def test_requires_http_for_advanced(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.create_mtext(
                CadMText(top_left=Point2D(x=0, y=0), bottom_right=Point2D(x=10, y=10), content="X", height=1)
            )
        with pytest.raises(NotSupportedError):
            repo.create_ellipse(CadEllipse(center=Point2D(x=0, y=0), major_axis_end=Point2D(x=5, y=0), radius_ratio=0.5))
        with pytest.raises(NotSupportedError):
            repo.create_spline(CadSpline(fit_points=[Point2D(x=0, y=0), Point2D(x=10, y=10)], degree=3))
        with pytest.raises(NotSupportedError):
            repo.create_ray(CadRay(start=Point2D(x=0, y=0), direction=Point2D(x=1, y=0)))
        with pytest.raises(NotSupportedError):
            repo.create_xline(CadXLine(through=Point2D(x=0, y=0), direction=Point2D(x=1, y=0)))
        with pytest.raises(NotSupportedError):
            repo.create_solid(CadSolid(points=[Point2D(x=0, y=0), Point2D(x=10, y=0), Point2D(x=5, y=10)]))
        with pytest.raises(NotSupportedError):
            repo.create_hatch(
                CadHatch(
                    boundaries=[self._fake_boundary()],
                )
            )

    @staticmethod
    def _fake_boundary() -> Any:
        from src.domain.entities import CadHatchBoundary
        return CadHatchBoundary(
            type="closed_polyline",
            points=[Point2D(x=0, y=0), Point2D(x=10, y=0), Point2D(x=10, y=10), Point2D(x=0, y=10)],
        )


# ── Entity Manipulation ─────────────────────────────────────────


class TestEntityManipulation:
    def test_get_entity(self, repo: CadRepository) -> None:
        repo._http.get_entity.return_value = {
            "handle": {"value": "H1"}, "type": "LINE", "layer": {"value": "0"}
        }
        result = repo.get_entity(EntityHandle(value="H1"))
        assert result is not None
        assert result is not None
        assert result.handle is not None
        assert result.handle.value == "H1"

    def test_get_entity_not_found(self, repo: CadRepository) -> None:
        repo._http.get_entity.return_value = None
        result = repo.get_entity(EntityHandle(value="NONEXIST"))
        assert result is None

    def test_delete_entity_http(self, repo: CadRepository) -> None:
        repo._http.delete_entity.return_value = True
        assert repo.delete_entity(EntityHandle(value="H1")) is True

    def test_delete_entity_http_fail_com(self, repo: CadRepository) -> None:
        repo._http.delete_entity.return_value = False
        repo._com.com_delete_entity.return_value = True
        assert repo.delete_entity(EntityHandle(value="H1")) is True
        repo._com.com_delete_entity.assert_called_once()

    def test_move_entity(self, repo: CadRepository) -> None:
        repo._http.move_entity.return_value = True
        assert repo.move_entity(EntityHandle(value="H1"), 5, 10) is True

    def test_move_entity_com_fail(self, repo: CadRepository) -> None:
        repo._http.move_entity.return_value = False
        with pytest.raises(NotSupportedError):
            repo.move_entity(EntityHandle(value="H1"), 5, 10)

    def test_copy_entity(self, repo: CadRepository) -> None:
        repo._http.copy_entity.return_value = "H2"
        result = repo.copy_entity(EntityHandle(value="H1"))
        assert result is not None
        assert str(result) == "H2"

    def test_copy_entity_fails(self, repo: CadRepository) -> None:
        repo._http.copy_entity.return_value = None
        result = repo.copy_entity(EntityHandle(value="H1"))
        assert result is None

    def test_rotate_entity(self, repo: CadRepository) -> None:
        repo._http.rotate_entity.return_value = True
        assert repo.rotate_entity(EntityHandle(value="H1"), 45, Point2D(x=0, y=0)) is True

    def test_scale_entity(self, repo: CadRepository) -> None:
        repo._http.scale_entity.return_value = True
        assert repo.scale_entity(EntityHandle(value="H1"), 2.0) is True

    def test_mirror_entity(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        assert repo.mirror_entity(
            EntityHandle(value="H1"), Point2D(x=0, y=0), Point2D(x=10, y=0)
        ) is True

    def test_mirror_entity_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.mirror_entity(
                EntityHandle(value="H1"), Point2D(x=0, y=0), Point2D(x=10, y=0)
            )

    def test_set_entity_layer(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.set_entity_layer(EntityHandle(value="H1"), LayerName(value="NewLayer"))
        repo._http._request.assert_called_once_with(
            "PATCH",
            "/api/entity/H1/layer",
            json_body={"layer": "NewLayer"},
        )

    def test_get_entities_by_type(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {
            "entities": [
                {"handle": {"value": "H1"}, "type": "LINE", "layer": {"value": "0"}}
            ]
        }
        result = repo.get_entities_by_type("LINE")
        assert len(result) == 1

    def test_get_entities_by_type_empty(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {}
        assert repo.get_entities_by_type("LINE") == []


# ── Layer Management ────────────────────────────────────────────


class TestLayerManagement:
    def test_create_layer(self, repo: CadRepository) -> None:
        repo._http.create_layer.return_value = True
        layer = CadLayer(name=LayerName(value="Test"))
        repo.create_layer(layer)
        repo._http.create_layer.assert_called_once_with("Test", str(layer.color))

    def test_create_layer_com_fallback(self, repo: CadRepository) -> None:
        repo._http.create_layer.return_value = False
        layer = CadLayer(name=LayerName(value="Test"))
        repo.create_layer(layer)
        repo._com.com_add_layer.assert_called_once_with("Test")

    def test_get_layers_http(self, repo: CadRepository) -> None:
        repo._http.get_layers.return_value = [
            {"name": "0", "is_on": True, "is_frozen": False, "is_locked": False},
            {"name": "1", "is_on": False, "is_frozen": True, "is_locked": False},
        ]
        layers = repo.get_layers()
        assert len(layers) == 2
        assert str(layers[0].name) == "0"
        assert layers[0].is_on is True
        assert layers[1].is_on is False
        assert layers[1].is_frozen is True

    def test_get_layers_com_fallback(self, repo: CadRepository) -> None:
        repo._http.get_layers.return_value = None
        repo._com.com_get_layers.return_value = [
            {"name": "0", "is_on": True, "is_frozen": False, "is_locked": False},
        ]
        layers = repo.get_layers()
        assert len(layers) == 1

    def test_set_current_layer(self, repo: CadRepository) -> None:
        repo._http.set_current_layer.return_value = True
        repo.set_current_layer(LayerName(value="0"))
        repo._http.set_current_layer.assert_called_once()

    def test_set_current_layer_com_fallback(self, repo: CadRepository) -> None:
        repo._http.set_current_layer.return_value = False
        repo.set_current_layer(LayerName(value="0"))
        repo._com.com_set_current_layer.assert_called_once_with("0")

    def test_delete_layer(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        assert repo.delete_layer(LayerName(value="BadLayer")) is True

    def test_delete_layer_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.delete_layer(LayerName(value="X"))

    def test_set_layer_state(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.set_layer_state(LayerName(value="0"), on=False, frozen=True, locked=True)
        repo._http._request.assert_called_once_with(
            "PATCH", "/api/layer/0",
            json_body={"on": False, "frozen": True, "locked": True},
        )

    def test_set_layer_state_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.set_layer_state(LayerName(value="0"), on=False)


# ── Block Operations ────────────────────────────────────────────


class TestBlockOps:
    def test_get_blocks(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {
            "blocks": [{"name": {"value": "Block1"}, "base_point": {"x": 0, "y": 0}}]
        }
        blocks = repo.get_blocks()
        assert len(blocks) == 1
        assert str(blocks[0].name) == "Block1"

    def test_get_blocks_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.get_blocks()

    def test_insert_block(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"handle": "BR_001"}
        ref = CadBlockRef(
            block_name=LayerName(value="TestBlock"),
            insertion=Point2D(x=10, y=20),
        )
        result = repo.insert_block(ref)
        assert str(result) == "BR_001"

    def test_insert_block_fails(self, repo: CadRepository) -> None:
        repo._http._request.return_value = None
        ref = CadBlockRef(
            block_name=LayerName(value="TestBlock"),
            insertion=Point2D(x=10, y=20),
        )
        with pytest.raises(RuntimeError):
            repo.insert_block(ref)

    def test_insert_block_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        ref = CadBlockRef(
            block_name=LayerName(value="X"),
            insertion=Point2D(x=0, y=0),
        )
        with pytest.raises(NotSupportedError):
            repo.insert_block(ref)

    def test_delete_block(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        assert repo.delete_block(LayerName(value="OldBlock")) is True

    def test_delete_block_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.delete_block(LayerName(value="X"))


# ── Document Operations ─────────────────────────────────────────


class TestDocumentOps:
    def test_get_document_info_http(self, repo: CadRepository) -> None:
        repo._http.get_document_info.return_value = {
            "name": "drawing.dwg",
            "path": "C:\\drawing.dwg",
            "is_saved": True,
            "entities_count": 10,
            "layers_count": 3,
            "blocks_count": 2,
        }
        info = repo.get_document_info()
        assert info.name == "drawing.dwg"
        assert info.is_saved is True
        assert info.entities_count == 10

    def test_get_document_info_com(self, repo: CadRepository) -> None:
        repo._http.get_document_info.return_value = None
        repo._com.com_get_document_info.return_value = {
            "name": "drawing.dwg",
            "path": "",
            "is_saved": False,
            "entities_count": 5,
        }
        info = repo.get_document_info()
        assert info.name == "drawing.dwg"
        assert info.is_saved is False
        assert info.layers_count == 0  # COM doesn't provide this

    def test_save_document_http(self, repo: CadRepository) -> None:
        repo._http.save_document.return_value = True
        repo.save_document("C:\\out.dwg")
        repo._http.save_document.assert_called_once()

    def test_save_document_com(self, repo: CadRepository) -> None:
        repo._http.save_document.return_value = False
        repo.save_document("C:\\out.dwg")
        repo._com.com_save_document.assert_called_once()

    def test_save_document_no_path(self, repo: CadRepository) -> None:
        repo._http.save_document.return_value = True
        repo.save_document()
        repo._http.save_document.assert_called_once()

    def test_export_pdf_http(self, repo: CadRepository) -> None:
        repo._http.export_pdf.return_value = True
        repo.export_pdf("C:\\out.pdf")
        repo._http.export_pdf.assert_called_once()

    def test_export_pdf_com(self, repo: CadRepository) -> None:
        repo._http.export_pdf.return_value = False
        repo.export_pdf("C:\\out.pdf")
        repo._com.com_export_pdf.assert_called_once()

    def test_export_dwg(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.export_dwg("C:\\out.dwg")
        repo._http._request.assert_called_once_with(
            "POST", "/api/document/export/dwg", json_body={"path": "C:\\out.dwg"}
        )

    def test_export_dwg_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.export_dwg("C:\\out.dwg")

    def test_export_dxf(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.export_dxf("C:\\out.dxf")

    def test_zoom_extents_http(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.zoom_extents()
        repo._http._request.assert_called_once_with(
            "POST", "/api/document/zoom/extents"
        )

    def test_zoom_extents_com(self, repo: CadRepository) -> None:
        repo._http._request.return_value = None
        repo._mode = "com"
        repo.zoom_extents()
        repo._com.com_zoom_extents.assert_called_once()

    def test_new_document(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.new_document("template.dwt")
        repo._http._request.assert_called_once_with(
            "POST", "/api/document/new",
            json_body={"template": "template.dwt"},
        )

    def test_new_document_no_template(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.new_document()
        repo._http._request.assert_called_once_with(
            "POST", "/api/document/new", json_body={}
        )

    def test_new_document_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.new_document()

    def test_open_document(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.open_document("C:\\drawing.dwg")

    def test_open_document_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.open_document("C:\\x.dwg")


# ── System Operations ───────────────────────────────────────────


class TestSystemOps:
    def test_execute_command(self, repo: CadRepository) -> None:
        repo._http.execute_command.return_value = "Command output"
        result = repo.execute_command("_LINE")
        assert result == "Command output"

    def test_execute_command_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotSupportedError):
            repo.execute_command("_LINE")

    def test_get_system_variable_http(self, repo: CadRepository) -> None:
        repo._http.get_system_variable.return_value = "1"
        result = repo.get_system_variable("CMDECHO")
        assert result == "1"

    def test_get_system_variable_from_http(self, repo: CadRepository) -> None:
        repo._http.get_system_variable.return_value = "1"
        result = repo.get_system_variable("CMDECHO")
        assert result == "1"

    def test_get_system_variable_com_fallback(self) -> None:
        r = CadRepository()
        r._mode = "com"
        with patch.object(r, "_com") as mock_com:
            mock_com.com_get_system_variable.return_value = "0"
            result = r.get_system_variable("CMDECHO")
            assert result == "0"

    def test_set_system_variable_full(self, repo: CadRepository) -> None:
        repo.set_system_variable("CMDECHO", "0")
        repo._http.set_system_variable.assert_called_once_with("CMDECHO", "0")
        repo._com.com_set_system_variable.assert_called_once_with("CMDECHO", "0")


# ── Extended HTTP-only operations ──────────────────────────────


class TestExtendedHttpOperations:
    """Test delegate methods that call _http directly without mode guards."""

    @pytest.mark.parametrize(
        ("method", "kwargs"),
        [
            ("create_helix", {"axis": (0, 0, 1), "radius": 5}),
            ("create_region", {"boundary": [(0, 0), (10, 0), (10, 10)]}),
            ("create_boundary", {"points": [(0, 0), (10, 0)]}),
            ("create_gradient", {"color1": "red", "color2": "blue"}),
            ("create_arc_length_dimension", {"arc_handle": "H1", "text": "10"}),
            ("export_ifc", {"path": "out.ifc"}),
            ("create_mesh", {"vertices": [(0, 0, 0), (1, 0, 0)]}),
            ("edit_mesh", {"handle": "H1", "vertices": [(0, 0, 0)]}),
            ("set_viewport", {"view": "top"}),
            ("render", {"output": "render.png"}),
        ],
    )
    def test_delegate_method(
        self, repo: CadRepository, method: str, kwargs: dict[str, Any]
    ) -> None:
        """Extended HTTP methods delegate to self._http and return its result."""
        expected = f"{method}_result"
        getattr(repo._http, method).return_value = expected
        result = getattr(repo, method)(**kwargs)
        assert result == expected
        getattr(repo._http, method).assert_called_once_with(**kwargs)

    def test_delegate_method_no_http(self) -> None:
        """When _http is None, delegate methods return None."""
        r = CadRepository()
        r._http = None
        assert r.create_helix(axis=(0, 0, 1), radius=5) is None
        assert r.create_region(boundary=[]) is None
        assert r.create_boundary(points=[]) is None
        assert r.create_gradient(color1="", color2="") is None
        assert r.create_arc_length_dimension(arc_handle="", text="") is None
        assert r.export_ifc(path="") is None
        assert r.create_mesh(vertices=[]) is None
        assert r.edit_mesh(handle="", vertices=[]) is None
        assert r.set_viewport(view="") is None
        assert r.render(output="") is None


class TestSolidHttpSuccess:
    """Test solid methods in HTTP (full) mode."""

    def test_create_box(self, repo: CadRepository) -> None:
        repo._http.create_box.return_value = "H_BOX"
        result = repo.create_box(10, 20, 30)
        assert result == "H_BOX"
        repo._http.create_box.assert_called_once_with(10, 20, 30)

    def test_create_sphere(self, repo: CadRepository) -> None:
        repo._http.create_sphere.return_value = "H_SPH"
        result = repo.create_sphere(5)
        assert result == "H_SPH"
        repo._http.create_sphere.assert_called_once_with(5)

    def test_create_cylinder(self, repo: CadRepository) -> None:
        repo._http.create_cylinder.return_value = "H_CYL"
        result = repo.create_cylinder(3, 10)
        assert result == "H_CYL"
        repo._http.create_cylinder.assert_called_once_with(3, 10)

    def test_create_cone(self, repo: CadRepository) -> None:
        repo._http.create_cone.return_value = "H_CONE"
        result = repo.create_cone(5, 12)
        assert result == "H_CONE"
        repo._http.create_cone.assert_called_once_with(5, 12)

    def test_create_torus(self, repo: CadRepository) -> None:
        repo._http.create_torus.return_value = "H_TOR"
        result = repo.create_torus(10, 2)
        assert result == "H_TOR"
        repo._http.create_torus.assert_called_once_with(10, 2)

    def test_create_wedge(self, repo: CadRepository) -> None:
        repo._http.create_wedge.return_value = "H_WED"
        result = repo.create_wedge(10, 20, 30)
        assert result == "H_WED"
        repo._http.create_wedge.assert_called_once_with(10, 20, 30)

    def test_create_pyramid(self, repo: CadRepository) -> None:
        repo._http.create_pyramid.return_value = "H_PYR"
        result = repo.create_pyramid(height=10, sides=4, radius=5)
        assert result == "H_PYR"
        repo._http.create_pyramid.assert_called_once_with(10, 4, 5)

    def test_boolean_union(self, repo: CadRepository) -> None:
        repo._http.boolean_union.return_value = "H_BOOL"
        result = repo.boolean_union("H1", "H2")
        assert result == "H_BOOL"
        repo._http.boolean_union.assert_called_once_with("H1", "H2")

    def test_boolean_subtract(self, repo: CadRepository) -> None:
        repo._http.boolean_subtract.return_value = "H_BOOL"
        result = repo.boolean_subtract("H1", "H2")
        assert result == "H_BOOL"
        repo._http.boolean_subtract.assert_called_once_with("H1", "H2")

    def test_boolean_intersect(self, repo: CadRepository) -> None:
        repo._http.boolean_intersect.return_value = "H_BOOL"
        result = repo.boolean_intersect("H1", "H2")
        assert result == "H_BOOL"
        repo._http.boolean_intersect.assert_called_once_with("H1", "H2")

    def test_extrude_solid(self, repo: CadRepository) -> None:
        repo._http.extrude_solid.return_value = "H_EXTR"
        result = repo.extrude_solid("H1", 10, taper_angle=5)
        assert result == "H_EXTR"
        repo._http.extrude_solid.assert_called_once_with("H1", 10, 5)


class TestSolidOperationsHttp:
    """Test solid manipulation operations in HTTP mode."""

    def test_revolve_solid(self, repo: CadRepository) -> None:
        repo._http.revolve_solid.return_value = "H_REV"
        result = repo.revolve_solid(
            "H1", axis_x=0, axis_y=0, axis_z=0,
            dir_x=0, dir_y=0, dir_z=1, angle=180,
        )
        assert result == "H_REV"
        repo._http.revolve_solid.assert_called_once_with("H1", 0, 0, 0, 0, 0, 1, 180)

    def test_move_solid(self, repo: CadRepository) -> None:
        repo._http.move_solid.return_value = True
        assert repo.move_solid("H1", 5, 10, 0) is True
        repo._http.move_solid.assert_called_once_with("H1", 5, 10, 0)

    def test_set_3d_view(self, repo: CadRepository) -> None:
        repo._http.set_3d_view.return_value = True
        assert repo.set_3d_view("top", "wireframe") is True
        repo._http.set_3d_view.assert_called_once_with("top", "wireframe")

    def test_get_solid_properties(self, repo: CadRepository) -> None:
        expected = {"volume": 100.0}
        repo._http.get_solid_properties.return_value = expected
        result = repo.get_solid_properties("H1")
        assert result == expected
        repo._http.get_solid_properties.assert_called_once_with("H1")


class TestNurbIfcOperations:
    """Test NURBS and IFC operations in HTTP mode."""

    def test_create_nurb_curve(self, repo: CadRepository) -> None:
        from src.domain.entities import CreateNurbCurveRequest
        repo._http.create_nurb_curve.return_value = {"handle": "NC_001"}
        request = CreateNurbCurveRequest(
            control_points=[[0, 0, 0], [10, 10, 0]],
            knots=[0, 0, 0, 0.5, 1, 1, 1],
            degree=3,
        )
        result = repo.create_nurb_curve(request)
        assert result is not None
        assert str(result) == "NC_001"

    def test_create_nurb_curve_no_handle(self, repo: CadRepository) -> None:
        from src.domain.entities import CreateNurbCurveRequest
        repo._http.create_nurb_curve.return_value = {}
        request = CreateNurbCurveRequest(
            control_points=[[0, 0, 0]],
            knots=[0, 0, 0, 1, 1, 1],
        )
        assert repo.create_nurb_curve(request) is None

    def test_create_nurb_surface(self, repo: CadRepository) -> None:
        from src.domain.entities import CreateNurbSurfaceRequest
        repo._http.create_nurb_surface.return_value = {"handle": "NS_001"}
        request = CreateNurbSurfaceRequest(
            control_points=[[0, 0, 0], [10, 0, 0], [0, 10, 0], [10, 10, 0]],
            u_knots=[0, 0, 0, 1, 1, 1],
            v_knots=[0, 0, 0, 1, 1, 1],
            num_control_u=2,
            num_control_v=2,
        )
        result = repo.create_nurb_surface(request)
        assert result is not None
        assert str(result) == "NS_001"

    def test_modify_nurb_success(self, repo: CadRepository) -> None:
        from src.domain.entities import ModifyNurbRequest
        repo._http.modify_nurb.return_value = {}
        request = ModifyNurbRequest(
            handle="NC_001",
            fit_points=[(0, 0, 0)],
        )
        assert repo.modify_nurb(request) is True

    def test_modify_nurb_failure(self, repo: CadRepository) -> None:
        from src.domain.entities import ModifyNurbRequest
        repo._http.modify_nurb.return_value = None
        request = ModifyNurbRequest(handle="NC_001")
        assert repo.modify_nurb(request) is False

    def test_import_ifc(self, repo: CadRepository) -> None:
        repo._http.import_ifc.return_value = True
        assert repo.import_ifc("model.ifc") is True
        repo._http.import_ifc.assert_called_once_with(path="model.ifc")

    def test_get_ifc_entities(self, repo: CadRepository) -> None:
        expected = [{"type": "IfcWall", "handle": "W1"}]
        repo._http.get_ifc_entities.return_value = expected
        result = repo.get_ifc_entities()
        assert result == expected
        repo._http.get_ifc_entities.assert_called_once()


class TestProjectOperations:
    """Test project creation and save operations."""

    def test_create_project_success(self, repo: CadRepository) -> None:
        repo._http.create_project.return_value = True
        with patch("src.infrastructure.cad_repository.validate_project_path") as mock_val:
            mock_val.return_value = "C:\\projects\\test.ncproj"
            repo.create_project(filename="test.ncproj", directory="C:\\projects")
        repo._http.create_project.assert_called_once_with(
            filename="test.ncproj", directory="C:\\projects", template=None
        )

    def test_create_project_with_template(self, repo: CadRepository) -> None:
        repo._http.create_project.return_value = True
        with patch("src.infrastructure.cad_repository.validate_project_path") as mock_val:
            mock_val.return_value = "C:\\projects\\test.ncproj"
            repo.create_project(
                filename="test.ncproj", directory="C:\\projects",
                template="template.dwt",
            )
        repo._http.create_project.assert_called_once_with(
            filename="test.ncproj", directory="C:\\projects", template="template.dwt"
        )

    def test_create_project_failure(self, repo: CadRepository) -> None:
        repo._http.create_project.return_value = False
        with patch("src.infrastructure.cad_repository.validate_project_path") as mock_val:
            mock_val.return_value = "C:\\projects\\test.ncproj"
            with pytest.raises(RuntimeError, match="create_project failed"):
                repo.create_project(filename="test.ncproj", directory="C:\\projects")

    def test_create_project_empty_filename(self, repo: CadRepository) -> None:
        with pytest.raises(ValueError, match="filename is required"):
            repo.create_project(filename="", directory="C:\\projects")

    def test_create_project_empty_directory(self, repo: CadRepository) -> None:
        with pytest.raises(ValueError, match="directory is required"):
            repo.create_project(filename="test.ncproj", directory="")

    def test_create_project_not_supported(self) -> None:
        r = CadRepository()
        r._mode = "com"
        with pytest.raises(NotSupportedError, match=r"requires .NET engine"):
            r.create_project(filename="x", directory="C:\\")

    def test_save_project_success(self, repo: CadRepository) -> None:
        repo._http.save_project.return_value = True
        with patch("src.infrastructure.cad_repository.validate_project_path") as mock_val:
            mock_val.return_value = "C:\\projects\\out.ncproj"
            repo.save_project(filename="out.ncproj", directory="C:\\projects")
        repo._http.save_project.assert_called_once_with(
            filename="out.ncproj", directory="C:\\projects"
        )

    def test_save_project_failure(self, repo: CadRepository) -> None:
        repo._http.save_project.return_value = False
        with patch("src.infrastructure.cad_repository.validate_project_path") as mock_val:
            mock_val.return_value = "C:\\projects\\out.ncproj"
            with pytest.raises(RuntimeError, match="save_project failed"):
                repo.save_project(filename="out.ncproj", directory="C:\\projects")

    def test_save_project_empty_filename(self, repo: CadRepository) -> None:
        with pytest.raises(ValueError, match="filename is required"):
            repo.save_project(filename="", directory="C:\\projects")

    def test_save_project_empty_directory(self, repo: CadRepository) -> None:
        with pytest.raises(ValueError, match="directory is required"):
            repo.save_project(filename="out.ncproj", directory="")

    def test_save_project_not_supported(self) -> None:
        r = CadRepository()
        r._mode = "com"
        with pytest.raises(NotSupportedError, match=r"requires .NET engine"):
            r.save_project(filename="x", directory="C:\\")


class TestMiscOperations:
    """Test remaining uncovered operations."""

    def test_close_document(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.close_document()
        repo._http._request.assert_called_once_with("POST", "/api/document/close")

    def test_close_document_not_supported(self) -> None:
        r = CadRepository()
        r._mode = "com"
        with pytest.raises(NotSupportedError, match=r"requires .NET engine"):
            r.close_document()

    def test_get_system_fonts_full(self, repo: CadRepository) -> None:
        expected = [{"name": "Arial", "family": "sans"}]
        repo._http.get_system_fonts.return_value = expected
        result = repo.get_system_fonts()
        assert result == expected

    def test_get_system_fonts_not_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.get_system_fonts() == []


# ── MultiCAD API operations ─────────────────────────────────────


class TestMultiCadApi:
    """Test MultiCAD API operations in full and non-full modes."""

    def test_create_grid_axis_full(self, repo: CadRepository) -> None:
        repo._http.create_grid_axis.return_value = True
        request = GridAxisRequest()
        assert repo.create_grid_axis(request) is True
        repo._http.create_grid_axis.assert_called_once_with(
            grid_type="rect",
            origin_x=0,
            origin_y=0,
            spacings_x=[1000.0],
            spacings_y=[1000.0],
            naming_x="1,2,3...",
            naming_y="A,B,C...",
        )

    def test_create_grid_axis_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_grid_axis(GridAxisRequest()) is False

    def test_create_grid_label_full(self, repo: CadRepository) -> None:
        repo._http.create_grid_label.return_value = True
        request = GridLabelRequest(grid_handle="G1", label="A")
        assert repo.create_grid_label(request) is True
        repo._http.create_grid_label.assert_called_once_with(
            grid_handle="G1", label="A", axis_index=0, direction="x"
        )

    def test_create_grid_label_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_grid_label(GridLabelRequest(grid_handle="G1", label="A")) is False

    def test_create_room_full(self, repo: CadRepository) -> None:
        repo._http.create_room.return_value = True
        request = CreateRoomRequest(x=100, y=200, width=500, height=300, name="Office")
        assert repo.create_room(request) is True
        repo._http.create_room.assert_called_once_with(
            x=100, y=200, width=500, height=300, name="Office"
        )

    def test_create_room_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_room(CreateRoomRequest()) is False

    def test_get_room_properties_full(self, repo: CadRepository) -> None:
        expected = {"name": "Office", "area": 150000.0}
        repo._http.get_room_properties.return_value = expected
        result = repo.get_room_properties("H1")
        assert result == expected
        repo._http.get_room_properties.assert_called_once_with(handle="H1")

    def test_get_room_properties_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.get_room_properties("H1") is None

    def test_create_custom_object_full(self, repo: CadRepository) -> None:
        repo._http.create_custom_object.return_value = True
        request = CustomObjectRequest(class_name="MyClass", properties={"key": "val"})
        assert repo.create_custom_object(request) is True
        repo._http.create_custom_object.assert_called_once_with(
            class_name="MyClass", properties={"key": "val"}
        )

    def test_create_custom_object_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_custom_object(CustomObjectRequest(class_name="X")) is False

    def test_create_parametric_object_full(self, repo: CadRepository) -> None:
        repo._http.create_parametric_object.return_value = True
        request = ParametricObjectRequest(type="gear", parameters={"teeth": 12})
        assert repo.create_parametric_object(request) is True
        repo._http.create_parametric_object.assert_called_once_with(
            object_type="gear", parameters={"teeth": 12}
        )

    def test_create_parametric_object_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_parametric_object(ParametricObjectRequest(type="x")) is False

    def test_create_reactor_full(self, repo: CadRepository) -> None:
        repo._http.create_reactor.return_value = True
        request = ReactorRequest(entity_handle="H1", event_type="modified")
        assert repo.create_reactor(request) is True
        repo._http.create_reactor.assert_called_once_with(
            entity_handle="H1", event_type="modified"
        )

    def test_create_reactor_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_reactor(ReactorRequest(entity_handle="H1")) is False

    def test_create_2d_break_full(self, repo: CadRepository) -> None:
        repo._http.create_2d_break.return_value = True
        request = Break2dRequest(view_handle="V1", x1=0, y1=0, x2=100, y2=100)
        assert repo.create_2d_break(request) is True
        repo._http.create_2d_break.assert_called_once_with(
            view_handle="V1", x1=0, y1=0, x2=100, y2=100
        )

    def test_create_2d_break_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_2d_break(Break2dRequest(view_handle="V1")) is False

    def test_start_motion_preview_full(self, repo: CadRepository) -> None:
        repo._http.start_motion_preview.return_value = True
        assert repo.start_motion_preview(MotionPreviewRequest(handle="H1")) is True
        repo._http.start_motion_preview.assert_called_once_with(handle="H1")

    def test_start_motion_preview_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.start_motion_preview(MotionPreviewRequest(handle="H1")) is False

    def test_stop_motion_preview_full(self, repo: CadRepository) -> None:
        repo._http.stop_motion_preview.return_value = True
        assert repo.stop_motion_preview() is True
        repo._http.stop_motion_preview.assert_called_once()

    def test_stop_motion_preview_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.stop_motion_preview() is False

    def test_create_body_contour_full(self, repo: CadRepository) -> None:
        repo._http.create_body_contour.return_value = True
        assert repo.create_body_contour(BodyContourRequest(solid_handle="S1")) is True
        repo._http.create_body_contour.assert_called_once_with(solid_handle="S1")

    def test_create_body_contour_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.create_body_contour(BodyContourRequest(solid_handle="S1")) is False

    def test_check_3d_faces_full(self, repo: CadRepository) -> None:
        expected = {"faces": 12, "errors": []}
        repo._http.check_3d_faces.return_value = expected
        result = repo.check_3d_faces("H1")
        assert result == expected
        repo._http.check_3d_faces.assert_called_once_with(handle="H1")

    def test_check_3d_faces_non_full(self) -> None:
        r = CadRepository()
        r._mode = "com"
        assert r.check_3d_faces("H1") is None


# ── EntityHandle helper ──────────────────────────────────────────


class TestEntityHandle:
    def test_to_handle_non_none(self) -> None:
        from src.infrastructure.cad_repository import CadRepository
        r = CadRepository()
        result = r._to_handle("ABC")  # type: ignore[attr-defined]
        assert result is not None
        assert str(result) == "ABC"

    def test_to_handle_none(self) -> None:
        from src.infrastructure.cad_repository import CadRepository
        r = CadRepository()
        result = r._to_handle(None)  # type: ignore[attr-defined]
        assert result is None
