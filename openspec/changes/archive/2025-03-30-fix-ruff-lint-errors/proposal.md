## Why

CI中的ruff lint检查被临时禁用，因为存在11处pre-existing的lint错误。这导致代码质量无法自动保障，且需要手动维护，增加了代码债务。现在需要修复这些错误并重新启用CI检查。

## What Changes

- 修复 `src/agent_framework_ep/code_executor/base.py` 中的 SIM102 错误（嵌套if合并）
- 修复 `src/agent_framework_ep/code_executor/docker/executor.py` 中的 SIM105 错误（使用contextlib.suppress）
- 修复 `src/agent_framework_ep/openai_like/_reasoning_content.py` 中的 SIM108 和 SIM102 错误
- 修复 `tests/openai_like/test_init.py` 中的 F401 和 F811 错误（未使用和重复导入）
- 修复 `tests/openai_like/test_response_format.py` 中的 F401 和 B017 错误
- 取消 `.github/workflows/release.yml` 中ruff check的注释

## Capabilities

### New Capabilities

无新功能

### Modified Capabilities

无规格变更（仅代码风格修复）

## Impact

- 代码文件：4个源文件和测试文件
- CI配置：`.github/workflows/release.yml`
- 无API变更
- 无依赖变更

## Non-goals

- 不修改任何功能逻辑
- 不改变测试行为（仅修复导入问题）
- 不添加新的lint规则
