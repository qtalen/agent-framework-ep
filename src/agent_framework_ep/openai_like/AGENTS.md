# openai_like Module

## Overview

Extends Microsoft Agent Framework's OpenAI ChatCompletion client with structured output support and reasoning_content extraction. Uses Chat Completions API, which is compatible with domestic LLMs (DeepSeek, Kimi, Qwen).

**Requirements**: `agent-framework>=1.0.0rc6` and `agent-framework-openai>=1.0.0rc6`

## File Structure

```
openai_like/
├── _exceptions.py       # Custom exceptions
├── _reasoning_content.py # Reasoning content extraction mixin
├── _response_format.py  # Structured output handling
└── __init__.py          # Main client class
```

## Files

### _exceptions.py

**Classes:**

- `StructuredOutputParseError` - Raised when structured output parsing fails
  - Stores `response_format`, `raw_text`, and `cause`
  - `to_dict()` - Converts to dict for logging

### _reasoning_content.py

**Classes:**

- `ReasoningContentMixin` - Mixin for extracting/propagating reasoning content (e.g., DeepSeek-R1)
  - `_propagate_reasoning_in_messages()` - Propagates reasoning to tool call messages
  - `_extract_reasoning_from_message()` - Extracts `text_reasoning` content from messages
  - `_inject_reasoning_to_openai_message()` - Injects reasoning into OpenAI format
  - `_extract_reasoning_from_response()` - Extracts from `message.reasoning_content` (non-streaming)
  - `_extract_reasoning_from_update()` - Extracts from `delta.reasoning_content` (streaming)

**Functions:**

- `_set_additional_property(obj, key, value)` - Helper to set additional_properties

### _response_format.py

**Classes:**

- `ResponseFormatMixin` - Mixin for structured JSON output support
  - `_inject_response_format_prompt()` - Injects JSON schema prompt into instructions
  - `_parse_structured_output()` - Parses response into Pydantic model
  - `_build_structured_prompt()` - Builds system prompt with JSON schema and rules

**Functions:**

- `_extract_json_from_markdown(text)` - Strips markdown code blocks from JSON
- `_try_parse_json_with_fallbacks(text)` - Tries json, dirtyjson, then repair_json

### __init__.py

**Classes:**

- `OpenAILikeChatCompletionClient` - Extended OpenAI ChatCompletion client combining both mixins
  - Inherits: `ResponseFormatMixin`, `ReasoningContentMixin`, `OpenAIChatCompletionClient`
  - Uses Chat Completions API (compatible with domestic LLMs)
  - `_prepare_options()` - Injects structured output prompt
  - `_prepare_messages_for_openai()` - Propagates reasoning in message list
  - `_prepare_message_for_openai()` - Extracts/injects reasoning per message
  - `_parse_response_from_openai()` - Extracts reasoning and parses structured output (non-streaming)
  - `_parse_response_update_from_openai()` - Handles streaming with reasoning extraction

**Aliases:**

- `OpenAILikeChatClient` - Backward compatibility alias for `OpenAILikeChatCompletionClient`

**Functions:**

- `get_reasoning_content(response)` - Extracts reasoning from ChatResponse/ChatResponseUpdate
  - Checks `additional_properties["reasoning_content"]` or collects `text_reasoning` contents

**Exports:** `OpenAILikeChatCompletionClient`, `OpenAILikeChatClient`, `get_reasoning_content`, `StructuredOutputParseError`

## API Compatibility

| Client | API Type | Reasoning Field | Compatible Models |
|--------|----------|-----------------|-------------------|
| `OpenAILikeChatCompletionClient` | Chat Completions | `message.reasoning_content` | DeepSeek, Kimi, Qwen |
| `OpenAIChatClient` (official) | Responses API | `item.type == "reasoning"` | OpenAI official models |

## Usage

```python
from agent_framework_ep import OpenAILikeChatCompletionClient

# For domestic LLMs (DeepSeek, Kimi, Qwen)
client = OpenAILikeChatCompletionClient(
    model="deepseek-chat",
    api_key="your-api-key",
    base_url="https://api.deepseek.com/v1",  # Optional
)

# Backward compatible
from agent_framework_ep import OpenAILikeChatClient  # Same as above
```