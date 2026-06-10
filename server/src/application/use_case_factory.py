"""UseCaseFactory — caches and provides use case instances.

Decouples server.py from the 30+ global variables.
Created once at startup with a reference to the repository.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.application.extended_use_cases import (
    AssemblyUseCase,
    BlockManagementUseCase,
    ConstraintUseCase,
    DimensionUseCase,
    DocumentManagementUseCase,
    EdgeOpUseCase,
    FeatureUseCase,
    HatchUseCase,
    LayerManagementUseCase,
    LinearDimUseCase,
    MeasurementUseCase,
    MLeaderUseCase,
    MultiCadUseCase,
    NurbIfcUseCase,
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
from src.application.use_cases import (
    BlockUseCase,
    DocumentUseCase,
    EntityUseCase,
    LayerUseCase,
    SolidUseCase,
    SystemUseCase,
)

if TYPE_CHECKING:
    from src.domain.interfaces import ICadRepository
    from src.infrastructure.cad_repository import CadRepository
    from src.infrastructure.http_bridge import HttpCadBridge


def _get_http(repo: CadRepository) -> HttpCadBridge | None:
    """Extract the HTTP bridge from a CadRepository."""
    return getattr(repo, "_http", None)


class UseCaseFactory:
    """Factory for use case instances. Caches after first creation."""

    def __init__(self, repo: CadRepository) -> None:
        self._repo: ICadRepository = repo
        self._http = _get_http(repo)
        self._cache: dict[str, Any] = {}

    def _get(self, key: str, factory: Any) -> Any:
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    # -- Use cases that take ICadRepository --

    @property
    def entity(self) -> EntityUseCase:
        return self._get("entity", lambda: EntityUseCase(self._repo))

    @property
    def layer(self) -> LayerUseCase:
        return self._get("layer", lambda: LayerUseCase(self._repo))

    @property
    def block(self) -> BlockUseCase:
        return self._get("block", lambda: BlockUseCase(self._repo))

    @property
    def document(self) -> DocumentUseCase:
        return self._get("document", lambda: DocumentUseCase(self._repo))

    @property
    def system(self) -> SystemUseCase:
        return self._get("system", lambda: SystemUseCase(self._repo))

    @property
    def solid(self) -> SolidUseCase:
        return self._get("solid", lambda: SolidUseCase(self._repo))

    # -- Use cases that take HttpCadBridge directly --

    @property
    def symbol(self) -> SymbolUseCase:
        return self._get("symbol", lambda: SymbolUseCase(self._http))

    @property
    def table(self) -> TableUseCase:
        return self._get("table", lambda: TableUseCase(self._http))

    @property
    def hatch(self) -> HatchUseCase:
        return self._get("hatch", lambda: HatchUseCase(self._http))

    @property
    def dimension(self) -> DimensionUseCase:
        return self._get("dimension", lambda: DimensionUseCase(self._http))

    @property
    def measurement(self) -> MeasurementUseCase:
        return self._get("measurement", lambda: MeasurementUseCase(self._http))

    @property
    def transform(self) -> TransformationUseCase:
        return self._get("transform", lambda: TransformationUseCase(self._http))

    @property
    def primitive(self) -> PrimitiveUseCase:
        return self._get("primitive", lambda: PrimitiveUseCase(self._http))

    @property
    def doc_mgmt(self) -> DocumentManagementUseCase:
        return self._get("doc_mgmt", lambda: DocumentManagementUseCase(self._http))

    @property
    def block_mgmt(self) -> BlockManagementUseCase:
        return self._get("block_mgmt", lambda: BlockManagementUseCase(self._http))

    @property
    def teo(self) -> TrimExtendOffsetUseCase:
        return self._get("teo", lambda: TrimExtendOffsetUseCase(self._http))

    @property
    def layer_mgmt(self) -> LayerManagementUseCase:
        return self._get("layer_mgmt", lambda: LayerManagementUseCase(self._http))

    @property
    def linear_dim(self) -> LinearDimUseCase:
        return self._get("linear_dim", lambda: LinearDimUseCase(self._http))

    @property
    def sweep_loft(self) -> SweepLoftUseCase:
        return self._get("sweep_loft", lambda: SweepLoftUseCase(self._http))

    @property
    def edge_op(self) -> EdgeOpUseCase:
        return self._get("edge_op", lambda: EdgeOpUseCase(self._http))

    @property
    def assembly(self) -> AssemblyUseCase:
        return self._get("assembly", lambda: AssemblyUseCase(self._http))

    @property
    def selection(self) -> SelectionUseCase:
        return self._get("selection", lambda: SelectionUseCase(self._http))

    @property
    def stl(self) -> StlExportUseCase:
        return self._get("stl", lambda: StlExportUseCase(self._http))

    @property
    def constraint(self) -> ConstraintUseCase:
        return self._get("constraint", lambda: ConstraintUseCase(self._http))

    @property
    def mleader(self) -> MLeaderUseCase:
        return self._get("mleader", lambda: MLeaderUseCase(self._http))

    @property
    def sheet_metal(self) -> SheetMetalUseCase:
        return self._get("sheet_metal", lambda: SheetMetalUseCase(self._http))

    @property
    def feature(self) -> FeatureUseCase:
        return self._get("feature", lambda: FeatureUseCase(self._http))

    @property
    def nurb_ifc(self) -> NurbIfcUseCase:
        return self._get("nurb_ifc", lambda: NurbIfcUseCase(self._http))

    @property
    def multicad(self) -> MultiCadUseCase:
        return self._get("multicad", lambda: MultiCadUseCase(self._http))


__all__ = ["UseCaseFactory"]
