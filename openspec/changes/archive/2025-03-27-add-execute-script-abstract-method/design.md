## Context

`CodeExecutor` 是代码执行模块的抽象基类，定义于 `src/agent_framework_ep/code_executor/base.py`。目前它定义了以下抽象方法：

- `execute_code_blocks()` —— 执行代码块列表
- `start()` / `stop()` / `restart()` —— 生命周期管理

两个具体实现 `DockerCommandLineCodeExecutor` 和 `LocalCommandLineCodeExecutor` 都已经实现了 `execute_script()` 方法，但基类没有声明这个接口。这导致：
- 无法对 `CodeExecutor` 类型的变量调用 `execute_script()`
- 新实现者可能遗漏这个重要方法

## Goals / Non-Goals

**Goals:**
- 在 `CodeExecutor` 基类添加 `execute_script` 抽象方法
- 保持方法签名与现有实现一致
- 确保类型检查器能验证所有子类都实现了该方法

**Non-Goals:**
- 修改现有子类的实现逻辑
- 添加新功能或行为变更
- 复杂的重构

## Decisions

### 方法签名设计

采用与现有实现一致的签名：

```python
@abstractmethod
async def execute_script(
    self,
    script_path: str,
    args: dict[str, str] | None = None,
    cancellation_token: CancellationToken | None = None,
) -> CommandLineCodeResult:
    ...
```

**理由：**
- 与两个现有实现 100% 兼容
- `args` 字典格式（`{"key": "value"}` → `--key value`）已在两个实现中统一
- 空字符串 key 用于 positional arguments 的约定保持一致

## Risks / Trade-offs

**[风险] 破坏性变更？** → 无。所有现有子类已实现该方法，这只是显式声明已有契约。

**[风险] 子类需要修改？** → 不需要。现有实现完全符合新接口。
