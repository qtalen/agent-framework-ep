from typing import Literal

from .base import (
    CancellationToken,
    CodeBlock,
    CodeExecutor,
    CodeResult,
    CommandLineCodeResult,
    get_file_name_from_content,
    lang_to_cmd,
    silence_pip,
)
from .docker import DockerCommandLineCodeExecutor, DockerCommandLineCodeExecutorConfig
from .local import LocalCommandLineCodeExecutor


class CodeExecutionTool:
    """Tool for executing code using a CodeExecutor."""

    def __init__(self, executor: CodeExecutor) -> None:
        self._executor = executor

    async def execute_code(self, code: str, language: Literal["python", "sh"] = "python") -> str:
        """Execute code and return the output.

        Args:
            code: The code to execute.
            language: The programming language. Supported values: "python", "sh". Defaults to "python".

        Returns:
            The output of the code execution.
        """
        result = await self._executor.execute_code_blocks(
            [CodeBlock(code=code, language=language)],
            CancellationToken(),
        )
        return result.output


__all__ = [
    "CodeBlock",
    "CodeExecutor",
    "CodeResult",
    "CommandLineCodeResult",
    "CancellationToken",
    "CodeExecutionTool",
    "DockerCommandLineCodeExecutor",
    "DockerCommandLineCodeExecutorConfig",
    "LocalCommandLineCodeExecutor",
    "lang_to_cmd",
    "silence_pip",
    "get_file_name_from_content",
]
