"""Unit tests for the SafeBridge wrapper."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, PropertyMock

import pytest

from src.infrastructure.http_bridge import HttpCadBridge
from src.infrastructure.safe_bridge import SafeBridge


@pytest.fixture
def mock_bridge() -> MagicMock:
    """Create a mock HttpCadBridge for SafeBridge tests."""
    bridge = MagicMock(spec=HttpCadBridge)
    type(bridge).is_available = PropertyMock(return_value=True)
    bridge.check_health.return_value = {"status": "ok", "version": "test"}
    bridge.get_layers.return_value = [{"name": "0"}]
    bridge.create_box.return_value = "BOX_001"
    bridge.create_cylinder.return_value = "CYL_001"
    bridge.move_entity.return_value = True
    bridge.get_system_info.return_value = {"version": "test"}
    return bridge


class TestSafeBridge:
    def test_wraps_successful_call(self, mock_bridge: MagicMock) -> None:
        safe = SafeBridge(mock_bridge)
        result = safe.check_health()
        assert result == {"status": "ok", "version": "test"}
        mock_bridge.check_health.assert_called_once()

    def test_returns_none_on_error(self, mock_bridge: MagicMock) -> None:
        mock_bridge.check_health.side_effect = RuntimeError("fail")
        safe = SafeBridge(mock_bridge)
        result = safe.check_health()
        assert result is None

    def test_reconnects_if_unavailable(self, mock_bridge: MagicMock) -> None:
        type(mock_bridge).is_available = PropertyMock(
            side_effect=[False, False, True]
        )
        mock_bridge.connect.return_value = True

        safe = SafeBridge(mock_bridge, auto_reconnect=True)
        safe.check_health()
        mock_bridge.connect.assert_called_once()

    def test_does_not_reconnect_if_disabled(self, mock_bridge: MagicMock) -> None:
        type(mock_bridge).is_available = PropertyMock(return_value=False)
        safe = SafeBridge(mock_bridge, auto_reconnect=False)
        result = safe.check_health()
        assert result is None
        mock_bridge.connect.assert_not_called()

    def test_raises_attribute_error_for_unknown_method(
        self, mock_bridge: MagicMock
    ) -> None:
        safe = SafeBridge(mock_bridge)
        with pytest.raises(AttributeError, match="no method"):
            safe.nonexistent_method()  # type: ignore[attr-defined]

    def test_call_delay_is_applied(self, mock_bridge: MagicMock) -> None:
        safe = SafeBridge(mock_bridge, call_delay=0.01)
        t0 = time.monotonic()
        safe.check_health()
        t1 = time.monotonic()
        assert t1 - t0 >= 0.01

    def test_consecutive_errors_tracked(self, mock_bridge: MagicMock) -> None:
        mock_bridge.check_health.side_effect = RuntimeError("fail")
        safe = SafeBridge(mock_bridge)
        assert safe._consecutive_errors == 0
        safe.check_health()
        assert safe._consecutive_errors == 1
        safe.check_health()
        assert safe._consecutive_errors == 2

    def test_success_resets_error_count(self, mock_bridge: MagicMock) -> None:
        mock_bridge.check_health.side_effect = RuntimeError("fail")
        safe = SafeBridge(mock_bridge)
        safe.check_health()
        assert safe._consecutive_errors == 1
        mock_bridge.check_health.side_effect = None
        safe.check_health()
        assert safe._consecutive_errors == 0

    def test_bridge_property(self, mock_bridge: MagicMock) -> None:
        safe = SafeBridge(mock_bridge)
        assert safe.bridge is mock_bridge

    def test_is_available_property(self, mock_bridge: MagicMock) -> None:
        type(mock_bridge).is_available = PropertyMock(return_value=True)
        safe = SafeBridge(mock_bridge)
        assert safe.is_available is True

        type(mock_bridge).is_available = PropertyMock(return_value=False)
        assert safe.is_available is False

    def test_wraps_all_http_methods(self, mock_bridge: MagicMock) -> None:
        """SafeBridge wraps every method on HttpCadBridge."""
        safe = SafeBridge(mock_bridge)
        assert safe.check_health() == {"status": "ok", "version": "test"}
        assert safe.get_layers() == [{"name": "0"}]
        assert safe.create_box(x=10, y=10, z=5) == "BOX_001"

    def test_wraps_method_with_multiple_params(
        self, mock_bridge: MagicMock
    ) -> None:
        safe = SafeBridge(mock_bridge)
        result = safe.move_entity("HANDLE_1", dx=10, dy=20)
        assert result is True
        mock_bridge.move_entity.assert_called_once_with(
            "HANDLE_1", dx=10, dy=20
        )

    def test_safe_bridge_handles_none_return(self, mock_bridge: MagicMock) -> None:
        """When the underlying method returns None, SafeBridge passes it through."""
        mock_bridge.check_health.return_value = None
        safe = SafeBridge(mock_bridge)
        result = safe.check_health()
        assert result is None
