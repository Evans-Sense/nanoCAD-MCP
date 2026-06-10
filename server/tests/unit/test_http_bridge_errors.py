"""Unit tests for error paths in HttpCadBridge.

Tests cover all 5 exception types in ``_request()`` plus ``_read_port_file()``:
- ConnectError (connection refused)
- TimeoutException
- HTTPStatusError (500)
- RequestError (generic HTTP failure)
- JSONDecodeError (invalid response)
- Port file parse errors
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import psutil
import pytest

from src.infrastructure.http_bridge import HttpCadBridge, _read_port_file


@pytest.fixture(autouse=True)
def _set_test_data_dir() -> None:
    """Set NANOCAD_MCP_DATA_DIR to C: so tests with C:/projects pass validation."""
    os.environ["NANOCAD_MCP_DATA_DIR"] = "C:\\"


@pytest.fixture
def bridge() -> HttpCadBridge:
    b = HttpCadBridge(port=9999)
    b._client = MagicMock()
    b._available = True
    return b


# ── Port file errors ──────────────────────────────────────────


class TestReadPortFile:
    def test_returns_none_when_no_file(self) -> None:
        with patch.object(Path, "exists", return_value=False):
            assert _read_port_file() is None

    def test_returns_none_on_parse_error(self) -> None:
        """ValueError from invalid port string is caught and returns None."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", return_value="not-a-number"):
            assert _read_port_file() is None

    def test_returns_none_on_os_error(self) -> None:
        """OSError from reading the file is caught and returns None."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", side_effect=OSError("access denied")):
            assert _read_port_file() is None

    def test_returns_none_on_psutil_error(self) -> None:
        """psutil.Error from pid_exists is caught and returns None."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", return_value="5080:12345"), \
             patch("src.infrastructure.http_bridge.psutil.pid_exists", side_effect=psutil.Error("bad")):
            assert _read_port_file() is None

    def test_removes_stale_port_file(self) -> None:
        """Port file referencing a dead PID is removed."""
        with (
            patch("src.infrastructure.http_bridge.Path.home", return_value=Path("/fake")),
            patch("src.infrastructure.http_bridge.Path.exists", return_value=True),
            patch("src.infrastructure.http_bridge.Path.read_text", return_value="5080:99999"),
            patch("src.infrastructure.http_bridge.psutil.pid_exists", return_value=False),
            patch("src.infrastructure.http_bridge.Path.unlink") as mock_unlink,
        ):
            result = _read_port_file()
            assert result is None
            mock_unlink.assert_called_once_with(missing_ok=True)

    def test_reads_valid_port(self) -> None:
        """Valid port file with live PID returns the port number."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", return_value="5080:12345"), \
             patch("src.infrastructure.http_bridge.psutil.pid_exists", return_value=True):
            assert _read_port_file() == 5080

    def test_reads_port_without_pid(self) -> None:
        """Port file without PID suffix still returns the port."""
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", return_value="5080"):
            assert _read_port_file() == 5080


# ── _request() error paths ────────────────────────────────────


class TestRequestErrors:
    def test_connect_error_sets_unavailable(self, bridge: HttpCadBridge) -> None:
        """httpx.ConnectError marks bridge as unavailable and returns None."""
        bridge._client.request.side_effect = httpx.ConnectError("connection refused")
        result = bridge._request("GET", "/api/test")
        assert result is None
        assert bridge.is_available is False

    def test_timeout_does_not_mark_unavailable(self, bridge: HttpCadBridge) -> None:
        """httpx.TimeoutException is per-request; bridge stays available."""
        bridge._client.request.side_effect = httpx.TimeoutException("timed out")
        assert bridge.is_available is True
        result = bridge._request("GET", "/api/test")
        assert result is None
        assert bridge.is_available is True

    def test_http_500_returns_none(self, bridge: HttpCadBridge) -> None:
        """HTTP 500 (HTTPStatusError) returns None, bridge stays available."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_resp
        )
        result = bridge._request("GET", "/api/test")
        assert result is None
        # HTTP errors don't mark unavailable — the engine may recover
        assert bridge.is_available is True

    def test_http_400_returns_none(self, bridge: HttpCadBridge) -> None:
        """HTTP 400 (HTTPStatusError) returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"
        bridge._client.request.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=mock_resp
        )
        result = bridge._request("GET", "/api/test")
        assert result is None

    def test_generic_request_error_returns_none(self, bridge: HttpCadBridge) -> None:
        """Generic httpx.RequestError returns None without marking unavailable."""
        bridge._client.request.side_effect = httpx.RequestError("some error")
        assert bridge.is_available is True
        result = bridge._request("GET", "/api/test")
        assert result is None
        assert bridge.is_available is True

    def test_json_decode_error_returns_none(self, bridge: HttpCadBridge) -> None:
        """JSONDecodeError from invalid response body returns None."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = json.JSONDecodeError("bad json", "doc", 0)
        bridge._client.request.return_value = mock_resp
        result = bridge._request("GET", "/api/test")
        assert result is None

    def test_no_client_returns_none(self) -> None:
        """_request() with no client returns None immediately."""
        b = HttpCadBridge(port=9999)
        result = b._request("GET", "/api/test")
        assert result is None


# ── connect() error paths ─────────────────────────────────────


class TestConnectErrors:
    def test_connect_timeout_returns_false(self) -> None:
        """httpx.ConnectError in connect() returns False and marks unavailable."""
        b = HttpCadBridge(port=9999)
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("timeout")
            assert b.connect() is False
            assert b.is_available is False

    def test_connect_generic_exception_returns_false(self) -> None:
        """Generic Exception in connect() is caught, returns False."""
        b = HttpCadBridge(port=9999)
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.get.side_effect = RuntimeError("unexpected")
            assert b.connect() is False
            assert b.is_available is False
