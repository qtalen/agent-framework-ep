"""Tests for openai_like reasoning_content module."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agent_framework_ep.openai_like._reasoning_content import (
    ReasoningContentMixin,
    _set_additional_property,
)


class TestSetAdditionalProperty:
    """Tests for _set_additional_property function."""

    def test_sets_property_when_none_exists(self) -> None:
        """Test property is set when additional_properties is None."""
        obj = MagicMock()
        obj.additional_properties = None

        _set_additional_property(obj, "key", "value")

        assert obj.additional_properties == {"key": "value"}

    def test_adds_to_existing_properties(self) -> None:
        """Test property is added to existing properties."""
        obj = MagicMock()
        obj.additional_properties = {"existing": "value"}

        _set_additional_property(obj, "new_key", "new_value")

        assert obj.additional_properties == {
            "existing": "value",
            "new_key": "new_value",
        }

    def test_overwrites_existing_key(self) -> None:
        """Test that existing key is overwritten."""
        obj = MagicMock()
        obj.additional_properties = {"key": "old_value"}

        _set_additional_property(obj, "key", "new_value")

        assert obj.additional_properties["key"] == "new_value"


class TestPropagateReasoningInMessages:
    """Tests for _propagate_reasoning_in_messages method."""

    def test_no_messages_returns_empty(self) -> None:
        """Test empty messages list returns empty."""
        mixin = ReasoningContentMixin()
        result = mixin._propagate_reasoning_in_messages([])
        assert result == []

    def test_non_assistant_messages_ignored(self) -> None:
        """Test non-assistant messages don't affect propagation."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "system", "content": "System prompt"},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result == messages

    def test_reasoning_captured_without_tool_calls(self) -> None:
        """Test reasoning is captured from assistant messages without tool_calls."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "content": "Hello", "reasoning_content": "Thinking..."},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result[0]["reasoning_content"] == "Thinking..."

    def test_reasoning_propagated_to_tool_call_message(self) -> None:
        """Test reasoning is propagated to message with tool_calls."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "content": "Let me think", "reasoning_content": "Step 1..."},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "1"}]},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result[1].get("reasoning_content") == "Step 1..."

    def test_reasoning_details_alternative_field(self) -> None:
        """Test reasoning_details field is used as alternative."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "reasoning_details": "Detailed thinking..."},
            {"role": "assistant", "tool_calls": [{"id": "1"}]},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result[1].get("reasoning_content") == "Detailed thinking..."

    def test_existing_reasoning_not_overwritten(self) -> None:
        """Test existing reasoning_content is not overwritten."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "reasoning_content": "First thought"},
            {"role": "assistant", "reasoning_content": "Existing", "tool_calls": [{"id": "1"}]},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result[1]["reasoning_content"] == "Existing"

    def test_multiple_tool_calls_reset_propagation(self) -> None:
        """Test propagation resets after tool_calls message."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "reasoning_content": "First"},
            {"role": "assistant", "tool_calls": [{"id": "1"}]},
            {"role": "assistant", "tool_calls": [{"id": "2"}]},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result[1].get("reasoning_content") == "First"
        assert result[2].get("reasoning_content") is None

    def test_user_message_resets_propagation(self) -> None:
        """Test user message resets pending reasoning."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "reasoning_content": "Thinking"},
            {"role": "user", "content": "Question?"},
            {"role": "assistant", "tool_calls": [{"id": "1"}]},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        assert result[2].get("reasoning_content") is None

    def test_deep_copy_preserves_original(self) -> None:
        """Test original messages are not modified."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "reasoning_content": "Original"},
        ]
        result = mixin._propagate_reasoning_in_messages(messages)
        result[0]["reasoning_content"] = "Modified"
        assert messages[0]["reasoning_content"] == "Original"


class MockContent:
    """Mock Content class for testing."""

    def __init__(self, content_type: str, text: str | None = None, protected_data: Any = None):
        self.type = content_type
        self.text = text
        self.protected_data = protected_data

    @classmethod
    def from_text_reasoning(cls, text: str) -> "MockContent":
        return cls("text_reasoning", text=text)


@pytest.fixture
def mock_message_class():
    """Fixture to patch Message class."""
    with patch("agent_framework_ep.openai_like._reasoning_content.Message") as mock_msg_cls:

        def create_mock_message(**kwargs):
            msg = MagicMock()
            for key, value in kwargs.items():
                setattr(msg, key, value)
            return msg

        mock_msg_cls.side_effect = create_mock_message
        yield mock_msg_cls


class TestExtractReasoningFromMessage:
    """Tests for _extract_reasoning_from_message method."""

    def create_mock_message(
        self,
        contents: list[MockContent],
        additional_props: dict[str, Any] | None = None,
    ) -> MagicMock:
        """Helper to create mock message."""
        msg = MagicMock()
        msg.role = "assistant"
        msg.contents = contents
        msg.author_name = None
        msg.additional_properties = additional_props or {}
        return msg

    def test_no_text_reasoning_returns_unchanged(self, mock_message_class) -> None:
        """Test message without text_reasoning is unchanged."""
        mixin = ReasoningContentMixin()
        contents = [MockContent("text", "Hello")]
        message = self.create_mock_message(contents)

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        assert reasoning is None
        assert len(result_msg.contents) == 1
        mock_message_class.assert_not_called()

    def test_extracts_text_reasoning_content(self, mock_message_class) -> None:
        """Test text_reasoning content is extracted."""
        mixin = ReasoningContentMixin()
        contents = [
            MockContent("text_reasoning", "Thinking step 1"),
            MockContent("text", "Final answer"),
        ]
        message = self.create_mock_message(contents)

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        assert reasoning == "Thinking step 1"
        mock_message_class.assert_called_once()

    def test_concatenates_multiple_text_reasoning(self, mock_message_class) -> None:
        """Test multiple text_reasoning contents are concatenated."""
        mixin = ReasoningContentMixin()
        contents = [
            MockContent("text_reasoning", "Part 1"),
            MockContent("text", "Answer"),
            MockContent("text_reasoning", "Part 2"),
        ]
        message = self.create_mock_message(contents)

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        assert reasoning == "Part 1Part 2"
        mock_message_class.assert_called_once()

    def test_skips_protected_text_reasoning(self, mock_message_class) -> None:
        """Test text_reasoning with protected_data is kept in message."""
        mixin = ReasoningContentMixin()
        contents = [
            MockContent("text_reasoning", "Protected thought", protected_data={}),
            MockContent("text", "Answer"),
        ]
        message = self.create_mock_message(contents)

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        # Protected content is NOT extracted as reasoning
        assert reasoning is None
        # But Message is still recreated (filtering happened since content types differ)
        mock_message_class.assert_called_once()

    def test_extracts_from_additional_properties(self) -> None:
        """Test reasoning from additional_properties."""
        mixin = ReasoningContentMixin()
        contents = [MockContent("text", "Answer")]
        message = self.create_mock_message(contents, {"reasoning_content": "From props"})

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        assert reasoning == "From props"

    def test_combines_additional_props_and_contents(self, mock_message_class) -> None:
        """Test reasoning from both sources is combined correctly."""
        mixin = ReasoningContentMixin()
        contents = [MockContent("text_reasoning", "From content")]
        message = self.create_mock_message(contents, {"reasoning_content": "From props "})

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        assert reasoning == "From props From content"

    def test_empty_reasoning_content_ignored(self, mock_message_class) -> None:
        """Test empty text_reasoning content is not extracted (falsy check)."""
        mixin = ReasoningContentMixin()
        contents = [
            MockContent("text_reasoning", ""),  # Empty string is falsy
            MockContent("text", "Answer"),
        ]
        message = self.create_mock_message(contents)

        result_msg, reasoning = mixin._extract_reasoning_from_message(message)

        # Empty string is falsy, so not extracted as reasoning
        assert reasoning is None
        # Message is recreated because filtering happened
        mock_message_class.assert_called_once()


class TestInjectReasoningToOpenAiMessage:
    """Tests for _inject_reasoning_to_openai_message method."""

    def test_no_reasoning_no_changes(self) -> None:
        """Test no changes when reasoning is None."""
        mixin = ReasoningContentMixin()
        messages = [{"role": "assistant", "content": "Hello"}]

        mixin._inject_reasoning_to_openai_message(messages, None)

        assert "reasoning_content" not in messages[0]

    def test_injects_into_last_assistant_with_content(self) -> None:
        """Test reasoning injected into last assistant message with content."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]

        mixin._inject_reasoning_to_openai_message(messages, "My reasoning")

        assert messages[1]["reasoning_content"] == "My reasoning"

    def test_injects_into_message_with_tool_calls(self) -> None:
        """Test reasoning injected into message with tool_calls."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "tool_calls": [{"id": "1"}]},
        ]

        mixin._inject_reasoning_to_openai_message(messages, "Tool reasoning")

        assert messages[0]["reasoning_content"] == "Tool reasoning"

    def test_skips_non_assistant_messages(self) -> None:
        """Test non-assistant messages are skipped."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        mixin._inject_reasoning_to_openai_message(messages, "Reasoning")

        assert "reasoning_content" not in messages[0]
        assert messages[1]["reasoning_content"] == "Reasoning"

    def test_empty_messages_list(self) -> None:
        """Test empty message list is handled gracefully."""
        mixin = ReasoningContentMixin()

        # Should not raise
        mixin._inject_reasoning_to_openai_message([], "Reasoning")

    def test_injects_into_only_assistant_message(self) -> None:
        """Test reasoning injected when only assistant messages exist."""
        mixin = ReasoningContentMixin()
        messages = [
            {"role": "assistant", "content": "First"},
            {"role": "assistant", "content": "Last"},
        ]

        mixin._inject_reasoning_to_openai_message(messages, "Final reasoning")

        # Should inject into the last one with content
        assert messages[1]["reasoning_content"] == "Final reasoning"


