"""Agent Framework EP - Microsoft Agent Framework extensions for open-source LLMs."""

from agent_framework_ep.code_executor import (
    CancellationToken,
    CodeBlock,
    CodeExecutionTool,
    CodeExecutor,
    CodeResult,
    CommandLineCodeResult,
    DockerCommandLineCodeExecutor,
    DockerCommandLineCodeExecutorConfig,
    get_file_name_from_content,
    lang_to_cmd,
    silence_pip,
)
from agent_framework_ep.openai_like import (
    OpenAILikeChatClient,
    StructuredOutputParseError,
    get_reasoning_content,
)
from agent_framework_ep.skills_provider import UpdatableSkillsProvider

__all__ = [
    # Code Executor
    "CodeBlock",
    "CodeExecutor",
    "CodeResult",
    "CommandLineCodeResult",
    "CancellationToken",
    "CodeExecutionTool",
    "DockerCommandLineCodeExecutor",
    "DockerCommandLineCodeExecutorConfig",
    "lang_to_cmd",
    "silence_pip",
    "get_file_name_from_content",
    # OpenAI Like
    "OpenAILikeChatClient",
    "get_reasoning_content",
    "StructuredOutputParseError",
    # Skills Provider
    "UpdatableSkillsProvider",
]

__version__ = "0.1.0"
