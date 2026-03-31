## 1. 代码修改

- [x] 1.1 在 `src/agent_framework_ep/openai_like/__init__.py` 中重写 `_parse_chunk_from_openai` 方法，替代 `_parse_response_update_from_openai`
- [x] 1.2 在 `src/agent_framework_ep/openai_like/_reasoning_content.py` 中新增 `_accumulate_reasoning_in_update` 方法，累积 reasoning 到 additional_properties
- [x] 1.3 移除废弃的 `_parse_response_update_from_openai` 方法重写
- [x] 1.4 保留 `_extract_reasoning_from_update` 方法作为备用（新 API 不调用）

## 2. 测试更新

- [x] 2.1 添加 `pytest-recording` 和 `vcrpy` 到 dev dependencies
- [x] 2.2 创建 mock `OpenAIResponseStreamEvent` 对象用于单元测试
- [x] 2.3 新增 `_accumulate_reasoning_in_update` 方法的单元测试
- [x] 2.4 新增流式 reasoning content 提取的单元测试
- [ ] 2.5 使用 VCR.py 录制 DeepSeek-R1 流式响应 cassette（需要开发者手动录制一次）
- [ ] 2.6 新增基于 cassette 的集成测试，验证流式 reasoning 提取
- [x] 2.7 运行现有测试确保非流式响应功能不受影响

## 3. 文档更新

- [x] 3.1 创建 `CHANGELOG.md` 记录 breaking change
- [x] 3.2 更新 `README.md` 说明 rc6 兼容性
- [x] 3.3 更新 `AGENTS.md` 中的模块说明

## 4. 验证

- [x] 4.1 运行 `uv run pytest tests/openai_like/` 确保所有测试通过
- [ ] 4.2 运行 `uv run mypy src/agent_framework_ep` 确保类型检查通过（LSP 环境问题，实际运行正常）
- [x] 4.3 运行 `uv run ruff check .` 确保代码风格检查通过