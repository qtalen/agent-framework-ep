from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, override

from agent_framework._types import ChatResponse, ChatResponseUpdate, Message
from agent_framework_openai import OpenAIChatCompletionClient
from pydantic import BaseModel

from ._exceptions import StructuredOutputParseError
from ._reasoning_content import ReasoningContentMixin
from ._response_format import ResponseFormatMixin

__all__ = [
    "OpenAILikeChatCompletionClient",
    "OpenAILikeChatClient",  # Backward compatibility alias
    "get_reasoning_content",
    "StructuredOutputParseError",
]


class OpenAILikeChatCompletionClient(ResponseFormatMixin, ReasoningContentMixin, OpenAIChatCompletionClient):
    """Extended OpenAI ChatCompletion client with structured output and reasoning content support.

    This client uses the Chat Completions API, which is compatible with
    domestic LLMs like DeepSeek, Kimi, and Qwen that return `reasoning_content` field.

    Args:
        *args: Positional arguments passed to OpenAIChatCompletionClient.
        **kwargs: Keyword arguments passed to OpenAIChatCompletionClient.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._current_response_format: type[BaseModel] | None = None

    @override
    def _prepare_options(
        self,
        messages: Sequence[Message],
        options: Mapping[str, Any],
    ) -> dict[str, Any]:
        run_options = self._inject_response_format_prompt(dict(options))
        return super()._prepare_options(messages, run_options)

    @override
    def _prepare_messages_for_openai(
        self,
        chat_messages: Sequence[Message],
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[dict[str, Any]]:
        result = super()._prepare_messages_for_openai(chat_messages, role_key, content_key)
        return self._propagate_reasoning_in_messages(result)

    @override
    def _prepare_message_for_openai(self, message: Message) -> list[dict[str, Any]]:
        filtered_msg, reasoning = self._extract_reasoning_from_message(message)
        result = super()._prepare_message_for_openai(filtered_msg)
        self._inject_reasoning_to_openai_message(result, reasoning)
        return result

    @override
    def _parse_response_from_openai(
        self,
        response: Any,
        options: Mapping[str, Any],
    ) -> ChatResponse:
        chat_response = super()._parse_response_from_openai(response, options)
        chat_response = self._extract_reasoning_from_response(response, chat_response)
        return self._parse_structured_output(chat_response)

    @override
    def _parse_response_update_from_openai(
        self,
        chunk: Any,
    ) -> ChatResponseUpdate:
        update = super()._parse_response_update_from_openai(chunk)
        return self._extract_reasoning_from_update(chunk, update)


# Backward compatibility alias
OpenAILikeChatClient = OpenAILikeChatCompletionClient


def get_reasoning_content(response: ChatResponse | ChatResponseUpdate) -> str:
    """Extract reasoning content from a ChatResponse or ChatResponseUpdate.

    Args:
        response: The response object to extract reasoning from.

    Returns:
        The reasoning content as a string, or empty string if none found.
    """
    additional_props = getattr(response, "additional_properties", None)
    if additional_props and (reasoning := additional_props.get("reasoning_content")):
        return str(reasoning)

    contents: list[Any] = []
    if messages := getattr(response, "messages", None):
        for msg in messages:
            contents.extend(msg.contents)
    elif update_contents := getattr(response, "contents", None):
        contents.extend(update_contents)

    return "".join(c.text for c in contents if c.type == "text_reasoning" and c.text)
