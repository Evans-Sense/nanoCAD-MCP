from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.application.use_cases import (
    BlockUseCase,
    DocumentUseCase,
    EntityUseCase,
    SolidUseCase,
)
from src.domain.entities import CadBlock, EntityHandle, LayerName, Point2D


# ── SolidUseCase ────────────────────────────────────────────


class TestSolidUseCase:
    @pytest.fixture
    def mock_http(self) -> MagicMock:
        http = MagicMock()
        http.is_available = True
        return http

    @pytest.fixture
    def mock_repo_with_http(self, mock_http: MagicMock) -> MagicMock:
        repo = MagicMock()
        repo._http = mock_http
        return repo

    def test_requires_http(self) -> None:
        repo = MagicMock()
        repo._http = None
        with pytest.raises(RuntimeError, match="requires a CadRepository"):
            SolidUseCase(repo)

    def test_create_box(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_box.return_value = "BOX_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_box(x=10, y=20, z=30)
        assert result["handle"] == "BOX_001"
        assert result["type"] == "BOX"
        mock_http.create_box.assert_called_once_with(10, 20, 30)

    def test_create_box_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_box.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_box(x=10, y=20, z=30)
        assert "error" in result

    def test_create_sphere(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_sphere.return_value = "SPH_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_sphere(radius=15.0)
        assert result["handle"] == "SPH_001"
        assert result["type"] == "SPHERE"

    def test_create_sphere_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_sphere.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_sphere(radius=15.0)
        assert "error" in result

    def test_create_cylinder(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_cylinder.return_value = "CYL_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_cylinder(radius=5.0, height=20.0)
        assert result["handle"] == "CYL_001"
        assert result["type"] == "CYLINDER"

    def test_create_cylinder_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_cylinder.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_cylinder(radius=5.0, height=20.0)
        assert "error" in result

    def test_create_cone(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_cone.return_value = "CONE_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_cone(radius_bottom=5.0, height=15.0)
        assert result["handle"] == "CONE_001"
        assert result["type"] == "CONE"

    def test_create_cone_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_cone.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_cone(radius_bottom=5.0, height=15.0)
        assert "error" in result

    def test_create_torus(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_torus.return_value = "TOR_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_torus(major_radius=20.0, minor_radius=5.0)
        assert result["handle"] == "TOR_001"
        assert result["type"] == "TORUS"

    def test_create_torus_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_torus.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_torus(major_radius=20.0, minor_radius=5.0)
        assert "error" in result

    def test_create_wedge(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_wedge.return_value = "WDG_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_wedge(x=10, y=20, z=30)
        assert result["handle"] == "WDG_001"
        assert result["type"] == "WEDGE"

    def test_create_wedge_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_wedge.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_wedge(x=10, y=20, z=30)
        assert "error" in result

    def test_create_pyramid(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_pyramid.return_value = "PYR_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_pyramid(height=25.0, sides=6, radius=10.0)
        assert result["handle"] == "PYR_001"
        assert result["type"] == "PYRAMID"

    def test_create_pyramid_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.create_pyramid.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.create_pyramid(height=25.0, sides=6, radius=10.0)
        assert "error" in result

    def test_boolean_union(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.boolean_union.return_value = "BOOL_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.boolean_union(handle1="BOX_1", handle2="BOX_2")
        assert result["handle"] == "BOOL_001"
        assert result["type"] == "SOLID3D"
        mock_http.boolean_union.assert_called_once_with("BOX_1", "BOX_2")

    def test_boolean_union_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.boolean_union.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.boolean_union(handle1="BOX_1", handle2="BOX_2")
        assert "error" in result

    def test_boolean_subtract(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.boolean_subtract.return_value = "BOOL_002"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.boolean_subtract(handle1="BOX_1", handle2="CYL_1")
        assert result["handle"] == "BOOL_002"
        mock_http.boolean_subtract.assert_called_once_with("BOX_1", "CYL_1")

    def test_boolean_subtract_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.boolean_subtract.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.boolean_subtract(handle1="BOX_1", handle2="CYL_1")
        assert "error" in result

    def test_boolean_intersect(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.boolean_intersect.return_value = "BOOL_003"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.boolean_intersect(handle1="BOX_1", handle2="SPH_1")
        assert result["handle"] == "BOOL_003"
        mock_http.boolean_intersect.assert_called_once_with("BOX_1", "SPH_1")

    def test_boolean_intersect_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.boolean_intersect.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.boolean_intersect(handle1="BOX_1", handle2="SPH_1")
        assert "error" in result

    def test_extrude_solid(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.extrude_solid.return_value = "EXT_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.extrude_solid(handle="PLINE_1", height=50.0, taper_angle=5.0)
        assert result["handle"] == "EXT_001"
        mock_http.extrude_solid.assert_called_once_with("PLINE_1", 50.0, 5.0)

    def test_extrude_solid_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.extrude_solid.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.extrude_solid(handle="PLINE_1", height=50.0)
        assert "error" in result

    def test_revolve_solid(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.revolve_solid.return_value = "REV_001"
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.revolve_solid(
            handle="PLINE_1", axis_x=0, axis_y=0, axis_z=0,
            dir_x=0, dir_y=0, dir_z=1, angle=360,
        )
        assert result["handle"] == "REV_001"
        mock_http.revolve_solid.assert_called_once_with(
            "PLINE_1", 0, 0, 0, 0, 0, 1, 360
        )

    def test_revolve_solid_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.revolve_solid.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.revolve_solid(handle="PLINE_1")
        assert "error" in result

    def test_move_solid(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.move_solid.return_value = True
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.move_solid(handle="BOX_1", dx=10, dy=20, dz=30)
        assert result["success"] is True
        assert result["dx"] == 10
        assert result["dy"] == 20
        assert result["dz"] == 30
        mock_http.move_solid.assert_called_once_with("BOX_1", 10, 20, 30)

    def test_move_solid_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.move_solid.return_value = False
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.move_solid(handle="BOX_1", dx=10, dy=20)
        assert result["success"] is False

    def test_set_3d_view(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.set_3d_view.return_value = True
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.set_3d_view(direction="SW Isometric", render_mode="wireframe")
        assert result["success"] is True
        assert result["direction"] == "SW Isometric"
        mock_http.set_3d_view.assert_called_once_with("SW Isometric", "wireframe")

    def test_set_3d_view_failure(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.set_3d_view.return_value = False
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.set_3d_view(direction="Top")
        assert result["success"] is False

    def test_get_solid_properties(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.get_solid_properties.return_value = {
            "volume": 1000.0,
            "surface_area": 600.0,
            "centroid": (5.0, 5.0, 5.0),
        }
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.get_solid_properties(handle="BOX_1")
        assert result["volume"] == 1000.0
        assert result["surface_area"] == 600.0
        mock_http.get_solid_properties.assert_called_once_with("BOX_1")

    def test_get_solid_properties_none(self, mock_repo_with_http: MagicMock, mock_http: MagicMock) -> None:
        mock_http.get_solid_properties.return_value = None
        uc = SolidUseCase(mock_repo_with_http)
        result = uc.get_solid_properties(handle="INVALID")
        assert result == {}


# ── EntityUseCase additional tests ──────────────────────────


class TestEntityUseCaseAdditional:
    def test_create_mtext(self, mock_repo: MagicMock) -> None:
        mock_repo.create_mtext.return_value = EntityHandle(value="MTEXT_001")
        uc = EntityUseCase(mock_repo)
        result = uc.create_mtext(
            x1=0, y1=0, x2=100, y2=50,
            content="Hello World", height=5.0, layer="0",
        )
        assert result["type"] == "MTEXT"
        assert result["handle"] == "MTEXT_001"
        mock_repo.create_mtext.assert_called_once()

    def test_create_ellipse(self, mock_repo: MagicMock) -> None:
        mock_repo.create_ellipse.return_value = EntityHandle(value="ELLIPSE_001")
        uc = EntityUseCase(mock_repo)
        result = uc.create_ellipse(
            cx=0, cy=0, major_axis_x=10, major_axis_y=0,
            radius_ratio=0.5, layer="0",
        )
        assert result["type"] == "ELLIPSE"
        assert result["handle"] == "ELLIPSE_001"
        mock_repo.create_ellipse.assert_called_once()

    def test_get_entity_found(self, mock_repo: MagicMock) -> None:
        from src.domain.entities import CadLine, EntityHandle, LayerName, Point2D

        entity = CadLine(
            start=Point2D(x=0, y=0),
            end=Point2D(x=10, y=10),
            layer=LayerName(value="0"),
        )
        mock_repo.get_entity.return_value = entity
        uc = EntityUseCase(mock_repo)
        result = uc.get_entity(handle="LINE_001")
        assert result["entity_type"] == "LINE"

    def test_get_entity_not_found(self, mock_repo: MagicMock) -> None:
        mock_repo.get_entity.return_value = None
        uc = EntityUseCase(mock_repo)
        result = uc.get_entity(handle="INVALID")
        assert "error" in result

    def test_copy_entity_success(self, mock_repo: MagicMock) -> None:
        mock_repo.copy_entity.return_value = EntityHandle(value="COPY_001")
        uc = EntityUseCase(mock_repo)
        result = uc.copy_entity(handle="LINE_001")
        assert result["success"] is True
        assert result["new_handle"] == "COPY_001"

    def test_copy_entity_failure(self, mock_repo: MagicMock) -> None:
        mock_repo.copy_entity.return_value = None
        uc = EntityUseCase(mock_repo)
        result = uc.copy_entity(handle="LINE_001")
        assert result["success"] is False

    def test_rotate_entity_with_center(self, mock_repo: MagicMock) -> None:
        mock_repo.rotate_entity.return_value = True
        uc = EntityUseCase(mock_repo)
        result = uc.rotate_entity(handle="LINE_001", angle=45.0, cx=5.0, cy=5.0)
        assert result["success"] is True
        assert result["angle"] == 45.0

    def test_rotate_entity_without_center(self, mock_repo: MagicMock) -> None:
        mock_repo.rotate_entity.return_value = True
        uc = EntityUseCase(mock_repo)
        result = uc.rotate_entity(handle="LINE_001", angle=90.0)
        assert result["success"] is True

    def test_rotate_entity_partial_center_raises(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        with pytest.raises(ValueError, match="Both cx and cy must be provided"):
            uc.rotate_entity(handle="LINE_001", angle=45.0, cx=5.0)

    def test_scale_entity_with_center(self, mock_repo: MagicMock) -> None:
        mock_repo.scale_entity.return_value = True
        uc = EntityUseCase(mock_repo)
        result = uc.scale_entity(handle="LINE_001", factor=2.0, cx=0.0, cy=0.0)
        assert result["success"] is True
        assert result["factor"] == 2.0

    def test_scale_entity_without_center(self, mock_repo: MagicMock) -> None:
        mock_repo.scale_entity.return_value = True
        uc = EntityUseCase(mock_repo)
        result = uc.scale_entity(handle="LINE_001", factor=3.0)
        assert result["success"] is True


# ── BlockUseCase additional tests ───────────────────────────


class TestBlockUseCaseAdditional:
    def test_delete_block(self, mock_repo: MagicMock) -> None:
        mock_repo.delete_block.return_value = True
        uc = BlockUseCase(mock_repo)
        result = uc.delete_block(name="MyBlock")
        assert result["success"] is True
        assert result["name"] == "MyBlock"
        mock_repo.delete_block.assert_called_once()

    def test_get_blocks_empty(self, mock_repo: MagicMock) -> None:
        mock_repo.get_blocks.return_value = []
        uc = BlockUseCase(mock_repo)
        result = uc.get_blocks()
        assert result == []

    def test_get_blocks_with_items(self, mock_repo: MagicMock) -> None:
        mock_repo.get_blocks.return_value = [
            CadBlock(name=LayerName(value="BlockA"), base_point=Point2D(x=0, y=0)),
            CadBlock(name=LayerName(value="BlockB"), base_point=Point2D(x=0, y=0)),
        ]
        uc = BlockUseCase(mock_repo)
        result = uc.get_blocks()
        assert len(result) == 2
        assert result[0]["name"] == "BlockA"
        assert result[1]["name"] == "BlockB"

    def test_insert_block(self, mock_repo: MagicMock) -> None:
        mock_repo.insert_block.return_value = EntityHandle(value="INST_001")
        uc = BlockUseCase(mock_repo)
        result = uc.insert_block(name="Chair", x=10.0, y=20.0, scale=1.5, rotation=45.0)
        assert result["handle"] == "INST_001"
        assert result["block_name"] == "Chair"
        assert result["insertion"] == (10.0, 20.0)
        mock_repo.insert_block.assert_called_once()

    def test_get_block_entities_requires_http(self, mock_repo: MagicMock) -> None:
        mock_repo._http = None
        uc = BlockUseCase(mock_repo)
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.get_block_entities(name="MyBlock")


# ── DocumentUseCase additional tests ────────────────────────


class TestDocumentUseCaseAdditional:
    def test_new_document(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.new_document(template="acadiso.dwt")
        assert result["success"] is True
        assert result["template"] == "acadiso.dwt"
        mock_repo.new_document.assert_called_once_with("acadiso.dwt")

    def test_new_document_no_template(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.new_document()
        assert result["success"] is True
        assert result["template"] is None
        mock_repo.new_document.assert_called_once_with(None)

    def test_export_dwg(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.export_dwg(path="C:/output.dwg")
        assert result["success"] is True
        assert result["path"] == "C:/output.dwg"
        mock_repo.export_dwg.assert_called_once_with("C:/output.dwg")

    def test_export_dxf(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.export_dxf(path="C:/output.dxf")
        assert result["success"] is True
        assert result["path"] == "C:/output.dxf"
        mock_repo.export_dxf.assert_called_once_with("C:/output.dxf")

    def test_zoom_extents(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.zoom_extents()
        assert result["success"] is True
        mock_repo.zoom_extents.assert_called_once()

    def test_get_info(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.get_info()
        assert result["name"] == "test.dwg"
        assert result["entities_count"] == 5