class TestExtractReasoningFromResponse:
    """Tests for _extract_reasoning_from_response method."""

    def create_mock_choice(self, reasoning_content: str | None = None) -> MagicMock:
        """Helper to create mock choice."""
        choice = MagicMock()
        choice.message = MagicMock()
        choice.message.reasoning_content = reasoning_content
        return choice

    def create_mock_response(self, choices: list[MagicMock]) -> MagicMock:
        """Helper to create mock response."""
        response = MagicMock()
        response.choices = choices
        return response

    def create_mock_chat_response(self, messages: list[MagicMock]) -> MagicMock:
        """Helper to create mock chat response."""
        chat_response = MagicMock()
        chat_response.messages = messages
        chat_response.additional_properties = None
        return chat_response

    def test_no_reasoning_content(self) -> None:
        """Test response without reasoning_content is unchanged."""
        mixin = ReasoningContentMixin()
        choice = self.create_mock_choice(None)
        response = self.create_mock_response([choice])
        chat_response = self.create_mock_chat_response([])

        result = mixin._extract_reasoning_from_response(response, chat_response)

        assert result.additional_properties is None

    def test_extracts_single_reasoning_content(self) -> None:
        """Test single reasoning_content is extracted."""
        mixin = ReasoningContentMixin()
        choice = self.create_mock_choice("My reasoning")
        response = self.create_mock_response([choice])
        chat_response = self.create_mock_chat_response([])

        result = mixin._extract_reasoning_from_response(response, chat_response)

        assert result.additional_properties["reasoning_content"] == "My reasoning"

    def test_concatenates_multiple_reasoning_contents(self) -> None:
        """Test multiple reasoning_contents are concatenated."""
        mixin = ReasoningContentMixin()
        choices = [
            self.create_mock_choice("Part 1"),
            self.create_mock_choice("Part 2"),
        ]
        response = self.create_mock_response(choices)
        chat_response = self.create_mock_chat_response([])

        result = mixin._extract_reasoning_from_response(response, chat_response)

        assert result.additional_properties["reasoning_content"] == "Part 1Part 2"

    def test_adds_content_to_message_if_not_present(self) -> None:
        """Test Content is added to message if reasoning not already present."""
        mixin = ReasoningContentMixin()
        choice = self.create_mock_choice("New reasoning")
        response = self.create_mock_response([choice])

        mock_msg = MagicMock()
        mock_msg.contents = []
        chat_response = self.create_mock_chat_response([mock_msg])

        with patch("agent_framework_ep.openai_like._reasoning_content.Content") as MockContentClass:
            MockContentClass.from_text_reasoning.return_value = MagicMock(type="text_reasoning")

            mixin._extract_reasoning_from_response(response, chat_response)

            MockContentClass.from_text_reasoning.assert_called_once_with(text="New reasoning")
            assert len(mock_msg.contents) == 1

    def test_skips_adding_if_already_present(self) -> None:
        """Test Content is not added if reasoning already in message."""
        mixin = ReasoningContentMixin()
        choice = self.create_mock_choice("Duplicate reasoning")
        response = self.create_mock_response([choice])

        mock_content = MagicMock()
        mock_content.type = "text_reasoning"
        mock_content.text = "Duplicate reasoning"

        mock_msg = MagicMock()
        mock_msg.contents = [mock_content]
        chat_response = self.create_mock_chat_response([mock_msg])

        with patch("agent_framework_ep.openai_like._reasoning_content.Content") as MockContentClass:
            mixin._extract_reasoning_from_response(response, chat_response)
            MockContentClass.from_text_reasoning.assert_not_called()


