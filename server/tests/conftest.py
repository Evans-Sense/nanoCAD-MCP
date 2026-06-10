from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.entities import (
    CadDocumentInfo,
    CadLayer,
    CadSystemInfo,
    EntityHandle,
    LayerName,
)
from src.domain.interfaces import ICadRepository


@pytest.fixture
def mock_repo() -> MagicMock:
    """Create a mock ICadRepository for testing."""
    repo = MagicMock(spec=ICadRepository)

    # Default health checks
    repo.is_available.return_value = True
    repo.get_system_info.return_value = CadSystemInfo(
        version="Test",
        is_com_available=True,
        is_engine_available=True,
        active_documents=1,
    )

    # Entity creation mocks
    repo.create_line.return_value = EntityHandle(value="LINE_001")
    repo.create_circle.return_value = EntityHandle(value="CIRCLE_001")
    repo.create_arc.return_value = EntityHandle(value="ARC_001")
    repo.create_polyline.return_value = EntityHandle(value="PLINE_001")
    repo.create_point.return_value = EntityHandle(value="POINT_001")
    repo.create_text.return_value = EntityHandle(value="TEXT_001")

    # Layer mocks
    repo.get_layers.return_value = [
        CadLayer(name=LayerName(value="0")),
        CadLayer(
            name=LayerName(value="Hidden"),
            is_on=False,
            is_frozen=True,
        ),
    ]

    # Document mocks
    repo.get_document_info.return_value = CadDocumentInfo(
        name="test.dwg",
        path="C:/test.dwg",
        is_saved=True,
        entities_count=5,
        layers_count=2,
        blocks_count=0,
    )

    return repo
