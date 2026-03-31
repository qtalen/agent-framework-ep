## ADDED Requirements

### Requirement: OpenAI ChatClient 流式响应适配
`OpenAILikeChatClient` SHALL 适配 Microsoft Agent Framework 1.0.0rc6 的流式响应 API 变化。

#### Scenario: 方法重写正确
- **WHEN** `OpenAILikeChatClient` 继承 `agent_framework_openai.OpenAIChatClient`
- **THEN** SHALL 重写 `_parse_chunk_from_openai` 方法而非 `_parse_response_update_from_openai`
- **THEN** 废弃的 `_parse_response_update_from_openai` 重写 SHALL 被移除

#### Scenario: 非流式响应保持不变
- **WHEN** 处理非流式响应
- **THEN** `_parse_response_from_openai` 重写 SHALL 保持不变
- **THEN** reasoning content 提取 SHALL 继续正常工作

#### Scenario: 结构化输出保持不变
- **WHEN** 使用 `response_format` 参数
- **THEN** `_inject_response_format_prompt` SHALL 继续正常工作
- **THEN** `_parse_structured_output` SHALL 继续正常工作

### Requirement: 消息处理方法保持兼容
`OpenAILikeChatClient` 的消息处理方法 SHALL 保持与 rc6 兼容。

#### Scenario: _prepare_options 方法
- **WHEN** 调用 `_prepare_options` 方法
- **THEN** SHALL 正确注入 response_format prompt
- **THEN** 方法签名 SHALL 与父类一致

#### Scenario: _prepare_messages_for_openai 方法
- **WHEN** 调用 `_prepare_messages_for_openai` 方法
- **THEN** SHALL 正确传播 reasoning content
- **THEN** 方法签名 SHALL 与父类一致

#### Scenario: _prepare_message_for_openai 方法
- **WHEN** 调用 `_prepare_message_for_openai` 方法
- **THEN** SHALL 正确提取和注入 reasoning
- **THEN** 方法签名 SHALL 与父类一致