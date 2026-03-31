"""Tests for DockerCommandLineCodeExecutor."""

import asyncio
from pathlib import Path

import pytest

from agent_framework_ep.code_executor import (
    CancellationToken,
    CodeBlock,
    DockerCommandLineCodeExecutor,
    DockerCommandLineCodeExecutorConfig,
)

# Docker image to use for tests
TEST_IMAGE = "python:3.12-slim-bookworm"


class TestDockerCommandLineCodeExecutorInitialization:
    """Tests for DockerCommandLineCodeExecutor initialization."""

    def test_default_initialization(self) -> None:
        """Test executor can be initialized with defaults."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        assert executor.timeout == 60
        assert executor.container_name.startswith("code-exec-")

    def test_custom_timeout(self) -> None:
        """Test executor with custom timeout."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE, timeout=120)
        assert executor.timeout == 120

    def test_invalid_timeout(self) -> None:
        """Test executor raises ValueError for invalid timeout."""
        with pytest.raises(ValueError, match="Timeout must be greater than or equal to 1"):
            DockerCommandLineCodeExecutor(image=TEST_IMAGE, timeout=0)

    def test_custom_container_name(self) -> None:
        """Test executor with custom container name."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE, container_name="my-container")
        assert executor.container_name == "my-container"

    def test_custom_work_dir(self, tmp_path: Path) -> None:
        """Test executor with custom work directory."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE, work_dir=tmp_path)
        assert executor.work_dir == tmp_path

    def test_work_dir_created_if_not_exists(self, tmp_path: Path) -> None:
        """Test executor creates work directory if it doesn't exist."""
        new_dir = tmp_path / "new_workspace"
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE, work_dir=new_dir)
        assert new_dir.exists()
        assert executor.work_dir == new_dir

    def test_supported_languages(self) -> None:
        """Test SUPPORTED_LANGUAGES contains expected values."""
        expected = ["bash", "shell", "sh", "pwsh", "powershell", "ps1", "python"]
        assert expected == DockerCommandLineCodeExecutor.SUPPORTED_LANGUAGES


@pytest.mark.docker
class TestDockerCommandLineCodeExecutorLifecycle:
    """Tests for DockerCommandLineCodeExecutor lifecycle (requires Docker)."""

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self) -> None:
        """Test executor can start and stop."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        await executor.start()
        assert executor._running
        await executor.stop()
        assert not executor._running

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test executor works as async context manager."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            assert executor._running
        assert not executor._running

    @pytest.mark.asyncio
    async def test_stop_idempotent(self) -> None:
        """Test stopping an already stopped executor doesn't raise."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        await executor.start()
        await executor.stop()
        # Should not raise
        await executor.stop()

    @pytest.mark.asyncio
    async def test_restart(self) -> None:
        """Test executor can be restarted."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        await executor.start()
        await executor.restart()
        assert executor._running
        await executor.stop()

    @pytest.mark.asyncio
    async def test_restart_without_start_raises(self) -> None:
        """Test restart raises if executor hasn't been started."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        with pytest.raises(ValueError, match="Container is not running"):
            await executor.restart()


@pytest.mark.docker
class TestDockerCommandLineCodeExecutorExecution:
    """Tests for code execution (requires Docker)."""

    @pytest.mark.asyncio
    async def test_execute_python_code_success(self) -> None:
        """Test executing simple Python code."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            code_block = CodeBlock(code="print('hello world')", language="python")
            result = await executor.execute_code_blocks([code_block], CancellationToken())
            assert result.exit_code == 0
            assert "hello world" in result.output

    @pytest.mark.asyncio
    async def test_execute_python_code_with_error(self) -> None:
        """Test executing Python code that raises an error."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            code_block = CodeBlock(code="raise ValueError('test error')", language="python")
            result = await executor.execute_code_blocks([code_block], CancellationToken())
            assert result.exit_code != 0
            assert "ValueError" in result.output

    @pytest.mark.asyncio
    async def test_execute_bash_code(self) -> None:
        """Test executing bash code."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            code_block = CodeBlock(code="echo 'hello from bash'", language="bash")
            result = await executor.execute_code_blocks([code_block], CancellationToken())
            assert result.exit_code == 0
            assert "hello from bash" in result.output

    @pytest.mark.asyncio
    async def test_execute_multiple_code_blocks(self) -> None:
        """Test executing multiple code blocks in sequence.

        Note: Each code block runs in a separate file, so state doesn't persist.
        """
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            code_blocks = [
                CodeBlock(code="x = 1; print('first')", language="python"),
                CodeBlock(code="print('second')", language="python"),
            ]
            result = await executor.execute_code_blocks(code_blocks, CancellationToken())
            assert result.exit_code == 0
            assert "first" in result.output
            assert "second" in result.output

    @pytest.mark.asyncio
    async def test_execute_empty_code_blocks_raises(self) -> None:
        """Test executing empty code blocks raises ValueError."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            with pytest.raises(ValueError, match="No code blocks to execute"):
                await executor.execute_code_blocks([], CancellationToken())

    @pytest.mark.asyncio
    async def test_execute_without_start_raises(self) -> None:
        """Test executing without starting raises ValueError."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        code_block = CodeBlock(code="print('hello')", language="python")
        with pytest.raises(ValueError, match="Container is not running"):
            await executor.execute_code_blocks([code_block], CancellationToken())

    @pytest.mark.asyncio
    async def test_execute_script(self) -> None:
        """Test execute_script method."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            # Create a script file in the workspace
            script_path = executor.work_dir / "test_script.py"
            script_path.write_text("print('from script')")

            result = await executor.execute_script("test_script.py")
            assert result.exit_code == 0
            assert "from script" in result.output

    @pytest.mark.asyncio
    async def test_execute_script_with_args(self) -> None:
        """Test execute_script with command line arguments."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            script_path = executor.work_dir / "args_script.py"
            script_path.write_text("import sys; print(sys.argv)")

            result = await executor.execute_script("args_script.py", args={"name": "test", "value": "123"})
            assert result.exit_code == 0
            assert "--name" in result.output
            assert "test" in result.output


@pytest.mark.docker
class TestDockerCommandLineCodeExecutorTimeout:
    """Tests for timeout behavior (requires Docker)."""

    @pytest.mark.asyncio
    async def test_execution_timeout(self) -> None:
        """Test code execution times out."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE, timeout=1) as executor:
            # Code that sleeps longer than timeout
            code_block = CodeBlock(code="import time; time.sleep(10)", language="python")
            result = await executor.execute_code_blocks([code_block], CancellationToken())
            # Timeout exit code is typically 124
            assert result.exit_code == 124 or "Timeout" in result.output


