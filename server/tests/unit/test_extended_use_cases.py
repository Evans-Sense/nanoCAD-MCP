from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.application.extended_use_cases import (
    AssemblyUseCase,
    BlockManagementUseCase,
    ConstraintUseCase,
    DimensionUseCase,
    DocumentManagementUseCase,
    EdgeOpUseCase,
    HatchUseCase,
    LayerManagementUseCase,
    LinearDimUseCase,
    MeasurementUseCase,
    MLeaderUseCase,
    PrimitiveUseCase,
    SelectionUseCase,
    SheetMetalUseCase,
    StlExportUseCase,
    SweepLoftUseCase,
    SymbolUseCase,
    TableUseCase,
    TransformationUseCase,
    TrimExtendOffsetUseCase,
)
from src.domain.exceptions import NotSupportedError

# ── TrimExtendOffsetUseCase ─────────────────────────────────


class TestTrimExtendOffsetUseCase:
    def test_requires_http(self) -> None:
        uc = TrimExtendOffsetUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.trim_entity(handle="A1", cut_x=5, cut_y=0)

    def test_requires_http_not_available(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = False
        uc = TrimExtendOffsetUseCase(http=mock_http)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.extend_entity(handle="A1", end_x=10, end_y=0)

    def test_trim_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.trim_entity.return_value = {"handle": "A2", "success": True}
        uc = TrimExtendOffsetUseCase(http=mock_http)
        result = uc.trim_entity(handle="A1", cut_x=5, cut_y=0, keep_start=True)
        assert result["success"] is True
        mock_http.trim_entity.assert_called_once_with(
            handle="A1", cut_x=5, cut_y=0, keep_start=True
        )

    def test_extend_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.extend_entity.return_value = True
        uc = TrimExtendOffsetUseCase(http=mock_http)
        result = uc.extend_entity(handle="A1", end_x=20, end_y=0)
        assert result is True
        mock_http.extend_entity.assert_called_once_with(
            handle="A1", end_x=20, end_y=0
        )

    def test_offset_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.offset_entity.return_value = {"handle": "A3", "distance": 5.0}
        uc = TrimExtendOffsetUseCase(http=mock_http)
        result = uc.offset_entity(handle="A1", distance=5.0)
        assert result["distance"] == 5.0
        mock_http.offset_entity.assert_called_once_with(handle="A1", distance=5.0)


# ── LayerManagementUseCase ──────────────────────────────────


class TestLayerManagementUseCase:
    def test_requires_http(self) -> None:
        uc = LayerManagementUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.layer_isolate(name="Walls")

    def test_layer_isolate(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.layer_isolate.return_value = True
        uc = LayerManagementUseCase(http=mock_http)
        result = uc.layer_isolate(name="Walls")
        assert result is True
        mock_http.layer_isolate.assert_called_once_with(name="Walls")

    def test_layer_off(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.layer_off.return_value = True
        uc = LayerManagementUseCase(http=mock_http)
        result = uc.layer_off(name="Hidden")
        assert result is True
        mock_http.layer_off.assert_called_once_with(name="Hidden")

    def test_layer_freeze(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.layer_freeze.return_value = True
        uc = LayerManagementUseCase(http=mock_http)
        result = uc.layer_freeze(name="Construction")
        assert result is True
        mock_http.layer_freeze.assert_called_once_with(name="Construction")

    def test_layer_on_all(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.layer_on_all.return_value = True
        uc = LayerManagementUseCase(http=mock_http)
        result = uc.layer_on_all()
        assert result is True
        mock_http.layer_on_all.assert_called_once()

    def test_layer_thaw_all(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.layer_thaw_all.return_value = True
        uc = LayerManagementUseCase(http=mock_http)
        result = uc.layer_thaw_all()
        assert result is True
        mock_http.layer_thaw_all.assert_called_once()


# ── LinearDimUseCase ────────────────────────────────────────


class TestLinearDimUseCase:
    def test_requires_http(self) -> None:
        uc = LinearDimUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_linear_dimension()

    def test_create_linear_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_linear_dimension.return_value = {"handle": "DIM_001"}
        uc = LinearDimUseCase(http=mock_http)
        result = uc.create_linear_dimension(
            x1=0, y1=0, x2=100, y2=0, dim_x=0, dim_y=-20, direction="horizontal"
        )
        assert result["handle"] == "DIM_001"
        mock_http.create_linear_dimension.assert_called_once_with(
            x1=0, y1=0, x2=100, y2=0, dim_x=0, dim_y=-20, direction="horizontal"
        )

    def test_create_linear_dimension_defaults(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_linear_dimension.return_value = {"handle": "DIM_002"}
        uc = LinearDimUseCase(http=mock_http)
        result = uc.create_linear_dimension()
        assert result["handle"] == "DIM_002"
        mock_http.create_linear_dimension.assert_called_once_with(
            x1=0, y1=0, x2=0, y2=0, dim_x=0, dim_y=0, direction="horizontal"
        )


# ── SweepLoftUseCase ────────────────────────────────────────


class TestSweepLoftUseCase:
    def test_requires_http(self) -> None:
        uc = SweepLoftUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.sweep_solid(profile_handle="A", path_handle="B")

    def test_sweep_solid(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.sweep_solid.return_value = True
        uc = SweepLoftUseCase(http=mock_http)
        result = uc.sweep_solid(profile_handle="CIRCLE_1", path_handle="LINE_1")
        assert result is True
        mock_http.sweep_solid.assert_called_once_with(
            profile_handle="CIRCLE_1", path_handle="LINE_1"
        )

    def test_loft_solid(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.loft_solid.return_value = True
        uc = SweepLoftUseCase(http=mock_http)
        result = uc.loft_solid(section_handles=["SEC1", "SEC2", "SEC3"])
        assert result is True
        mock_http.loft_solid.assert_called_once_with(
            section_handles=["SEC1", "SEC2", "SEC3"]
        )


# ── EdgeOpUseCase ───────────────────────────────────────────


class TestEdgeOpUseCase:
    def test_requires_http(self) -> None:
        uc = EdgeOpUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.fillet_edge(handle="BOX_1", radius=5.0)

    def test_fillet_edge(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.fillet_edge.return_value = "1F5"
        uc = EdgeOpUseCase(http=mock_http)
        result = uc.fillet_edge(handle="BOX_1", radius=3.5)
        assert result == {"success": True, "handle": "1F5"}
        mock_http.fillet_edge.assert_called_once_with(handle="BOX_1", radius=3.5)

    def test_fillet_edge_defaults(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.fillet_edge.return_value = "2A0"
        uc = EdgeOpUseCase(http=mock_http)
        result = uc.fillet_edge(handle="BOX_1")
        assert result == {"success": True, "handle": "2A0"}
        mock_http.fillet_edge.assert_called_once_with(handle="BOX_1", radius=5.0)

    def test_fillet_edge_failure(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.fillet_edge.return_value = None
        uc = EdgeOpUseCase(http=mock_http)
        result = uc.fillet_edge(handle="BOX_1")
        assert result == {"success": False, "error": "Fillet failed"}

    def test_chamfer_edge(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.chamfer_edge.return_value = "3B0"
        uc = EdgeOpUseCase(http=mock_http)
        result = uc.chamfer_edge(handle="BOX_1", dist1=2.0, dist2=3.0)
        assert result == {"success": True, "handle": "3B0"}
        mock_http.chamfer_edge.assert_called_once_with(
            handle="BOX_1", dist1=2.0, dist2=3.0
        )

    def test_chamfer_edge_defaults(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.chamfer_edge.return_value = "4C0"
        uc = EdgeOpUseCase(http=mock_http)
        result = uc.chamfer_edge(handle="BOX_1")
        assert result == {"success": True, "handle": "4C0"}
        mock_http.chamfer_edge.assert_called_once_with(
            handle="BOX_1", dist1=5.0, dist2=5.0
        )

    def test_chamfer_edge_failure(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.chamfer_edge.return_value = None
        uc = EdgeOpUseCase(http=mock_http)
        result = uc.chamfer_edge(handle="BOX_1")
        assert result == {"success": False, "error": "Chamfer failed"}


# ── AssemblyUseCase ─────────────────────────────────────────


class TestAssemblyUseCase:
    def test_requires_http(self) -> None:
        uc = AssemblyUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.insert_part(block_name="Part1", x=0, y=0, z=0)

    def test_insert_part(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.insert_part.return_value = True
        uc = AssemblyUseCase(http=mock_http)
        result = uc.insert_part(block_name="Bolt_M10", x=10, y=20, z=0)
        assert result is True
        mock_http.insert_part.assert_called_once_with(
            block_name="Bolt_M10", x=10, y=20, z=0
        )

    def test_assembly_mate(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.assembly_mate.return_value = True
        uc = AssemblyUseCase(http=mock_http)
        result = uc.assembly_mate(handle1="FACE_1", handle2="FACE_2")
        assert result is True
        mock_http.assembly_mate.assert_called_once_with(
            handle1="FACE_1", handle2="FACE_2"
        )

    def test_assembly_angle(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.assembly_angle.return_value = True
        uc = AssemblyUseCase(http=mock_http)
        result = uc.assembly_angle(
            handle1="FACE_1", handle2="FACE_2", angle=45.0
        )
        assert result is True
        mock_http.assembly_angle.assert_called_once_with(
            handle1="FACE_1", handle2="FACE_2", angle=45.0
        )

    def test_assembly_tangent(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.assembly_tangent.return_value = True
        uc = AssemblyUseCase(http=mock_http)
        result = uc.assembly_tangent(handle1="CYL_1", handle2="PLANE_1")
        assert result is True
        mock_http.assembly_tangent.assert_called_once_with(
            handle1="CYL_1", handle2="PLANE_1"
        )

    def test_assembly_symmetry(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.assembly_symmetry.return_value = True
        uc = AssemblyUseCase(http=mock_http)
        result = uc.assembly_symmetry(
            handle1="PART_1", handle2="PART_2", plane_handle="PLANE_1"
        )
        assert result is True
        mock_http.assembly_symmetry.assert_called_once_with(
            handle1="PART_1", handle2="PART_2", plane_handle="PLANE_1"
        )


# ── DocumentManagementUseCase ───────────────────────────────


class TestDocumentManagementUseCase:
    def test_requires_http(self) -> None:
        uc = DocumentManagementUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.undo()

    def test_undo(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.undo.return_value = True
        uc = DocumentManagementUseCase(http=mock_http)
        result = uc.undo()
        assert result is True
        mock_http.undo.assert_called_once()

    def test_redo(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.redo.return_value = True
        uc = DocumentManagementUseCase(http=mock_http)
        result = uc.redo()
        assert result is True
        mock_http.redo.assert_called_once()

    def test_purge(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.purge.return_value = True
        uc = DocumentManagementUseCase(http=mock_http)
        result = uc.purge()
        assert result is True
        mock_http.purge.assert_called_once()

    def test_import_step(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.import_step.return_value = True
        uc = DocumentManagementUseCase(http=mock_http)
        result = uc.import_step(path="C:/models/bracket.step")
        assert result is True
        mock_http.import_step.assert_called_once_with(path="C:/models/bracket.step")

    def test_export_step(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.export_step.return_value = True
        uc = DocumentManagementUseCase(http=mock_http)
        result = uc.export_step(path="C:/output/assembly.step")
        assert result is True
        mock_http.export_step.assert_called_once_with(path="C:/output/assembly.step")


# ── BlockManagementUseCase ──────────────────────────────────


class TestBlockManagementUseCase:
    def test_requires_http(self) -> None:
        uc = BlockManagementUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_block(name="MyBlock", handles=["A1"])

    def test_create_block(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_block.return_value = "BLK_001"
        uc = BlockManagementUseCase(http=mock_http)
        result = uc.create_block(
            name="MyBlock", handles=["LINE_1", "CIRCLE_1"], base_x=0, base_y=0
        )
        assert result == "BLK_001"
        mock_http.create_block.assert_called_once_with(
            name="MyBlock", handles=["LINE_1", "CIRCLE_1"], base_x=0, base_y=0
        )

    def test_explode_block(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.explode_block.return_value = True
        uc = BlockManagementUseCase(http=mock_http)
        result = uc.explode_block(name="MyBlock")
        assert result is True
        mock_http.explode_block.assert_called_once_with(name="MyBlock")


# ── PrimitiveUseCase ────────────────────────────────────────


class TestPrimitiveUseCase:
    def test_requires_http(self) -> None:
        uc = PrimitiveUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_polygon(center_x=0, center_y=0, radius=10)

    def test_create_polygon(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_polygon.return_value = "POLY_001"
        uc = PrimitiveUseCase(http=mock_http)
        result = uc.create_polygon(
            center_x=0, center_y=0, radius=10, sides=6, inscribed=True, layer="0"
        )
        assert result == "POLY_001"
        mock_http.create_polygon.assert_called_once_with(
            center_x=0, center_y=0, radius=10, sides=6, inscribed=True, layer="0"
        )

    def test_create_donut(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_donut.return_value = "DONUT_001"
        uc = PrimitiveUseCase(http=mock_http)
        result = uc.create_donut(
            center_x=0, center_y=0, inner_radius=5, outer_radius=10, layer="0"
        )
        assert result == "DONUT_001"
        mock_http.create_donut.assert_called_once_with(
            center_x=0, center_y=0, inner_radius=5, outer_radius=10, layer="0"
        )

    def test_create_xline(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_xline.return_value = "XLINE_001"
        uc = PrimitiveUseCase(http=mock_http)
        result = uc.create_xline(
            p1_x=0, p1_y=0, p2_x=10, p2_y=10, layer="0"
        )
        assert result == "XLINE_001"
        mock_http.create_xline.assert_called_once_with(
            p1_x=0, p1_y=0, p2_x=10, p2_y=10, layer="0"
        )

    def test_create_ray(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_ray.return_value = "RAY_001"
        uc = PrimitiveUseCase(http=mock_http)
        result = uc.create_ray(
            p1_x=0, p1_y=0, p2_x=10, p2_y=10, layer="0"
        )
        assert result == "RAY_001"
        mock_http.create_ray.assert_called_once_with(
            p1_x=0, p1_y=0, p2_x=10, p2_y=10, layer="0"
        )


# ── TransformationUseCase ───────────────────────────────────


class TestTransformationUseCase:
    def test_requires_http(self) -> None:
        uc = TransformationUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.stretch_entity(handle="A1", dx=5, dy=5)

    def test_stretch_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.stretch_entity.return_value = True
        uc = TransformationUseCase(http=mock_http)
        result = uc.stretch_entity(handle="LINE_1", dx=10, dy=5)
        assert result is True
        mock_http.stretch_entity.assert_called_once_with(
            handle="LINE_1", dx=10, dy=5
        )

    def test_explode_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.explode_entity.return_value = {"parts": ["L1", "L2", "L3"]}
        uc = TransformationUseCase(http=mock_http)
        result = uc.explode_entity(handle="BLOCK_1")
        assert result["parts"] == ["L1", "L2", "L3"]
        mock_http.explode_entity.assert_called_once_with(handle="BLOCK_1")

    def test_divide_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.divide_entity.return_value = {"points": [(0, 0), (5, 0), (10, 0)]}
        uc = TransformationUseCase(http=mock_http)
        result = uc.divide_entity(handle="LINE_1", segments=2)
        assert len(result["points"]) == 3
        mock_http.divide_entity.assert_called_once_with(handle="LINE_1", segments=2)

    def test_measure_entity(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.measure_entity.return_value = {"distance": 10.0, "points": [(0, 0), (10, 0)]}
        uc = TransformationUseCase(http=mock_http)
        result = uc.measure_entity(handle="LINE_1", distance=10.0)
        assert result["distance"] == 10.0
        mock_http.measure_entity.assert_called_once_with(
            handle="LINE_1", distance=10.0
        )

    def test_array_3d(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.array_3d.return_value = {"count": 8}
        uc = TransformationUseCase(http=mock_http)
        result = uc.array_3d(
            handle="BOX_1", count_x=2, count_y=2, count_z=2,
            spacing_x=20, spacing_y=20, spacing_z=20,
        )
        assert result["count"] == 8
        mock_http.array_3d.assert_called_once_with(
            handle="BOX_1", count_x=2, count_y=2, count_z=2,
            spacing_x=20, spacing_y=20, spacing_z=20,
        )

    def test_align_3d(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.align_3d.return_value = True
        uc = TransformationUseCase(http=mock_http)
        result = uc.align_3d(
            handle="PART_1",
            src_p1_x=0, src_p1_y=0, src_p1_z=0,
            src_p2_x=1, src_p2_y=0, src_p2_z=0,
            src_p3_x=0, src_p3_y=1, src_p3_z=0,
            dst_p1_x=10, dst_p1_y=0, dst_p1_z=0,
            dst_p2_x=11, dst_p2_y=0, dst_p2_z=0,
            dst_p3_x=10, dst_p3_y=1, dst_p3_z=0,
        )
        assert result is True
        mock_http.align_3d.assert_called_once_with(
            handle="PART_1",
            src_p1=(0, 0, 0), src_p2=(1, 0, 0), src_p3=(0, 1, 0),
            dst_p1=(10, 0, 0), dst_p2=(11, 0, 0), dst_p3=(10, 1, 0),
        )

    def test_mirror_3d(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.mirror_3d.return_value = True
        uc = TransformationUseCase(http=mock_http)
        result = uc.mirror_3d(
            handle="PART_1",
            p1_x=0, p1_y=0, p1_z=0,
            p2_x=1, p2_y=0, p2_z=0,
            p3_x=0, p3_y=1, p3_z=0,
        )
        assert result is True
        mock_http.mirror_3d.assert_called_once_with(
            handle="PART_1",
            p1=(0, 0, 0), p2=(1, 0, 0), p3=(0, 1, 0),
        )


# ── SymbolUseCase ───────────────────────────────────────────


class TestSymbolUseCase:
    def test_requires_http(self) -> None:
        uc = SymbolUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_roughness(value="Ra 3.2")

    def test_create_roughness(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_roughness.return_value = {"handle": "SYM_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_roughness(value="Ra 3.2", angle=45)
        assert result["handle"] == "SYM_1"
        mock_http.create_roughness.assert_called_once_with(
            value="Ra 3.2", angle=45, allowance="", symbol_type=1
        )

    def test_create_old_roughness(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_old_roughness.return_value = {"handle": "OR_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_old_roughness(value="6.3", angle=0, method="")
        assert result["handle"] == "OR_1"
        mock_http.create_old_roughness.assert_called_once_with(
            value="6.3", angle=0, method="", companion_mirror=False, surf_pos=0,
        )

    def test_create_tolerance(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_tolerance.return_value = {"handle": "TOL_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_tolerance(type1="H7", value1="0.021", text="General")
        assert result["handle"] == "TOL_1"
        mock_http.create_tolerance.assert_called_once_with(
            type1="H7", value1="0.021", letters1=None,
            type2=None, value2=None, letters2=None, text="General",
        )

    def test_create_datum(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_datum.return_value = {"handle": "DAT_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_datum(letter="A")
        assert result["handle"] == "DAT_1"
        mock_http.create_datum.assert_called_once_with(letter="A")

    def test_create_weld(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_weld.return_value = {"handle": "WLD_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_weld(swap_sides=False, right_orientation=True)
        assert result["handle"] == "WLD_1"
        mock_http.create_weld.assert_called_once_with(
            swap_sides=False, right_orientation=True,
            length_above=None, length_below=None,
        )

    def test_create_leader(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_leader.return_value = {"handle": "LDR_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_leader(
            arrow_x=0, arrow_y=0, bend_x=5, bend_y=5,
            shelf_x=5, shelf_y=10, text="M10",
        )
        assert result["handle"] == "LDR_1"

    def test_create_note_comb(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_note_comb.return_value = {"handle": "NC_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_note_comb(angle=45, first_line="T1", second_line="T2")
        assert result["handle"] == "NC_1"

    def test_create_dim_number(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_dim_number.return_value = {"handle": "DN_1"}
        uc = SymbolUseCase(http=mock_http)
        result = uc.create_dim_number(
            x=0, y=0, arrow_x=5, arrow_y=5, text="1", index=1, autonum=True
        )
        assert result["handle"] == "DN_1"


# ── TableUseCase ────────────────────────────────────────────


class TestTableUseCase:
    def test_requires_http(self) -> None:
        uc = TableUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_table(rows=3, columns=3)

    def test_create_table(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_table.return_value = {"handle": "TBL_1"}
        uc = TableUseCase(http=mock_http)
        result = uc.create_table(rows=5, columns=4, row_height=30, column_width=100)
        assert result["handle"] == "TBL_1"
        mock_http.create_table.assert_called_once_with(
            rows=5, columns=4, row_height=30, column_width=100, cells=None
        )

    def test_edit_table_cell(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.edit_table_cell.return_value = {"success": True}
        uc = TableUseCase(http=mock_http)
        result = uc.edit_table_cell(handle="TBL_1", row_index=1, column_index=2, value="new val")
        assert result["success"] is True
        mock_http.edit_table_cell.assert_called_once_with(
            handle="TBL_1", row_index=1, column_index=2, value="new val"
        )

    def test_get_table_info(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_table_info.return_value = {"handle": "TBL_1", "row_count": 5}
        uc = TableUseCase(http=mock_http)
        result = uc.get_table_info(handle="TBL_1")
        assert result["row_count"] == 5
        mock_http.get_table_info.assert_called_once_with(handle="TBL_1")

    def test_delete_table(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.delete_table.return_value = {"success": True}
        uc = TableUseCase(http=mock_http)
        result = uc.delete_table(handle="TBL_1")
        assert result["success"] is True
        mock_http.delete_table.assert_called_once_with(handle="TBL_1")

    def test_table_requires_http_for_edit(self) -> None:
        uc = TableUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.edit_table_cell(handle="TBL_1", row_index=0, column_index=0, value="x")

    def test_table_requires_http_for_info(self) -> None:
        uc = TableUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.get_table_info(handle="TBL_1")

    def test_table_requires_http_for_delete(self) -> None:
        uc = TableUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.delete_table(handle="TBL_1")


# ── HatchUseCase ────────────────────────────────────────────


class TestHatchUseCase:
    def test_requires_http(self) -> None:
        uc = HatchUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_hatch(pattern="ANSI31")

    def test_create_hatch(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_hatch.return_value = {"handle": "HATCH_1"}
        uc = HatchUseCase(http=mock_http)
        result = uc.create_hatch(
            pattern="ANSI31", scale=2.0, boundary_handles=["PLINE_1"]
        )
        assert result["handle"] == "HATCH_1"
        mock_http.create_hatch.assert_called_once_with(
            pattern="ANSI31", scale=2.0,
            boundary_handles=["PLINE_1"], boundary_points=None,
        )

    def test_get_hatch_info(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_hatch_info.return_value = {"handle": "HATCH_1", "pattern": "ANSI31"}
        uc = HatchUseCase(http=mock_http)
        result = uc.get_hatch_info(handle="HATCH_1")
        assert result["pattern"] == "ANSI31"

    def test_edit_hatch(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.edit_hatch.return_value = {"handle": "HATCH_1"}
        uc = HatchUseCase(http=mock_http)
        result = uc.edit_hatch(handle="HATCH_1", pattern="SOLID", scale=1.0)
        assert result["handle"] == "HATCH_1"
        mock_http.edit_hatch.assert_called_once_with(
            handle="HATCH_1", pattern="SOLID", scale=1.0
        )

    def test_create_gradient_requires_http(self) -> None:
        uc = HatchUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_gradient()

    def test_create_gradient(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_gradient.return_value = {"handle": "GRD_001"}
        uc = HatchUseCase(http=mock_http)
        result = uc.create_gradient(color1="1,0,0", color2="0,0,1", scale=2.0, gradient_type="radial")
        assert result["handle"] == "GRD_001"
        mock_http.create_gradient.assert_called_once_with(
            color1="1,0,0", color2="0,0,1", scale=2.0,
            gradient_type="radial", boundary_handles=None,
            point_xs=None, point_ys=None,
        )

    def test_create_gradient_defaults(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_gradient.return_value = {"handle": "GRD_002"}
        uc = HatchUseCase(http=mock_http)
        result = uc.create_gradient()
        assert result["handle"] == "GRD_002"
        mock_http.create_gradient.assert_called_once_with(
            color1="1,1,1", color2="0,0,0", scale=1.0,
            gradient_type="linear", boundary_handles=None,
            point_xs=None, point_ys=None,
        )


# ── DimensionUseCase ────────────────────────────────────────


class TestDimensionUseCase:
    def test_requires_http(self) -> None:
        uc = DimensionUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_aligned_dimension()

    def test_create_aligned_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_aligned_dimension.return_value = {"handle": "DIM_A1"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_aligned_dimension(
            x1=0, y1=0, x2=50, y2=30, dim_x=0, dim_y=-15
        )
        assert result["handle"] == "DIM_A1"

    def test_create_rotated_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_rotated_dimension.return_value = {"handle": "DIM_R1"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_rotated_dimension(
            x1=0, y1=0, x2=50, y2=0, dim_x=0, dim_y=-15, rotation=45
        )
        assert result["handle"] == "DIM_R1"

    def test_create_radial_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_radial_dimension.return_value = {"handle": "DIM_RD1"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_radial_dimension(
            center_x=0, center_y=0, arc_x=10, arc_y=0
        )
        assert result["handle"] == "DIM_RD1"

    def test_create_diametric_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_diametric_dimension.return_value = {"handle": "DIM_DD1"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_diametric_dimension(
            center_x=0, center_y=0, arc_x=10, arc_y=0
        )
        assert result["handle"] == "DIM_DD1"

    def test_create_angular_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_angular_dimension.return_value = {"handle": "DIM_AN1"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_angular_dimension(
            center_x=0, center_y=0, p1_x=10, p1_y=0, p2_x=0, p2_y=10
        )
        assert result["handle"] == "DIM_AN1"

    def test_create_ordinate_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_ordinate_dimension.return_value = {"handle": "DIM_OR1"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_ordinate_dimension(
            use_x_axis=True, defining_x=0, defining_y=0, leader_x=10, leader_y=10
        )
        assert result["handle"] == "DIM_OR1"

    def test_create_arc_length_dimension_requires_http(self) -> None:
        uc = DimensionUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_arc_length_dimension()

    def test_create_arc_length_dimension(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_arc_length_dimension.return_value = {"handle": "DIM_AL_001"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_arc_length_dimension(
            center_x=0, center_y=0, radius=50, start_angle=0, end_angle=90, dim_x=0, dim_y=0
        )
        assert result["handle"] == "DIM_AL_001"
        mock_http.create_arc_length_dimension.assert_called_once_with(
            center_x=0, center_y=0, radius=50,
            start_angle=0, end_angle=90, dim_x=0, dim_y=0,
        )

    def test_create_arc_length_dimension_defaults(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_arc_length_dimension.return_value = {"handle": "DIM_AL_002"}
        uc = DimensionUseCase(http=mock_http)
        result = uc.create_arc_length_dimension()
        assert result["handle"] == "DIM_AL_002"
        mock_http.create_arc_length_dimension.assert_called_once_with(
            center_x=0, center_y=0, radius=50,
            start_angle=0, end_angle=90, dim_x=0, dim_y=0,
        )


# ── MeasurementUseCase ──────────────────────────────────────


class TestMeasurementUseCase:
    def test_requires_http(self) -> None:
        uc = MeasurementUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.get_distance(x1=0, y1=0, z1=0, x2=10, y2=0, z2=0)

    def test_get_distance(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_distance.return_value = {"distance": 10.0}
        uc = MeasurementUseCase(http=mock_http)
        result = uc.get_distance(x1=0, y1=0, z1=0, x2=10, y2=0, z2=0)
        assert result["distance"] == 10.0

    def test_get_angle(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_angle.return_value = {"angle_degrees": 90.0}
        uc = MeasurementUseCase(http=mock_http)
        result = uc.get_angle(x1=0, y1=0, z1=0, x2=0, y2=0, z2=0, x3=10, y3=0, z3=0)
        assert result["angle_degrees"] == 90.0

    def test_get_area(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_area.return_value = {"area": 100.0}
        uc = MeasurementUseCase(http=mock_http)
        result = uc.get_area(handle="PLINE_1")
        assert result["area"] == 100.0

    def test_get_entity_info(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_entity_info.return_value = {"type": "LINE", "length": 10.0}
        uc = MeasurementUseCase(http=mock_http)
        result = uc.get_entity_info(handle="LINE_1")
        assert result["type"] == "LINE"

    def test_get_all_entities(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_all_entities.return_value = {"count": 42}
        uc = MeasurementUseCase(http=mock_http)
        result = uc.get_all_entities()
        assert result["count"] == 42


# ── SelectionUseCase ────────────────────────────────────────


class TestSelectionUseCase:
    def test_requires_http(self) -> None:
        uc = SelectionUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.select_entities(entity_type="Line")

    def test_select_entities(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.select_entities.return_value = {
            "success": True,
            "entities": [{"handle": "100", "type": "Line", "layer": "0"}],
        }
        uc = SelectionUseCase(http=mock_http)
        result = uc.select_entities(entity_type="Line", layer="0")
        assert result["success"] is True
        assert len(result["entities"]) == 1
        mock_http.select_entities.assert_called_once_with(
            entity_type="Line", layer="0", color=None, max_count=1000
        )

    def test_select_entities_all(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.select_entities.return_value = {"success": True, "entities": []}
        uc = SelectionUseCase(http=mock_http)
        result = uc.select_entities()
        assert result["success"] is True

    def test_select_by_handles(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.select_by_handles.return_value = {
            "success": True,
            "entities": [{"handle": "100", "type": "Line", "layer": "0"}],
        }
        uc = SelectionUseCase(http=mock_http)
        result = uc.select_by_handles(handles=["100", "101"])
        assert result["success"] is True
        mock_http.select_by_handles.assert_called_once_with(handles=["100", "101"])

    def test_get_entity_detail(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.get_entity_detail.return_value = {
            "success": True,
            "handle": "100",
            "type": "Line",
            "length": 100.0,
        }
        uc = SelectionUseCase(http=mock_http)
        result = uc.get_entity_detail(handle="100")
        assert result["success"] is True
        assert result["length"] == 100.0
        mock_http.get_entity_detail.assert_called_once_with(handle="100")


# ── StlExportUseCase ────────────────────────────────────────


class TestStlExportUseCase:
    def test_requires_http(self) -> None:
        uc = StlExportUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.export_stl(path="/tmp/model.stl")

    def test_export_stl(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.export_stl.return_value = True
        uc = StlExportUseCase(http=mock_http)
        result = uc.export_stl(path="/tmp/model.stl", binary=True)
        assert result is True
        mock_http.export_stl.assert_called_once_with(path="/tmp/model.stl", binary=True)

    def test_export_stl_ascii(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.export_stl.return_value = True
        uc = StlExportUseCase(http=mock_http)
        result = uc.export_stl(path="/tmp/model.stl", binary=False)
        assert result is True
        mock_http.export_stl.assert_called_once_with(path="/tmp/model.stl", binary=False)


# ── ConstraintUseCase ───────────────────────────────────────


class TestConstraintUseCase:
    def test_requires_http(self) -> None:
        uc = ConstraintUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.constraint_parallel(handle1="A", handle2="B")

    def test_constraint_parallel(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_parallel.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_parallel(handle1="L1", handle2="L2")
        assert result is True
        mock_http.constraint_parallel.assert_called_once_with(handle1="L1", handle2="L2")

    def test_constraint_coincident(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_coincident.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_coincident(handle1="P1", handle2="P2")
        assert result is True
        mock_http.constraint_coincident.assert_called_once_with(handle1="P1", handle2="P2")

    def test_constraint_fix(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_fix.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_fix(handle="L1")
        assert result is True
        mock_http.constraint_fix.assert_called_once_with(handle="L1")

    def test_constraint_horizontal(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_horizontal.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_horizontal(handle="L1")
        assert result is True
        mock_http.constraint_horizontal.assert_called_once_with(handle="L1")

    def test_constraint_vertical(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_vertical.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_vertical(handle="L1")
        assert result is True
        mock_http.constraint_vertical.assert_called_once_with(handle="L1")

    def test_constraint_tangent(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_tangent.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_tangent(handle_line="L1", handle_curve="C1")
        assert result is True
        mock_http.constraint_tangent.assert_called_once_with(
            handle_line="L1", handle_curve="C1"
        )

    def test_constraint_perpendicular(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_perpendicular.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_perpendicular(handle1="L1", handle2="L2")
        assert result is True
        mock_http.constraint_perpendicular.assert_called_once_with(
            handle1="L1", handle2="L2"
        )

    def test_constraint_collinear(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_collinear.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_collinear(handle1="L1", handle2="L2")
        assert result is True
        mock_http.constraint_collinear.assert_called_once_with(
            handle1="L1", handle2="L2"
        )

    def test_constraint_concentric(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_concentric.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_concentric(handle1="C1", handle2="C2")
        assert result is True
        mock_http.constraint_concentric.assert_called_once_with(
            handle1="C1", handle2="C2"
        )

    def test_constraint_equal(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_equal.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_equal(handle1="L1", handle2="L2")
        assert result is True
        mock_http.constraint_equal.assert_called_once_with(
            handle1="L1", handle2="L2"
        )

    def test_constraint_symmetric(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_symmetric.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_symmetric(handle1="L1", handle2="L2", plane_handle="AX")
        assert result is True
        mock_http.constraint_symmetric.assert_called_once_with(
            handle1="L1", handle2="L2", plane_handle="AX"
        )

    def test_constraint_distance(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.constraint_distance.return_value = True
        uc = ConstraintUseCase(http=mock_http)
        result = uc.constraint_distance(handle1="P1", handle2="P2", distance=50.0)
        assert result is True
        mock_http.constraint_distance.assert_called_once_with(
            handle1="P1", handle2="P2", distance=50.0
        )


# ── MLeaderUseCase ──────────────────────────────────────────


class TestMLeaderUseCase:
    def test_requires_http(self) -> None:
        uc = MLeaderUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_mleader(arrow_x=0, arrow_y=0, leader_x=5, leader_y=5, text="Note")

    def test_create_mleader(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_mleader.return_value = {"success": True}
        uc = MLeaderUseCase(http=mock_http)
        result = uc.create_mleader(
            arrow_x=0, arrow_y=0, leader_x=10, leader_y=10,
            text="M10x1.5", text_height=3.5, layer="0",
        )
        assert result["success"] is True
        mock_http.create_mleader.assert_called_once_with(
            arrow_x=0, arrow_y=0, leader_x=10, leader_y=10,
            text="M10x1.5", text_height=3.5, layer="0",
        )

    def test_create_mleader_defaults(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_mleader.return_value = {"success": True}
        uc = MLeaderUseCase(http=mock_http)
        result = uc.create_mleader(
            arrow_x=0, arrow_y=0, leader_x=5, leader_y=5, text="Note",
        )
        assert result["success"] is True
        mock_http.create_mleader.assert_called_once_with(
            arrow_x=0, arrow_y=0, leader_x=5, leader_y=5,
            text="Note", text_height=3.5, layer=None,
        )


# ── SheetMetalUseCase ──────────────────────────────────────────


class TestSheetMetalUseCase:
    def test_requires_http(self) -> None:
        uc = SheetMetalUseCase(http=None)
        with pytest.raises(NotSupportedError, match="Requires .NET engine"):
            uc.create_base_flange(width=100, length=100, thickness=2)

    def test_create_base_flange(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_base_flange.return_value = True
        uc = SheetMetalUseCase(http=mock_http)
        result = uc.create_base_flange(x=0, y=0, width=100, length=200, thickness=3)
        assert result is True
        mock_http.create_base_flange.assert_called_once_with(
            x=0, y=0, width=100, length=200, thickness=3,
        )

    def test_create_edge_flange(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_edge_flange.return_value = True
        uc = SheetMetalUseCase(http=mock_http)
        result = uc.create_edge_flange(base_handle="A1", bend_radius=10.0)
        assert result is True
        mock_http.create_edge_flange.assert_called_once_with(
            base_handle="A1", bend_radius=10.0,
        )

    def test_create_bend(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_bend.return_value = True
        uc = SheetMetalUseCase(http=mock_http)
        result = uc.create_bend(handle="B1", bend_radius=5.0)
        assert result is True
        mock_http.create_bend.assert_called_once_with(
            handle="B1", bend_radius=5.0,
        )

    def test_unfold_sheet_metal(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.unfold_sheet_metal.return_value = True
        uc = SheetMetalUseCase(http=mock_http)
        result = uc.unfold_sheet_metal(handle="S1", x=0, y=0)
        assert result is True
        mock_http.unfold_sheet_metal.assert_called_once_with(
            handle="S1", x=0, y=0,
        )

    def test_create_base_plate(self) -> None:
        mock_http = MagicMock()
        mock_http.is_available = True
        mock_http.create_base_plate.return_value = True
        uc = SheetMetalUseCase(http=mock_http)
        result = uc.create_base_plate(x=10, y=20, width=100, length=200, thickness=2)
        assert result is True
        mock_http.create_base_plate.assert_called_once_with(
            x=10, y=20, width=100, length=200, thickness=2,
        )
