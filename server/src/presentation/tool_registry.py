"""Tool registry for the nanoCAD MCP server.

Provides a declarative way to define MCP tools with schema validation,
eliminating the need for repetitive boilerplate in server.py.

Usage:
    from src.presentation.tool_registry import ToolRegistry, tool

    registry = ToolRegistry()

    @registry.tool(
        name="create_line",
        description="Create a line",
        required=["x1", "y1", "x2", "y2"],
        properties={
            "x1": {"type": "number"},
            "y1": {"type": "number"},
            "x2": {"type": "number"},
            "y2": {"type": "number"},
            "layer": {"type": "string"},
        },
    )
    def create_line(x1: float, y1: float, x2: float, y2: float, layer: str = "0") -> dict:
        ...

    # Get MCP Tool list
    tools = registry.to_mcp_tools()

    # Get handler by name
    handler = registry.get_handler("create_line")

    # Get all handlers as routing dict
    routing = registry.build_routing()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class ToolDef:
    """Definition of a single MCP tool."""

    name: str
    description: str
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    handler: Callable[..., Any] | None = None

    def to_mcp_tool(self) -> Any:
        """Convert to mcp.types.Tool."""
        from mcp.types import Tool

        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": self.properties,
                "required": self.required,
            },
        )


class ToolRegistry:
    """Registry of MCP tools with handler mapping.

    Collects tool definitions via the @tool() decorator and provides:
    - MCP Tool list for list_tools handler
    - Handler lookup for call_tool routing
    - Schema validation (future)
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDef] = {}

    def tool(
        self,
        *,
        name: str,
        description: str,
        required: list[str] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a tool handler.

        Usage:
            @registry.tool(
                name="create_line",
                description="Create a line",
                required=["x1", "y1", "x2", "y2"],
                properties={...},
            )
            def create_line(x1, y1, x2, y2, layer="0"):
                ...
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            td = ToolDef(
                name=name,
                description=description,
                properties=properties or {},
                required=required or [],
                handler=fn,
            )
            self._tools[name] = td
            return fn

        return decorator

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        *,
        required: list[str] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool programmatically (without decorator)."""
        td = ToolDef(
            name=name,
            description=description,
            properties=properties or {},
            required=required or [],
            handler=handler,
        )
        self._tools[name] = td

    def to_mcp_tools(self) -> list[Any]:
        """Return list of mcp.types.Tool for the list_tools handler."""
        return [td.to_mcp_tool() for td in self._tools.values()]

    def get_handler(self, name: str) -> Callable[..., Any] | None:
        """Get the handler function for a tool by name."""
        td = self._tools.get(name)
        return td.handler if td else None

    def build_routing(self) -> dict[str, Callable[..., Any]]:
        """Build routing dict: tool_name -> handler function."""
        routing: dict[str, Callable[..., Any]] = {}
        for name, td in self._tools.items():
            if td.handler is not None:
                routing[name] = td.handler
        return routing

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return list(self._tools.keys())
