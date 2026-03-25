from __future__ import annotations

import asyncio
import contextlib
import logging
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import ClassVar, Self

from agent_framework_ep.code_executor.base import (
    CancellationToken,
    CodeBlock,
    CodeExecutor,
    CommandLineCodeResult,
    get_file_name_from_content,
    lang_to_cmd,
    silence_pip,
)

logger = logging.getLogger(__name__)


class LocalCommandLineCodeExecutor(CodeExecutor):
    """Executes code blocks directly on the host machine using subprocess.

    This executor provides a lightweight alternative to Docker-based execution
    for environments where Docker is not available or when performance is
    prioritized over isolation.

    **SECURITY WARNING**: This executor runs code directly on the host machine
    without any sandboxing or isolation. Only use this for trusted code.
    For untrusted code, use DockerCommandLineCodeExecutor instead.

    Args:
        timeout: The timeout in seconds for code execution. Defaults to 60.
        work_dir: The working directory for code execution. If None, a temporary
            directory will be created.
        delete_tmp_files: If True, temporary files will be deleted after execution.
            Defaults to False.

    Example:
        >>> async with LocalCommandLineCodeExecutor(timeout=30) as executor:
        ...     result = await executor.execute_code_blocks(
        ...         [CodeBlock(code="print('hello')", language="python")],
        ...         CancellationToken()
        ...     )
        ...     print(result.output)
        hello
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
        """Initialize the local code executor.

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

        self._warned_security = False

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

    def _check_security_warning(self) -> None:
        """Log security warning on first use."""
        if not self._warned_security:
            logger.warning(
                "SECURITY WARNING: LocalCommandLineCodeExecutor runs code directly on the host "
                "machine without isolation. Only use this for trusted code. "
                "For untrusted code, use DockerCommandLineCodeExecutor."
            )
            self._warned_security = True

    async def _execute_command(
        self,
        command: list[str],
        cancellation_token: CancellationToken,
    ) -> tuple[str, int]:
        """Execute a command with timeout and cancellation support.

        Args:
            command: The command to execute as a list of strings.
            cancellation_token: Token for cancellation support.

        Returns:
            A tuple of (output, exit_code).
        """
        process: asyncio.subprocess.Process | None = None

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self.work_dir),
            )

            # Create a task that watches for cancellation
            cancel_task = asyncio.create_task(self._wait_for_cancellation(cancellation_token))
            cancel_task.add_done_callback(lambda _: asyncio.create_task(self._kill_process_if_cancelled(process)))

            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )
                cancel_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await cancel_task
                output = stdout.decode("utf-8") if stdout else ""
                exit_code = process.returncode if process.returncode is not None else 1
                return output, exit_code
            except TimeoutError:
                cancel_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await cancel_task
                if process.returncode is None:
                    with contextlib.suppress(Exception):
                        process.kill()
                        await process.wait()
                return f"\nTimeout: Code execution exceeded {self._timeout} seconds", 124

        except asyncio.CancelledError:
            if process is not None and process.returncode is None:
                with contextlib.suppress(Exception):
                    process.kill()
                    await process.wait()
            raise

    async def _wait_for_cancellation(self, cancellation_token: CancellationToken) -> None:
        """Wait for cancellation token to be cancelled."""
        while not cancellation_token.is_cancellation_requested:
            await asyncio.sleep(0.01)

    async def _kill_process_if_cancelled(self, process: asyncio.subprocess.Process) -> None:
        """Kill the process if it hasn't completed."""
        if process.returncode is None:
            with contextlib.suppress(Exception):
                process.kill()
                await process.wait()

    async def _execute_code_dont_check_setup(
        self,
        code_blocks: list[CodeBlock],
        cancellation_token: CancellationToken,
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
                    filename = f"tmp_code_{sha256(code.encode()).hexdigest()}.{lang}"

                code_path = self.work_dir / filename
                code_path.write_text(code, encoding="utf-8")
                files.append(code_path)

                cmd = lang_to_cmd(lang)
                command = [cmd, str(code_path)]

                output, exit_code = await self._execute_command(command, cancellation_token)
                outputs.append(output)
                last_exit_code = exit_code

                if exit_code != 0:
                    break
        finally:
            if self._delete_tmp_files:
                for file in files:
                    with contextlib.suppress(OSError, FileNotFoundError):
                        file.unlink()

        code_file = str(files[0]) if files else None
        return CommandLineCodeResult(exit_code=last_exit_code, output="".join(outputs), code_file=code_file)

    async def execute_code_blocks(
        self,
        code_blocks: list[CodeBlock],
        cancellation_token: CancellationToken,
    ) -> CommandLineCodeResult:
        """Execute code blocks and return the result.

        Args:
            code_blocks: List of code blocks to execute.
            cancellation_token: Token for cancellation support.

        Returns:
            The result of code execution.

        Raises:
            ValueError: If the executor is not running or no code blocks provided.
            asyncio.TimeoutError: If execution exceeds the timeout.
            asyncio.CancelledError: If cancellation is requested.
        """
        if not self._running:
            raise ValueError("Executor is not running. Must first be started with either start or a context manager.")

        self._check_security_warning()

        try:
            return await self._execute_code_dont_check_setup(code_blocks, cancellation_token)
        except asyncio.CancelledError:
            return CommandLineCodeResult(exit_code=1, output="Code execution was cancelled.", code_file=None)

    async def start(self) -> None:
        """Start the code executor.

        Creates a temporary directory if no working directory was specified.
        """
        if self._work_dir is None and self._temp_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory()
            Path(self._temp_dir.name).mkdir(exist_ok=True, parents=True)

        self._running = True
        logger.debug("LocalCommandLineCodeExecutor started")

    async def stop(self) -> None:
        """Stop the code executor and release resources.

        Cleans up the temporary directory if one was created.
        """
        if not self._running:
            return

        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

        self._running = False
        logger.debug("LocalCommandLineCodeExecutor stopped")

    async def restart(self) -> None:
        """Restart the code executor.

        Stops and then starts the executor, resetting it to initial state.
        """
        await self.stop()
        await self.start()

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> bool | None:
        """Async context manager exit."""
        await self.stop()
        return None
