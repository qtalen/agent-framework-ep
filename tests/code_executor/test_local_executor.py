"""Tests for LocalCommandLineCodeExecutor."""

import asyncio
import sys
from pathlib import Path

import pytest

from agent_framework_ep.code_executor import (
    CancellationToken,
    CodeBlock,
    LocalCommandLineCodeExecutor,
)


class TestLocalCommandLineCodeExecutor:
    """Test suite for LocalCommandLineCodeExecutor."""

    @pytest.fixture
    async def executor(self):
        """Create a local executor for testing."""
        async with LocalCommandLineCodeExecutor(timeout=5) as exec:
            yield exec

    @pytest.mark.asyncio
    async def test_basic_python_execution(self, executor):
        """Test basic Python code execution."""
        result = await executor.execute_code_blocks(
            [CodeBlock(code="print('hello world')", language="python")],
            CancellationToken(),
        )
        assert result.exit_code == 0
        assert "hello world" in result.output

    @pytest.mark.asyncio
    async def test_python_multiple_lines(self, executor):
        """Test Python code with multiple lines."""
        code = """
x = 5
y = 10
print(f"Sum: {x + y}")
"""
        result = await executor.execute_code_blocks(
            [CodeBlock(code=code, language="python")],
            CancellationToken(),
        )
        assert result.exit_code == 0
        assert "Sum: 15" in result.output

    @pytest.mark.asyncio
    async def test_bash_execution(self, executor):
        """Test bash shell execution."""
        # Skip on Windows due to path issues with bash
        if sys.platform == "win32":
            pytest.skip("bash path handling issues on Windows")
        result = await executor.execute_code_blocks(
            [CodeBlock(code="echo 'hello from bash'", language="bash")],
            CancellationToken(),
        )
        assert result.exit_code == 0
        assert "hello from bash" in result.output

    @pytest.mark.asyncio
    async def test_sh_execution(self, executor):
        """Test sh shell execution."""
        result = await executor.execute_code_blocks(
            [CodeBlock(code="echo 'hello from sh'", language="sh")],
            CancellationToken(),
        )
        assert result.exit_code == 0
        assert "hello from sh" in result.output

    @pytest.mark.asyncio
    async def test_shell_execution(self, executor):
        """Test shell execution."""
        result = await executor.execute_code_blocks(
            [CodeBlock(code="echo 'hello from shell'", language="shell")],
            CancellationToken(),
        )
        assert result.exit_code == 0
        assert "hello from shell" in result.output

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeout is enforced."""
        async with LocalCommandLineCodeExecutor(timeout=1) as executor:
            result = await executor.execute_code_blocks(
                [CodeBlock(code="import time; time.sleep(10)", language="python")],
                CancellationToken(),
            )
            assert result.exit_code == 124
            assert "Timeout" in result.output

    @pytest.mark.asyncio
    async def test_cancellation(self):
        """Test cancellation via CancellationToken."""
        async with LocalCommandLineCodeExecutor(timeout=30) as executor:
            token = CancellationToken()

            # Start execution and cancel it
            task = asyncio.create_task(
                executor.execute_code_blocks(
                    [CodeBlock(code="import time; time.sleep(60)", language="python")],
                    token,
                )
            )

            # Cancel after a short delay to ensure process is running
            await asyncio.sleep(0.2)
            token.cancel()

            result = await task
            # Process was killed, so exit code should be non-zero
            assert result.exit_code != 0

    @pytest.mark.asyncio
    async def test_default_working_directory(self):
        """Test that a temp directory is created when none is specified."""
        async with LocalCommandLineCodeExecutor() as executor:
            work_dir = executor.work_dir
            assert work_dir.exists()
            assert work_dir.is_dir()

    @pytest.mark.asyncio
    async def test_custom_working_directory(self, tmp_path):
        """Test custom working directory."""
        custom_dir = tmp_path / "custom_work"
        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            assert executor.work_dir == custom_dir
            assert custom_dir.exists()

    @pytest.mark.asyncio
    async def test_filename_extraction_from_comments(self, tmp_path):
        """Test filename extraction from comments."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            code = "# filename: test_script.py\nprint('executed from file')"
            result = await executor.execute_code_blocks(
                [CodeBlock(code=code, language="python")],
                CancellationToken(),
            )
            assert result.exit_code == 0
            assert "executed from file" in result.output
            # Verify file was created
            assert (custom_dir / "test_script.py").exists()

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_path):
        """Test context manager usage."""
        custom_dir = tmp_path / "work"
        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            result = await executor.execute_code_blocks(
                [CodeBlock(code="print('context manager works')", language="python")],
                CancellationToken(),
            )
            assert result.exit_code == 0
            assert "context manager works" in result.output

    @pytest.mark.asyncio
    async def test_explicit_start_stop(self, tmp_path):
        """Test explicit start/stop lifecycle."""
        custom_dir = tmp_path / "work"
        executor = LocalCommandLineCodeExecutor(work_dir=custom_dir)

        await executor.start()
        result = await executor.execute_code_blocks(
            [CodeBlock(code="print('explicit lifecycle')", language="python")],
            CancellationToken(),
        )
        await executor.stop()

        assert result.exit_code == 0
        assert "explicit lifecycle" in result.output

    @pytest.mark.asyncio
    async def test_restart(self):
        """Test restart functionality."""
        async with LocalCommandLineCodeExecutor() as executor:
            # Execute something
            result1 = await executor.execute_code_blocks(
                [CodeBlock(code="print('before restart')", language="python")],
                CancellationToken(),
            )
            assert result1.exit_code == 0

            # Restart
            await executor.restart()

            # Execute after restart
            result2 = await executor.execute_code_blocks(
                [CodeBlock(code="print('after restart')", language="python")],
                CancellationToken(),
            )
            assert result2.exit_code == 0

    @pytest.mark.asyncio
    async def test_exit_code_non_zero(self, executor):
        """Test that non-zero exit codes are captured."""
        result = await executor.execute_code_blocks(
            [CodeBlock(code="import sys; sys.exit(42)", language="python")],
            CancellationToken(),
        )
        assert result.exit_code == 42

    @pytest.mark.asyncio
    async def test_multiple_code_blocks(self, executor):
        """Test executing multiple code blocks in sequence."""
        blocks = [
            CodeBlock(code="print('first')", language="python"),
            CodeBlock(code="print('second')", language="python"),
        ]
        result = await executor.execute_code_blocks(blocks, CancellationToken())
        assert result.exit_code == 0
        assert "first" in result.output
        assert "second" in result.output

    @pytest.mark.asyncio
    async def test_empty_code_blocks_raises_error(self, executor):
        """Test that empty code blocks raise an error."""
        with pytest.raises(ValueError, match="No code blocks to execute"):
            await executor.execute_code_blocks([], CancellationToken())

    @pytest.mark.asyncio
    async def test_not_running_raises_error(self):
        """Test that using executor without starting raises an error."""
        executor = LocalCommandLineCodeExecutor()
        with pytest.raises(ValueError, match="not running"):
            await executor.execute_code_blocks(
                [CodeBlock(code="print('test')", language="python")],
                CancellationToken(),
            )

    @pytest.mark.asyncio
    async def test_invalid_timeout_raises_error(self):
        """Test that invalid timeout values raise an error."""
        with pytest.raises(ValueError, match="Timeout must be greater"):
            LocalCommandLineCodeExecutor(timeout=0)

    @pytest.mark.asyncio
    async def test_work_dir_property_before_start(self):
        """Test that work_dir property raises error before start."""
        executor = LocalCommandLineCodeExecutor()
        with pytest.raises(RuntimeError, match="not properly initialized"):
            _ = executor.work_dir

    @pytest.mark.asyncio
    async def test_code_file_in_result(self, executor):
        """Test that code_file is set in the result."""
        result = await executor.execute_code_blocks(
            [CodeBlock(code="print('test')", language="python")],
            CancellationToken(),
        )
        assert result.code_file is not None
        assert Path(result.code_file).exists()

    @pytest.mark.asyncio
    async def test_delete_tmp_files(self, tmp_path):
        """Test that temporary files are deleted when delete_tmp_files=True."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir, delete_tmp_files=True) as executor:
            result = await executor.execute_code_blocks(
                [CodeBlock(code="print('temp file test')", language="python")],
                CancellationToken(),
            )
            code_file = result.code_file

        # After context manager exits, file should be deleted
        assert not Path(code_file).exists()

    @pytest.mark.asyncio
    async def test_delete_tmp_files_false(self, tmp_path):
        """Test that temporary files are kept when delete_tmp_files=False."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir, delete_tmp_files=False) as executor:
            result = await executor.execute_code_blocks(
                [CodeBlock(code="print('temp file test')", language="python")],
                CancellationToken(),
            )
            code_file = result.code_file

        # After context manager exits, file should still exist
        assert Path(code_file).exists()


