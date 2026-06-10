"""Unit tests for error paths in CadRepository.

Covers ``NotSupportedError`` thrown when methods are called in ``"com"``
or ``"offline"`` mode — specifically methods that are not yet covered
by the existing ``test_requires_http_for_advanced`` or ``*_not_implemented`` tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.entities import (
    CadBlock,
    CadLine,
    CreateNurbCurveRequest,
    CreateNurbSurfaceRequest,
    LayerName,
    ModifyNurbRequest,
    Point2D,
)
from src.domain.exceptions import NotSupportedError
from src.infrastructure.cad_repository import CadRepository


@pytest.fixture
def com_repo() -> CadRepository:
    """Repository in COM mode — all HTTP-only methods should raise NotSupportedError."""
    r = CadRepository()
    r._http = MagicMock()
    r._com = MagicMock()
    r._mode = "com"
    return r


@pytest.fixture
def offline_repo() -> CadRepository:
    """Repository in offline mode."""
    r = CadRepository()
    r._http = MagicMock()
    r._com = MagicMock()
    r._mode = "offline"
    return r


# ── 3D Solids (15 methods) ───────────────────────────────────


class TestSolidErrors:
    """All 15 solid methods raise NotSupportedError in com/offline mode."""

    @pytest.mark.parametrize(
        "method_call",
        [
            lambda r: r.create_box(10.0, 10.0, 10.0),
            lambda r: r.create_sphere(5.0),
            lambda r: r.create_cylinder(5.0, 10.0),
            lambda r: r.create_cone(5.0, 10.0),
            lambda r: r.create_torus(10.0, 2.0),
            lambda r: r.create_wedge(10.0, 10.0, 10.0),
            lambda r: r.create_pyramid(10.0, 6, 5.0),
            lambda r: r.boolean_union("H1", "H2"),
            lambda r: r.boolean_subtract("H1", "H2"),
            lambda r: r.boolean_intersect("H1", "H2"),
            lambda r: r.extrude_solid("H1", 10.0),
            lambda r: r.revolve_solid("H1"),
            lambda r: r.move_solid("H1", 5.0, 5.0),
            lambda r: r.set_3d_view("front"),
            lambda r: r.get_solid_properties("H1"),
        ],
    )
    def test_all_solids_raise_not_supported_in_com(
        self, com_repo: CadRepository, method_call: object
    ) -> None:
        with pytest.raises(NotSupportedError):
            method_call(com_repo)

    @pytest.mark.parametrize(
        "method_call",
        [
            lambda r: r.create_box(10.0, 10.0, 10.0),
            lambda r: r.create_sphere(5.0),
            lambda r: r.create_cylinder(5.0, 10.0),
            lambda r: r.create_cone(5.0, 10.0),
            lambda r: r.create_torus(10.0, 2.0),
            lambda r: r.create_wedge(10.0, 10.0, 10.0),
            lambda r: r.create_pyramid(10.0, 6, 5.0),
            lambda r: r.boolean_union("H1", "H2"),
            lambda r: r.boolean_subtract("H1", "H2"),
            lambda r: r.boolean_intersect("H1", "H2"),
            lambda r: r.extrude_solid("H1", 10.0),
            lambda r: r.revolve_solid("H1"),
            lambda r: r.move_solid("H1", 5.0, 5.0),
            lambda r: r.set_3d_view("front"),
            lambda r: r.get_solid_properties("H1"),
        ],
    )
    def test_all_solids_raise_not_supported_in_offline(
        self, offline_repo: CadRepository, method_call: object
    ) -> None:
        with pytest.raises(NotSupportedError):
            method_call(offline_repo)


# ── NURBS / IFC (5 methods) ──────────────────────────────────


class TestNurbIfcErrors:
    def test_create_nurb_curve_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.create_nurb_curve(
                CreateNurbCurveRequest(
                    control_points=[[0.0, 0.0], [10.0, 10.0]],
                    knots=[0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
                    degree=2,
                )
            )

    def test_create_nurb_surface_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.create_nurb_surface(
                CreateNurbSurfaceRequest(
                    control_points=[[0.0, 0.0], [10.0, 10.0]],
                    u_knots=[0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
                    v_knots=[0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
                    num_control_u=2,
                    num_control_v=1,
                    degree_u=2,
                    degree_v=2,
                )
            )

    def test_modify_nurb_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.modify_nurb(
                ModifyNurbRequest(
                    handle="H1",
                    control_points=[Point2D(x=5, y=5)],
                )
            )

    def test_import_ifc_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.import_ifc("C:/test.ifc")

    def test_get_ifc_entities_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.get_ifc_entities()


# ── Document Operations (methods not yet tested) ─────────────


class TestDocumentErrors:
    def test_export_dwg_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.export_dwg("C:/out.dwg")

    def test_export_dxf_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.export_dxf("C:/out.dxf")

    def test_new_document_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.new_document(template="acad.dwt")

    def test_create_project_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.create_project(filename="test.dwg", directory="projects")

    def test_save_project_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.save_project(filename="test.dwg", directory="projects")

    def test_open_document_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.open_document("C:/test.dwg")

    def test_close_document_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.close_document()


# ── Block Operations (methods not yet tested) ────────────────


class TestBlockErrors:
    def test_create_block_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.create_block(
                CadBlock(
                    name=LayerName(value="NewBlock"),
                    base_point=Point2D(x=0, y=0),
                    entities=[CadLine(start=Point2D(x=0, y=0), end=Point2D(x=10, y=10))],
                )
            )

    def test_get_block_entities_in_com(self, com_repo: CadRepository) -> None:
        with pytest.raises(NotSupportedError):
            com_repo.get_block_entities("MyBlock")


# ── Other HTTP-only methods ──────────────────────────────────


class TestOtherErrors:
    def test_create_layer_state_not_supported_in_offline(
        self, offline_repo: CadRepository
    ) -> None:
        with pytest.raises(NotSupportedError):
            offline_repo.set_layer_state(LayerName(value="0"), on=False)

    def test_delete_layer_not_supported_in_offline(
        self, offline_repo: CadRepository
    ) -> None:
        with pytest.raises(NotSupportedError):
            offline_repo.delete_layer(LayerName(value="X"))
