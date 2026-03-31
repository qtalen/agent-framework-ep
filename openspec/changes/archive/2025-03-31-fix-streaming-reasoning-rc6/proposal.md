## Why

Microsoft Agent Framework 升级至 1.0.0rc6 版本，对流式响应 API 进行了重大重构。原有的 `_parse_response_update_from_openai(chunk)` 方法被废弃，改为 `_parse_chunk_from_openai(event, options, function_call_ids)` 新 API。当前项目的 `OpenAILikeChatClient` 重写了旧方法，但父类已不再调用它，导致流式响应中的 reasoning content 提取功能完全失效。

## What Changes

- **BREAKING**: 重命名 `_parse_response_update_from_openai` 为 `_parse_chunk_from_openai`
- 更新方法签名以匹配新 API：`(event, options, function_call_ids)`
- 适配新的 `OpenAIResponseStreamEvent` 结构，从 `event.type` 和 `event.data` 提取 reasoning
- 更新 `_extract_reasoning_from_update` 方法或创建新的 `_extract_reasoning_from_chunk` 方法
- 保持向后兼容：非流式响应的 reasoning content 提取不受影响

## Capabilities

### New Capabilities

- `streaming-reasoning-extraction`: 流式响应中提取 reasoning content 的能力，适配 rc6 新 API

### Modified Capabilities

- `openai-like-client`: `OpenAILikeChatClient` 的流式响应处理逻辑需要适配新 API

## Impact

- **代码变更**:
  - `src/agent_framework_ep/openai_like/__init__.py` - 重写 `_parse_chunk_from_openai`
  - `src/agent_framework_ep/openai_like/_reasoning_content.py` - 新增或更新 reasoning 提取方法
- **依赖变更**: 已添加 `agent-framework-openai>=1.0.0rc6`
- **API 兼容**: 非流式 API 保持不变，流式 API 内部实现变更但外部行为一致
- **测试影响**: 需要新增流式 reasoning content 的集成测试

## Non-goals

- 不修改 `code_executor` 模块（完全独立，不受影响）
- 不修改 `skills_provider` 模块（正常工作）
- 不修改非流式响应的处理逻辑
- 不添加新的 reasoning content 来源（仅适配现有 DeepSeek-R1 等模型）