class TestLocalCommandLineCodeExecutorExecuteScript:
    """Test suite for execute_script method."""

    @pytest.fixture
    async def executor(self):
        """Create a local executor for testing."""
        async with LocalCommandLineCodeExecutor(timeout=5) as exec:
            yield exec

    @pytest.mark.asyncio
    async def test_execute_script_success(self, tmp_path):
        """Test successful Python script execution."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        # Create a test script
        script_file = custom_dir / "test_script.py"
        script_file.write_text("print('hello from script')", encoding="utf-8")

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            result = await executor.execute_script(
                "test_script.py",
                cancellation_token=CancellationToken(),
            )
            assert result.exit_code == 0
            assert "hello from script" in result.output
            assert result.code_file is not None

    @pytest.mark.asyncio
    async def test_execute_script_with_absolute_path(self, tmp_path):
        """Test script execution with absolute path."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        script_file = custom_dir / "absolute_script.py"
        script_file.write_text("print('absolute path works')", encoding="utf-8")

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            result = await executor.execute_script(
                str(script_file.absolute()),
                cancellation_token=CancellationToken(),
            )
            assert result.exit_code == 0
            assert "absolute path works" in result.output

    @pytest.mark.asyncio
    async def test_execute_script_with_args(self, tmp_path):
        """Test script execution with command-line arguments."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        script_file = custom_dir / "args_script.py"
        script_content = """
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--verbose", required=True)
args = parser.parse_args()
print(f"input={args.input}, verbose={args.verbose}")
"""
        script_file.write_text(script_content, encoding="utf-8")

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            result = await executor.execute_script(
                "args_script.py",
                args={"input": "data.txt", "verbose": "true"},
                cancellation_token=CancellationToken(),
            )
            assert result.exit_code == 0
            assert "input=data.txt" in result.output
            assert "verbose=true" in result.output

    @pytest.mark.asyncio
    async def test_execute_script_with_positional_args(self, tmp_path):
        """Test script execution with positional arguments."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        script_file = custom_dir / "pos_args_script.py"
        script_content = """
import sys
print(f"args: {sys.argv[1:]}")
"""
        script_file.write_text(script_content, encoding="utf-8")

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            result = await executor.execute_script(
                "pos_args_script.py",
                args={"": "arg1 arg2 arg3"},
                cancellation_token=CancellationToken(),
            )
            assert result.exit_code == 0
            assert "args: ['arg1', 'arg2', 'arg3']" in result.output

    @pytest.mark.asyncio
    async def test_execute_script_file_not_found(self, tmp_path):
        """Test error handling for non-existent script file."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            with pytest.raises(ValueError, match="Script file not found"):
                await executor.execute_script(
                    "non_existent_script.py",
                    cancellation_token=CancellationToken(),
                )

    @pytest.mark.asyncio
    async def test_execute_script_path_traversal(self, tmp_path):
        """Test path traversal prevention."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            with pytest.raises(ValueError, match="outside the working directory"):
                await executor.execute_script(
                    "../../../etc/passwd",
                    cancellation_token=CancellationToken(),
                )

    @pytest.mark.asyncio
    async def test_execute_script_timeout(self, tmp_path):
        """Test script execution timeout."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        script_file = custom_dir / "timeout_script.py"
        script_file.write_text("import time; time.sleep(10)", encoding="utf-8")

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir, timeout=1) as executor:
            result = await executor.execute_script(
                "timeout_script.py",
                cancellation_token=CancellationToken(),
            )
            assert result.exit_code == 124
            assert "Timeout" in result.output

    @pytest.mark.asyncio
    async def test_execute_script_cancellation(self, tmp_path):
        """Test script execution cancellation."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        script_file = custom_dir / "cancel_script.py"
        script_file.write_text("import time; time.sleep(60)", encoding="utf-8")

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir, timeout=30) as executor:
            token = CancellationToken()

            # Start execution and cancel it
            task = asyncio.create_task(
                executor.execute_script(
                    "cancel_script.py",
                    cancellation_token=token,
                )
            )

            # Cancel after a short delay to ensure process is running
            await asyncio.sleep(0.2)
            token.cancel()

            result = await task
            # Process was killed, so exit code should be non-zero
            assert result.exit_code != 0
            assert "cancelled" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_script_not_running(self, tmp_path):
        """Test that using execute_script without starting raises an error."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        executor = LocalCommandLineCodeExecutor(work_dir=custom_dir)
        with pytest.raises(ValueError, match="not running"):
            await executor.execute_script(
                "test.py",
                cancellation_token=CancellationToken(),
            )

    @pytest.mark.asyncio
    async def test_execute_script_directory_path(self, tmp_path):
        """Test error handling when path is a directory."""
        custom_dir = tmp_path / "work"
        custom_dir.mkdir()

        # Create a directory instead of a file
        (custom_dir / "not_a_file").mkdir()

        async with LocalCommandLineCodeExecutor(work_dir=custom_dir) as executor:
            with pytest.raises(ValueError, match="not a file"):
                await executor.execute_script(
                    "not_a_file",
                    cancellation_token=CancellationToken(),
                )
