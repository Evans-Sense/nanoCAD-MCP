from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.application.use_cases import (
    BlockUseCase,
    DocumentUseCase,
    EntityUseCase,
    LayerUseCase,
    SystemUseCase,
)
from src.domain.entities import EntityHandle, LayerName


class TestEntityUseCase:
    def test_create_line(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_line(x1=0, y1=0, x2=10, y2=10, layer="0")
        assert result["type"] == "LINE"
        assert result["handle"] == "LINE_001"
        mock_repo.create_line.assert_called_once()

    def test_create_circle(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_circle(cx=5, cy=5, radius=10)
        assert result["type"] == "CIRCLE"
        assert result["radius"] == 10

    def test_create_arc(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_arc(cx=0, cy=0, radius=5, start_angle=0, end_angle=180)
        assert result["type"] == "ARC"

    def test_create_polyline(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_polyline(
            vertices=[(0, 0), (10, 0), (10, 10), (0, 10)],
            closed=True,
        )
        assert result["type"] == "POLYLINE"
        assert result["vertices_count"] == 4

    def test_create_rectangle(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_rectangle(x1=0, y1=0, x2=10, y2=10)
        assert result["type"] == "POLYLINE"
        assert result["vertices_count"] == 4

    def test_create_text(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_text(x=1, y=1, content="Hello", height=2.5)
        assert result["type"] == "TEXT"
        assert result["content"] == "Hello"

    def test_create_point(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        result = uc.create_point(x=10, y=20)
        assert result["type"] == "POINT"

    def test_delete_entity(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo.delete_entity.return_value = True
        result = uc.delete_entity(handle="LINE_001")
        assert result["success"] is True

    def test_move_entity(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo.move_entity.return_value = True
        result = uc.move_entity(handle="LINE_001", dx=5.0, dy=10.0)
        assert result["success"] is True
        assert result["delta"] == (5.0, 10.0)

    def test_scale_entity(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo.scale_entity.return_value = True
        result = uc.scale_entity(handle="LINE_001", factor=2.0, cx=0, cy=0)
        assert result["success"] is True
        assert result["factor"] == 2.0

    def test_mirror_entity(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo.mirror_entity.return_value = True
        result = uc.mirror_entity(handle="LINE_001", p1_x=0, p1_y=0, p2_x=10, p2_y=10)
        assert result["success"] is True

    def test_create_spline(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo.create_spline.return_value = EntityHandle(value="SPLINE_001")
        result = uc.create_spline(
            fit_points=[(0, 0), (5, 10), (10, 0)],
            degree=3,
            closed=False,
        )
        assert result["type"] == "SPLINE"
        assert result["handle"] == "SPLINE_001"
        assert result["fit_points_count"] == 3
        mock_repo.create_spline.assert_called_once()

    def test_create_helix_requires_http(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        del mock_repo._http
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.create_helix()

    def test_create_helix(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.create_helix.return_value = "HLX_001"
        result = uc.create_helix(
            center_x=0, center_y=0, center_z=0, start_radius=20,
            end_radius=10, height=50, turns=3,
        )
        assert result == "HLX_001"
        mock_repo._http.create_helix.assert_called_once_with(
            center_x=0, center_y=0, center_z=0, start_radius=20,
            end_radius=10, height=50, turns=3, layer=None,
        )

    def test_create_region(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.create_region.return_value = {"handle": "REG_001"}
        result = uc.create_region(curve_handles=["C1", "C2"])
        assert result == {"handle": "REG_001"}
        mock_repo._http.create_region.assert_called_once_with(
            curve_handles=["C1", "C2"],
        )

    def test_create_boundary(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.create_boundary.return_value = {"handle": "BND_001"}
        result = uc.create_boundary(point_x=50, point_y=50)
        assert result == {"handle": "BND_001"}
        mock_repo._http.create_boundary.assert_called_once_with(
            point_x=50, point_y=50, layer=None,
        )

    def test_create_mesh(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.create_mesh.return_value = {"handle": "M001"}
        result = uc.create_mesh(
            vertices=[[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
            face_indices=[3, 2, 1, 0],
            smooth_level=0,
        )
        assert result == {"handle": "M001"}
        mock_repo._http.create_mesh.assert_called_once_with(
            vertices=[[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
            face_indices=[3, 2, 1, 0],
            smooth_level=0,
            layer=None,
        )

    def test_create_mesh_requires_http(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        del mock_repo._http
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.create_mesh()

    def test_edit_mesh(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.edit_mesh.return_value = {"success": True}
        result = uc.edit_mesh(handle="M001", vertices=[[1, 1, 1]], subdivide=1)
        assert result == {"success": True}

    def test_set_viewport(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.set_viewport.return_value = True
        result = uc.set_viewport(name="test", vp_type="2vert")
        assert result is True

    def test_render(self, mock_repo: MagicMock) -> None:
        uc = EntityUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.render.return_value = True
        result = uc.render(output_file="out.png")
        assert result is True


class TestLayerUseCase:
    def test_create_layer(self, mock_repo: MagicMock) -> None:
        uc = LayerUseCase(mock_repo)
        result = uc.create_layer(name="Walls")
        assert result["success"] is True
        mock_repo.create_layer.assert_called_once()

    def test_get_linetypes(self, mock_repo: MagicMock) -> None:
        uc = LayerUseCase(mock_repo)
        mock_repo.get_linetypes.return_value = [
            {"name": "Continuous", "description": "Solid line"},
            {"name": "Dashed", "description": "Broken line"},
        ]
        result = uc.get_linetypes()
        assert len(result) == 2
        assert result[0]["name"] == "Continuous"
        mock_repo.get_linetypes.assert_called_once()

    def test_get_layers(self, mock_repo: MagicMock) -> None:
        uc = LayerUseCase(mock_repo)
        layers = uc.get_layers()
        assert len(layers) == 2
        assert layers[0]["name"] == "0"

    def test_set_current_layer(self, mock_repo: MagicMock) -> None:
        uc = LayerUseCase(mock_repo)
        result = uc.set_current_layer(name="Walls")
        assert result["success"] is True
        mock_repo.set_current_layer.assert_called_once()

    def test_delete_layer(self, mock_repo: MagicMock) -> None:
        uc = LayerUseCase(mock_repo)
        mock_repo.delete_layer.return_value = True
        result = uc.delete_layer(name="OldLayer")
        assert result["success"] is True
        assert result["name"] == "OldLayer"
        mock_repo.delete_layer.assert_called_once_with(LayerName(value="OldLayer"))

    def test_set_layer_state(self, mock_repo: MagicMock) -> None:
        uc = LayerUseCase(mock_repo)
        result = uc.set_layer_state(name="Hidden", on=False, frozen=True, locked=False)
        assert result["success"] is True
        assert result["name"] == "Hidden"
        mock_repo.set_layer_state.assert_called_once_with(
            LayerName(value="Hidden"), on=False, frozen=True, locked=False,
        )


class TestDocumentUseCase:
    def test_get_info(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        info = uc.get_info()
        assert info["name"] == "test.dwg"
        assert info["entities_count"] == 5

    def test_save(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.save(path="C:/output.dwg")
        assert result["success"] is True

    def test_save_no_path(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.save()
        assert result["success"] is True

    def test_export_pdf(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.export_pdf(path="C:/output.pdf")
        assert result["success"] is True

    def test_open_document(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.open_document(path="C:/drawing.dwg")
        assert result["success"] is True
        assert result["path"] == "C:/drawing.dwg"
        mock_repo.open_document.assert_called_once_with("C:/drawing.dwg")

    def test_close_document(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.close_document()
        assert result["success"] is True
        mock_repo.close_document.assert_called_once()

    def test_create_project(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.create_project(
            filename="model.dwg", directory="C:/projects"
        )
        assert result["success"] is True
        assert result["filename"] == "model.dwg"
        assert result["directory"] == "C:/projects"
        assert result["path"] == "C:/projects/model.dwg"
        mock_repo.create_project.assert_called_once_with(
            filename="model.dwg", directory="C:/projects", template=None
        )

    def test_create_project_with_template(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.create_project(
            filename="model.dwg",
            directory="C:/projects",
            template="ansi.dwt",
        )
        assert result["success"] is True
        assert result["path"] == "C:/projects/model.dwg"
        mock_repo.create_project.assert_called_once_with(
            filename="model.dwg", directory="C:/projects", template="ansi.dwt"
        )

    def test_create_project_normalizes_backslashes(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.create_project(
            filename="model.dwg", directory="C:\\projects\\sub"
        )
        # backslashes in returned path are normalized to forward slashes
        assert "\\" not in result["path"]
        assert result["path"] == "C:/projects/sub/model.dwg"

    def test_save_project(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.save_project(
            filename="out.dwg", directory="C:/projects"
        )
        assert result["success"] is True
        assert result["filename"] == "out.dwg"
        assert result["directory"] == "C:/projects"
        assert result["path"] == "C:/projects/out.dwg"
        mock_repo.save_project.assert_called_once_with(
            filename="out.dwg", directory="C:/projects"
        )

    def test_save_project_normalizes_backslashes(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        result = uc.save_project(
            filename="out.dwg", directory="C:\\projects\\sub"
        )
        assert "\\" not in result["path"]
        assert result["path"] == "C:/projects/sub/out.dwg"

    def test_export_ifc_requires_http(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        del mock_repo._http
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.export_ifc(path="C:/model.ifc")

    def test_export_ifc(self, mock_repo: MagicMock) -> None:
        uc = DocumentUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.export_ifc.return_value = {"success": True}
        result = uc.export_ifc(path="C:/model.ifc")
        assert result == {"success": True}
        mock_repo._http.export_ifc.assert_called_once_with(
            path="C:/model.ifc",
        )


class TestSystemUseCase:
    def test_get_fonts(self, mock_repo: MagicMock) -> None:
        uc = SystemUseCase(mock_repo)
        mock_repo.get_system_fonts.return_value = [
            {"name": "Arial", "type": "truetype"},
        ]
        result = uc.get_fonts()
        assert len(result) == 1
        assert result[0]["name"] == "Arial"
        mock_repo.get_system_fonts.assert_called_once()

    def test_is_available(self, mock_repo: MagicMock) -> None:
        uc = SystemUseCase(mock_repo)
        result = uc.is_available()
        assert result["available"] is True
        assert result["mode"] == "full"

    def test_get_info(self, mock_repo: MagicMock) -> None:
        uc = SystemUseCase(mock_repo)
        info = uc.get_info()
        assert info["version"] == "Test"

    def test_get_variable(self, mock_repo: MagicMock) -> None:
        uc = SystemUseCase(mock_repo)
        mock_repo.get_system_variable.return_value = "test.dwg"
        result = uc.get_variable(name="DWGNAME")
        assert result["value"] == "test.dwg"

    def test_set_variable(self, mock_repo: MagicMock) -> None:
        uc = SystemUseCase(mock_repo)
        result = uc.set_variable(name="FILEDIA", value="1")
        assert result["success"] is True

    def test_execute_command(self, mock_repo: MagicMock) -> None:
        uc = SystemUseCase(mock_repo)
        mock_repo.execute_command.return_value = "Command completed"
        result = uc.execute_command(command="LINE")
        assert result["command"] == "LINE"
        assert result["output"] == "Command completed"
        mock_repo.execute_command.assert_called_once_with("LINE")


class TestBlockUseCase:
    def test_get_block_entities_raises_without_http(self, mock_repo: MagicMock) -> None:
        uc = BlockUseCase(mock_repo)
        del mock_repo._http
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.get_block_entities(name="Block1")

    def test_get_block_entities_raises_when_http_unavailable(self, mock_repo: MagicMock) -> None:
        uc = BlockUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = False
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.get_block_entities(name="Block1")

    def test_get_block_entities(self, mock_repo: MagicMock) -> None:
        uc = BlockUseCase(mock_repo)
        mock_repo._http = MagicMock()
        mock_repo._http.is_available = True
        mock_repo._http.get_block_entities.return_value = [{"handle": "E1"}]
        result = uc.get_block_entities(name="Block1")
        assert result == [{"handle": "E1"}]


class TestFeatureUseCase:
    def test_create_simple_hole(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        http = MagicMock()
        http.is_available = True
        http.create_simple_hole.return_value = {"success": True}
        uc = FeatureUseCase(http)
        result = uc.create_simple_hole(solid_handle="S1", diameter=10, depth=50)
        assert result == {"success": True}
        http.create_simple_hole.assert_called_once_with(
            solid_handle="S1", diameter=10, depth=50
        )

    def test_create_threaded_hole(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        http = MagicMock()
        http.is_available = True
        http.create_threaded_hole.return_value = {"success": True}
        uc = FeatureUseCase(http)
        result = uc.create_threaded_hole(solid_handle="S1", diameter=10, depth=50)
        assert result == {"success": True}

    def test_create_shell(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        http = MagicMock()
        http.is_available = True
        http.create_shell.return_value = {"success": True}
        uc = FeatureUseCase(http)
        result = uc.create_shell(solid_handle="S1", thickness=2, outward=False)
        assert result == {"success": True}

    def test_create_mirror_feature(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        http = MagicMock()
        http.is_available = True
        http.create_mirror_feature.return_value = {"success": True}
        uc = FeatureUseCase(http)
        result = uc.create_mirror_feature(solid_handle="S1", plane_handle="P1")
        assert result == {"success": True}

    def test_create_circular_pattern(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        http = MagicMock()
        http.is_available = True
        http.create_circular_pattern.return_value = {"success": True}
        uc = FeatureUseCase(http)
        result = uc.create_circular_pattern(
            solid_handle="S1", feature_handle="F1", count=4, angle=360
        )
        assert result == {"success": True}

    def test_create_sketch(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        http = MagicMock()
        http.is_available = True
        http.create_sketch.return_value = "SKETCH_001"
        uc = FeatureUseCase(http)
        result = uc.create_sketch(solid_handle="S1")
        assert result == "SKETCH_001"

    def test_raises_without_http(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import FeatureUseCase

        uc = FeatureUseCase(None)
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.create_simple_hole(solid_handle="S1", diameter=10, depth=50)


class TestNurbIfcUseCase:
    def test_create_nurb_curve(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.create_nurb_curve.return_value = {"handle": "NC_001"}
        uc = NurbIfcUseCase(http)
        result = uc.create_nurb_curve(
            degree=3, control_points=[[0, 0], [5, 10], [10, 0]],
            knots=[0, 0, 0, 1, 1, 1],
        )
        assert result == "NC_001"
        http.create_nurb_curve.assert_called_once()

    def test_create_nurb_curve_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.create_nurb_curve.return_value = {}
        uc = NurbIfcUseCase(http)
        result = uc.create_nurb_curve(degree=3, control_points=[[0, 0]], knots=[0, 1])
        assert result is None

    def test_create_nurb_curve_with_weights_and_layer(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.create_nurb_curve.return_value = {"handle": "NC_001"}
        uc = NurbIfcUseCase(http)
        result = uc.create_nurb_curve(
            degree=3, control_points=[[0, 0], [10, 0], [10, 10]],
            knots=[0, 0, 0, 1, 1, 1], weights=[1, 1, 1], layer="NURBS",
        )
        assert result == "NC_001"

    def test_create_nurb_surface(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.create_nurb_surface.return_value = {"handle": "NS_001"}
        uc = NurbIfcUseCase(http)
        result = uc.create_nurb_surface(
            degree_u=3, degree_v=2,
            control_points=[[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
            u_knots=[0, 0, 0, 1, 1, 1], v_knots=[0, 0, 1, 1],
            num_control_u=2, num_control_v=2,
        )
        assert result == "NS_001"
        http.create_nurb_surface.assert_called_once()

    def test_create_nurb_surface_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.create_nurb_surface.return_value = {}
        uc = NurbIfcUseCase(http)
        result = uc.create_nurb_surface(
            degree_u=2, degree_v=2,
            control_points=[[0, 0]], u_knots=[0, 1], v_knots=[0, 1],
            num_control_u=1, num_control_v=1,
        )
        assert result is None

    def test_modify_nurb(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.modify_nurb.return_value = {"success": True}
        uc = NurbIfcUseCase(http)
        result = uc.modify_nurb(handle="NC_001", control_points=[[0, 0], [5, 5], [10, 0]])
        assert result is True

    def test_modify_nurb_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.modify_nurb.return_value = None
        uc = NurbIfcUseCase(http)
        result = uc.modify_nurb(handle="BAD")
        assert result is False

    def test_import_ifc(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.import_ifc.return_value = True
        uc = NurbIfcUseCase(http)
        result = uc.import_ifc(path="C:/model.ifc")
        assert result is True
        http.import_ifc.assert_called_once_with(path="C:/model.ifc")

    def test_import_ifc_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.import_ifc.return_value = False
        uc = NurbIfcUseCase(http)
        result = uc.import_ifc(path="C:/bad.ifc")
        assert result is False

    def test_get_ifc_entities(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.get_ifc_entities.return_value = [
            {"handle": "I1", "type": "IfcWall", "layer": "0", "visible": True},
        ]
        uc = NurbIfcUseCase(http)
        result = uc.get_ifc_entities()
        assert result == [{"handle": "I1", "type": "IfcWall", "layer": "0", "visible": True}]

    def test_get_ifc_entities_empty(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        http = MagicMock()
        http.is_available = True
        http.get_ifc_entities.return_value = []
        uc = NurbIfcUseCase(http)
        result = uc.get_ifc_entities()
        assert result == []

    def test_raises_without_http(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import NurbIfcUseCase

        uc = NurbIfcUseCase(None)
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.create_nurb_curve(degree=3, control_points=[[0, 0]], knots=[0, 1])


class TestMultiCadUseCase:
    def test_create_grid_axis(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_grid_axis.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_grid_axis(grid_type="rect", origin_x=0, origin_y=0)
        assert result is True
        http.create_grid_axis.assert_called_once_with(
            grid_type="rect", origin_x=0, origin_y=0,
            spacings_x=None, spacings_y=None,
            naming_x="1,2,3...", naming_y="A,B,C...",
        )

    def test_create_grid_axis_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_grid_axis.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_grid_axis() is False

    def test_create_grid_label(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_grid_label.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_grid_label(grid_handle="GH1", label="A")
        assert result is True
        http.create_grid_label.assert_called_once_with(
            grid_handle="GH1", label="A", axis_index=0, direction="x",
        )

    def test_create_room(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_room.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_room(x=0, y=0, width=5000, height=4000, name="Hall")
        assert result is True
        http.create_room.assert_called_once_with(
            x=0, y=0, width=5000, height=4000, name="Hall",
        )

    def test_create_room_without_name(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_room.return_value = True
        uc = MultiCadUseCase(http)
        assert uc.create_room(x=0, y=0, width=1000, height=1000) is True

    def test_create_room_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_room.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_room(x=0, y=0, width=100, height=100) is False

    def test_get_room_properties(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.get_room_properties.return_value = {"success": True, "room": {"name": "Room1"}}
        uc = MultiCadUseCase(http)
        result = uc.get_room_properties(handle="RM1")
        assert result == {"success": True, "room": {"name": "Room1"}}
        http.get_room_properties.assert_called_once_with(handle="RM1")

    def test_get_room_properties_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.get_room_properties.return_value = None
        uc = MultiCadUseCase(http)
        assert uc.get_room_properties(handle="BAD") is None

    def test_create_custom_object(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_custom_object.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_custom_object(class_name="Wall", properties={"h": 3000})
        assert result is True
        http.create_custom_object.assert_called_once_with(
            class_name="Wall", properties={"h": 3000},
        )

    def test_create_custom_object_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_custom_object.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_custom_object(class_name="Wall") is False

    def test_create_parametric_object(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_parametric_object.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_parametric_object(object_type="Column", parameters={"w": 400})
        assert result is True
        http.create_parametric_object.assert_called_once_with(
            object_type="Column", parameters={"w": 400},
        )

    def test_create_parametric_object_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_parametric_object.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_parametric_object(object_type="Beam") is False

    def test_create_reactor(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_reactor.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_reactor(entity_handle="H1", event_type="modified")
        assert result is True
        http.create_reactor.assert_called_once_with(
            entity_handle="H1", event_type="modified",
        )

    def test_create_reactor_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_reactor.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_reactor(entity_handle="H1") is False

    def test_create_2d_break(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_2d_break.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_2d_break(view_handle="V1", x1=100, y1=200, x2=300, y2=400)
        assert result is True
        http.create_2d_break.assert_called_once_with(
            view_handle="V1", x1=100, y1=200, x2=300, y2=400,
        )

    def test_create_2d_break_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_2d_break.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_2d_break(view_handle="V1") is False

    def test_start_motion_preview(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.start_motion_preview.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.start_motion_preview(handle="H1")
        assert result is True
        http.start_motion_preview.assert_called_once_with(handle="H1")

    def test_start_motion_preview_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.start_motion_preview.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.start_motion_preview(handle="H1") is False

    def test_stop_motion_preview(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.stop_motion_preview.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.stop_motion_preview()
        assert result is True
        http.stop_motion_preview.assert_called_once_with()

    def test_stop_motion_preview_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.stop_motion_preview.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.stop_motion_preview() is False

    def test_create_body_contour(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_body_contour.return_value = True
        uc = MultiCadUseCase(http)
        result = uc.create_body_contour(solid_handle="H1")
        assert result is True
        http.create_body_contour.assert_called_once_with(solid_handle="H1")

    def test_create_body_contour_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.create_body_contour.return_value = False
        uc = MultiCadUseCase(http)
        assert uc.create_body_contour(solid_handle="H1") is False

    def test_check_3d_faces(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.check_3d_faces.return_value = {
            "success": True, "faces": [{"id": 1}], "count": 1,
        }
        uc = MultiCadUseCase(http)
        result = uc.check_3d_faces(handle="H1")
        assert result == {"success": True, "faces": [{"id": 1}], "count": 1}
        http.check_3d_faces.assert_called_once_with(handle="H1")

    def test_check_3d_faces_failure(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        http = MagicMock()
        http.is_available = True
        http.check_3d_faces.return_value = None
        uc = MultiCadUseCase(http)
        assert uc.check_3d_faces(handle="BAD") is None

    def test_requires_http(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        uc = MultiCadUseCase(None)
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.create_grid_axis()

    def test_requires_http_for_room(self, mock_repo: MagicMock) -> None:
        from src.application.extended_use_cases import MultiCadUseCase

        uc = MultiCadUseCase(None)
        with pytest.raises(NotImplementedError, match="Requires .NET engine"):
            uc.create_room()
