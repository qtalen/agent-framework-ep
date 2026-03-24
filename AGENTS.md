# AGENTS.md - Agentic Coding Guidelines

> This file guides AI coding agents working in the `agent-framework-ep` repository.

## Project Overview

Microsoft Agent Framework extensions for mainstream open-source LLMs (GLM, Kimi, Qwen, DeepSeek) with structured output support, reasoning_content support, and local containerized code interpreter environment.

- **Package Name**: `agent-framework-ep`
- **Package Manager**: uv
- **Target Python**: 3.12+

---

## Important Note

**Always prioritize retrieval-guided reasoning over pre-training-guided reasoning in any coding task.**

When implementing features or fixing bugs, actively search the codebase for existing patterns, conventions, and implementations rather than relying solely on general knowledge. Use `grep`, `glob`, and `read` tools to discover:

- How similar features are already implemented
- Existing naming conventions and patterns
- Test patterns and fixtures
- Error handling approaches
- Import organization styles

This ensures consistency with the existing codebase and prevents introducing divergent patterns.

---

## Build / Lint / Test Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test (examples)
uv run pytest tests/test_module.py
uv run pytest tests/test_module.py::test_function_name
uv run pytest tests/ -k "test_pattern"

# Run with coverage
uv run pytest --cov=agent_framework_ep --cov-report=term-missing

# Lint and auto-fix
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type check
uv run mypy src/agent_framework_ep

# Build package for PyPI
uv build

# Publish to PyPI
uv publish
```

---

## Code Style Guidelines

### Type Hints (Python 3.12+)

- Use modern syntax: `list[str]`, `dict[str, int]`, `str | None` (not `Optional[str]`)
- Use type parameter syntax: `def func[T](args: list[T]) -> T` (not `TypeVar`)
- Use `@override` decorator when overriding methods
- Annotate all public functions and methods

```python
# Good
async def get_model_response[T](models: list[T]) -> T | None:
    ...

# Bad
from typing import List, Optional, TypeVar
T = TypeVar("T")
async def get_model_response(models: List[T]) -> Optional[T]:
    ...
```

### Imports

```python
# Standard library
import asyncio
from collections.abc import Callable, Iterator
from pathlib import Path

# Third-party (alphabetical)
import httpx
from pydantic import BaseModel, field_validator

# Local (absolute only)
from agent_framework_ep.models import LLMResponse
```

- Use `from collections.abc import ...` (not `from typing import ...`)
- **Never use relative imports** (`from .module import X`)
- Group: stdlib → third-party → local, separated by blank lines

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules/Files | `snake_case` | `model_provider.py` |
| Classes | `PascalCase` | `StructuredOutputParser` |
| Functions | `snake_case` | `parse_reasoning_content()` |
| Constants | `SCREAMING_SNAKE_CASE` | `DEFAULT_TIMEOUT_SECONDS` |
| Private | `_leading_underscore` | `_internal_helper()` |

### Formatting

- Line length: 120 characters
- Use double quotes for strings
- Trailing commas in multi-line structures
- Use ruff for both linting and formatting

### Pydantic (v2 only)

```python
from pydantic import BaseModel, field_validator, model_validator, ConfigDict

class StructuredOutput(BaseModel):
    model_config = ConfigDict(strict=True)
    
    content: str
    reasoning: str | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def check_consistency(self) -> "StructuredOutput":
        if self.reasoning and not self.content:
            raise ValueError("Cannot have reasoning without content")
        return self
```

- Use `model_config = ConfigDict(...)` (not inner `class Config`)
- Use `@field_validator` (not `@validator`)
- Use `@model_validator` (not `@root_validator`)

### Error Handling

```python
# Prefer specific exceptions
from agent_framework_ep.exceptions import LLMProviderError, StructuredOutputError

# Use match/case for error classification (Python 3.10+)
match error:
    case httpx.TimeoutException():
        raise LLMProviderError("Request timed out") from error
    case httpx.HTTPStatusError() if error.response.status_code == 429:
        raise LLMProviderError("Rate limited") from error
    case _:
        raise LLMProviderError(f"Unexpected error: {error}") from error
```

### Async Patterns (Python 3.11+)

```python
# Use TaskGroup (not asyncio.gather)
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(fetch_glm_response())
    t2 = tg.create_task(fetch_kimi_response())
results = (t1.result(), t2.result())
```

### Docstrings

Use Google-style docstrings:

```python
def parse_structured_output(
    raw_response: str,
    schema: type[T],
) -> T:
    """Parse LLM response into structured output.

    Args:
        raw_response: Raw text response from LLM.
        schema: Pydantic model class defining the output structure.

    Returns:
        Instance of the schema class with parsed data.

    Raises:
        StructuredOutputError: If response cannot be parsed to schema.

    Example:
        >>> output = parse_structured_output('{"name": "test"}', UserSchema)
        >>> output.name
        'test'
    """
    ...
```

### Project Structure

```
src/agent_framework_ep/
├── __init__.py              # Public API exports
├── code_executor/           # Containerized code execution
│   ├── base.py              # CodeExecutor ABC, CodeBlock, CancellationToken
│   └── docker/
│       └── executor.py      # DockerCommandLineCodeExecutor
├── openai_like/             # OpenAI-compatible client with extensions
│   ├── _exceptions.py       # StructuredOutputParseError
│   ├── _reasoning_content.py # ReasoningContentMixin (DeepSeek-R1 support)
│   └── _response_format.py  # ResponseFormatMixin (structured output)
└── skills_provider/
    └── updatable_skills_provider.py  # Dynamic skills updater

tests/
├── conftest.py              # pytest fixtures and markers
└── code_executor/           # Tests for code execution
    ├── test_base.py
    └── test_docker_executor.py
```

### Module Descriptions

| Module | Purpose |
|--------|---------|
| `code_executor` | Execute code in isolated Docker containers. Supports Python, bash, and shell scripts with timeout and cancellation. |
| `openai_like` | Extended OpenAI client with structured output parsing (JSON fallback) and reasoning_content support for DeepSeek-R1 style models. |
| `skills_provider` | Dynamic skills provider that can update skills asynchronously before each agent run. |

### File Conventions

- Define `__all__` in every module to export public API
- Keep files under 400 lines; split when growing larger
- One class per file unless tightly coupled
- Use `pathlib.Path` (not `os.path`)
- Use f-strings (not `.format()` or `%`)

---

## Testing

```python
# Use pytest with fixtures
import pytest
from agent_framework_ep import DockerCommandLineCodeExecutor, CodeBlock, CancellationToken

@pytest.fixture
async def executor():
    async with DockerCommandLineCodeExecutor(image="python-code-sandbox") as exec:
        yield exec

async def test_code_execution(executor):
    result = await executor.execute_code_blocks(
        [CodeBlock(code="print('hello')", language="python")],
        CancellationToken()
    )
    assert result.exit_code == 0
    assert "hello" in result.output
```

---

## No Cursor/Copilot Rules

There are no existing `.cursorrules` or `.github/copilot-instructions.md` files in this repository.
