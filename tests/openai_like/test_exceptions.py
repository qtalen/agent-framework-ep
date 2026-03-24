"""Tests for openai_like exceptions module."""

import pytest
from pydantic import BaseModel

from agent_framework_ep.openai_like._exceptions import StructuredOutputParseError


class DummyResponseFormat(BaseModel):
    """Dummy response format for testing."""

    name: str
    value: int


class TestStructuredOutputParseError:
    """Tests for StructuredOutputParseError exception."""

    def test_initialization(self) -> None:
        """Test error initialization with all parameters."""
        cause = ValueError("original error")
        raw_text = '{"name": "test", "value": 42}'

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)

        assert error.response_format == DummyResponseFormat
        assert error.raw_text == raw_text
        assert error.__cause__ is cause

    def test_error_message_formatting(self) -> None:
        """Test error message includes format name and cause."""
        cause = ValueError("invalid json")
        raw_text = '{"name": "test"}'

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)

        assert "Failed to parse response as DummyResponseFormat" in str(error)
        assert "Parse error: invalid json" in str(error)
        assert raw_text in str(error)

    def test_error_message_truncation_long_text(self) -> None:
        """Test raw text is truncated at 500 characters."""
        cause = ValueError("parse error")
        raw_text = "x" * 1000

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)
        message = str(error)

        assert "..." in message
        assert len(message.split("Raw response:\n")[-1]) <= 503  # 500 + "..."

    def test_error_message_no_truncation_short_text(self) -> None:
        """Test raw text is not truncated when under 500 characters."""
        cause = ValueError("parse error")
        raw_text = '{"name": "test"}'

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)
        message = str(error)

        assert "..." not in message.split("Raw response:")[-1]
        assert raw_text in message

    def test_error_message_exactly_500_chars(self) -> None:
        """Test raw text of exactly 500 characters is not truncated."""
        cause = ValueError("parse error")
        raw_text = "x" * 500

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)
        message = str(error)

        assert "..." not in message
        assert raw_text in message

    def test_repr(self) -> None:
        """Test __repr__ method formatting."""
        cause = ValueError("original error")
        raw_text = '{"name": "test"}'

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)
        repr_str = repr(error)

        assert "StructuredOutputParseError(" in repr_str
        assert "response_format='DummyResponseFormat'" in repr_str
        assert "raw_text_length=16" in repr_str
        assert "cause=" in repr_str

    def test_to_dict(self) -> None:
        """Test to_dict method returns expected structure."""
        cause = ValueError("original error")
        raw_text = '{"name": "test"}'

        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)
        result = error.to_dict()

        assert result == {
            "response_format": "DummyResponseFormat",
            "raw_text_length": 16,
            "cause": "original error",
            "cause_type": "ValueError",
        }

    def test_to_dict_with_different_cause_types(self) -> None:
        """Test to_dict with various exception types as cause."""
        test_cases = [
            (TypeError("type error"), "TypeError"),
            (KeyError("missing_key"), "KeyError"),
            (RuntimeError("runtime error"), "RuntimeError"),
        ]

        for cause, expected_type in test_cases:
            error = StructuredOutputParseError(DummyResponseFormat, "text", cause)
            result = error.to_dict()
            assert result["cause_type"] == expected_type

    def test_error_inheritance(self) -> None:
        """Test StructuredOutputParseError inherits from Exception."""
        assert issubclass(StructuredOutputParseError, Exception)

    def test_can_be_caught_as_exception(self) -> None:
        """Test error can be caught as generic Exception."""
        cause = ValueError("original")
        error = StructuredOutputParseError(DummyResponseFormat, "text", cause)

        try:
            raise error
        except Exception as e:
            assert e is error

    @pytest.mark.parametrize(
        "raw_text",
        [
            "",
            "single line",
            "multi\nline\ntext",
            '{"nested": {"value": 1}}',
        ],
    )
    def test_various_raw_text_formats(self, raw_text: str) -> None:
        """Test error handles various raw text formats."""
        cause = ValueError("error")
        error = StructuredOutputParseError(DummyResponseFormat, raw_text, cause)

        assert error.raw_text == raw_text
        assert error.response_format == DummyResponseFormat
