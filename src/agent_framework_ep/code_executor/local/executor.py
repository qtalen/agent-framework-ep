from __future__ import annotations

import asyncio
import contextlib
import logging
from pathlib import Path
from types import TracebackType
from typing import Self

from agent_framework_ep.code_executor.base import (
    BaseCommandLineCodeExecutor,
    CancellationToken,
    CodeBlock,
    CommandLineCodeResult,
)

logger = logging.getLogger(__name__)


class LocalCommandLineCodeExecutor(BaseCommandLineCodeExecutor):
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
        super().__init__(
            timeout=timeout,
            work_dir=work_dir,
            delete_tmp_files=delete_tmp_files,
        )
        self._warned_security = False

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
        cancelled_event = asyncio.Event()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self.work_dir),
            )

            # Create a task that watches for cancellation and kills process
            async def watch_cancellation() -> None:
                await cancellation_token.wait()
                cancelled_event.set()
                if process.returncode is None:
                    with contextlib.suppress(Exception):
                        process.kill()
                        await process.wait()

            cancel_task = asyncio.create_task(watch_cancellation())

            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )
                # Check if cancellation occurred while we were waiting
                if cancelled_event.is_set():
                    raise asyncio.CancelledError()
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

    async def execute_script(
        self,
        script_path: str,
        args: dict[str, str] | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> CommandLineCodeResult:
        """Execute an external Python script file with optional command-line arguments.

        This method allows running an existing Python script with custom arguments.
        The args dictionary is converted to command-line arguments in the form
        of --key value.

        Args:
            script_path: Absolute or relative path to the Python script.
                Relative paths are resolved against the working directory.
            args: Optional dictionary of command-line arguments. Each key-value pair
                is converted to --key value. For example: {"input": "data.txt", "verbose": "true"}
                becomes --input data.txt --verbose true.

                To pass positional arguments (without -- prefix), use an empty string as the key.
                For example: {"": "arg1 arg2"} becomes: script.py arg1 arg2
            cancellation_token: Optional token to cancel the execution. If None, the
                execution cannot be cancelled externally.

        Returns:
            CommandLineCodeResult containing the execution output and exit code.

        Raises:
            ValueError: If the executor is not running or script file not found.
        """
        if not self._running:
            raise ValueError("Executor is not running. Must first be started with either start or a context manager.")

        self._check_security_warning()

        # Resolve and validate script path
        script_path_obj = Path(script_path)
        if not script_path_obj.is_absolute():
            script_path_obj = self.work_dir / script_path_obj

        script_path_obj = script_path_obj.resolve()
        work_dir_resolved = self.work_dir.resolve()

        # Security: prevent path traversal
        try:
            script_path_obj.relative_to(work_dir_resolved)
        except ValueError as e:
            raise ValueError(
                f"Script path '{script_path}' is outside the working directory. Resolved to: {script_path_obj}"
            ) from e

        if not script_path_obj.exists():
            raise ValueError(f"Script file not found: {script_path}")

        if not script_path_obj.is_file():
            raise ValueError(f"Script path is not a file: {script_path}")

        # Build command
        command = ["python", str(script_path_obj)]
        if args:
            for key, value in args.items():
                if key == "":
                    command.extend(value.split())
                else:
                    command.extend([f"--{key}", value])

        if cancellation_token is None:
            cancellation_token = CancellationToken()

        try:
            output, exit_code = await self._execute_command(command, cancellation_token)
            return CommandLineCodeResult(
                exit_code=exit_code,
                output=output,
                code_file=str(script_path_obj),
            )
        except asyncio.CancelledError:
            return CommandLineCodeResult(
                exit_code=1,
                output="Script execution was cancelled.",
                code_file=str(script_path_obj),
            )

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        """Async context manager exit."""
        await self.stop()
        return None
