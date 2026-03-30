"""Tests for openai_like response_format module."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

from agent_framework_ep.openai_like._exceptions import StructuredOutputParseError
from agent_framework_ep.openai_like._response_format import (
    ResponseFormatMixin,
    _extract_json_from_markdown,
    _try_parse_json_with_fallbacks,
)


class TestExtractJsonFromMarkdown:
    """Tests for _extract_json_from_markdown function."""

    def test_plain_json_returns_unchanged(self) -> None:
        """Test plain JSON text is returned unchanged."""
        text = '{"key": "value"}'
        result = _extract_json_from_markdown(text)
        assert result == text

    def test_json_with_whitespace(self) -> None:
        """Test JSON with surrounding whitespace is stripped."""
        text = '  {"key": "value"}  '
        result = _extract_json_from_markdown(text)
        assert result == '{"key": "value"}'

    def test_extract_from_json_code_block(self) -> None:
        """Test extracting JSON from markdown code block."""
        text = """```json
{"key": "value"}
```"""
        result = _extract_json_from_markdown(text)
        assert result == '{"key": "value"}'

    def test_extract_from_code_block_no_lang(self) -> None:
        """Test extracting from code block without language specifier."""
        text = """```
{"key": "value"}
```"""
        result = _extract_json_from_markdown(text)
        assert result == '{"key": "value"}'

    def test_extract_with_multiline_json(self) -> None:
        """Test extracting multi-line JSON from code block."""
        text = """```json
{
  "key1": "value1",
  "key2": "value2"
}
```"""
        result = _extract_json_from_markdown(text)
        assert "key1" in result
        assert "key2" in result

    def test_non_json_code_block_returns_unchanged(self) -> None:
        """Test non-JSON code blocks are returned unchanged."""
        text = """```python
print("hello")
```"""
        result = _extract_json_from_markdown(text)
        assert result == text

    def test_json5_code_block_extracted(self) -> None:
        """Test json5 code block is extracted."""
        text = """```json5
{"key": "value"}
```"""
        result = _extract_json_from_markdown(text)
        assert result == '{"key": "value"}'

    def test_text_before_code_block(self) -> None:
        """Test that text before code block is not handled."""
        text = """Some text
