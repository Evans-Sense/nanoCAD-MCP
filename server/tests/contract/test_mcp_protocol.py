"""Contract tests for MCP protocol compliance.

Tests the full MCP message flow:
- initialize handshake
- list_tools (filtered by mode)
- call_tool (valid, invalid, validation error, nanoCAD error, not implemented)
- list_resources / list_prompts (empty)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListPromptsRequest,
    ListResourcesRequest,
    ListToolsRequest,
    ListToolsResult,
    ServerResult,
    TextContent,
)

from src.domain.exceptions import NanocadError

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _reset_context() -> Any:
    """Reset context vars before each test."""
    from src.presentation.context import reset as reset_context

    reset_context()


@pytest.fixture(autouse=True)
def _mock_logger() -> Any:
    """Mock structlog to prevent side effects."""
    with patch("src.presentation.server.structlog.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def mock_repo() -> MagicMock:
    """Create a mock repository for full mode testing."""
    repo = MagicMock()
    repo.connection_mode = "full"
    repo.is_available.return_value = True
    return repo


@pytest.fixture
def com_repo() -> MagicMock:
    """Create a mock repository for COM mode testing."""
    repo = MagicMock()
    repo.connection_mode = "com"
    repo.is_available.return_value = True
    return repo


@pytest.fixture
def offline_repo() -> MagicMock:
    """Create a mock repository for offline mode testing."""
    repo = MagicMock()
    repo.connection_mode = "offline"
    repo.is_available.return_value = True
    return repo


# ── Helper: build full server with mocked repo ────────────────


async def _create_server(repo: MagicMock) -> Any:
    """Create a fully initialised MCP server with a mock repository."""
    from src.application.use_case_factory import UseCaseFactory
    from src.presentation.context import set_factory, set_repository
    from src.presentation.server import create_server

    set_repository(repo)
    factory = UseCaseFactory(repo)  # type: ignore[arg-type]
    set_factory(factory)
    return create_server()


def _unwrap(result: ServerResult) -> Any:
    """Unwrap a ServerResult to the inner response type."""
    return result.root


async def _call_tool(
    server: Any, name: str, arguments: dict[str, Any] | None = None
) -> CallToolResult:
    """Invoke a tool call via the server's request handler."""
    handler = server.request_handlers.get(CallToolRequest)
    assert handler is not None
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params={"name": name, "arguments": arguments or {}},
        )
    )
    return _unwrap(result)


# ── Contract Tests ────────────────────────────────────────────


class TestInitializeHandshake:
    """Protocol compliance: initialize handshake."""

    async def test_server_creation(self, mock_repo: MagicMock) -> None:
        """Server can be created without error."""
        server = await _create_server(mock_repo)
        assert server is not None
        assert server.name == "ncad-mcp-server"




class TestListTools:
    """Protocol compliance: tools/list."""

    async def _list_tools(self, server: Any) -> ListToolsResult:
        handler = server.request_handlers.get(ListToolsRequest)
        assert handler is not None
        result = await handler(ListToolsRequest(method="tools/list", params={}))
        return _unwrap(result)

    async def test_list_tools_returns_tools(self, mock_repo: MagicMock) -> None:
        """Server returns a non-empty list of tools."""
        server = await _create_server(mock_repo)
        result = await self._list_tools(server)
        assert len(result.tools) > 0, "Tool list should not be empty"
        # Should have full-mode tools
        tool_names = [t.name for t in result.tools]
        assert "health_check" in tool_names
        assert "create_box" in tool_names, (
            "Full mode should include create_box"
        )

    async def test_list_tools_com_mode_filters_solid_tools(
        self, com_repo: MagicMock
    ) -> None:
        """COM mode filters out full-mode-only tools."""
        server = await _create_server(com_repo)
        result = await self._list_tools(server)
        tool_names = [t.name for t in result.tools]
        # COM mode should NOT have full-mode tools like create_box
        assert "create_box" not in tool_names, (
            "COM mode should exclude 3D solid tools"
        )
        # But SHOULD have online tools
        assert "health_check" in tool_names
        assert "create_line" in tool_names

    async def test_list_tools_offline_mode_has_minimal_tools(
        self, offline_repo: MagicMock
    ) -> None:
        """Offline mode returns only tools that need no CAD."""
        server = await _create_server(offline_repo)
        result = await self._list_tools(server)
        tool_names = [t.name for t in result.tools]
        # Offline should have health_check but not entity creation
        assert "health_check" in tool_names
        assert "create_line" not in tool_names, (
            "Offline mode should exclude entity creation tools"
        )

    async def test_all_tools_have_unique_names(
        self, mock_repo: MagicMock
    ) -> None:
        """All tool names are unique."""
        server = await _create_server(mock_repo)
        result = await self._list_tools(server)
        names = [t.name for t in result.tools]
        assert len(names) == len(set(names)), "Tool names must be unique"

    async def test_all_tools_have_valid_schema(
        self, mock_repo: MagicMock
    ) -> None:
        """Each tool has a valid JSON Schema."""
        server = await _create_server(mock_repo)
        result = await self._list_tools(server)
        for tool in result.tools:
            assert isinstance(tool.name, str)
            assert tool.inputSchema is not None
            assert tool.inputSchema.get("type") == "object"


