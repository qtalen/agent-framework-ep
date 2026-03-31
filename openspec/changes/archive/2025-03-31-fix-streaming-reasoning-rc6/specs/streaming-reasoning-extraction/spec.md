## ADDED Requirements

### Requirement: 流式响应 reasoning content 提取
`OpenAILikeChatClient` SHALL 在流式响应中正确提取 reasoning content，适配 Microsoft Agent Framework 1.0.0rc6 新 API。

#### Scenario: 基本流式 reasoning 提取
- **WHEN** 流式响应包含 reasoning 事件（如 `response.reasoning_summary_text_delta`）
- **THEN** `ChatResponseUpdate` 的 `contents` SHALL 包含 `text_reasoning` 类型的 Content
- **THEN** `additional_properties["reasoning_content"]` SHALL 包含累积的 reasoning 文本

#### Scenario: 多个 reasoning 事件累积
- **WHEN** 连续多个流式事件包含 reasoning content
- **THEN** reasoning content SHALL 正确累积拼接
- **THEN** 每个 `ChatResponseUpdate` SHALL 包含当前累积的 reasoning

#### Scenario: 无 reasoning 的流式响应
- **WHEN** 流式响应不包含 reasoning 事件
- **THEN** `ChatResponseUpdate` SHALL 不包含 `text_reasoning` content
- **THEN** `additional_properties` SHALL 不包含 `reasoning_content` 键

### Requirement: 新 API 方法签名适配
`OpenAILikeChatClient._parse_chunk_from_openai` SHALL 使用 rc6 新方法签名。

#### Scenario: 方法签名正确
- **WHEN** 重写 `_parse_chunk_from_openai` 方法
- **THEN** 方法签名 SHALL 为 `(self, event, options, function_call_ids) -> ChatResponseUpdate`
- **THEN** 方法 SHALL 正确调用父类实现

#### Scenario: 事件类型处理
- **WHEN** 处理 `OpenAIResponseStreamEvent`
- **THEN** SHALL 根据 `event.type` 判断是否为 reasoning 事件
- **THEN** reasoning 相关事件类型 SHALL 包括 `response.reasoning_summary_text_delta` 等

### Requirement: 向后兼容性
流式 reasoning 提取 SHALL 保持与现有 `get_reasoning_content()` 函数兼容。

#### Scenario: get_reasoning_content 函数兼容
- **WHEN** 使用 `get_reasoning_content(ChatResponseUpdate)` 提取 reasoning
- **THEN** SHALL 正确返回流式响应中累积的 reasoning content
- **THEN** 函数行为 SHALL 与非流式响应一致