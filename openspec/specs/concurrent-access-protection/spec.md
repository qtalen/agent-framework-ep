## ADDED Requirements

### Requirement: _cancellation_futures 必须使用锁保护
`DockerCommandLineCodeExecutor` SHALL 使用 `asyncio.Lock` 保护对 `_cancellation_futures` 列表的并发访问。

#### Scenario: 并发执行和取消
- **WHEN** 多个代码块同时执行且其中一个被取消
- **THEN** 对 `_cancellation_futures` 的修改 SHALL 是原子操作

#### Scenario: 取消和 stop 并发
- **WHEN** 代码执行被取消的同时调用 `stop()`
- **THEN** 系统 SHALL 正确处理并发访问，不抛出异常

### Requirement: 任务创建和取消链接必须原子化
创建异步任务和链接到取消 token 的操作 SHALL 确保在任务开始前完成链接，防止竞态条件。

#### Scenario: 快速取消
- **WHEN** 任务创建后立即收到取消信号
- **THEN** 取消 SHALL 能被正确传播到任务

#### Scenario: 正常执行
- **WHEN** 任务正常执行完成
- **THEN** 取消链接 SHALL 不影响任务执行

## MODIFIED Requirements

### Requirement: execute_script 参数 SHALL 使用 shlex 分割
修改自 `local-executor` 和 `docker-executor`: `execute_script` 的位置参数分割 SHALL 使用 `shlex.split()` 而非 `str.split()`。

#### Scenario: 带空格的参数
- **WHEN** 位置参数包含带空格的路径（如 `"/path/with spaces/file.txt"`）
- **THEN** 系统 SHALL 正确将其作为单个参数传递

#### Scenario: 引号内的空格
- **WHEN** 位置参数使用引号包裹（如 `'arg with spaces'`）
- **THEN** 系统 SHALL 正确处理引号，不将内容分割

## REMOVED Requirements

无。
