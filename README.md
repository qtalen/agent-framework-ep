# agent-framework-ep

Microsoft Agent Framework extensions for mainstream open-source LLMs, including structured output support for GLM, Kimi, Qwen, and DeepSeek, along with reasoning_content support. Plus a local containerized code interpreter environment. 'ep' stands for enterprise-level applications.

## Features

- **OpenAI-like Client Extensions** (`openai_like`)
  - Structured output parsing with JSON fallback (dirtyjson, json-repair)
  - Reasoning content support for DeepSeek-R1 style models
  - Compatible with Microsoft Agent Framework's OpenAIChatClient

- **Code Executor** (`code_executor`)
  - Docker-based code execution environment
  - Supports Python, bash, and shell scripts
  - Timeout and cancellation support
  - Isolated execution for security

- **Dynamic Skills Provider** (`skills_provider`)
  - Async skill updates before each agent run
  - Extendable skills from external sources

## Installation

```bash
pip install agent-framework-ep
```

Or with uv:

```bash
uv add agent-framework-ep
```

### Prerequisites

- Python 3.12+
- Docker (for code execution features)

## Quick Start

### OpenAI-like Client with Structured Output

```python
from pydantic import BaseModel
from agent_framework import Agent
from agent_framework_ep import OpenAILikeChatClient

class Response(BaseModel):
    answer: str
    confidence: float

# Create client with structured output support
client = OpenAILikeChatClient(
    model="deepseek-chat",
    api_key="your-api-key"
)

# Use with Agent framework
agent = Agent(client=client)
response = await agent.run(
    "What is the capital of France?",
    response_format=Response
)
print(response)  # Parsed Response object
```

### Code Execution

```python
import asyncio
import os
from agent_framework_ep import DockerCommandLineCodeExecutor
from agent_framework_ep import OpenAILikeChatClient, CodeExecutionTool

chat_client = OpenAILikeChatClient(
    model_id="kimi/kimi-k2.5",
)

code_executor = DockerCommandLineCodeExecutor(
    image="python-code-sandbox",
    work_dir="some_of_your_working_directory",
    delete_tmp_files=True,
    environment={
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY"),
    }
)

code_tool = CodeExecutionTool(code_executor).execute_code

agent = chat_client.as_agent(
    name="SkillsAssistant",
    instructions="You're a helpful assistant.",
    tools=[code_tool],
)
```

### Dynamic Skills Provider

```python
from agent_framework_ep import UpdatableSkillsProvider
from agent_framework import Skill

async def fetch_dynamic_skills():
    # Fetch skills from external source
    return [
        Skill(name="web-search", description="Search the web", content="..."),
    ]

provider = UpdatableSkillsProvider(
    skill_paths="./skills",
    skills_updater=fetch_dynamic_skills
)
```

## Development

```bash
# Clone the repository
git clone https://github.com/qianpeng/agent-framework-ep.git
cd agent-framework-ep

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with Docker (requires Docker)
uv run pytest -m docker

# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run mypy src/agent_framework_ep
```

## License

MIT License - see [LICENSE](LICENSE) for details.
