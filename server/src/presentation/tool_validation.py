"""Input validation for MCP tool calls.

Validates tool arguments against Pydantic models (when available)
or JSON Schema as a fallback. All validation happens before use case handlers.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError as PydanticValidationError

from src.presentation.tool_defs import TOOL_DEFS
from src.presentation.tool_models import get_model

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

    Tries Pydantic model validation first (for type/range checks),
    then falls back to JSON Schema validation if no model is registered.

    Raises ToolValidationError if validation fails.
    """
    model_cls = get_model(tool_name)
    if model_cls is not None:
        # Pydantic validation with type coercion and range checks
        try:
            model_cls(**arguments)
        except PydanticValidationError as e:
            errors = _format_pydantic_errors(e)
            raise ToolValidationError(tool_name, errors) from e
        return

    # Fallback: JSON Schema validation
    _validate_schema(tool_name, arguments)


def _format_pydantic_errors(exc: PydanticValidationError) -> list[str]:
    """Convert Pydantic errors to user-friendly message list."""
    errors: list[str] = []
    for err in exc.errors():
        loc = " → ".join(str(l) for l in err["loc"])
        msg = err["msg"]
        errors.append(f"'{loc}': {msg}")
    return errors


def _validate_schema(tool_name: str, arguments: dict[str, Any]) -> None:
    """JSON Schema fallback validation."""
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
            continue

        prop = properties[key]
        expected_type = prop.get("type")
        if expected_type is None:
            continue

        python_types = _TYPE_MAP.get(expected_type)
        if python_types is None:
            continue

        if expected_type == "number" or expected_type == "integer":
            if isinstance(value, bool):
                errors.append(f"Field '{key}' expects {expected_type}, got bool")
            elif not isinstance(value, python_types):
                errors.append(f"Field '{key}' expects {expected_type}, got {type(value).__name__}")
        else:  # noqa: PLR5501
            if not isinstance(value, python_types):
                errors.append(f"Field '{key}' expects {expected_type}, got {type(value).__name__}")

    if errors:
        raise ToolValidationError(tool_name, errors)
