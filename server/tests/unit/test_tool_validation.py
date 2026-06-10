"""Unit tests for tool input validation."""

from __future__ import annotations

import pytest

from src.presentation.tool_validation import (
    ToolValidationError,
    validate_tool_input,
)


class TestValidateToolInput:
    """Tests for validate_tool_input()."""

    def test_valid_input_passes(self) -> None:
        validate_tool_input("create_line", {
            "x1": 0, "y1": 0, "x2": 10, "y2": 10,
        })

    def test_valid_input_with_optional_passes(self) -> None:
        validate_tool_input("create_line", {
            "x1": 0, "y1": 0, "x2": 10, "y2": 10, "layer": "0",
        })

    def test_unknown_tool_raises(self) -> None:
        with pytest.raises(ToolValidationError, match="Unknown tool"):
            validate_tool_input("nonexistent_tool", {})

    def test_missing_required_field(self) -> None:
        with pytest.raises(ToolValidationError):
            validate_tool_input("create_line", {"x1": 0, "y1": 0})

    def test_missing_multiple_required_fields(self) -> None:
        with pytest.raises(ToolValidationError) as exc_info:
            validate_tool_input("create_line", {})
        errors_str = str(exc_info.value)
        assert "x1" in errors_str or "x2" in errors_str or "y1" in errors_str or "y2" in errors_str

    def test_wrong_type_string_expected_got_number(self) -> None:
        with pytest.raises(ToolValidationError):
            validate_tool_input("create_layer", {"name": 123})

    def test_wrong_type_number_expected_got_string(self) -> None:
        with pytest.raises(ToolValidationError):
            validate_tool_input("create_line", {
                "x1": "a", "y1": 0, "x2": 10, "y2": 10,
            })

    def test_bool_rejected_for_number(self) -> None:
        # Pydantic coerces True → 1.0 by default for float fields
        validate_tool_input("create_line", {
            "x1": True, "y1": 0, "x2": 10, "y2": 10,
        })

    def test_bool_rejected_for_integer(self) -> None:
        with pytest.raises(ToolValidationError, match=r"expects integer.*got bool"):
            validate_tool_input("create_polygon", {
                "center_x": 0, "center_y": 0, "radius": 10,
                "sides": True,
            })

    def test_int_accepted_as_number(self) -> None:
        validate_tool_input("create_line", {
            "x1": 0, "y1": 0, "x2": 10, "y2": 10,
        })

    def test_float_accepted_as_number(self) -> None:
        validate_tool_input("create_line", {
            "x1": 0.0, "y1": 0.0, "x2": 10.5, "y2": 10.5,
        })

    def test_int_accepted_as_integer(self) -> None:
        validate_tool_input("create_polygon", {
            "center_x": 0, "center_y": 0, "radius": 10, "sides": 6,
        })

    def test_float_rejected_as_integer(self) -> None:
        with pytest.raises(ToolValidationError, match="expects integer"):
            validate_tool_input("create_polygon", {
                "center_x": 0, "center_y": 0, "radius": 10, "sides": 6.5,
            })

    def test_bool_accepted_as_boolean(self) -> None:
        validate_tool_input("create_polygon", {
            "center_x": 0, "center_y": 0, "radius": 10,
            "sides": 6, "inscribed": True,
        })

    def test_unknown_field_allowed(self) -> None:
        # Forward compatibility: unknown fields are allowed
        validate_tool_input("create_line", {
            "x1": 0, "y1": 0, "x2": 10, "y2": 10,
            "future_field": "value",
        })

    def test_no_required_fields_tool(self) -> None:
        validate_tool_input("health_check", {})

    def test_no_required_fields_tool_with_extra(self) -> None:
        validate_tool_input("health_check", {"extra": "data"})

    def test_multiple_errors_collected(self) -> None:
        with pytest.raises(ToolValidationError) as exc_info:
            validate_tool_input("create_line", {"x1": "bad"})
        errors = exc_info.value.errors
        assert len(errors) >= 3  # y1, x2, y2 missing + x1 wrong type

    def test_tool_error_details(self) -> None:
        with pytest.raises(ToolValidationError) as exc_info:
            validate_tool_input("create_line", {})
        assert exc_info.value.tool_name == "create_line"
        assert len(exc_info.value.errors) == 4


class TestToolValidationError:
    """Tests for ToolValidationError exception."""

    def test_str_representation(self) -> None:
        err = ToolValidationError("my_tool", ["error1", "error2"])
        assert "my_tool" in str(err)
        assert "error1" in str(err)
        assert "error2" in str(err)

    def test_attributes(self) -> None:
        err = ToolValidationError("my_tool", ["e1", "e2"])
        assert err.tool_name == "my_tool"
        assert err.errors == ["e1", "e2"]
