from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StructuredOutputParseError(Exception):
    def __init__(self, response_format: type[BaseModel], raw_text: str, cause: Exception) -> None:
        self.response_format = response_format
        self.raw_text = raw_text
        self.__cause__ = cause
        super().__init__(
            f"Failed to parse response as {response_format.__name__}:\n"
            f"Parse error: {cause}\n"
            f"Raw response:\n{raw_text[:500]}{'...' if len(raw_text) > 500 else ''}"
        )

    def __repr__(self) -> str:
        return (
            f"StructuredOutputParseError("
            f"response_format={self.response_format.__name__!r}, "
            f"raw_text_length={len(self.raw_text)}, "
            f"cause={self.__cause__!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_format": self.response_format.__name__,
            "raw_text_length": len(self.raw_text),
            "cause": str(self.__cause__),
            "cause_type": type(self.__cause__).__name__,
        }
