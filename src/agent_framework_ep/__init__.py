"""Agent Framework EP - Microsoft Agent Framework extensions for open-source LLMs."""

from agent_framework_ep.code_executor import (
    CodeExecutionTool,
    DockerCommandLineCodeExecutor,
    DockerCommandLineCodeExecutorConfig,
    get_file_name_from_content,
)
from agent_framework_ep.openai_like import (
    OpenAILikeChatClient,
    get_reasoning_content,
)
from agent_framework_ep.skills_provider import UpdatableSkillsProvider

__all__ = [
    # Code Executor
    "CodeExecutionTool",
    "DockerCommandLineCodeExecutor",
    "DockerCommandLineCodeExecutorConfig",
    "get_file_name_from_content",
    # OpenAI Like
    "OpenAILikeChatClient",
    "get_reasoning_content",
    # Skills Provider
    "UpdatableSkillsProvider",
]

__version__ = "0.1.3"