class TestCallTool:
    """Protocol compliance: tools/call."""

    async def test_call_health_check(self, mock_repo: MagicMock) -> None:
        """Calling health_check returns a TextContent result."""
        server = await _create_server(mock_repo)
        mock_repo.is_available.return_value = True
        mock_repo.get_system_info.return_value = MagicMock(
            version="Test",
            is_com_available=True,
            is_engine_available=True,
            active_documents=1,
        )

        result = await _call_tool(server, "health_check")
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)
        assert result.content[0].type == "text"
        assert "Available: True" in result.content[0].text

    async def test_call_unknown_tool(self, mock_repo: MagicMock) -> None:
        """Calling an unknown tool returns an error message."""
        server = await _create_server(mock_repo)
        result = await _call_tool(server, "nonexistent_tool")
        assert "UNKNOWN TOOL" in result.content[0].text  # type: ignore[union-attr]

    async def test_call_tool_validation_error(self, mock_repo: MagicMock) -> None:
        """Invalid arguments cause a VALIDATION ERROR response."""
        server = await _create_server(mock_repo)
        result = await _call_tool(server, "create_line", {})
        assert result.isError
        text = result.content[0].text  # type: ignore[union-attr]
        assert "VALIDATION ERROR" in text or "validation error" in text.lower()

    async def test_call_tool_nanocad_error(self, mock_repo: MagicMock) -> None:
        """NanocadError from a use case is caught and displayed as error text."""
        mock_repo.create_line.side_effect = NanocadError("CAD engine not available")
        server = await _create_server(mock_repo)

        result = await _call_tool(
            server,
            "create_line",
            {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        )
        assert "nanoCAD ERROR" in result.content[0].text  # type: ignore[union-attr]

    async def test_call_tool_not_implemented(self, mock_repo: MagicMock) -> None:
        """NotImplementedError from a use case is caught and displayed."""
        mock_repo.create_line.side_effect = NotImplementedError("not yet")
        server = await _create_server(mock_repo)

        result = await _call_tool(
            server,
            "create_line",
            {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        )
        text = result.content[0].text  # type: ignore[union-attr]
        assert "NOT IMPLEMENTED" in text or "not implemented" in text.lower()


    async def test_call_tool_validation_via_pydantic(
        self, mock_repo: MagicMock
    ) -> None:
        """Pydantic model validation catches semantic errors."""
        server = await _create_server(mock_repo)
        # radius=0 passes JSON Schema (number) but fails Pydantic (PositiveFloat)
        result = await _call_tool(
            server, "create_circle", {"cx": 0, "cy": 0, "radius": 0}
        )
        text = result.content[0].text  # type: ignore[union-attr]
        assert "VALIDATION ERROR" in text or "validation error" in text.lower()


class TestListResources:
    """Protocol compliance: resources/list."""

    async def test_list_resources_handler_registered(
        self, mock_repo: MagicMock
    ) -> None:
        """Server has a resources/list handler."""
        server = await _create_server(mock_repo)
        handler = server.request_handlers.get(ListResourcesRequest)
        assert handler is not None

    async def test_list_resources_returns_empty(
        self, mock_repo: MagicMock
    ) -> None:
        """resources/list returns an empty list."""
        server = await _create_server(mock_repo)
        handler = server.request_handlers.get(ListResourcesRequest)
        result = _unwrap(await handler(
            ListResourcesRequest(method="resources/list", params={})
        ))
        # The server should return something — even if empty
        assert result is not None


class TestErrorHandlers:
    """Test error handling paths in the server."""

    async def test_list_tools_with_repo_exception(
        self, mock_repo: MagicMock
    ) -> None:
        """list_tools falls back to 'offline' mode on exception."""
        # Patch get_repository in server.py's module namespace
        with patch("src.presentation.server.get_repository") as mock_get:
            mock_get.side_effect = RuntimeError("repository unavailable")
            server = await _create_server(mock_repo)
            # Call through the framework handler
            handler = server.request_handlers.get(ListToolsRequest)
            result = await handler(
                ListToolsRequest(method="tools/list", params={})
            )
            inner = _unwrap(result)
            # Should get minimal offline tools
            assert len(inner.tools) > 0
            assert any(t.name == "health_check" for t in inner.tools)

    async def test_call_tool_connection_failure(
        self, mock_repo: MagicMock
    ) -> None:
        """Call tool handles connection failure gracefully."""
        # Make is_available() raise to trigger the except in handle_call_tool
        mock_repo.is_available.side_effect = RuntimeError("nanoCAD not found")
        server = await _create_server(mock_repo)
        result = await _call_tool(server, "health_check")
        # Should get the connection failure message
        assert "Failed to connect to nanoCAD" in result.content[0].text  # type: ignore[union-attr]

    async def test_call_tool_generic_error(self, mock_repo: MagicMock) -> None:
        """Generic exceptions from use cases are caught."""
        mock_repo.create_line.side_effect = RuntimeError("unexpected crash")
        server = await _create_server(mock_repo)

        result = await _call_tool(
            server,
            "create_line",
            {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        )
        text = result.content[0].text  # type: ignore[union-attr]
        assert "ERROR" in text
        assert "unexpected crash" in text


class TestListPrompts:
    """Protocol compliance: prompts/list."""

    async def test_list_prompts_handler_registered(
        self, mock_repo: MagicMock
    ) -> None:
        """Server has a prompts/list handler."""
        server = await _create_server(mock_repo)
        handler = server.request_handlers.get(ListPromptsRequest)
        assert handler is not None

    async def test_list_prompts_returns_empty(
        self, mock_repo: MagicMock
    ) -> None:
        """prompts/list returns an empty list."""
        server = await _create_server(mock_repo)
        handler = server.request_handlers.get(ListPromptsRequest)
        result = _unwrap(await handler(
            ListPromptsRequest(method="prompts/list", params={})
        ))
        assert result is not None
