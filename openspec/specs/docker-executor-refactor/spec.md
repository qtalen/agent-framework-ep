## MODIFIED Requirements

### Requirement: DockerCommandLineCodeExecutor 初始化
系统 SHALL 重构 `DockerCommandLineCodeExecutor` 继承新的 `BaseCommandLineCodeExecutor`。

#### Scenario: 构造函数兼容性
- **WHEN** 使用现有参数创建 `DockerCommandLineCodeExecutor`
- **THEN** 所有现有参数 SHALL 继续工作
- **THEN** 返回配置正确的执行器实例

#### Scenario: Docker 客户端管理
- **WHEN** 执行器启动
- **THEN** 创建 Docker 客户端连接
- **THEN** 复用该连接直到执行器停止

### Requirement: 命令执行
`DockerCommandLineCodeExecutor` SHALL 实现 `_execute_command` 抽象方法。

#### Scenario: 容器内命令执行
- **WHEN** `_execute_command` 被调用
- **THEN** 在 Docker 容器内执行命令
- **THEN** 返回 `(output, exit_code)` 元组

#### Scenario: 取消支持
- **WHEN** 取消令牌被触发
- **THEN** 取消正在执行的命令
- **THEN** 通过 `pkill` 终止容器内进程

#### Scenario: 修复已弃用的 API
- **WHEN** 处理取消的并发 Future
- **THEN** 调用 `asyncio.wrap_future(f)` 而不带 `loop` 参数
- **THEN** 代码在 Python 3.12+ 正常运行

### Requirement: 生命周期管理
系统 SHALL 正确管理 Docker 容器的生命周期。

#### Scenario: 容器启动
- **WHEN** 调用 `start()`
- **THEN** 创建并启动 Docker 容器
- **THEN** 等待容器进入 running 状态

#### Scenario: 移除循环引用
- **WHEN** 启动执行器
- **THEN** 不存储 `asyncio.AbstractEventLoop` 引用
- **THEN** 需要时调用 `asyncio.get_running_loop()`

#### Scenario: 容器停止
- **WHEN** 调用 `stop()`
- **THEN** 停止并清理容器
- **THEN** 等待取消相关的 Future 完成

#### Scenario: 冗余检查移除
- **WHEN** `_wait_for_ready` 成功返回
- **THEN** 不重复检查容器状态（已保证 running）
