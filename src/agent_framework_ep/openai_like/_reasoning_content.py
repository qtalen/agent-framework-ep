from __future__ import annotations

import copy
from typing import Any

from agent_framework._types import (
    ChatResponse,
    ChatResponseUpdate,
    Content,
    Message,
)


def _set_additional_property(obj: ChatResponse | ChatResponseUpdate, key: str, value: str) -> None:
    if obj.additional_properties is None:
        obj.additional_properties = {}
    obj.additional_properties[key] = value


class ReasoningContentMixin:
    def _propagate_reasoning_in_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = copy.deepcopy(messages)
        pending_reasoning_content: str | None = None

        for msg in result:
            if msg.get("role") != "assistant":
                pending_reasoning_content = None
                continue

            has_tool_calls = "tool_calls" in msg
            has_reasoning = "reasoning_content" in msg or "reasoning_details" in msg

            if has_reasoning and not has_tool_calls:
                pending_reasoning_content = msg.get("reasoning_content") or msg.get("reasoning_details")
            elif has_tool_calls and pending_reasoning_content:
                if "reasoning_content" not in msg:
                    msg["reasoning_content"] = pending_reasoning_content
                pending_reasoning_content = None
            elif has_tool_calls:
                pending_reasoning_content = None

        return result

    def _extract_reasoning_from_message(self, message: Message) -> tuple[Message, str | None]:
        pending_reasoning_content: str | None = None
        filtered_contents: list[Content] = []

        for content in message.contents:
            if content.type == "text_reasoning":
                if content.text and content.protected_data is None:
                    if pending_reasoning_content is None:
                        pending_reasoning_content = content.text
                    else:
                        pending_reasoning_content += content.text
            else:
                filtered_contents.append(content)

        if "reasoning_content" in message.additional_properties:
            rc = message.additional_properties["reasoning_content"]
            pending_reasoning_content = rc if pending_reasoning_content is None else rc + pending_reasoning_content

        if len(filtered_contents) != len(message.contents):
            message = Message(
                role=message.role,
                contents=filtered_contents,
                author_name=message.author_name,
                additional_properties=message.additional_properties,
            )

        return message, pending_reasoning_content

    def _inject_reasoning_to_openai_message(self, result: list[dict[str, Any]], reasoning: str | None) -> None:
        if reasoning is None:
            return

        for msg in reversed(result):
            if msg.get("role") == "assistant" and ("content" in msg or "tool_calls" in msg):
                msg["reasoning_content"] = reasoning
                break
        else:
            if result and result[-1].get("role") == "assistant":
                result[-1]["reasoning_content"] = reasoning

    def _extract_reasoning_from_response(self, response: Any, chat_response: ChatResponse) -> ChatResponse:
        reasoning_content_parts: list[str] = []
        for choice in response.choices:
            message = choice.message
            if reasoning_content := getattr(message, "reasoning_content", None):
                reasoning_content_parts.append(reasoning_content)
                msg_index = response.choices.index(choice)
                if msg_index < len(chat_response.messages):
                    msg = chat_response.messages[msg_index]
                    has_text_reasoning = any(
                        c.type == "text_reasoning" and c.text == reasoning_content for c in msg.contents
                    )
                    if not has_text_reasoning:
                        msg.contents.append(Content.from_text_reasoning(text=reasoning_content))

        if reasoning_content_parts:
            _set_additional_property(chat_response, "reasoning_content", "".join(reasoning_content_parts))

        return chat_response

    def _extract_reasoning_from_update(self, chunk: Any, update: ChatResponseUpdate) -> ChatResponseUpdate:
        reasoning_content_value: str | None = None
        for choice in chunk.choices:
            delta = choice.delta
            if reasoning_content := getattr(delta, "reasoning_content", None):
                update.contents.append(Content.from_text_reasoning(text=reasoning_content))
                if reasoning_content_value is None:
                    reasoning_content_value = reasoning_content
                else:
                    reasoning_content_value += reasoning_content

        if reasoning_content_value is not None:
            _set_additional_property(update, "reasoning_content", reasoning_content_value)

        return update
