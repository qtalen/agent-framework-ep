from __future__ import annotations

import json
import re
from textwrap import dedent
from typing import Any, cast

import dirtyjson  # type: ignore[import-untyped]
from agent_framework._types import ChatResponse
from json_repair import repair_json
from pydantic import BaseModel, ValidationError

from ._exceptions import StructuredOutputParseError

_CODE_BLOCK_RE = re.compile(
    r"^\s*```(?P<lang>\w+)?\s*\n(?P<body>.*?)```\s*$",
    re.DOTALL,
)


def _extract_json_from_markdown(text: str) -> str:
    stripped = text.strip()
    match = _CODE_BLOCK_RE.match(stripped)
    if not match:
        return stripped
    lang = (match.group("lang") or "").lower()
    if lang and not lang.startswith("json"):
        return stripped
    return (match.group("body") or "").strip()


def _try_parse_json_with_fallbacks(text: str) -> Any:
    errors: list[Exception] = []

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        errors.append(e)

    try:
        return dirtyjson.loads(text)
    except Exception as e:
        errors.append(e)

    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except Exception as e:
        errors.append(e)

    raise errors[0]


class ResponseFormatMixin:
    _current_response_format: type[BaseModel] | None

    def _inject_response_format_prompt(self, options: dict[str, Any]) -> dict[str, Any]:
        run_options = dict(options)
        response_format = run_options.get("response_format")

        if response_format and isinstance(response_format, type) and issubclass(response_format, BaseModel):
            self._current_response_format = response_format
            structured_prompt = self._build_structured_prompt(response_format)

            if instructions := run_options.get("instructions"):
                run_options["instructions"] = f"{instructions}\n\n{structured_prompt}"
            else:
                run_options["instructions"] = structured_prompt

            del run_options["response_format"]

        return run_options

    def _parse_structured_output(self, chat_response: ChatResponse) -> ChatResponse:
        response_format = self._current_response_format
        self._current_response_format = None

        if not (response_format and chat_response.finish_reason != "tool_calls" and chat_response.text):
            return chat_response

        raw_text = chat_response.text
        json_text = _extract_json_from_markdown(raw_text)

        try:
            parsed_json = _try_parse_json_with_fallbacks(json_text)
        except Exception as e:
            raise StructuredOutputParseError(response_format, raw_text, e) from e

        try:
            chat_response._value = cast(Any, response_format).model_validate(parsed_json)
            chat_response._value_parsed = True
            chat_response._response_format = response_format
        except ValidationError as e:
            raise StructuredOutputParseError(response_format, raw_text, e) from e

        return chat_response

    @staticmethod
    def _build_structured_prompt(response_format: type[BaseModel]) -> str:
        schema = response_format.model_json_schema()
        return dedent(f"""
            CRITICAL: You MUST output ONLY valid JSON, nothing else.

            Required JSON Schema:
            {json.dumps(schema, indent=2, ensure_ascii=False)}

            STRICT RULES - VIOLATION WILL CAUSE ERRORS:
            1. Output ONLY the JSON object, NO markdown code blocks (NO ```json ... ```)
            2. NO text before or after the JSON - start with '{{' and end with '}}'
            3. ALL strings must use double quotes and be properly escaped
            4. ESCAPE SPECIAL CHARACTERS in strings:
               - Double quote (") must be escaped as \\"
               - Backslash (\\) must be escaped as \\\\
               - Newlines must be escaped as \\n
               EXAMPLE: if content contains: 黃金"瘋牛"行情
               CORRECT: "content": "黃金\\"瘋牛\\"行情"
               INCORRECT: "content": "黃金"瘋牛"行情"
            5. Do NOT include explanations, summaries, or any other content

            Example of CORRECT output format:
            {{"field1": "value1", "field2": ["item1", "item2"]}}

            Example of INCORRECT output format:
            ```json
            {{"field1": "value1"}}
            ```

            Your entire response MUST be valid JSON matching the schema above.
        """).strip()
