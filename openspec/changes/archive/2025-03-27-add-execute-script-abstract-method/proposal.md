## Why

目前 `DockerCommandLineCodeExecutor` 和 `LocalCommandLineCodeExecutor` 都实现了 `execute_script` 方法，但父类 `CodeExecutor` 没有声明这个抽象方法。这导致：

1. 接口不一致——新实现者可能遗漏这个方法
2. 缺乏契约——无法通过类型检查确保所有 executor 都支持脚本执行
3. 多态困难——无法针对抽象类型调用 `execute_script`

通过在基类添加抽象方法，强制所有子类实现统一的脚本执行接口。

## What Changes

- 在 `CodeExecutor` 抽象基类中添加 `execute_script` 抽象方法
- 现有子类 (`DockerCommandLineCodeExecutor`, `LocalCommandLineCodeExecutor`) 无需修改，已实现该方法

## Capabilities

### New Capabilities

(无——这是接口契约变更，非功能新增)

### Modified Capabilities

(无——现有 spec 不需要修改)

## Impact

- **代码文件**: `src/agent_framework_ep/code_executor/base.py`
- **受影响类**: 所有 `CodeExecutor` 的子类必须实现 `execute_script`
- **API 变更**: 无破坏性变更——现有实现已包含该方法

## Non-goals

- 不修改 `DockerCommandLineCodeExecutor` 或 `LocalCommandLineCodeExecutor` 的具体实现
- 不添加新的功能或行为变更
- 不修改测试（除非需要添加针对抽象方法的测试）
