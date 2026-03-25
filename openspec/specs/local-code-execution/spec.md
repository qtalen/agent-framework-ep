# Local Code Execution Capability

This specification defines the requirements for local code execution support in the agent framework.

## Requirements

### Requirement: Local code execution support
The system SHALL provide a `LocalCommandLineCodeExecutor` class that executes code blocks directly on the host machine using subprocess.

#### Scenario: Execute Python code locally
- **WHEN** a code block with language "python" is passed to `execute_code_blocks()`
- **THEN** the code SHALL be executed using the local Python interpreter
- **AND** the exit code and output SHALL be returned in a `CommandLineCodeResult`

#### Scenario: Execute shell code locally
- **WHEN** a code block with language "bash", "shell", or "sh" is passed to `execute_code_blocks()`
- **THEN** the code SHALL be executed using the appropriate shell interpreter
- **AND** the exit code and output SHALL be returned

#### Scenario: Execute PowerShell code locally
- **WHEN** a code block with language "pwsh", "powershell", or "ps1" is passed to `execute_code_blocks()`
- **THEN** the code SHALL be executed using PowerShell if available on the system
- **AND** the exit code and output SHALL be returned

### Requirement: Timeout support
The system SHALL enforce a configurable timeout on code execution.

#### Scenario: Execution times out
- **WHEN** code execution exceeds the configured timeout
- **THEN** the process SHALL be terminated
- **AND** the result SHALL indicate timeout with exit code 124

### Requirement: Cancellation support
The system SHALL support cancellation of running code execution via `CancellationToken`.

#### Scenario: User cancels execution
- **WHEN** a `CancellationToken` is cancelled during execution
- **THEN** the running process SHALL be terminated
- **AND** the result SHALL indicate cancellation

### Requirement: Working directory management
The system SHALL execute code in a configurable working directory.

#### Scenario: Default working directory
- **WHEN** no working directory is specified
- **THEN** a temporary directory SHALL be created for execution

#### Scenario: Custom working directory
- **WHEN** a working directory is specified
- **THEN** code SHALL be executed in that directory

### Requirement: CodeExecutor interface compliance
The system SHALL implement the full `CodeExecutor` abstract base class interface.

#### Scenario: Context manager usage
- **WHEN** the executor is used as an async context manager
- **THEN** `start()` SHALL be called on entry
- **AND** `stop()` SHALL be called on exit

#### Scenario: Lifecycle management
- **WHEN** `start()` is called
- **THEN** the executor SHALL be ready to execute code
- **WHEN** `stop()` is called
- **THEN** resources SHALL be released
- **WHEN** `restart()` is called
- **THEN** the executor SHALL reset to initial state

### Requirement: File extraction from comments
The system SHALL support extracting filenames from code comments.

#### Scenario: Filename comment extraction
- **WHEN** code contains a comment like `# filename: path/to/file.py`
- **THEN** the code SHALL be saved to that path relative to the working directory
- **AND** that file SHALL be executed

### Requirement: Local Python script execution
The `LocalCommandLineCodeExecutor` SHALL support executing local Python script files (.py) with optional command-line arguments.

#### Scenario: Execute Python script successfully
- **WHEN** `execute_script()` is called with a valid Python script path
- **THEN** the script SHALL be executed using the local Python interpreter
- **AND** the exit code and output SHALL be returned in a `CommandLineCodeResult`

#### Scenario: Execute script with arguments
- **WHEN** `execute_script()` is called with `args` dictionary
- **THEN** the arguments SHALL be converted to command-line format (`--key value`)
- **AND** positional arguments (empty key) SHALL be passed as-is
- **AND** the script SHALL receive these arguments

#### Scenario: Script file not found
- **WHEN** `execute_script()` is called with a non-existent script path
- **THEN** a `ValueError` SHALL be raised with a clear error message

#### Scenario: Script with relative path
- **WHEN** `execute_script()` is called with a relative script path
- **THEN** the path SHALL be resolved relative to the working directory
- **AND** the script SHALL be executed if found

#### Scenario: Script execution timeout
- **WHEN** script execution exceeds the configured timeout
- **THEN** the process SHALL be terminated
- **AND** the result SHALL indicate timeout with exit code 124

#### Scenario: Script execution cancellation
- **WHEN** a `CancellationToken` is cancelled during script execution
- **THEN** the running process SHALL be terminated
- **AND** the result SHALL indicate cancellation

#### Scenario: Security - path traversal prevention
- **WHEN** `execute_script()` is called with a path attempting directory traversal (e.g., `../../../etc/passwd`)
- **THEN** the path SHALL be validated against the working directory
- **AND** a `ValueError` SHALL be raised if the resolved path is outside the working directory
