"""Input validation for MCP tool calls.

Validates tool arguments against schemas defined in tool_defs.py
before they reach use case handlers.
"""

from __future__ import annotations

from typing import Any

from src.presentation.tool_defs import TOOL_DEFS

# Build a lookup dict for O(1) schema access
_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {td["name"]: td for td in TOOL_DEFS}

# JSON Schema type → Python type(s) mapping
_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "object": (dict,),
    "array": (list,),
}


class ToolValidationError(Exception):
    """Raised when tool input fails validation."""

    def __init__(self, tool_name: str, errors: list[str]) -> None:
        self.tool_name = tool_name
        self.errors = errors
        msg = f"Validation failed for '{tool_name}': {'; '.join(errors)}"
        super().__init__(msg)


def validate_tool_input(tool_name: str, arguments: dict[str, Any]) -> None:
    """Validate tool arguments against the schema.

    Checks:
    1. Tool schema exists
    2. All required fields are present
    3. Field types match the schema

    Raises ToolValidationError if validation fails.
    """
    schema = _TOOL_SCHEMAS.get(tool_name)
    if schema is None:
        raise ToolValidationError(tool_name, [f"Unknown tool: {tool_name}"])

    errors: list[str] = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in arguments:
            errors.append(f"Missing required field: '{field}'")

    # Check types for provided fields
    for key, value in arguments.items():
        if key not in properties:
            # Unknown field — allow it (forward compatibility)
            continue

        prop = properties[key]
        expected_type = prop.get("type")
        if expected_type is None:
            continue

        python_types = _TYPE_MAP.get(expected_type)
        if python_types is None:
            continue

        # Handle special case: "number" accepts both int and float
        # but bool is a subclass of int, so we need to exclude it
        if expected_type == "number":
            if isinstance(value, bool):
                errors.append(f"Field '{key}' expects {expected_type}, got bool")
            elif not isinstance(value, python_types):
                errors.append(f"Field '{key}' expects {expected_type}, got {type(value).__name__}")
        elif expected_type == "integer":
            # bool is subclass of int, reject it
            if isinstance(value, bool):
                errors.append(f"Field '{key}' expects {expected_type}, got bool")
            elif not isinstance(value, python_types):
                errors.append(f"Field '{key}' expects {expected_type}, got {type(value).__name__}")
        else:  # noqa: PLR5501
            if not isinstance(value, python_types):
                errors.append(f"Field '{key}' expects {expected_type}, got {type(value).__name__}")

    if errors:
        raise ToolValidationError(tool_name, errors)
