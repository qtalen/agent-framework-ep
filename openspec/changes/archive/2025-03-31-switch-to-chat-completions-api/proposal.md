## Why

当前 `OpenAILikeChatClient` 继承 `OpenAIChatClient`，使用 OpenAI Responses API。但国产大模型（DeepSeek、Kimi、Qwen 等）使用 Chat Completions API，返回 `message.reasoning_content` 字段，与 Responses API 不兼容。

Microsoft Agent Framework rc6 提供了 `OpenAIChatCompletionClient`，使用 Chat Completions API，更适合国产大模型。

## What Changes

- **BREAKING**: `OpenAILikeChatClient` 重命名为 `OpenAILikeChatCompletionClient`
- 继承 `OpenAIChatCompletionClient`，使用 Chat Completions API
- 保留 reasoning content 处理逻辑（`OpenAIChatCompletionClient` 不内置处理）
- 流式响应方法恢复为 `_parse_response_update_from_openai`
- 移除 `_accumulate_reasoning_in_update` 方法（不再需要）
- 保留 `OpenAILikeChatClient` 作为别名（向后兼容）

## Capabilities

### Modified Capabilities

- `openai-like-client`: 改为使用 Chat Completions API，兼容国产大模型，类名更清晰

## Impact

- **代码变更**:
  - `src/agent_framework_ep/openai_like/__init__.py` - 更改父类继承
  - `src/agent_framework_ep/openai_like/_reasoning_content.py` - 恢复原有 reasoning 处理逻辑
- **API 兼容**: 外部 API 保持不变，`get_reasoning_content()` 函数行为一致
- **模型兼容**: DeepSeek、Kimi、Qwen 等国产大模型完全兼容
- **测试影响**: 需要更新测试以适配新父类

## Non-goals

- 不支持 OpenAI Responses API（用户应使用官方 `OpenAIChatClient`）
- 不修改 `code_executor` 和 `skills_provider` 模块
- 不添加新的 reasoning 来源类型