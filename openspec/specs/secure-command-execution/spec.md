## ADDED Requirements

### Requirement: 命令执行必须通过安全方式构建
所有 shell 命令的构建 SHALL 使用安全的参数处理方式，禁止直接拼接未经验证的输入。

#### Scenario: init_command 包含特殊字符
- **WHEN** `init_command` 参数包含 `$()` 或反引号等特殊字符
- **THEN** 系统 SHALL 转义或拒绝这些字符，防止命令注入

#### Scenario: 脚本参数包含空格
- **WHEN** `execute_script` 的 `args` 参数值包含空格（如 `"/path/with spaces"`）
- **THEN** 系统 SHALL 正确传递完整值，不应将其分割为多个参数

### Requirement: CancellationToken 必须提供资源清理机制
`CancellationToken` SHALL 提供 `cleanup()` 方法，允许调用方在完成使用后清理内部任务资源。

#### Scenario: Token 使用后清理
- **WHEN** 调用方完成使用 CancellationToken
- **AND** 调用 `token.cleanup()`
- **THEN** 所有内部 watcher 任务 SHALL 被取消和清理

#### Scenario: 重复清理安全
- **WHEN** 对同一个 token 多次调用 `cleanup()`
- **THEN** 系统 SHALL 不抛出异常，安全处理重复调用

### Requirement: Docker 客户端连接必须正确关闭
`DockerCommandLineCodeExecutor` SHALL 在 `stop()` 中关闭 Docker 客户端连接，防止连接泄漏。

#### Scenario: 正常停止释放连接
- **WHEN** executor 成功启动并执行代码
- **AND** 调用 `stop()`
- **THEN** Docker 客户端连接 SHALL 被关闭

#### Scenario: 异常停止也释放连接
- **WHEN** executor 启动过程中发生异常
- **THEN** 已创建的 Docker 客户端连接 SHALL 被关闭

### Requirement: 并发修改必须使用锁保护
`_cancellation_futures` 列表的修改 SHALL 使用 `asyncio.Lock` 保护，防止并发访问导致的数据竞争。

#### Scenario: 多个并发取消操作
- **WHEN** 多个代码块同时被取消
- **THEN** `_cancellation_futures` 列表的修改 SHALL 是线程安全的

## MODIFIED Requirements

### Requirement: 取消操作 SHALL 抛出 CancelledError
修改自 `code-execution-base`: `execute_code_blocks` 在取消时 SHALL 抛出 `asyncio.CancelledError` 而非返回结果对象。

#### Scenario: 正常取消流程
- **WHEN** 代码执行过程中收到取消信号
- **THEN** 系统 SHALL 抛出 `asyncio.CancelledError`
- **AND** 调用方可以通过捕获异常处理取消

#### Scenario: 取消后资源清理
- **WHEN** `CancelledError` 被抛出
- **THEN** 系统 SHALL 确保所有资源（进程、临时文件）被正确清理

### Requirement: 路径遍历检查失败 SHALL 抛出异常
修改自 `code-execution-base`: 当路径遍历检查失败时，系统 SHALL 抛出 `ValueError` 而非静默返回 `None`。

#### Scenario: 检测到路径遍历尝试
- **WHEN** 文件名包含 `../` 等路径遍历序列
- **AND** 解析后的路径在工作目录之外
- **THEN** 系统 SHALL 抛出 `ValueError`，包含明确的错误信息

#### Scenario: 有效的相对路径
- **WHEN** 文件名是有效的相对路径（如 `"subdir/file.py"`）
- **AND** 路径在工作目录内
- **THEN** 系统 SHALL 正常处理文件

## REMOVED Requirements

无。