@pytest.mark.docker
class TestDockerCommandLineCodeExecutorCancellation:
    """Tests for cancellation behavior (requires Docker)."""

    @pytest.mark.asyncio
    async def test_cancellation(self) -> None:
        """Test code execution can be cancelled."""
        async with DockerCommandLineCodeExecutor(image=TEST_IMAGE) as executor:
            token = CancellationToken()

            # Start long-running execution
            code_block = CodeBlock(code="import time; time.sleep(30)", language="python")
            task = asyncio.create_task(executor.execute_code_blocks([code_block], token))

            # Cancel after a short delay
            await asyncio.sleep(0.5)
            token.cancel()

            result = await task
            assert "cancelled" in result.output.lower() or result.exit_code != 0


class TestDockerCommandLineCodeExecutorConfig:
    """Tests for configuration serialization."""

    def test_to_config(self, tmp_path: Path) -> None:
        """Test to_config method."""
        executor = DockerCommandLineCodeExecutor(
            image=TEST_IMAGE,
            container_name="test-container",
            timeout=120,
            work_dir=tmp_path,
            auto_remove=False,
        )
        config = executor.to_config()

        assert config.image == TEST_IMAGE
        assert config.container_name == "test-container"
        assert config.timeout == 120
        assert config.work_dir == str(tmp_path)
        assert config.auto_remove is False

    def test_from_config(self, tmp_path: Path) -> None:
        """Test from_config class method."""
        config = DockerCommandLineCodeExecutorConfig(
            image=TEST_IMAGE,
            container_name="test-container",
            timeout=120,
            work_dir=str(tmp_path),
        )
        executor = DockerCommandLineCodeExecutor.from_config(config)

        assert executor._image == TEST_IMAGE
        assert executor.container_name == "test-container"
        assert executor.timeout == 120
        assert str(executor.work_dir) == str(tmp_path)

    def test_config_roundtrip(self, tmp_path: Path) -> None:
        """Test config roundtrip (to_config -> from_config)."""
        original = DockerCommandLineCodeExecutor(
            image=TEST_IMAGE,
            container_name="test-container",
            timeout=120,
            work_dir=tmp_path,
            auto_remove=False,
            delete_tmp_files=True,
        )
        config = original.to_config()
        restored = DockerCommandLineCodeExecutor.from_config(config)

        assert restored._image == original._image
        assert restored.container_name == original.container_name
        assert restored.timeout == original.timeout
        assert restored._auto_remove == original._auto_remove
        assert restored._delete_tmp_files == original._delete_tmp_files


class TestDockerCommandLineCodeExecutorProperties:
    """Tests for executor properties."""

    def test_work_dir_without_init_raises(self) -> None:
        """Test work_dir property raises if not initialized."""
        # Create executor without work_dir and without starting
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE)
        # Accessing work_dir before start should raise
        with pytest.raises(RuntimeError, match="Working directory not properly initialized"):
            _ = executor.work_dir

    def test_bind_dir_defaults_to_work_dir(self, tmp_path: Path) -> None:
        """Test bind_dir defaults to work_dir."""
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE, work_dir=tmp_path)
        assert executor.bind_dir == tmp_path

    def test_custom_bind_dir(self, tmp_path: Path) -> None:
        """Test custom bind_dir."""
        bind_path = tmp_path / "bind"
        executor = DockerCommandLineCodeExecutor(image=TEST_IMAGE, work_dir=tmp_path, bind_dir=bind_path)
        assert executor.bind_dir == bind_path
