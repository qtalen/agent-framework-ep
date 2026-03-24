"""Tests for code_executor base module."""

import asyncio
from pathlib import Path

import pytest

from agent_framework_ep.code_executor import (
    CancellationToken,
    CodeBlock,
    CodeResult,
    CommandLineCodeResult,
    get_file_name_from_content,
    lang_to_cmd,
    silence_pip,
)


class TestCodeBlock:
    """Tests for CodeBlock dataclass."""

    def test_code_block_creation(self) -> None:
        """Test CodeBlock can be created with code and language."""
        block = CodeBlock(code="print('hello')", language="python")
        assert block.code == "print('hello')"
        assert block.language == "python"

    def test_code_block_multiple_lines(self) -> None:
        """Test CodeBlock handles multi-line code."""
        code = "line1\nline2\nline3"
        block = CodeBlock(code=code, language="bash")
        assert block.code == code
        assert block.language == "bash"


class TestCodeResult:
    """Tests for CodeResult dataclass."""

    def test_code_result_creation(self) -> None:
        """Test CodeResult can be created."""
        result = CodeResult(exit_code=0, output="success")
        assert result.exit_code == 0
        assert result.output == "success"

    def test_code_result_error(self) -> None:
        """Test CodeResult with error exit code."""
        result = CodeResult(exit_code=1, output="error message")
        assert result.exit_code == 1
        assert result.output == "error message"


class TestCommandLineCodeResult:
    """Tests for CommandLineCodeResult class."""

    def test_command_line_code_result_creation(self) -> None:
        """Test CommandLineCodeResult can be created."""
        result = CommandLineCodeResult(exit_code=0, output="success", code_file="test.py")
        assert result.exit_code == 0
        assert result.output == "success"
        assert result.code_file == "test.py"

    def test_command_line_code_result_without_code_file(self) -> None:
        """Test CommandLineCodeResult without optional code_file."""
        result = CommandLineCodeResult(exit_code=0, output="success")
        assert result.exit_code == 0
        assert result.output == "success"
        assert result.code_file is None


class TestCancellationToken:
    """Tests for CancellationToken class."""

    def test_cancellation_token_initial_state(self) -> None:
        """Test CancellationToken starts not cancelled."""
        token = CancellationToken()
        assert not token.is_cancellation_requested

    def test_cancellation_token_cancel(self) -> None:
        """Test CancellationToken can be cancelled."""
        token = CancellationToken()
        token.cancel()
        assert token.is_cancellation_requested

    @pytest.mark.asyncio
    async def test_cancellation_token_link_future_cancels_task(self) -> None:
        """Test CancellationToken cancels linked future when cancelled."""
        token = CancellationToken()

        async def long_running_task() -> str:
            await asyncio.sleep(10)
            return "completed"

        task = asyncio.create_task(long_running_task())
        token.link_future(task)

        # Cancel the token
        token.cancel()

        # Wait a bit for the cancellation to propagate
        await asyncio.sleep(0.1)

        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_cancellation_token_link_future_already_done(self) -> None:
        """Test CancellationToken handles already done futures."""
        token = CancellationToken()

        async def quick_task() -> str:
            return "completed"

        task = asyncio.create_task(quick_task())
        await asyncio.sleep(0)  # Let task complete

        # Should not raise even though task is done
        token.link_future(task)
        assert task.done()

    @pytest.mark.asyncio
    async def test_cancellation_token_watcher_task_saved(self) -> None:
        """Test that link_future saves watcher task to prevent garbage collection."""
        token = CancellationToken()

        async def long_running_task() -> str:
            await asyncio.sleep(10)
            return "completed"

        task = asyncio.create_task(long_running_task())
        token.link_future(task)

        # Verify _watcher_task is saved
        assert token._watcher_task is not None
        assert isinstance(token._watcher_task, asyncio.Task)
        assert not token._watcher_task.done()

        # Clean up
        token.cancel()
        await asyncio.sleep(0.1)


