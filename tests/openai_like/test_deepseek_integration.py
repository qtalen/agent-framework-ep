"""Integration tests for DeepSeek-R1 reasoning content extraction.

Uses VCR.py cassettes to replay recorded API responses and tests that
OpenAILikeChatCompletionClient correctly extracts reasoning_content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import vcr
from agent_framework._types import Message

from agent_framework_ep.openai_like import OpenAILikeChatCompletionClient, get_reasoning_content

if TYPE_CHECKING:
    from agent_framework._types import ChatResponse, ChatResponseUpdate


class TestDeepSeekReasoningIntegration:
    """Integration tests for reasoning content extraction using VCR cassettes."""

    @pytest.mark.asyncio
    async def test_streaming_reasoning_extraction_via_client(self) -> None:
        """Test that OpenAILikeChatCompletionClient extracts reasoning from streaming response.

        Uses VCR cassette to replay recorded DeepSeek-R1 streaming response and
        verifies that reasoning_content is correctly extracted into additional_properties.
        """
        my_vcr = vcr.VCR(
            cassette_library_dir="tests/cassettes",
            record_mode="none",  # Only replay, don't record
        )

        with my_vcr.use_cassette("deepseek_reasoning_stream.yaml"):
            # Create client pointing to the mocked API via VCR
            client = OpenAILikeChatCompletionClient(
                model="deepseek-reasoner",
                api_key="fake-key",
                base_url="https://api.deepseek.com/v1",
            )

            # Collect streaming updates
            stream_result = await client.get_response(
                messages=[Message(role="user", contents=["What is 15 * 7? Think step by step."])],
                stream=True,
            )

            # stream_result is a ResponseStream, iterate over it
            updates: list[ChatResponseUpdate] = []
            async for update in stream_result:
                updates.append(update)

            # Verify we got updates
            assert len(updates) > 0, "No updates received from stream"

            # Collect reasoning content from updates using get_reasoning_content helper
            all_reasoning: list[str] = []
            all_content: list[str] = []

            for update in updates:
                # Extract reasoning using the helper function
                reasoning = get_reasoning_content(update)
                if reasoning:
                    all_reasoning.append(reasoning)

                # Check for text content
                for content in update.contents:
                    if hasattr(content, "text") and content.text and content.type == "text":
                        all_content.append(content.text)

            # Combine all reasoning parts
            full_reasoning = "".join(all_reasoning)

            # Verify reasoning content was extracted
            # The cassette contains reasoning about 15 * 7 = 105
            assert len(full_reasoning) > 50, (
                f"Reasoning content too short or not extracted. Got: {full_reasoning[:100]}"
            )

            # Verify specific reasoning content is present
            assert "15" in full_reasoning and "7" in full_reasoning, (
                f"Expected reasoning about '15 * 7' not found. Got: {full_reasoning[:200]}"
            )

            # Verify final answer content was also received
            full_content = "".join(all_content)
            assert "105" in full_content, f"Expected answer '105' not found in content. Got: {full_content[:200]}"

            print(f"Extracted reasoning: {len(full_reasoning)} chars")
            print(f"Extracted content: {len(full_content)} chars")

    @pytest.mark.asyncio
    async def test_get_reasoning_content_helper(self) -> None:
        """Test get_reasoning_content() helper works with streaming responses."""
        # Create a mock update with reasoning_content in additional_properties
        mock_update = MagicMock(spec=["additional_properties", "contents", "messages"])
        mock_update.additional_properties = {"reasoning_content": "My reasoning process"}
        mock_update.contents = []

        # Extract reasoning using our helper
        reasoning = get_reasoning_content(mock_update)

        assert reasoning == "My reasoning process", f"Expected 'My reasoning process', got '{reasoning}'"

    def test_reasoning_content_concatenation(self) -> None:
        """Test that reasoning content from multiple updates can be concatenated."""
        # Simulate multiple updates with reasoning content
        reasoning_parts = ["Step 1: ", "Break down ", "15 * 7", ". ", "Answer: 105"]

        all_reasoning: list[str] = []
        for part in reasoning_parts:
            mock_update = MagicMock(spec=["additional_properties", "contents", "messages"])
            mock_update.additional_properties = {"reasoning_content": part}
            mock_update.contents = []

            reasoning = get_reasoning_content(mock_update)
            if reasoning:
                all_reasoning.append(reasoning)

        # Verify concatenation
        full_reasoning = "".join(all_reasoning)
        expected = "".join(reasoning_parts)
        assert full_reasoning == expected, f"Expected '{expected}', got '{full_reasoning}'"

    @pytest.mark.asyncio
    async def test_non_streaming_response_has_reasoning(self) -> None:
        """Test that non-streaming response can have reasoning_content extracted.

        This test mocks the OpenAI client to simulate a non-streaming DeepSeek-R1
        response with reasoning_content field.
        """
        # Create mock message with reasoning_content
        mock_message = MagicMock()
        mock_message.role = "assistant"
        mock_message.content = "The answer is 105."
        mock_message.reasoning_content = "Let me calculate: 15 * 7 = (10+5) * 7 = 70 + 35 = 105."
        mock_message.reasoning_details = None
        mock_message.tool_calls = None

        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message, finish_reason="stop")]
        mock_response.usage = MagicMock(
            prompt_tokens=17,
            completion_tokens=50,
            total_tokens=67,
        )
        mock_response.id = "test-response-id"
        mock_response.model = "deepseek-reasoner"
        mock_response.created = 1700000000

        # Create mock OpenAI client
        mock_openai_client = MagicMock()
        mock_openai_client.chat = MagicMock()
        mock_openai_client.chat.completions = MagicMock()

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Create our client with mocked underlying client
        client = OpenAILikeChatCompletionClient(
            model="deepseek-reasoner",
            api_key="fake-key",
            base_url="https://api.deepseek.com/v1",
            async_client=mock_openai_client,
        )

        # Get non-streaming response
        response: ChatResponse = await client.get_response(
            messages=[Message(role="user", contents=["What is 15 * 7?"])],
        )

        # Verify response was received
        assert response is not None, "No response received"

        # Extract reasoning using helper
        reasoning = get_reasoning_content(response)

        # Verify reasoning content was extracted
        assert "15 * 7" in reasoning or "105" in reasoning, f"Expected reasoning content not found. Got: {reasoning}"

        # Verify reasoning is in additional_properties
        assert response.additional_properties is not None, "additional_properties is None"
        assert "reasoning_content" in response.additional_properties, (
            "reasoning_content not found in additional_properties"
        )
