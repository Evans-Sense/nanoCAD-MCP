"""Domain exceptions for nanoCAD MCP.

All CAD-related errors inherit from NanocadError.
Application code catches NanocadError at the boundary.
"""

from __future__ import annotations


class NanocadError(Exception):
    """Base for all nanoCAD MCP errors."""


class ConnectionError(NanocadError):
    """CAD is not reachable or connection was lost."""


class ValidationError(NanocadError):
    """Invalid input data from the client."""


class NotSupportedError(NanocadError):
    """Operation not supported in the current CAD mode (COM/Free)."""


class OperationError(NanocadError):
    """CAD operation failed at runtime."""


__all__ = [
    "ConnectionError",
    "NanocadError",
    "NotSupportedError",
    "OperationError",
    "ValidationError",
]
