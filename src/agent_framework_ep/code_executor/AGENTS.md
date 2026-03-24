# code_executor Module

## Overview

Provides a framework for executing code in isolated Docker containers. Solves the security problem of AI Agents safely running user-provided code.

## File Structure

```
code_executor/
├── base.py              # Core abstractions and data structures
├── docker/
│   ├── __init__.py      # Docker module exports
│   └── executor.py      # Docker-based code execution
└── __init__.py          # Public API exports
```

## Files

### base.py

Core abstractions for code execution.

**Classes:**

- `CodeBlock` - Represents a code block with `code` (str) and `language` (str)
- `CodeResult` - Base result class with `exit_code` (int) and `output` (str)
- `CommandLineCodeResult` - Extends `CodeResult` with `code_file` (str | None)
- `CancellationToken` - Async cancellation helper using `asyncio.Event`
  - `cancel()` - Sets cancellation flag
  - `is_cancellation_requested` - Property to check cancellation status
  - `link_future()` - Links a Future/Task to this token
- `CodeExecutor` (ABC) - Abstract base for code executors
  - `execute_code_blocks()` - Execute list of code blocks
  - `start()` / `stop()` / `restart()` - Lifecycle management
  - Async context manager support (`__aenter__` / `__aexit__`)

**Functions:**

- `lang_to_cmd(lang)` - Maps language to command (python, bash, pwsh, etc.)
- `silence_pip(code, lang)` - Adds `-qqq` to pip install commands
- `get_file_name_from_content(code, workspace_path)` - Extracts filename from `# filename: xxx` comment

### docker/executor.py

Docker container implementation of code execution.

**Classes:**

- `DockerCommandLineCodeExecutorConfig` - Pydantic config model for executor settings (image, timeout, volumes, etc.)

- `DockerCommandLineCodeExecutor` - Concrete executor using Docker
  - Supports: bash, shell, sh, pwsh, powershell, ps1, python
  - `execute_code_blocks()` - Runs code in container with timeout
  - `execute_script()` - Runs external Python scripts with arguments
  - `start()` - Creates/starts Docker container, pulls image if needed
  - `stop()` - Stops container, cleans up temp files
  - `restart()` - Restarts the container
  - `to_config()` / `from_config()` - Serialization support

**Internal:**
- `_execute_command()` - Runs command in container with cancellation support
- `_kill_running_command()` - Terminates running command via pkill

### __init__.py

Public API exports.

**Classes:**

- `CodeExecutionTool` - Wrapper for simplified code execution
  - `execute_code(code, language)` - Execute single code block, returns output string

**Exports:** `CodeBlock`, `CodeExecutor`, `CodeResult`, `CommandLineCodeResult`, `CancellationToken`, `CodeExecutionTool`, `DockerCommandLineCodeExecutor`, `DockerCommandLineCodeExecutorConfig`, utility functions

### docker/__init__.py

Exports `DockerCommandLineCodeExecutor` and `DockerCommandLineCodeExecutorConfig`
