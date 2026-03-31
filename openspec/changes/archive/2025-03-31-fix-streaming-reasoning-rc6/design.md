## Context

Microsoft Agent Framework 在 1.0.0rc6 版本中对流式响应 API 进行了重大重构：

**旧 API (rc5)**:
```python
def _parse_response_update_from_openai(self, chunk: Any) -> ChatResponseUpdate:
    # chunk 是原始 OpenAI API 返回的流式数据块
    # chunk.choices[0].delta.reasoning_content 包含 reasoning
```

**新 API (rc6)**:
```python
def _parse_chunk_from_openai(
    self,
    event: OpenAIResponseStreamEvent,
    options: dict[str, Any],
    function_call_ids: dict[int, tuple[str, str]],
) -> ChatResponseUpdate:
    # event 是 OpenAI Responses API 的流式事件
    # event.type 标识事件类型（如 "response.reasoning_summary_text_delta"）
    # event.data 包含具体数据
```

当前项目的 `OpenAILikeChatClient` 继承自 `agent_framework_openai.OpenAIChatClient`，通过重写 `_parse_response_update_from_openai` 来提取 reasoning content。但父类在 rc6 中已不再调用此方法，而是使用 `_parse_chunk_from_openai`。

## Goals / Non-Goals

**Goals:**
- 适配 rc6 新的流式响应 API，恢复 reasoning content 提取功能
- 保持非流式响应的处理逻辑不变
- 保持外部 API 兼容性（`get_reasoning_content()` 函数行为不变）
- 支持 DeepSeek-R1 等模型的 reasoning content 提取

**Non-Goals:**
- 不修改 `code_executor` 和 `skills_provider` 模块
- 不添加新的 reasoning 来源类型
- 不修改 `ChatResponse` 或 `ChatResponseUpdate` 的类型定义

## Decisions

### Decision 1: 方法重命名策略

**选择**: 直接重写 `_parse_chunk_from_openai`，废弃 `_parse_response_update_from_openai`

**理由**:
- 父类只调用 `_parse_chunk_from_openai`，重写旧方法无效
- 新方法签名更复杂，但提供了更多上下文（options、function_call_ids）
- 保持单一方法重写，避免维护两个无效方法

**替代方案**: 同时保留两个方法重写（被否决）
- 问题：旧方法不会被调用，保留会增加维护负担和混淆

### Decision 2: Reasoning 提取逻辑适配

**选择**: 在 `_parse_chunk_from_openai` 中内联处理 reasoning 提取

**理由**:
- 新 API 的 `event` 结构与旧 `chunk` 完全不同
- `OpenAIResponseStreamEvent` 使用 match/case 模式匹配不同事件类型
- reasoning 相关事件类型包括：
  - `response.reasoning_summary_text_delta`
  - `response.reasoning_summary_part_added`
  - `response.reasoning_summary_part_done`

**实现方式**:
```python
@override
def _parse_chunk_from_openai(
    self,
    event: Any,
    options: dict[str, Any],
    function_call_ids: dict[int, tuple[str, str]],
) -> ChatResponseUpdate:
    update = super()._parse_chunk_from_openai(event, options, function_call_ids)
    
    # 从 event 中提取 reasoning
    if hasattr(event, 'type') and 'reasoning' in event.type:
        # 处理 reasoning 事件
        ...
    
    return update
```

### Decision 3: 保持 `_extract_reasoning_from_update` 方法

**选择**: 保留现有方法，但标记为内部使用

**理由**:
- 非流式响应仍使用 `_extract_reasoning_from_response`
- 方法命名一致性
- 未来可能有其他用途

## Risks / Trade-offs

### Risk 1: OpenAI Responses API 事件类型变化

**风险**: rc6 使用 OpenAI Responses API 而非 Chat Completions API，事件类型可能继续演进

**缓解**: 
- 使用字符串匹配而非精确类型检查
- 添加 fallback 逻辑处理未知事件类型
- 监控官方文档更新

### Risk 2: 测试覆盖不足

**风险**: 流式响应测试需要真实 API 调用，但公开库无法使用 API key

**缓解**:
- 使用 **VCR.py** 录制真实 API 响应，保存为 cassette 文件（YAML 格式）
- 测试时重放 cassette，无需 API key，测试真实场景
- cassette 文件提交到仓库，CI/CD 可直接运行
- 开发者可使用自己的 API key 重新录制 cassette（可选）
- 添加 `pytest-recording` 插件简化 VCR.py 与 pytest 的集成

### Risk 3: 向后兼容性

**风险**: 用户可能依赖 `_parse_response_update_from_openai` 方法

**缓解**:
- 方法仍存在（继承自父类），只是不会被调用
- 添加文档说明变更
- 在 CHANGELOG 中记录 breaking change