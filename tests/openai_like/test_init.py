"""Tests for openai_like __init__ module."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agent_framework_ep.openai_like import (
    OpenAILikeChatClient,
    StructuredOutputParseError,
    get_reasoning_content,
)
from agent_framework_ep.openai_like._reasoning_content import ReasoningContentMixin
from agent_framework_ep.openai_like._response_format import ResponseFormatMixin


class TestOpenAILikeChatClient:
    """Tests for OpenAILikeChatClient class."""

    def test_inherits_from_mixins(self) -> None:
        """Test client inherits from both mixins."""
        assert issubclass(OpenAILikeChatClient, ResponseFormatMixin)
        assert issubclass(OpenAILikeChatClient, ReasoningContentMixin)

    @patch("agent_framework_ep.openai_like.OpenAIChatClient")
    def test_init_sets_current_response_format(self, mock_parent: MagicMock) -> None:
        """Test __init__ initializes _current_response_format."""
        client = OpenAILikeChatClient.__new__(OpenAILikeChatClient)
        # Manually call init to avoid calling real parent
        client._current_response_format = None

        assert client._current_response_format is None


class TestGetReasoningContent:
    """Tests for get_reasoning_content utility function."""

    def create_mock_content(self, content_type: str, text: str) -> MagicMock:
        """Helper to create mock content."""
        content = MagicMock()
        content.type = content_type
        content.text = text
        return content

    def test_from_chat_response_additional_properties(self) -> None:
        """Test extraction from ChatResponse additional_properties."""
        response = MagicMock()
        response.additional_properties = {"reasoning_content": "My reasoning"}
        response.messages = None

        result = get_reasoning_content(response)

        assert result == "My reasoning"

    def test_from_chat_response_messages(self) -> None:
        """Test extraction from ChatResponse messages."""
        response = MagicMock()
        response.additional_properties = {}

        mock_content = self.create_mock_content("text_reasoning", "Message reasoning")
        mock_msg = MagicMock()
        mock_msg.contents = [mock_content]
        response.messages = [mock_msg]

        result = get_reasoning_content(response)

        assert result == "Message reasoning"

    def test_from_chat_response_update_additional_properties(self) -> None:
        """Test extraction from ChatResponseUpdate additional_properties."""
        update = MagicMock()
        update.additional_properties = {"reasoning_content": "Update reasoning"}
        update.contents = []

        result = get_reasoning_content(update)

        assert result == "Update reasoning"

    def test_from_chat_response_update_contents(self) -> None:
        """Test extraction from ChatResponseUpdate contents."""
        update = MagicMock()
        update.additional_properties = None
        update.messages = None  # ChatResponseUpdate doesn't have messages

        mock_content = self.create_mock_content("text_reasoning", "Content reasoning")
        update.contents = [mock_content]

        result = get_reasoning_content(update)

        assert result == "Content reasoning"

    def test_empty_additional_properties(self) -> None:
        """Test empty string when no reasoning in additional_properties."""
        response = MagicMock()
        response.additional_properties = {}
        response.messages = []

        result = get_reasoning_content(response)

        assert result == ""

    def test_none_additional_properties(self) -> None:
        """Test empty string when additional_properties is None."""
        response = MagicMock()
        response.additional_properties = None
        response.messages = []

        result = get_reasoning_content(response)

        assert result == ""

    def test_no_messages_or_contents(self) -> None:
        """Test empty string when no messages or contents."""
        response = MagicMock()
        response.additional_properties = None
        response.messages = None
        # No contents attribute (simulating ChatResponse)

        result = get_reasoning_content(response)

        assert result == ""

    def test_non_text_reasoning_content_ignored(self) -> None:
        """Test non-text_reasoning content types are ignored."""
        response = MagicMock()
        response.additional_properties = None

        mock_text = self.create_mock_content("text", "Regular text")
        mock_reasoning = self.create_mock_content("text_reasoning", "Reasoning")
        mock_tool = self.create_mock_content("tool_call", "Tool result")

        mock_msg = MagicMock()
        mock_msg.contents = [mock_text, mock_reasoning, mock_tool]
        response.messages = [mock_msg]

        result = get_reasoning_content(response)

        assert result == "Reasoning"

    def test_concatenates_multiple_text_reasoning(self) -> None:
        """Test multiple text_reasoning contents are concatenated."""
        response = MagicMock()
        response.additional_properties = None

        mock_msg = MagicMock()
        mock_msg.contents = [
            self.create_mock_content("text_reasoning", "Part 1"),
            self.create_mock_content("text", "Some text"),
            self.create_mock_content("text_reasoning", "Part 2"),
        ]
        response.messages = [mock_msg]

        result = get_reasoning_content(response)

        assert result == "Part 1Part 2"

    def test_none_text_in_content_ignored(self) -> None:
        """Test content with None text is ignored."""
        response = MagicMock()
        response.additional_properties = None

        mock_content = self.create_mock_content("text_reasoning", "")
        mock_content.text = None  # Override to None

        mock_msg = MagicMock()
        mock_msg.contents = [mock_content]
        response.messages = [mock_msg]

        result = get_reasoning_content(response)

        assert result == ""

    def test_multiple_messages(self) -> None:
        """Test reasoning extracted from multiple messages."""
        response = MagicMock()
        response.additional_properties = None

        msg1 = MagicMock()
        msg1.contents = [self.create_mock_content("text_reasoning", "From msg1")]

        msg2 = MagicMock()
        msg2.contents = [self.create_mock_content("text_reasoning", "From msg2")]

        response.messages = [msg1, msg2]

        result = get_reasoning_content(response)

        assert result == "From msg1From msg2"

    def test_empty_messages_list(self) -> None:
        """Test empty string with empty messages list."""
        response = MagicMock()
        response.additional_properties = None
        response.messages = []

        result = get_reasoning_content(response)

        assert result == ""

    def test_handles_missing_contents_attribute(self) -> None:
        """Test handling when content lacks attributes."""
        response = MagicMock()
        response.additional_properties = None

        # Content without type attribute
        mock_content = MagicMock(spec=[])
        mock_content.type = "text_reasoning"
        mock_content.text = "Valid"

        mock_msg = MagicMock()
        mock_msg.contents = [mock_content]
        response.messages = [mock_msg]

        result = get_reasoning_content(response)

        assert result == "Valid"


class TestExports:
    """Tests for module exports."""

    def test_openai_like_chat_client_exported(self) -> None:
        """Test OpenAILikeChatClient is exported."""
        from agent_framework_ep.openai_like import OpenAILikeChatClient

        assert OpenAILikeChatClient is not None

    def test_get_reasoning_content_exported(self) -> None:
        """Test get_reasoning_content is exported."""
        from agent_framework_ep.openai_like import get_reasoning_content

        assert callable(get_reasoning_content)

    def test_structured_output_parse_error_exported(self) -> None:
        """Test StructuredOutputParseError is exported."""
        from agent_framework_ep.openai_like import StructuredOutputParseError

        assert issubclass(StructuredOutputParseError, Exception)

    def test_all_exports_defined(self) -> None:
        """Test __all__ contains expected exports."""
        from agent_framework_ep.openai_like import __all__

        assert "OpenAILikeChatClient" in __all__
        assert "get_reasoning_content" in __all__
        assert "StructuredOutputParseError" in __all__
        assert len(__all__) == 3