class TestExtractReasoningFromUpdate:
    """Tests for _extract_reasoning_from_update method."""

    def create_mock_delta(self, reasoning_content: str | None = None) -> MagicMock:
        """Helper to create mock delta."""
        delta = MagicMock()
        delta.reasoning_content = reasoning_content
        return delta

    def create_mock_choice(self, delta: MagicMock) -> MagicMock:
        """Helper to create mock choice."""
        choice = MagicMock()
        choice.delta = delta
        return choice

    def create_mock_chunk(self, choices: list[MagicMock]) -> MagicMock:
        """Helper to create mock chunk."""
        chunk = MagicMock()
        chunk.choices = choices
        return chunk

    def create_mock_update(self) -> MagicMock:
        """Helper to create mock update."""
        update = MagicMock()
        update.contents = []
        update.additional_properties = None
        return update

    def test_no_reasoning_in_chunk(self) -> None:
        """Test update unchanged when chunk has no reasoning."""
        mixin = ReasoningContentMixin()
        delta = self.create_mock_delta(None)
        choice = self.create_mock_choice(delta)
        chunk = self.create_mock_chunk([choice])
        update = self.create_mock_update()

        result = mixin._extract_reasoning_from_update(chunk, update)

        assert result.additional_properties is None
        assert result.contents == []

    def test_extracts_reasoning_from_delta(self) -> None:
        """Test reasoning_content from delta is extracted."""
        mixin = ReasoningContentMixin()
        delta = self.create_mock_delta("Stream reasoning")
        choice = self.create_mock_choice(delta)
        chunk = self.create_mock_chunk([choice])
        update = self.create_mock_update()

        with patch("agent_framework_ep.openai_like._reasoning_content.Content") as MockContentClass:
            MockContentClass.from_text_reasoning.return_value = MagicMock(type="text_reasoning")

            result = mixin._extract_reasoning_from_update(chunk, update)

            MockContentClass.from_text_reasoning.assert_called_once_with(text="Stream reasoning")
            assert result.additional_properties["reasoning_content"] == "Stream reasoning"

    def test_concatenates_multiple_deltas(self) -> None:
        """Test reasoning from multiple choices is concatenated."""
        mixin = ReasoningContentMixin()
        choices = [
            self.create_mock_choice(self.create_mock_delta("Part 1")),
            self.create_mock_choice(self.create_mock_delta("Part 2")),
        ]
        chunk = self.create_mock_chunk(choices)
        update = self.create_mock_update()

        with patch("agent_framework_ep.openai_like._reasoning_content.Content") as MockContentClass:
            MockContentClass.from_text_reasoning.return_value = MagicMock(type="text_reasoning")

            result = mixin._extract_reasoning_from_update(chunk, update)

            assert result.additional_properties["reasoning_content"] == "Part 1Part 2"
            assert MockContentClass.from_text_reasoning.call_count == 2

    def test_appends_content_to_update(self) -> None:
        """Test content is appended to update.contents."""
        mixin = ReasoningContentMixin()
        delta = self.create_mock_delta("Thinking...")
        choice = self.create_mock_choice(delta)
        chunk = self.create_mock_chunk([choice])

        update = self.create_mock_update()
        existing_content = MagicMock(type="text")
        update.contents = [existing_content]

        with patch("agent_framework_ep.openai_like._reasoning_content.Content") as MockContentClass:
            mock_reasoning = MagicMock(type="text_reasoning")
            MockContentClass.from_text_reasoning.return_value = mock_reasoning

            result = mixin._extract_reasoning_from_update(chunk, update)

            assert len(result.contents) == 2
            assert result.contents[0] is existing_content
            assert result.contents[1] is mock_reasoning

    def test_mixed_reasoning_and_non_reasoning_choices(self) -> None:
        """Test handling mix of choices with and without reasoning."""
        mixin = ReasoningContentMixin()
        choices = [
            self.create_mock_choice(self.create_mock_delta(None)),
            self.create_mock_choice(self.create_mock_delta("Some reasoning")),
        ]
        chunk = self.create_mock_chunk(choices)
        update = self.create_mock_update()

        with patch("agent_framework_ep.openai_like._reasoning_content.Content") as MockContentClass:
            MockContentClass.from_text_reasoning.return_value = MagicMock(type="text_reasoning")

            result = mixin._extract_reasoning_from_update(chunk, update)

            # Only one from_text_reasoning call (for the choice with reasoning)
            assert MockContentClass.from_text_reasoning.call_count == 1
            assert result.additional_properties["reasoning_content"] == "Some reasoning"
