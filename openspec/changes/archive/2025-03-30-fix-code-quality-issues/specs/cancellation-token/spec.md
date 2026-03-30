## MODIFIED Requirements

### Requirement: CancellationToken wait 支持
`CancellationToken` SHALL 提供 `wait()` 方法支持异步等待取消事件。

#### Scenario: 异步等待取消
- **WHEN** 调用 `await token.wait()`
- **THEN** 异步等待直到 `cancel()` 被调用
- **THEN** 使用内部 `asyncio.Event` 实现（不暴露内部状态）

#### Scenario: 向后兼容
- **WHEN** 使用现有的 `is_cancellation_requested` 属性
- **THEN** 继续正常工作

#### Scenario: 消除轮询
- **WHEN** 使用新的 `wait()` 方法
- **THEN** 不使用 `while` 循环轮询
- **THEN** 不使用 `asyncio.sleep()` 延迟
