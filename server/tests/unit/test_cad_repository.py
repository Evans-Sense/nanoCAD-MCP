from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.domain.entities import (
    CadArc,
    CadBlock,
    CadBlockRef,
    CadCircle,
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
    CadText,
    CadXLine,
    EntityHandle,
    LayerName,
    Point2D,
)
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
        with pytest.raises(NotImplementedError):
            repo.create_mtext(
                CadMText(top_left=Point2D(x=0, y=0), bottom_right=Point2D(x=10, y=10), content="X", height=1)
            )
        with pytest.raises(NotImplementedError):
            repo.create_ellipse(CadEllipse(center=Point2D(x=0, y=0), major_axis_end=Point2D(x=5, y=0), radius_ratio=0.5))
        with pytest.raises(NotImplementedError):
            repo.create_spline(CadSpline(fit_points=[Point2D(x=0, y=0), Point2D(x=10, y=10)], degree=3))
        with pytest.raises(NotImplementedError):
            repo.create_ray(CadRay(start=Point2D(x=0, y=0), direction=Point2D(x=1, y=0)))
        with pytest.raises(NotImplementedError):
            repo.create_xline(CadXLine(through=Point2D(x=0, y=0), direction=Point2D(x=1, y=0)))
        with pytest.raises(NotImplementedError):
            repo.create_solid(CadSolid(points=[Point2D(x=0, y=0), Point2D(x=10, y=0), Point2D(x=5, y=10)]))
        with pytest.raises(NotImplementedError):
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
        assert result is not None and result.handle is not None
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
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
            repo.insert_block(ref)

    def test_delete_block(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        assert repo.delete_block(LayerName(value="OldBlock")) is True

    def test_delete_block_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
            repo.new_document()

    def test_open_document(self, repo: CadRepository) -> None:
        repo._http._request.return_value = {"success": True}
        repo.open_document("C:\\drawing.dwg")

    def test_open_document_not_implemented(self) -> None:
        repo = CadRepository()
        repo._mode = "com"
        with pytest.raises(NotImplementedError):
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
        with pytest.raises(NotImplementedError):
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
