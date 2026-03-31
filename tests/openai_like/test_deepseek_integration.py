"""Integration tests for DeepSeek-R1 reasoning content extraction.

Uses VCR.py cassettes to replay recorded API responses.
"""

from __future__ import annotations

import pytest
import vcr


class TestDeepSeekReasoningIntegration:
    """Integration tests using recorded DeepSeek-R1 responses."""

    @pytest.mark.asyncio
    async def test_streaming_reasoning_extraction(self) -> None:
        """Test reasoning extraction from DeepSeek-R1 streaming response."""
        from openai import AsyncOpenAI

        my_vcr = vcr.VCR(
            cassette_library_dir="tests/cassettes",
            record_mode="none",  # Only replay, don't record
        )

        with my_vcr.use_cassette("deepseek_reasoning_stream.yaml"):
            openai_client = AsyncOpenAI(
                api_key="fake-key",
                base_url="https://api.deepseek.com/v1",
            )

            stream = await openai_client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": "What is 15 * 7? Think step by step."}],
                stream=True,
            )

            reasoning_parts: list[str] = []
            content_parts: list[str] = []

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        reasoning_parts.append(delta.reasoning_content)
                    if delta.content:
                        content_parts.append(delta.content)

            # Verify reasoning was extracted
            assert len(reasoning_parts) > 0, "No reasoning content found in streaming response"
            full_reasoning = "".join(reasoning_parts)
            assert len(full_reasoning) > 50, "Reasoning content too short"

            # Verify final answer was provided
            assert len(content_parts) > 0, "No final content found in streaming response"

            print(f"Reasoning length: {len(full_reasoning)} chars")
            print(f"Content length: {len(''.join(content_parts))} chars")
