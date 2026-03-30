"""Agent Framework EP - Microsoft Agent Framework extensions for open-source LLMs."""

from agent_framework_ep.code_executor import (
    CodeExecutionTool,
    DockerCommandLineCodeExecutor,
    DockerCommandLineCodeExecutorConfig,
    LocalCommandLineCodeExecutor,
    get_file_name_from_content,
)
from agent_framework_ep.openai_like import (
    OpenAILikeChatClient,
    get_reasoning_content,
)
from agent_framework_ep.skills_provider import UpdatableSkillsProvider

try:
    from agent_framework_ep._version import __version__
except ImportError:
    # Development mode (package not installed, _version.py not generated)
    __version__ = "0.0.0+dev"

__all__ = [
    # Version
    "__version__",
    # Code Executor
    "CodeExecutionTool",
    "DockerCommandLineCodeExecutor",
    "DockerCommandLineCodeExecutorConfig",
    "LocalCommandLineCodeExecutor",
    "get_file_name_from_content",
    # OpenAI Like
    "OpenAILikeChatClient",
    "get_reasoning_content",
    # Skills Provider
    "UpdatableSkillsProvider",
]
