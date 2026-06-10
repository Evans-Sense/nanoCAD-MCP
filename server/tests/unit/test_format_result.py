"""Tests for _format_result and __label utility functions.

These are pure functions in server.py that format tool output for display.
"""

from __future__ import annotations

import src.presentation.server as srv


class TestFormatResult:
    """Format tool results for user display."""

    def test_format_none(self) -> None:
        assert srv._format_result(None) == "nil (no result)"

    def test_format_dict_success_false_with_error(self) -> None:
        assert srv._format_result({"success": False, "error": "fail"}) == "ERROR: fail"

    def test_format_dict_success_false_without_error(self) -> None:
        assert srv._format_result({"success": False}) == "ERROR: unknown error"

    def test_format_dict_success_true_empty(self) -> None:
        assert srv._format_result({"success": True}) == "OK"

    def test_format_dict_success_true_with_data(self) -> None:
        result = srv._format_result({"success": True, "handle": "H1", "type": "LINE"})
        assert "Handle: H1" in result
        assert "Type: LINE" in result
        assert "Success" not in result  # success stripped

    def test_format_general_dict(self) -> None:
        result = srv._format_result({"key1": "val1", "key2": 42})
        assert "Key1: val1" in result
        assert "Key2: 42" in result

    def test_format_empty_list(self) -> None:
        assert srv._format_result([]) == "(empty)"

    def test_format_list_with_items(self) -> None:
        result = srv._format_result(["item1", "item2"])
        assert "  1. item1" in result
        assert "  2. item2" in result

    def test_format_string(self) -> None:
        assert srv._format_result("hello") == "hello"

    def test_format_number(self) -> None:
        assert srv._format_result(42) == "42"


class TestLabel:
    """Map JSON keys to human-readable labels."""

    def test_known_labels(self) -> None:
        assert srv._label("handle") == "Handle"
        assert srv._label("name") == "Name"
        assert srv._label("version") == "Version"
        assert srv._label("is_saved") == "Saved"
        assert srv._label("entities_count") == "Entities"
        assert srv._label("layers_count") == "Layers"
        assert srv._label("blocks_count") == "Blocks"
        assert srv._label("active_documents") == "Active documents"
        assert srv._label("success") == "Success"
        assert srv._label("error") == "Error"
        assert srv._label("error_message") == "Error"
        assert srv._label("output") == "Result"
        assert srv._label("command") == "Command"
        assert srv._label("is_on") == "On"
        assert srv._label("is_frozen") == "Frozen"
        assert srv._label("is_locked") == "Locked"
        assert srv._label("color") == "Color"
        assert srv._label("value") == "Value"
        assert srv._label("type") == "Type"

    def test_unknown_label_capitalized(self) -> None:
        assert srv._label("custom_field") == "Custom_field"

    def test_empty_string_label(self) -> None:
        assert srv._label("") == ""
