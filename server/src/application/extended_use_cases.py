from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.domain.exceptions import NotSupportedError

if TYPE_CHECKING:
    from src.infrastructure.http_bridge import HttpCadBridge

log = logging.getLogger(__name__)


class SymbolUseCase:
    """Use case: engineering symbols via MultiCAD (roughness, welds, tolerances, leaders)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for MultiCAD symbols")

    def create_roughness(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_roughness(  # type: ignore[union-attr]
            value=kwargs.get("value", "Ra 6.3"),
            angle=kwargs.get("angle", 0),
            allowance=kwargs.get("allowance", ""),
            symbol_type=kwargs.get("type", 1),
        )

    def create_old_roughness(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_old_roughness(  # type: ignore[union-attr]
            value=kwargs.get("value", "6.3"),
            angle=kwargs.get("angle", 0),
            method=kwargs.get("method", ""),
            companion_mirror=kwargs.get("companion_mirror", False),
            surf_pos=kwargs.get("surf_pos", 0),
        )

    def create_tolerance(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_tolerance(  # type: ignore[union-attr]
            type1=kwargs.get("type1"),
            value1=kwargs.get("value1"),
            letters1=kwargs.get("letters1"),
            type2=kwargs.get("type2"),
            value2=kwargs.get("value2"),
            letters2=kwargs.get("letters2"),
            text=kwargs.get("text"),
        )

    def create_datum(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_datum(  # type: ignore[union-attr]
            letter=kwargs.get("letter", "A"),
        )

    def create_weld(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_weld(  # type: ignore[union-attr]
            swap_sides=kwargs.get("swap_sides", False),
            right_orientation=kwargs.get("right_orientation", False),
            length_above=kwargs.get("length_above"),
            length_below=kwargs.get("length_below"),
        )

    def create_leader(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_leader(  # type: ignore[union-attr]
            arrow_x=kwargs.get("arrow_x", 0),
            arrow_y=kwargs.get("arrow_y", 0),
            bend_x=kwargs.get("bend_x", 0),
            bend_y=kwargs.get("bend_y", 0),
            shelf_x=kwargs.get("shelf_x", 0),
            shelf_y=kwargs.get("shelf_y", 0),
            text=kwargs.get("text", ""),
            text_below=kwargs.get("text_below"),
        )

    def create_note_comb(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_note_comb(  # type: ignore[union-attr]
            angle=kwargs.get("angle", 45),
            text_size=kwargs.get("text_size", 12),
            first_line=kwargs.get("first_line", ""),
            second_line=kwargs.get("second_line", ""),
        )

    def create_dim_number(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_dim_number(  # type: ignore[union-attr]
            x=kwargs.get("x", 0),
            y=kwargs.get("y", 0),
            arrow_x=kwargs.get("arrow_x", 0),
            arrow_y=kwargs.get("arrow_y", 0),
            text=kwargs.get("text", ""),
            index=kwargs.get("index", 1),
            autonum=kwargs.get("autonum", True),
        )


class TableUseCase:
    """Use case: tables via MultiCAD."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for MultiCAD tables")

    def create_table(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_table(  # type: ignore[union-attr]
            rows=kwargs.get("rows", 3),
            columns=kwargs.get("columns", 3),
            row_height=kwargs.get("row_height", 30),
            column_width=kwargs.get("column_width", 100),
            cells=kwargs.get("cells"),
        )

    def edit_table_cell(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.edit_table_cell(  # type: ignore[union-attr]
            handle=kwargs["handle"],
            row_index=kwargs["row_index"],
            column_index=kwargs["column_index"],
            value=kwargs["value"],
        )

    def get_table_info(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_table_info(handle=kwargs["handle"])  # type: ignore[union-attr]

    def delete_table(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.delete_table(handle=kwargs["handle"])  # type: ignore[union-attr]


class HatchUseCase:
    """Use case: hatch operations."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for hatch operations")

    def create_hatch(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_hatch(  # type: ignore[union-attr]
            pattern=kwargs.get("pattern", "ANSI31"),
            scale=kwargs.get("scale", 1.0),
            boundary_handles=kwargs.get("boundary_handles"),
            boundary_points=kwargs.get("boundary_points"),
        )

    def get_hatch_info(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_hatch_info(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def edit_hatch(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.edit_hatch(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            pattern=kwargs.get("pattern"),
            scale=kwargs.get("scale"),
        )

    def create_gradient(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_gradient(  # type: ignore[union-attr]
            color1=kwargs.get("color1", "1,1,1"),
            color2=kwargs.get("color2", "0,0,0"),
            scale=kwargs.get("scale", 1.0),
            gradient_type=kwargs.get("gradient_type", "linear"),
            boundary_handles=kwargs.get("boundary_handles"),
            point_xs=kwargs.get("point_xs"),
            point_ys=kwargs.get("point_ys"),
        )


class DimensionUseCase:
    """Use case: dimension operations."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for dimension operations")

    def create_aligned_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_aligned_dimension(  # type: ignore[union-attr]
            x1=kwargs.get("x1", 0),
            y1=kwargs.get("y1", 0),
            x2=kwargs.get("x2", 0),
            y2=kwargs.get("y2", 0),
            dim_x=kwargs.get("dim_x", 0),
            dim_y=kwargs.get("dim_y", 0),
        )

    def create_rotated_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_rotated_dimension(  # type: ignore[union-attr]
            x1=kwargs.get("x1", 0),
            y1=kwargs.get("y1", 0),
            x2=kwargs.get("x2", 0),
            y2=kwargs.get("y2", 0),
            dim_x=kwargs.get("dim_x", 0),
            dim_y=kwargs.get("dim_y", 0),
            rotation=kwargs.get("rotation", 0),
        )

    def create_radial_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_radial_dimension(  # type: ignore[union-attr]
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            arc_x=kwargs.get("arc_x", 0),
            arc_y=kwargs.get("arc_y", 0),
        )

    def create_diametric_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_diametric_dimension(  # type: ignore[union-attr]
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            arc_x=kwargs.get("arc_x", 0),
            arc_y=kwargs.get("arc_y", 0),
        )

    def create_angular_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_angular_dimension(  # type: ignore[union-attr]
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            p1_x=kwargs.get("p1_x", 0),
            p1_y=kwargs.get("p1_y", 0),
            p2_x=kwargs.get("p2_x", 0),
            p2_y=kwargs.get("p2_y", 0),
        )

    def create_ordinate_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_ordinate_dimension(  # type: ignore[union-attr]
            use_x_axis=kwargs.get("use_x_axis", True),
            defining_x=kwargs.get("defining_x", 0),
            defining_y=kwargs.get("defining_y", 0),
            leader_x=kwargs.get("leader_x", 0),
            leader_y=kwargs.get("leader_y", 0),
        )

    def create_arc_length_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_arc_length_dimension(  # type: ignore[union-attr]
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            radius=kwargs.get("radius", 50),
            start_angle=kwargs.get("start_angle", 0),
            end_angle=kwargs.get("end_angle", 90),
            dim_x=kwargs.get("dim_x", 0),
            dim_y=kwargs.get("dim_y", 0),
        )


class MeasurementUseCase:
    """Use case: measurement operations."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for measurements")

    def get_distance(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_distance(  # type: ignore[union-attr]
            x1=kwargs.get("x1", 0),
            y1=kwargs.get("y1", 0),
            z1=kwargs.get("z1", 0),
            x2=kwargs.get("x2", 0),
            y2=kwargs.get("y2", 0),
            z2=kwargs.get("z2", 0),
        )

    def get_angle(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_angle(  # type: ignore[union-attr]
            x1=kwargs.get("x1", 0),
            y1=kwargs.get("y1", 0),
            z1=kwargs.get("z1", 0),
            x2=kwargs.get("x2", 0),
            y2=kwargs.get("y2", 0),
            z2=kwargs.get("z2", 0),
            x3=kwargs.get("x3", 0),
            y3=kwargs.get("y3", 0),
            z3=kwargs.get("z3", 0),
        )

    def get_area(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_area(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def get_entity_info(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_entity_info(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def get_all_entities(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_all_entities()  # type: ignore[union-attr]


class TransformationUseCase:
    """Use case: transformations (stretch, explode, divide, measure, array, align, mirror 3D)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for transformations")

    def stretch_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.stretch_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            dx=kwargs.get("dx", 0),
            dy=kwargs.get("dy", 0),
        )

    def explode_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.explode_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def divide_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.divide_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            segments=kwargs.get("segments", 3),
        )

    def measure_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.measure_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            distance=kwargs.get("distance", 10),
        )

    def array_3d(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.array_3d(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            count_x=kwargs.get("count_x", 2),
            count_y=kwargs.get("count_y", 1),
            count_z=kwargs.get("count_z", 1),
            spacing_x=kwargs.get("spacing_x", 10),
            spacing_y=kwargs.get("spacing_y", 10),
            spacing_z=kwargs.get("spacing_z", 10),
        )

    def align_3d(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.align_3d(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            src_p1=(
                kwargs.get("src_p1_x", 0),
                kwargs.get("src_p1_y", 0),
                kwargs.get("src_p1_z", 0),
            ),
            src_p2=(
                kwargs.get("src_p2_x", 0),
                kwargs.get("src_p2_y", 0),
                kwargs.get("src_p2_z", 0),
            ),
            src_p3=(
                kwargs.get("src_p3_x", 0),
                kwargs.get("src_p3_y", 0),
                kwargs.get("src_p3_z", 0),
            ),
            dst_p1=(
                kwargs.get("dst_p1_x", 0),
                kwargs.get("dst_p1_y", 0),
                kwargs.get("dst_p1_z", 0),
            ),
            dst_p2=(
                kwargs.get("dst_p2_x", 0),
                kwargs.get("dst_p2_y", 0),
                kwargs.get("dst_p2_z", 0),
            ),
            dst_p3=(
                kwargs.get("dst_p3_x", 0),
                kwargs.get("dst_p3_y", 0),
                kwargs.get("dst_p3_z", 0),
            ),
        )

    def mirror_3d(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.mirror_3d(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            p1=(kwargs.get("p1_x", 0), kwargs.get("p1_y", 0), kwargs.get("p1_z", 0)),
            p2=(kwargs.get("p2_x", 0), kwargs.get("p2_y", 0), kwargs.get("p2_z", 0)),
            p3=(kwargs.get("p3_x", 0), kwargs.get("p3_y", 0), kwargs.get("p3_z", 0)),
        )


class PrimitiveUseCase:
    """Use case: additional 2D primitives (polygon, donut, xline, ray)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for primitive creation")

    def create_polygon(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_polygon(  # type: ignore[union-attr]
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            radius=kwargs.get("radius", 10),
            sides=kwargs.get("sides", 6),
            inscribed=kwargs.get("inscribed", True),
            layer=kwargs.get("layer"),
        )

    def create_donut(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_donut(  # type: ignore[union-attr]
            center_x=kwargs.get("center_x", 0),
            center_y=kwargs.get("center_y", 0),
            inner_radius=kwargs.get("inner_radius", 5),
            outer_radius=kwargs.get("outer_radius", 10),
            layer=kwargs.get("layer"),
        )

    def create_xline(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_xline(  # type: ignore[union-attr]
            p1_x=kwargs.get("p1_x", 0),
            p1_y=kwargs.get("p1_y", 0),
            p2_x=kwargs.get("p2_x", 10),
            p2_y=kwargs.get("p2_y", 10),
            layer=kwargs.get("layer"),
        )

    def create_ray(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_ray(  # type: ignore[union-attr]
            p1_x=kwargs.get("p1_x", 0),
            p1_y=kwargs.get("p1_y", 0),
            p2_x=kwargs.get("p2_x", 10),
            p2_y=kwargs.get("p2_y", 10),
            layer=kwargs.get("layer"),
        )


class TrimExtendOffsetUseCase:
    """Use case: trim, extend, and offset curve entities."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for trim/extend/offset")

    def trim_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.trim_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            cut_x=kwargs.get("cut_x", 0),
            cut_y=kwargs.get("cut_y", 0),
            keep_start=kwargs.get("keep_start", True),
        )

    def extend_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.extend_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            end_x=kwargs.get("end_x", 0),
            end_y=kwargs.get("end_y", 0),
        )

    def offset_entity(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.offset_entity(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            distance=kwargs.get("distance", 10),
        )


class LayerManagementUseCase:
    """Use case: layer isolation, on/off, freeze/thaw."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for layer management")

    def layer_isolate(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.layer_isolate(name=kwargs.get("name", ""))  # type: ignore[union-attr]

    def layer_off(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.layer_off(name=kwargs.get("name", ""))  # type: ignore[union-attr]

    def layer_freeze(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.layer_freeze(name=kwargs.get("name", ""))  # type: ignore[union-attr]

    def layer_on_all(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.layer_on_all()  # type: ignore[union-attr]

    def layer_thaw_all(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.layer_thaw_all()  # type: ignore[union-attr]


class LinearDimUseCase:
    """Use case: DIMLINEAR (horizontal/vertical dimensions)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for DIMLINEAR")

    def create_linear_dimension(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_linear_dimension(  # type: ignore[union-attr]
            x1=kwargs.get("x1", 0),
            y1=kwargs.get("y1", 0),
            x2=kwargs.get("x2", 0),
            y2=kwargs.get("y2", 0),
            dim_x=kwargs.get("dim_x", 0),
            dim_y=kwargs.get("dim_y", 0),
            direction=kwargs.get("direction", "horizontal"),
        )


class SweepLoftUseCase:
    """Use case: SWEEP and LOFT 3D operations."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for SWEEP/LOFT")

    def sweep_solid(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.sweep_solid(  # type: ignore[union-attr]
            profile_handle=kwargs.get("profile_handle", ""),
            path_handle=kwargs.get("path_handle", ""),
        )

    def loft_solid(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.loft_solid(  # type: ignore[union-attr]
            section_handles=kwargs.get("section_handles", []),
        )


class EdgeOpUseCase:
    """Use case: FILLETEDGE and CHAMFEREDGE 3D operations."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for FILLETEDGE/CHAMFEREDGE")

    def fillet_edge(self, **kwargs: Any) -> dict[str, Any]:
        self._require_http()
        handle = self._http.fillet_edge(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            radius=kwargs.get("radius", 5.0),
        )
        if handle:
            return {"success": True, "handle": handle}
        return {"success": False, "error": "Fillet failed"}

    def chamfer_edge(self, **kwargs: Any) -> dict[str, Any]:
        self._require_http()
        handle = self._http.chamfer_edge(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            dist1=kwargs.get("dist1", 5.0),
            dist2=kwargs.get("dist2", 5.0),
        )
        if handle:
            return {"success": True, "handle": handle}
        return {"success": False, "error": "Chamfer failed"}


class AssemblyUseCase:
    """Use case: 3D assembly operations (insert, mate, angle, tangent, symmetry)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for assembly operations")

    def insert_part(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.insert_part(  # type: ignore[union-attr]
            block_name=kwargs.get("block_name", ""),
            x=kwargs.get("x", 0),
            y=kwargs.get("y", 0),
            z=kwargs.get("z", 0),
        )

    def assembly_mate(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.assembly_mate(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def assembly_angle(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.assembly_angle(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
            angle=kwargs.get("angle", 0),
        )

    def assembly_tangent(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.assembly_tangent(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def assembly_symmetry(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.assembly_symmetry(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
            plane_handle=kwargs.get("plane_handle", ""),
        )


class DocumentManagementUseCase:
    """Use case: document management (undo, redo, purge, import/export)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for document management")

    def undo(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.undo()  # type: ignore[union-attr]

    def redo(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.redo()  # type: ignore[union-attr]

    def purge(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.purge()  # type: ignore[union-attr]

    def import_step(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.import_step(  # type: ignore[union-attr]
            path=kwargs.get("path", ""),
        )

    def export_step(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.export_step(  # type: ignore[union-attr]
            path=kwargs.get("path", ""),
        )


class BlockManagementUseCase:
    """Use case: block create and explode."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for block management")

    def create_block(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_block(  # type: ignore[union-attr]
            name=kwargs.get("name", ""),
            handles=kwargs.get("handles", []),
            base_x=kwargs.get("base_x", 0),
            base_y=kwargs.get("base_y", 0),
        )

    def explode_block(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.explode_block(  # type: ignore[union-attr]
            name=kwargs.get("name", ""),
        )


class SelectionUseCase:
    """Use case: select entities by criteria (type, layer, color) and get entity details."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for selection")

    def select_entities(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.select_entities(  # type: ignore[union-attr]
            entity_type=kwargs.get("entity_type"),
            layer=kwargs.get("layer"),
            color=kwargs.get("color"),
            max_count=kwargs.get("max_count", 1000),
        )

    def select_by_handles(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.select_by_handles(  # type: ignore[union-attr]
            handles=kwargs.get("handles", []),
        )

    def get_entity_detail(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.get_entity_detail(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )


class StlExportUseCase:
    """Use case: export to STL for 3D printing."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for STL export")

    def export_stl(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.export_stl(  # type: ignore[union-attr]
            path=kwargs.get("path", ""),
            binary=kwargs.get("binary", True),
        )


class ConstraintUseCase:
    """Use case: 2D geometric constraints."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for 2D constraints")

    def constraint_parallel(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_parallel(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def constraint_coincident(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_coincident(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def constraint_fix(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_fix(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def constraint_horizontal(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_horizontal(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def constraint_vertical(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_vertical(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
        )

    def constraint_tangent(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_tangent(  # type: ignore[union-attr]
            handle_line=kwargs.get("handle_line", ""),
            handle_curve=kwargs.get("handle_curve", ""),
        )

    def constraint_perpendicular(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_perpendicular(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def constraint_collinear(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_collinear(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def constraint_concentric(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_concentric(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def constraint_equal(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_equal(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
        )

    def constraint_symmetric(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_symmetric(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
            plane_handle=kwargs.get("plane_handle", ""),
        )

    def constraint_distance(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.constraint_distance(  # type: ignore[union-attr]
            handle1=kwargs.get("handle1", ""),
            handle2=kwargs.get("handle2", ""),
            distance=kwargs.get("distance", 0),
        )


class MLeaderUseCase:
    """Use case: multileader creation."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for MLEADER")

    def create_mleader(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_mleader(  # type: ignore[union-attr]
            arrow_x=kwargs.get("arrow_x", 0),
            arrow_y=kwargs.get("arrow_y", 0),
            leader_x=kwargs.get("leader_x", 0),
            leader_y=kwargs.get("leader_y", 0),
            text=kwargs.get("text", ""),
            text_height=kwargs.get("text_height", 3.5),
            layer=kwargs.get("layer"),
        )


class SheetMetalUseCase:
    """Use case: sheet metal operations."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for sheet metal")

    def create_base_flange(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_base_flange(  # type: ignore[union-attr]
            x=kwargs.get("x", 0),
            y=kwargs.get("y", 0),
            width=kwargs.get("width", 100),
            length=kwargs.get("length", 100),
            thickness=kwargs.get("thickness", 2),
        )

    def create_edge_flange(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_edge_flange(  # type: ignore[union-attr]
            base_handle=kwargs.get("base_handle", ""),
            bend_radius=kwargs.get("bend_radius", 5.0),
        )

    def create_bend(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_bend(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            bend_radius=kwargs.get("bend_radius", 5.0),
        )

    def unfold_sheet_metal(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.unfold_sheet_metal(  # type: ignore[union-attr]
            handle=kwargs.get("handle", ""),
            x=kwargs.get("x", 0),
            y=kwargs.get("y", 0),
        )

    def create_base_plate(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_base_plate(  # type: ignore[union-attr]
            x=kwargs.get("x", 0),
            y=kwargs.get("y", 0),
            width=kwargs.get("width", 100),
            length=kwargs.get("length", 100),
            thickness=kwargs.get("thickness", 2),
        )


class FeatureUseCase:
    """Use case: 3D parametric features (holes, shell, mirror, pattern, sketch)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for 3D features")

    def create_simple_hole(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_simple_hole(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            diameter=kwargs.get("diameter", 10),
            depth=kwargs.get("depth", 50),
        )

    def create_threaded_hole(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_threaded_hole(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            diameter=kwargs.get("diameter", 10),
            depth=kwargs.get("depth", 50),
        )

    def create_standard_hole(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_standard_hole(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            diameter=kwargs.get("diameter", 10),
            depth=kwargs.get("depth", 50),
            standard=kwargs.get("standard", "ISO"),
        )

    def create_shell(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_shell(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            thickness=kwargs.get("thickness", 2),
            outward=kwargs.get("outward", False),
        )

    def create_mirror_feature(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_mirror_feature(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            plane_handle=kwargs.get("plane_handle", ""),
        )

    def create_circular_pattern(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_circular_pattern(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            feature_handle=kwargs.get("feature_handle", ""),
            count=kwargs.get("count", 4),
            angle=kwargs.get("angle", 360),
        )

    def create_rectangular_pattern(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_rectangular_pattern(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            feature_handle=kwargs.get("feature_handle", ""),
            count_x=kwargs.get("count_x", 2),
            spacing_x=kwargs.get("spacing_x", 50),
            count_y=kwargs.get("count_y", 2),
            spacing_y=kwargs.get("spacing_y", 50),
        )

    def create_sketch(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_sketch(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
        )

    def add_sketch_circle(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.add_sketch_circle(  # type: ignore[union-attr]
            sketch_handle=kwargs.get("sketch_handle", ""),
            cx=kwargs.get("cx", 0),
            cy=kwargs.get("cy", 0),
            cz=kwargs.get("cz", 0),
            radius=kwargs.get("radius", 10),
        )

    def add_sketch_line(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.add_sketch_line(  # type: ignore[union-attr]
            sketch_handle=kwargs.get("sketch_handle", ""),
            x1=kwargs.get("x1", 0),
            y1=kwargs.get("y1", 0),
            z1=kwargs.get("z1", 0),
            x2=kwargs.get("x2", 100),
            y2=kwargs.get("y2", 0),
            z2=kwargs.get("z2", 0),
        )

    def create_profile(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_profile(  # type: ignore[union-attr]
            sketch_handle=kwargs.get("sketch_handle", ""),
        )

    def create_extrude_feature(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_extrude_feature(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            profile_handle=kwargs.get("profile_handle", ""),
            height=kwargs.get("height", 100),
            taper_angle=kwargs.get("taper_angle", 0),
            direction=kwargs.get("direction", True),
        )

    def create_revolve_feature(self, **kwargs: Any) -> Any:
        self._require_http()
        return self._http.create_revolve_feature(  # type: ignore[union-attr]
            solid_handle=kwargs.get("solid_handle", ""),
            profile_handle=kwargs.get("profile_handle", ""),
            axis_x=kwargs.get("axis_x", 0),
            axis_y=kwargs.get("axis_y", 0),
            axis_z=kwargs.get("axis_z", 0),
            dir_x=kwargs.get("dir_x", 0),
            dir_y=kwargs.get("dir_y", 0),
            dir_z=kwargs.get("dir_z", 1),
            angle=kwargs.get("angle", 360),
        )


class NurbIfcUseCase:
    """Use case: NURBS curve/surface creation and IFC import."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for NURBS/IFC operations")

    def create_nurb_curve(
        self,
        degree: int = 3,
        periodic: bool = False,
        control_points: list[list[float]] | None = None,
        knots: list[float] | None = None,
        weights: list[float] | None = None,
        layer: str | None = None,
    ) -> str | None:
        self._require_http()
        body: dict[str, Any] = {
            "degree": degree,
            "periodic": periodic,
            "control_points": control_points or [],
            "knots": knots or [],
        }
        if weights:
            body["weights"] = weights
        if layer:
            body["layer"] = layer
        result = self._http.create_nurb_curve(**body)  # type: ignore[union-attr]
        return str(result["handle"]) if result and "handle" in result else None

    def create_nurb_surface(
        self,
        degree_u: int = 3,
        degree_v: int = 3,
        rational: bool = False,
        control_points: list[list[float]] | None = None,
        u_knots: list[float] | None = None,
        v_knots: list[float] | None = None,
        weights: list[float] | None = None,
        num_control_u: int = 2,
        num_control_v: int = 2,
        layer: str | None = None,
    ) -> str | None:
        self._require_http()
        body: dict[str, Any] = {
            "degree_u": degree_u,
            "degree_v": degree_v,
            "rational": rational,
            "control_points": control_points or [],
            "u_knots": u_knots or [],
            "v_knots": v_knots or [],
            "num_control_u": num_control_u,
            "num_control_v": num_control_v,
        }
        if weights:
            body["weights"] = weights
        if layer:
            body["layer"] = layer
        result = self._http.create_nurb_surface(**body)  # type: ignore[union-attr]
        return str(result["handle"]) if result and "handle" in result else None

    def modify_nurb(
        self,
        handle: str,
        control_points: list[list[float]] | None = None,
        knots: list[float] | None = None,
    ) -> bool:
        self._require_http()
        body: dict[str, Any] = {"handle": handle}
        if control_points is not None:
            body["control_points"] = control_points
        if knots is not None:
            body["knots"] = knots
        result = self._http.modify_nurb(**body)  # type: ignore[union-attr]
        return result is not None

    def import_ifc(self, path: str) -> bool:
        self._require_http()
        return self._http.import_ifc(path=path)  # type: ignore[union-attr]

    def get_ifc_entities(self) -> list[dict[str, Any]] | None:
        self._require_http()
        return self._http.get_ifc_entities()  # type: ignore[union-attr]


class MultiCadUseCase:
    """Use case: MultiCAD-specific operations (grids, rooms, symbols, etc.)."""

    def __init__(self, http: HttpCadBridge | None) -> None:
        self._http = http

    def _require_http(self) -> None:
        if not self._http or not self._http.is_available:
            raise NotSupportedError("Requires .NET engine for MultiCAD operations")

    def create_grid_axis(
        self,
        grid_type: str = "rect",
        origin_x: float = 0,
        origin_y: float = 0,
        spacings_x: list[float] | None = None,
        spacings_y: list[float] | None = None,
        naming_x: str = "1,2,3...",
        naming_y: str = "A,B,C...",
    ) -> bool:
        self._require_http()
        return self._http.create_grid_axis(  # type: ignore[union-attr]
            grid_type=grid_type,
            origin_x=origin_x,
            origin_y=origin_y,
            spacings_x=spacings_x,
            spacings_y=spacings_y,
            naming_x=naming_x,
            naming_y=naming_y,
        )

    def create_grid_label(
        self,
        grid_handle: str,
        label: str,
        axis_index: int = 0,
        direction: str = "x",
    ) -> bool:
        self._require_http()
        return self._http.create_grid_label(  # type: ignore[union-attr]
            grid_handle=grid_handle,
            label=label,
            axis_index=axis_index,
            direction=direction,
        )

    def create_room(
        self,
        x: float = 0,
        y: float = 0,
        width: float = 1000,
        height: float = 1000,
        name: str | None = None,
    ) -> bool:
        self._require_http()
        return self._http.create_room(  # type: ignore[union-attr]
            x=x,
            y=y,
            width=width,
            height=height,
            name=name,
        )

    def get_room_properties(self, handle: str) -> dict[str, Any] | None:
        self._require_http()
        return self._http.get_room_properties(handle=handle)  # type: ignore[union-attr]

    def create_custom_object(
        self,
        class_name: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        self._require_http()
        return self._http.create_custom_object(  # type: ignore[union-attr]
            class_name=class_name,
            properties=properties,
        )

    def create_parametric_object(
        self,
        object_type: str,
        parameters: dict[str, Any] | None = None,
    ) -> bool:
        self._require_http()
        return self._http.create_parametric_object(  # type: ignore[union-attr]
            object_type=object_type,
            parameters=parameters,
        )

    def create_reactor(self, entity_handle: str, event_type: str = "modified") -> bool:
        self._require_http()
        return self._http.create_reactor(  # type: ignore[union-attr]
            entity_handle=entity_handle,
            event_type=event_type,
        )

    def create_2d_break(
        self,
        view_handle: str,
        x1: float = 0,
        y1: float = 0,
        x2: float = 0,
        y2: float = 0,
    ) -> bool:
        self._require_http()
        return self._http.create_2d_break(  # type: ignore[union-attr]
            view_handle=view_handle,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

    def start_motion_preview(self, handle: str) -> bool:
        self._require_http()
        return self._http.start_motion_preview(handle=handle)  # type: ignore[union-attr]

    def stop_motion_preview(self) -> bool:
        self._require_http()
        return self._http.stop_motion_preview()  # type: ignore[union-attr]

    def create_body_contour(self, solid_handle: str) -> bool:
        self._require_http()
        return self._http.create_body_contour(solid_handle=solid_handle)  # type: ignore[union-attr]

    def check_3d_faces(self, handle: str) -> dict[str, Any] | None:
        self._require_http()
        return self._http.check_3d_faces(handle=handle)  # type: ignore[union-attr]
