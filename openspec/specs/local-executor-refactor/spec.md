## MODIFIED Requirements

### Requirement: LocalCommandLineCodeExecutor 初始化
系统 SHALL 重构 `LocalCommandLineCodeExecutor` 继承新的 `BaseCommandLineCodeExecutor`。

#### Scenario: 构造函数兼容性
- **WHEN** 使用现有参数创建 `LocalCommandLineCodeExecutor`
- **THEN** 所有现有参数 SHALL 继续工作
- **THEN** 返回配置正确的执行器实例

### Requirement: 命令执行
`LocalCommandLineCodeExecutor` SHALL 实现 `_execute_command` 抽象方法。

#### Scenario: 本地子进程执行
- **WHEN** `_execute_command` 被调用
- **THEN** 使用 `asyncio.create_subprocess_exec` 创建进程
- **THEN** 返回 `(output, exit_code)` 元组

#### Scenario: 超时处理
- **WHEN** 执行超过配置的超时时间
- **THEN** 终止进程
- **THEN** 返回 exit code 124 和超时消息

#### Scenario: 取消支持
- **WHEN** 取消令牌被触发
- **THEN** 使用 `CancellationToken.wait()` 等待取消事件
- **THEN** 终止子进程

### Requirement: 安全功能
Local 执行器 SHALL 保持现有的安全功能。

#### Scenario: 安全警告
- **WHEN** 首次执行代码
- **THEN** 记录 WARNING 级别日志提醒安全风险

#### Scenario: 脚本路径验证
- **WHEN** 执行外部脚本
- **THEN** 验证脚本路径在工作目录内
- **THEN** 阻止路径遍历攻击

### Requirement: 死代码移除
系统 SHALL 移除未使用的私有方法。

#### Scenario: 清理未使用方法
- **WHEN** 审查 `LocalCommandLineCodeExecutor`
- **THEN** `_wait_for_cancellation` 方法已不存在
- **THEN** `_kill_process_if_cancelled` 方法已不存在
