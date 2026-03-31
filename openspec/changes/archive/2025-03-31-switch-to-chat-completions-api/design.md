## Context

Microsoft Agent Framework rc6 提供了两个 OpenAI 客户端：

| 客户端 | API 类型 | reasoning 处理 |
|--------|----------|----------------|
| `OpenAIChatClient` | Responses API | 内置处理 `item.type == "reasoning"` |
| `OpenAIChatCompletionClient` | Chat Completions API | 不处理 `message.reasoning_content` |

国产大模型（DeepSeek、Kimi、Qwen）使用 Chat Completions API，返回 `message.reasoning_content` 字段。

当前 `OpenAILikeChatClient` 继承 `OpenAIChatClient`，与国产大模型不兼容。

## Goals / Non-Goals

**Goals:**
- 创建 `OpenAILikeChatCompletionClient` 继承 `OpenAIChatCompletionClient`
- 使用 Chat Completions API，兼容国产大模型
- 保留 reasoning content 处理逻辑
- 保持外部 API 兼容性（`OpenAILikeChatClient` 作为别名）

**Non-Goals:**
- 不支持 OpenAI Responses API
- 不修改 `code_executor` 和 `skills_provider` 模块

## Decisions

### Decision 1: 类命名

**选择**: 新类名为 `OpenAILikeChatCompletionClient`，保留 `OpenAILikeChatClient` 作为别名

**理由**:
- 类名清晰表明使用 Chat Completions API
- 与父类 `OpenAIChatCompletionClient` 命名一致
- 别名保证向后兼容

```python
# 新主类
class OpenAILikeChatCompletionClient(ResponseFormatMixin, ReasoningContentMixin, OpenAIChatCompletionClient):
    ...

# 向后兼容别名
OpenAILikeChatClient = OpenAILikeChatCompletionClient
```

### Decision 2: 父类切换

**选择**: `OpenAILikeChatClient` 继承 `OpenAIChatCompletionClient`

**理由**:
- 国产大模型使用 Chat Completions API
- `OpenAIChatCompletionClient` 提供了 `_parse_response_update_from_openai` 方法（流式）
- 不需要 `_parse_chunk_from_openai`（Responses API 专用）

**方法对比**:

| 方法 | OpenAIChatClient | OpenAIChatCompletionClient |
|------|------------------|---------------------------|
| `_prepare_options` | ✓ | ✓ |
| `_prepare_messages_for_openai` | ✓ | ✓ |
| `_prepare_message_for_openai` | ✓ | ✓ |
| `_parse_response_from_openai` | ✓ | ✓ |
| `_parse_response_update_from_openai` | ✗ | ✓ |
| `_parse_chunk_from_openai` | ✓ | ✗ |

### Decision 2: Reasoning 处理逻辑

**选择**: 保留现有的 `_extract_reasoning_from_response` 和 `_extract_reasoning_from_update`

**理由**:
- `OpenAIChatCompletionClient` 不处理 `message.reasoning_content`
- 国产大模型返回 `message.reasoning_content` 字段
- 需要我们的逻辑来提取和累积 reasoning

### Decision 3: 移除 `_accumulate_reasoning_in_update`

**选择**: 移除此方法，恢复使用 `_extract_reasoning_from_update`

**理由**:
- `OpenAIChatCompletionClient` 使用 `_parse_response_update_from_openai`
- 该方法接收原始 `chunk` 参数，可以直接提取 `delta.reasoning_content`
- 不需要从 `ChatResponseUpdate.contents` 累积

## Risks / Trade-offs

### Risk 1: OpenAI 官方模型兼容性

**风险**: 不支持 OpenAI Responses API 的新特性

**缓解**: 
- 用户如需 OpenAI 官方模型，可直接使用 `OpenAIChatClient`
- 文档说明 `OpenAILikeChatClient` 主要用于国产大模型

### Risk 2: 方法签名差异

**风险**: `_parse_response_update_from_openai` 签名可能与当前实现不同

**缓解**: 
- 检查父类方法签名，确保兼容
- 运行测试验证

## Migration Plan

1. 修改 `OpenAILikeChatClient` 继承关系
2. 恢复 `_parse_response_update_from_openai` 方法重写
3. 移除 `_parse_chunk_from_openai` 和 `_accumulate_reasoning_in_update`
4. 运行测试验证
5. 更新文档