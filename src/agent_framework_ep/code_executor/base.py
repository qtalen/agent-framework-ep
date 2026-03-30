from __future__ import annotations

import asyncio
import logging
import re
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import TracebackType
from typing import Any, ClassVar, Self


@dataclass
class CodeBlock:
    """A code block extracted from a message."""

    code: str
    language: str


@dataclass
class CodeResult:
    """Result of a code execution."""

    exit_code: int
    output: str


class CommandLineCodeResult(CodeResult):
    """A code result class for command line code executor."""

    def __init__(
        self,
        exit_code: int,
        output: str,
        code_file: str | None = None,
    ):
        super().__init__(exit_code=exit_code, output=output)
        self.code_file = code_file


class CancellationToken:
    """Very small cancellation helper, independent of Autogen."""

    def __init__(self) -> None:
        self._event = asyncio.Event()
        self._watcher_task: asyncio.Task[Any] | None = None

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancellation_requested(self) -> bool:
        return self._event.is_set()

    async def wait(self) -> None:
        """Wait until cancellation is requested."""
        await self._event.wait()

    def link_future(self, fut: asyncio.Future[Any] | asyncio.Task[Any]) -> None:
        async def watcher() -> None:
            await self._event.wait()
            if not fut.done():
                fut.cancel()

        self._watcher_task = asyncio.create_task(watcher())