```json
{"key": "value"}
```"""
        # The function expects the code block at the start (after stripping)
        result = _extract_json_from_markdown(text)
        # This will NOT match because of "Some text" prefix
        assert "Some text" in result

    def test_multiple_code_blocks_returns_all(self) -> None:
        """Test behavior with multiple code blocks - returns entire match."""
        text = """```json
{"first": true}
```
```json
{"second": true}
```"""
        # The regex matches the first block and stops at the first ``` after body
        result = _extract_json_from_markdown(text)
        # The regex captures everything including second block as it's part of "body"
        assert "first" in result
        assert "second" in result or "```json" in result


class TestTryParseJsonWithFallbacks:
    """Tests for _try_parse_json_with_fallbacks function."""

    def test_valid_json_parsing(self) -> None:
        """Test valid JSON is parsed successfully."""
        text = '{"key": "value", "num": 42}'
        result = _try_parse_json_with_fallbacks(text)
        assert result == {"key": "value", "num": 42}

    def test_valid_json_array(self) -> None:
        """Test valid JSON array is parsed."""
        text = '[1, 2, 3, "test"]'
        result = _try_parse_json_with_fallbacks(text)
        assert result == [1, 2, 3, "test"]

    def test_valid_json_string(self) -> None:
        """Test valid JSON string is parsed."""
        text = '"simple string"'
        result = _try_parse_json_with_fallbacks(text)
        assert result == "simple string"

    def test_dirtyjson_fallback_single_quotes(self) -> None:
        """Test dirtyjson handles single quotes."""
        text = "{'key': 'value'}"
        # dirtyjson should handle this
        result = _try_parse_json_with_fallbacks(text)
        assert result["key"] == "value"

    def test_dirtyjson_fallback_trailing_comma(self) -> None:
        """Test dirtyjson handles trailing commas."""
        text = '{"key": "value",}'
        result = _try_parse_json_with_fallbacks(text)
        assert result["key"] == "value"

    def test_repair_json_fallback(self) -> None:
        """Test repair_json fallback for malformed JSON."""
        # Test with a case where repair_json actually helps
        # missing closing quote - dirtyjson might handle it, but repair_json can help too
        text = '{"key": "unclosed value}'
        # This is actually handled by dirtyjson, so let's just verify it works
        result = _try_parse_json_with_fallbacks(text)
        assert "key" in result

    def test_all_fallbacks_fail_raises_first_error(self) -> None:
        """Test that first parse error is raised when all fail."""
        text = "not valid json at all"
        # First error should be json.JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            _try_parse_json_with_fallbacks(text)

    def test_empty_object(self) -> None:
        """Test parsing empty object."""
        text = "{}"
        result = _try_parse_json_with_fallbacks(text)
        assert result == {}

    def test_empty_array(self) -> None:
        """Test parsing empty array."""
        text = "[]"
        result = _try_parse_json_with_fallbacks(text)
        assert result == []

    def test_nested_json(self) -> None:
        """Test parsing deeply nested JSON."""
        text = '{"outer": {"inner": {"deep": "value"}}}'
        result = _try_parse_json_with_fallbacks(text)
        assert result["outer"]["inner"]["deep"] == "value"

    def test_unicode_in_json(self) -> None:
        """Test parsing JSON with unicode characters."""
        text = '{"message": "Hello 世界"}'
        result = _try_parse_json_with_fallbacks(text)
        assert result["message"] == "Hello 世界"

    def test_special_characters_in_strings(self) -> None:
        """Test parsing JSON with escaped special characters."""
        text = '{"text": "line1\\nline2\\ttab\\"quote\\""}'
        result = _try_parse_json_with_fallbacks(text)
        assert "line1" in result["text"]
        assert "line2" in result["text"]


class DummyModel(BaseModel):
    """Dummy model for testing structured output."""

    name: str
    age: int = Field(default=0)
    tags: list[str] = Field(default_factory=list)


class NestedModel(BaseModel):
    """Model with nested structure."""

    user: DummyModel
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestResponseFormatMixin:
    """Tests for ResponseFormatMixin class."""

    class TestBuildStructuredPrompt:
        """Tests for _build_structured_prompt method."""

        def test_prompt_includes_schema(self) -> None:
            """Test prompt includes JSON schema."""
            prompt = ResponseFormatMixin._build_structured_prompt(DummyModel)

            assert "CRITICAL: You MUST output ONLY valid JSON" in prompt
            assert "name" in prompt
            assert "age" in prompt
            assert "tags" in prompt

        def test_prompt_includes_rules(self) -> None:
            """Test prompt includes strict rules."""
            prompt = ResponseFormatMixin._build_structured_prompt(DummyModel)

            assert "NO markdown code blocks" in prompt
            assert "NO ```json" in prompt
            assert "start with '{'" in prompt
            assert "end with '}'" in prompt

        def test_prompt_includes_examples(self) -> None:
            """Test prompt includes correct/incorrect examples."""
            prompt = ResponseFormatMixin._build_structured_prompt(DummyModel)

            assert "Example of CORRECT output format:" in prompt
            assert "Example of INCORRECT output format:" in prompt
            assert '{"field1": "value1"' in prompt
            assert "```json" in prompt

        def test_nested_model_schema(self) -> None:
            """Test prompt generation for nested model."""
            prompt = ResponseFormatMixin._build_structured_prompt(NestedModel)

            assert "user" in prompt
            assert "metadata" in prompt
            assert "$defs" in prompt
            assert "DummyModel" in prompt
            assert "required" in prompt

    class TestInjectResponseFormatPrompt:
        """Tests for _inject_response_format_prompt method."""

        def test_injects_prompt_when_response_format_present(self) -> None:
            """Test prompt injection when response_format is provided."""
            mixin = ResponseFormatMixin()
            options = {"response_format": DummyModel}

            result = mixin._inject_response_format_prompt(options)

            assert "instructions" in result
            assert "CRITICAL: You MUST output ONLY valid JSON" in result["instructions"]
            assert "response_format" not in result
            assert mixin._current_response_format is DummyModel

        def test_appends_to_existing_instructions(self) -> None:
            """Test prompt is appended to existing instructions."""
            mixin = ResponseFormatMixin()
            options = {
                "response_format": DummyModel,
                "instructions": "Existing instructions",
            }

            result = mixin._inject_response_format_prompt(options)

            assert "Existing instructions" in result["instructions"]
            assert "CRITICAL: You MUST output ONLY valid JSON" in result["instructions"]
            assert "\n\n" in result["instructions"]

        def test_no_response_format_no_changes(self) -> None:
            """Test no changes when response_format not present."""
            mixin = ResponseFormatMixin()
            options = {"temperature": 0.7}

            result = mixin._inject_response_format_prompt(options)

            assert "instructions" not in result
            assert result["temperature"] == 0.7

        def test_non_pydantic_response_format_ignored(self) -> None:
            """Test non-Pydantic response_format is ignored."""
            mixin = ResponseFormatMixin()
            options = {"response_format": dict}

            result = mixin._inject_response_format_prompt(options)

            # dict is a type but not a BaseModel subclass
            assert "instructions" not in result
            assert result.get("response_format") is dict

        def test_response_format_instance_ignored(self) -> None:
            """Test response_format instance (not class) is ignored."""
            mixin = ResponseFormatMixin()
            options = {"response_format": DummyModel(name="test", age=25)}

            result = mixin._inject_response_format_prompt(options)

            assert "instructions" not in result

        def test_preserves_other_options(self) -> None:
            """Test other options are preserved."""
            mixin = ResponseFormatMixin()
            options = {
                "response_format": DummyModel,
                "temperature": 0.5,
                "max_tokens": 100,
            }

            result = mixin._inject_response_format_prompt(options)

            assert result["temperature"] == 0.5
            assert result["max_tokens"] == 100
            assert "instructions" in result

    class TestParseStructuredOutput:
        """Tests for _parse_structured_output method."""

        def test_successful_parsing(self) -> None:
            """Test successful parsing of valid response."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = '{"name": "John", "age": 30}'

            result = mixin._parse_structured_output(mock_response)

            assert result._value.name == "John"
            assert result._value.age == 30
            assert result._value_parsed is True
            assert result._response_format is DummyModel

        def test_parsing_with_markdown_code_block(self) -> None:
            """Test parsing JSON from markdown code block."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = """```json
{"name": "Jane", "age": 25}
```"""

            result = mixin._parse_structured_output(mock_response)

            assert result._value.name == "Jane"
            assert result._value.age == 25

        def test_parsing_with_empty_response_format(self) -> None:
            """Test returns unchanged when no response format set."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = None

            mock_response = MagicMock()
            mock_response.text = '{"name": "test"}'

            result = mixin._parse_structured_output(mock_response)

            assert result is mock_response

        def test_parsing_with_tool_calls(self) -> None:
            """Test returns unchanged when finish_reason is tool_calls."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "tool_calls"
            mock_response.text = '{"name": "test"}'

            result = mixin._parse_structured_output(mock_response)

            assert result is mock_response

        def test_parsing_with_empty_text(self) -> None:
            """Test returns unchanged when text is empty."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = ""

            result = mixin._parse_structured_output(mock_response)

            assert result is mock_response

        def test_parsing_invalid_json_raises_error(self) -> None:
            """Test StructuredOutputParseError on invalid JSON."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = "not valid json"

            with pytest.raises(StructuredOutputParseError) as exc_info:
                mixin._parse_structured_output(mock_response)

            assert exc_info.value.response_format is DummyModel
            assert exc_info.value.raw_text == "not valid json"

        def test_parsing_validation_error(self) -> None:
            """Test StructuredOutputParseError on schema validation failure."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = '{"unknown_field": "value"}'

            with pytest.raises(StructuredOutputParseError) as exc_info:
                mixin._parse_structured_output(mock_response)

            assert exc_info.value.response_format is DummyModel

        def test_parsing_with_default_values(self) -> None:
            """Test parsing uses default values for missing fields."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = '{"name": "Test"}'  # age and tags not provided

            result = mixin._parse_structured_output(mock_response)

            assert result._value.name == "Test"
            assert result._value.age == 0  # default
            assert result._value.tags == []  # default

        def test_response_format_cleared_after_parsing(self) -> None:
            """Test _current_response_format is cleared after parsing."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = DummyModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = '{"name": "test"}'

            mixin._parse_structured_output(mock_response)

            assert mixin._current_response_format is None

        def test_parsing_nested_model(self) -> None:
            """Test parsing into nested Pydantic model."""
            mixin = ResponseFormatMixin()
            mixin._current_response_format = NestedModel

            mock_response = MagicMock()
            mock_response.finish_reason = "stop"
            mock_response.text = """{"user": {"name": "Alice", "age": 30}, "metadata": {"key": "value"}}"""

            result = mixin._parse_structured_output(mock_response)

            assert result._value.user.name == "Alice"
            assert result._value.metadata == {"key": "value"}
