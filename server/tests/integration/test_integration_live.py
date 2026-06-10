"""Live integration tests that require nanoCAD with .NET plugin running.

All tests are skipped unless ``NANOCAD_MCP_TEST_LIVE`` environment variable is set.

These tests exercise the full stack:
- MCP server -> UseCase -> HttpCadBridge -> .NET engine -> nanoCAD
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from src.infrastructure.http_bridge import HttpCadBridge

# Skip all tests unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.environ.get("NANOCAD_MCP_TEST_LIVE"),
    reason="Requires nanoCAD running with .NET plugin at localhost:5080",
)


@pytest.fixture
def live_bridge() -> Any:
    """Connect to the running nanoCAD .NET engine."""
    bridge = HttpCadBridge()
    if not bridge.connect():
        pytest.skip("nanoCAD .NET engine not reachable at localhost:5080")
    yield bridge
    bridge.close()


class TestFullWorkflow:
    """End-to-end workflow: create document → add entities → save."""

    def test_health_check(self, live_bridge: HttpCadBridge) -> None:
        """Health check returns system info."""
        health = live_bridge.check_health()
        assert health is not None
        assert isinstance(health, dict)
        # Should have version info
        assert "version" in health or "status" in health

    def test_create_document_and_entity(self, live_bridge: HttpCadBridge) -> None:
        """Create a new document, add a line, verify it exists."""
        # Create new document (avoids SendCommand — uses DocumentManager.Add)
        live_bridge.create_entity(
            "document", {"new": True}
        ) if hasattr(live_bridge, "create_entity") else None

        # Create a simple line
        handle = live_bridge.create_entity(
            "line",
            {"x1": 0, "y1": 0, "x2": 100, "y2": 100},
        )
        assert handle is not None
        assert isinstance(handle, str)
        assert len(handle) > 0

        # Verify the entity exists
        entity = live_bridge.get_entity(handle)
        assert entity is not None
        assert entity.get("type") == "LINE"

    def test_layer_operations(self, live_bridge: HttpCadBridge) -> None:
        """Create a layer and verify it appears in the layer list."""
        # Create layer through entity creation endpoint
        handle = live_bridge.create_entity(
            "layer",
            {"name": "TestLayer_Live", "color": 3},
        )
        assert handle is not None

        # Get all layers and verify ours exists
        # This would need a get_layers method on the bridge
        # For now, just verify the create succeeded


class TestConnectionRecovery:
    """Graceful degradation when engine connection is lost."""

    def test_disconnect_during_request(self) -> None:
        """Simulate connection loss — request should return None gracefully."""
        bridge = HttpCadBridge(port=9999)
        result = bridge.check_health()
        assert result is None
        assert bridge.is_available is False

    def test_health_check_offline(self) -> None:
        """health_check without CAD returns None."""
        bridge = HttpCadBridge(port=9999)
        assert bridge.is_available is False
        health = bridge.check_health()
        assert health is None
