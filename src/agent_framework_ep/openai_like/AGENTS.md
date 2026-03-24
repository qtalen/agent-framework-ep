# openai_like Module

## Overview

Extends Microsoft Agent Framework's OpenAI client with structured output support and reasoning_content extraction. Solves compatibility issues with open-source LLMs (GLM, Kimi, Qwen, DeepSeek).

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
  - `_extract_reasoning_from_response()` - Extracts from API response object
  - `_extract_reasoning_from_update()` - Extracts from streaming chunks

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

- `OpenAILikeChatClient` - Extended OpenAI client combining both mixins
  - Inherits: `ResponseFormatMixin`, `ReasoningContentMixin`, `OpenAIChatClient`
  - `_prepare_options()` - Injects structured output prompt
  - `_prepare_messages_for_openai()` - Propagates reasoning in message list
  - `_prepare_message_for_openai()` - Extracts/injects reasoning per message
  - `_parse_response_from_openai()` - Extracts reasoning and parses structured output
  - `_parse_response_update_from_openai()` - Handles streaming with reasoning

**Functions:**

- `get_reasoning_content(response)` - Extracts reasoning from ChatResponse/ChatResponseUpdate
  - Checks `additional_properties["reasoning_content"]` or collects `text_reasoning` contents

**Exports:** `OpenAILikeChatClient`, `get_reasoning_content`, `StructuredOutputParseError`