class TestLangToCmd:
    """Tests for lang_to_cmd function."""

    @pytest.mark.parametrize(
        ("lang", "expected"),
        [
            ("python", "python"),
            ("Python", "python"),
            ("py", "python"),
            ("bash", "bash"),
            ("sh", "sh"),
            ("shell", "sh"),
        ],
    )
    def test_lang_to_cmd_valid(self, lang: str, expected: str) -> None:
        """Test lang_to_cmd with valid languages."""
        assert lang_to_cmd(lang) == expected

    def test_lang_to_cmd_python_variants(self) -> None:
        """Test lang_to_cmd handles python variants."""
        for lang in ["python", "Python", "py", "PYTHON"]:
            assert lang_to_cmd(lang) == "python"

    def test_lang_to_cmd_unsupported(self) -> None:
        """Test lang_to_cmd raises ValueError for unsupported language."""
        with pytest.raises(ValueError, match="Unsupported language: ruby"):
            lang_to_cmd("ruby")

    def test_lang_to_cmd_powershell(self) -> None:
        """Test lang_to_cmd handles powershell variants."""
        # This may return pwsh or powershell depending on what's installed
        # Just verify it doesn't raise
        for lang in ["pwsh", "powershell", "ps1", "POWERSHELL"]:
            try:
                result = lang_to_cmd(lang)
                assert result in ["pwsh", "powershell"]
            except ValueError as e:
                # If neither is installed, it raises
                assert "Powershell or pwsh is not installed" in str(e)


class TestSilencePip:
    """Tests for silence_pip function."""

    def test_silence_pip_python_code(self) -> None:
        """Test silence_pip adds -qqq to pip install in python code."""
        code = "!pip install requests"
        result = silence_pip(code, "python")
        assert "-qqq" in result

    def test_silence_pip_bash_code(self) -> None:
        """Test silence_pip adds -qqq to pip install in bash code."""
        code = "pip install numpy"
        result = silence_pip(code, "bash")
        assert "-qqq" in result

    def test_silence_pip_no_pip_install(self) -> None:
        """Test silence_pip leaves non-pip code unchanged."""
        code = "print('hello world')"
        result = silence_pip(code, "python")
        assert result == code

    def test_silence_pip_already_quiet(self) -> None:
        """Test silence_pip doesn't duplicate -qqq if already present."""
        code = "!pip install -qqq requests"
        result = silence_pip(code, "python")
        # Should only have one -qqq
        assert result.count("-qqq") == 1

    def test_silence_pip_multiple_lines(self) -> None:
        """Test silence_pip handles multi-line code."""
        code = "!pip install requests\n!pip install numpy"
        result = silence_pip(code, "python")
        assert result.count("-qqq") == 2

    def test_silence_pip_unsupported_lang(self) -> None:
        """Test silence_pip returns unchanged for unsupported language."""
        code = "pip install requests"
        result = silence_pip(code, "ruby")
        assert result == code


class TestGetFileNameFromContent:
    """Tests for get_file_name_from_content function."""

    def test_get_file_name_from_content_with_filename(self, tmp_path: Path) -> None:
        """Test extracting filename from code comment."""
        code = "# filename: test.py\nprint('hello')"
        # Create the file so resolve() works
        (tmp_path / "test.py").write_text("print('hello')")
        result = get_file_name_from_content(code, tmp_path)
        assert result == "test.py"

    def test_get_file_name_from_content_without_filename(self, tmp_path: Path) -> None:
        """Test returns None when no filename comment."""
        code = "print('hello')"
        result = get_file_name_from_content(code, tmp_path)
        assert result is None

    def test_get_file_name_from_content_different_comment(self, tmp_path: Path) -> None:
        """Test returns None for different comment types."""
        code = "# This is a comment\nprint('hello')"
        result = get_file_name_from_content(code, tmp_path)
        assert result is None

    def test_get_file_name_from_content_path_traversal(self, tmp_path: Path) -> None:
        """Test get_file_name_from_content prevents path traversal."""
        code = "# filename: ../../etc/passwd\nprint('hello')"
        result = get_file_name_from_content(code, tmp_path)
        # Should not return the path traversal path
        assert result is None or ".." not in result

    def test_get_file_name_from_content_relative_path(self, tmp_path: Path) -> None:
        """Test get_file_name_from_content with relative path."""
        code = "# filename: subdir/test.py\nprint('hello')"
        # Create the directory and file so resolve() works
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test.py").write_text("print('hello')")
        result = get_file_name_from_content(code, tmp_path)
        # Should return relative path within workspace (platform-independent)
        assert result == str(Path("subdir") / "test.py")
