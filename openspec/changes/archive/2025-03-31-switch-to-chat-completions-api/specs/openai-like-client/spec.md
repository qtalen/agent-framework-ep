## MODIFIED Requirements

### Requirement: OpenAI ChatCompletionClient 使用 Chat Completions API
`OpenAILikeChatCompletionClient` SHALL 继承 `OpenAIChatCompletionClient`，使用 Chat Completions API。

#### Scenario: 父类继承正确
- **WHEN** 定义 `OpenAILikeChatCompletionClient` 类
- **THEN** SHALL 继承 `OpenAIChatCompletionClient` 而非 `OpenAIChatClient`
- **THEN** SHALL 使用 Chat Completions API 进行 API 调用

#### Scenario: 向后兼容别名
- **WHEN** 用户使用 `OpenAILikeChatClient`
- **THEN** SHALL 等同于 `OpenAILikeChatCompletionClient`
- **THEN** 代码 SHALL 正常工作

#### Scenario: 国产大模型兼容
- **WHEN** 使用 DeepSeek、Kimi、Qwen 等国产大模型
- **THEN** API 调用 SHALL 正常工作
- **THEN** `message.reasoning_content` 字段 SHALL 被正确处理

### Requirement: Reasoning content 处理保留
`OpenAILikeChatCompletionClient` SHALL 保留 reasoning content 提取逻辑。

#### Scenario: 非流式 reasoning 提取
- **WHEN** 响应包含 `message.reasoning_content` 字段
- **THEN** `_extract_reasoning_from_response` SHALL 正确提取
- **THEN** `ChatResponse.messages[].contents` SHALL 包含 `text_reasoning` Content

#### Scenario: 流式 reasoning 提取
- **WHEN** 流式响应包含 `delta.reasoning_content` 字段
- **THEN** `_extract_reasoning_from_update` SHALL 正确提取
- **THEN** `ChatResponseUpdate.contents` SHALL 包含 `text_reasoning` Content

### Requirement: 流式响应方法适配
`OpenAILikeChatClient` SHALL 使用 `_parse_response_update_from_openai` 处理流式响应。

#### Scenario: 流式方法正确
- **WHEN** 重写流式响应处理方法
- **THEN** SHALL 重写 `_parse_response_update_from_openai`
- **THEN** NOT SHALL 重写 `_parse_chunk_from_openai`（Responses API 专用）