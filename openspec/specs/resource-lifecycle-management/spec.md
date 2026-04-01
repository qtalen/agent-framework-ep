## ADDED Requirements

### Requirement: Docker 客户端必须单例管理
`DockerCommandLineCodeExecutor` SHALL 使用单个 Docker 客户端实例，并在生命周期结束时显式关闭。

#### Scenario: 多次 start/stop 周期
- **WHEN** 同一个 executor 实例被多次启动和停止
- **THEN** 每次启动创建新的客户端连接
- **AND** 每次停止关闭对应连接

#### Scenario: 客户端复用
- **WHEN** executor 在单次生命周期内执行多次操作
- **THEN** 使用同一个客户端连接

### Requirement: 容器创建失败必须清理资源
如果容器创建过程中失败，系统 SHALL 清理已创建的容器资源，防止资源泄漏。

#### Scenario: 创建后启动失败
- **WHEN** 容器创建成功但启动失败
- **THEN** 已创建的容器 SHALL 被删除

#### Scenario: 创建过程中异常
- **WHEN** 容器创建过程中抛出异常
- **THEN** 系统 SHALL 捕获异常并清理已分配资源

### Requirement: CancellationToken 必须清理 watcher 任务
`CancellationToken` SHALL 在取消后清理所有创建的 watcher 任务，防止任务泄漏。

#### Scenario: 取消后任务清理
- **WHEN** `cancel()` 被调用
- **THEN** 所有未完成的 watcher 任务 SHALL 被取消

#### Scenario: 正常完成后的清理
- **WHEN** 操作正常完成（未触发取消）
- **AND** 调用方调用 `cleanup()`
- **THEN** 所有 watcher 任务 SHALL 被清理

## MODIFIED Requirements

### Requirement: stop() 必须清理所有资源
修改自 `docker-executor`: `stop()` 方法 SHALL 确保所有资源（容器、客户端连接、临时目录、任务）被清理。

#### Scenario: 完整生命周期
- **WHEN** executor 从启动到停止的完整周期
- **THEN** 停止后不应残留任何资源

#### Scenario: 多次调用 stop
- **WHEN** `stop()` 被多次调用
- **THEN** 第二次及以后的调用 SHALL 安全返回，不抛出异常

## REMOVED Requirements

无。