class CodeExecutor(ABC):
    """Executes code blocks and returns the result.
    Subclasses should implement the abstract methods and are typically
    used as async context managers::
        async with MyExecutor(...) as executor:
            result = await executor.execute_code_blocks(...)
    """

    @abstractmethod
    async def execute_code_blocks(
        self, code_blocks: list[CodeBlock], cancellation_token: CancellationToken
    ) -> CodeResult:
        """Execute code blocks and return the result.
        Raises:
            ValueError: Errors in user inputs
            asyncio.TimeoutError: Code execution timeouts
            asyncio.CancelledError: CancellationToken evoked during execution
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the code executor."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the code executor and release any resources."""
        ...

    @abstractmethod
    async def restart(self) -> None:
        """Restart the code executor."""
        ...

    @abstractmethod
    async def execute_script(
        self,
        script_path: str,
        args: dict[str, str] | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> CommandLineCodeResult:
        """Execute an external Python script file with optional command-line arguments.

        Args:
            script_path: Path to the Python script.
            args: Optional dictionary of command-line arguments. Each key-value pair is
                converted to --key value. Use empty string key for positional arguments.
            cancellation_token: Optional token to cancel the execution.

        Returns:
            CommandLineCodeResult containing the execution output and exit code.

        Raises:
            ValueError: If the executor is not running.
        """
        ...

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        await self.stop()
        return None


class BaseCommandLineCodeExecutor(CodeExecutor):
    """Base class for command line code executors.

    Provides common functionality for executing code blocks via command line,
    including file management, command building, and output handling.

    Subclasses must implement `_execute_command` to define how commands are
    actually executed (e.g., in Docker container or local subprocess).
    """

    SUPPORTED_LANGUAGES: ClassVar[list[str]] = [
        "bash",
        "shell",
        "sh",
        "pwsh",
        "powershell",
        "ps1",
        "python",
    ]

    def __init__(
        self,
        *,
        timeout: int = 60,
        work_dir: Path | str | None = None,
        delete_tmp_files: bool = False,
    ):
        """Initialize the base command line executor.

        Args:
            timeout: Timeout in seconds for code execution.
            work_dir: Working directory for code execution.
            delete_tmp_files: Whether to delete temporary files after execution.
        """
        if timeout < 1:
            raise ValueError("Timeout must be greater than or equal to 1.")

        self._timeout = timeout
        self._delete_tmp_files = delete_tmp_files
        self._running = False
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None

        self._work_dir: Path | None = None
        if work_dir is not None:
            if isinstance(work_dir, str):
                work_dir = Path(work_dir)
            work_dir.mkdir(exist_ok=True, parents=True)
            self._work_dir = work_dir

    @property
    def timeout(self) -> int:
        """The timeout for code execution."""
        return self._timeout

    @property
    def work_dir(self) -> Path:
        """The working directory for code execution."""
        if self._work_dir is not None:
            return self._work_dir
        if self._temp_dir is not None:
            return Path(self._temp_dir.name)
        raise RuntimeError("Working directory not properly initialized")

    @abstractmethod
    async def _execute_command(self, command: list[str], cancellation_token: CancellationToken) -> tuple[str, int]:
        """Execute a command and return output and exit code.

        Args:
            command: The command to execute as a list of strings.
            cancellation_token: Token for cancellation support.

        Returns:
            A tuple of (output, exit_code).
        """
        ...

    async def _execute_code_dont_check_setup(
        self, code_blocks: list[CodeBlock], cancellation_token: CancellationToken
    ) -> CommandLineCodeResult:
        """Execute code blocks without checking setup.

        Args:
            code_blocks: List of code blocks to execute.
            cancellation_token: Token for cancellation support.

        Returns:
            The result of code execution.
        """
        if len(code_blocks) == 0:
            raise ValueError("No code blocks to execute.")

        outputs: list[str] = []
        files: list[Path] = []
        last_exit_code = 0

        try:
            for code_block in code_blocks:
                lang = code_block.language.lower()
                code = silence_pip(code_block.code, lang)

                filename = get_file_name_from_content(code, self.work_dir)
                if filename is None:
                    # Only compute hash when needed
                    hash_value = sha256(code.encode()).hexdigest()[:16]
                    filename = f"tmp_code_{hash_value}.{lang}"

                code_path = self.work_dir / filename
                code_path.write_text(code, encoding="utf-8")
                files.append(code_path)

                command = self._build_command(lang, filename)

                output, exit_code = await self._execute_command(command, cancellation_token)
                outputs.append(output)
                last_exit_code = exit_code

                if exit_code != 0:
                    break
        finally:
            if self._delete_tmp_files:
                for file in files:
                    try:
                        file.unlink()
                    except (OSError, FileNotFoundError):
                        logger.debug(f"Failed to delete temporary file: {file}")

        code_file = str(files[0]) if files else None
        return CommandLineCodeResult(exit_code=last_exit_code, output="".join(outputs), code_file=code_file)

    def _build_command(self, lang: str, filename: str) -> list[str]:
        """Build the command to execute a code file.

        Args:
            lang: The language of the code.
            filename: The filename of the code file.

        Returns:
            The command as a list of strings.
        """
        return [lang_to_cmd(lang), filename]

    async def execute_code_blocks(
        self, code_blocks: list[CodeBlock], cancellation_token: CancellationToken
    ) -> CommandLineCodeResult:
        """Execute code blocks and return the result."""
        return await self._execute_code_dont_check_setup(code_blocks, cancellation_token)

    async def start(self) -> None:
        """Start the code executor."""
        if self._work_dir is None and self._temp_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory()
            Path(self._temp_dir.name).mkdir(exist_ok=True, parents=True)

        self._running = True

    async def stop(self) -> None:
        """Stop the code executor and release resources."""
        if not self._running:
            return

        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

        self._running = False

    async def restart(self) -> None:
        """Restart the code executor."""
        await self.stop()
        await self.start()


logger = logging.getLogger(__name__)

PYTHON_VARIANTS = ["python", "Python", "py"]

# Pre-compiled regex patterns for silence_pip
_SILENCE_PIP_PYTHON_RE = re.compile(r"^! ?pip install")
_SILENCE_PIP_SHELL_RE = re.compile(r"^pip install")


def lang_to_cmd(lang: str) -> str:
    """Map language to command."""
    lang = lang.lower()
    if lang in PYTHON_VARIANTS:
        return "python"
    if lang.startswith("python") or lang in ["bash", "sh"]:
        return lang
    if lang in ["shell"]:
        return "sh"
    if lang in ["pwsh", "powershell", "ps1"]:
        if shutil.which("pwsh") is not None:
            return "pwsh"
        elif shutil.which("powershell") is not None:
            return "powershell"
        else:
            raise ValueError("Powershell or pwsh is not installed. Please install one of them.")
    else:
        raise ValueError(f"Unsupported language: {lang}")


def silence_pip(code: str, lang: str) -> str:
    """Apply -qqq flag to pip install commands."""
    if lang == "python":
        pattern = _SILENCE_PIP_PYTHON_RE
    elif lang in ["bash", "shell", "sh", "pwsh", "powershell", "ps1"]:
        pattern = _SILENCE_PIP_SHELL_RE
    else:
        return code

    lines = code.split("\n")
    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match is not None and "-qqq" not in line:
            lines[i] = line.replace(match.group(0), match.group(0) + " -qqq")
    return "\n".join(lines)


def get_file_name_from_content(code: str, workspace_path: Path) -> str | None:
    """Extract filename from code comment like '# filename: xxx'."""
    first_line = code.split("\n")[0]
    if first_line.startswith("# filename:"):
        filename = first_line.split(":")[1].strip()
        path = Path(filename)
        if not path.is_absolute():
            path = workspace_path / path
        try:
            # Use resolve() to normalize the path and check for traversal
            path = path.resolve()
            relative = path.relative_to(workspace_path.resolve())
            return str(relative)
        except ValueError:
            pass
    return None
