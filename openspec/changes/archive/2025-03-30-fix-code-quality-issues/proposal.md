## Why

代码审查发现 `agent-framework-ep` 项目存在多个代码质量问题，包括使用已弃用的 Python API、轮询反模式、代码重复、安全漏洞等。这些问题影响代码的可维护性、性能和正确性。需要系统性修复以提升代码质量和可靠性。

## What Changes

- **修复已弃用的 asyncio API**: 移除 `asyncio.wrap_future()` 的 `loop` 参数（Python 3.12 已移除）
- **消除轮询反模式**: 将 `while` 循环轮询替换为 `asyncio.Event.wait()`
- **移除事件循环缓存**: 删除存储的 `_loop` 引用，使用 `asyncio.get_running_loop()`
- **提取公共执行逻辑**: 将 `DockerCommandLineCodeExecutor` 和 `LocalCommandLineCodeExecutor` 的重复代码提取到共享基类
- **修复安全漏洞**: 修复 `get_file_name_from_content` 中的路径遍历问题（避免符号链接逃逸）
- **优化性能**: 预编译正则表达式、延迟计算 SHA256、使用浅拷贝替代深拷贝
- **改进错误处理**: 添加日志记录替代静默忽略异常、优化异常捕获范围
- **删除死代码**: 移除未使用的私有方法
- **类型安全**: 减少 `Any` 使用，添加更精确的类型注解
- **代码风格**: 统一异常处理模式、添加文档字符串

## Capabilities

### New Capabilities
- `code-executor-base`: 提取的代码执行器基类，包含公共执行逻辑
- `docker-executor-refactor`: Docker 执行器的重构实现
- `local-executor-refactor`: 本地执行器的重构实现

### Modified Capabilities
- `cancellation-token`: 优化取消机制，支持 `wait()` 方法
- `reasoning-content`: 使用浅拷贝优化消息处理性能

## Impact

- **Breaking Changes**: 无（所有修改保持向后兼容）
- **测试**: 需要更新测试以验证修复后的行为
- **性能**: 减少 CPU 轮询、降低内存使用、加快执行速度
- **安全**: 修复路径遍历漏洞
- **依赖**: 无新增依赖

## Non-goals

- 不修改多重继承架构（`OpenAILikeChatClient` 使用 Mixin 模式）
- 不引入新的外部库
- 不改变公共 API 签名
- 不改变现有功能行为（仅优化实现）
