## Context

`agent-framework-ep` 项目是基于 Microsoft Agent Framework 的扩展库，为开源 LLM（GLM、Kimi、Qwen、DeepSeek）提供结构化输出和 reasoning_content 支持。代码审查发现以下主要问题：

1. **已弃用的 Python API**: `docker/executor.py` 使用 `asyncio.wrap_future(f, loop=self._loop)`，其中 `loop` 参数在 Python 3.12 中已移除
2. **轮询反模式**: `local/executor.py` 使用 `while` 循环 + `asyncio.sleep(0.01)` 检查取消状态，造成 CPU 浪费
3. **事件循环缓存**: 存储 `asyncio.AbstractEventLoop` 引用在现代 asyncio 中是反模式
4. **代码重复**: Docker 和 Local 执行器有约 200 行几乎相同的逻辑
5. **安全漏洞**: `get_file_name_from_content` 使用 `path.resolve()` 会跟随符号链接，可能导致路径遍历
6. **性能问题**: 正则表达式重复编译、不必要的深拷贝、SHA256 哈希冗余计算

项目使用 Python 3.12+，依赖 `agent-framework>=1.0.0rc5`、Pydantic v2、Docker SDK。

## Goals / Non-Goals

**Goals:**
- 修复所有 Python 3.12 兼容性问题
- 消除轮询，改用事件驱动机制
- 提取公共代码，减少重复
- 修复安全漏洞（路径遍历）
- 优化性能（减少内存和 CPU 使用）
- 保持 100% 向后兼容

**Non-Goals:**
- 不修改 `OpenAILikeChatClient` 的多重继承架构
- 不引入新的外部依赖
- 不改变公共 API 的函数签名
- 不添加新功能（仅优化现有实现）

## Decisions

### 1. 提取 `BaseCommandLineCodeExecutor` 基类
**决策**: 创建抽象基类封装 `DockerCommandLineCodeExecutor` 和 `LocalCommandLineCodeExecutor` 的共同逻辑。

**理由**:
- 遵循 DRY 原则，消除 ~200 行重复代码
- 统一文件处理、命令构建、输出处理逻辑
- 子类只需实现 `_execute_command` 抽象方法

**替代方案**: 
- 使用 Mixin：增加复杂性，不如直接继承清晰
- 保持现状：代码重复问题持续存在

### 2. 修复 `CancellationToken` 支持 `wait()` 方法
**决策**: 在 `CancellationToken` 中添加 `wait()` 方法，包装内部的 `asyncio.Event.wait()`。

**理由**:
- 消除轮询，完全事件驱动
- 保持封装，不暴露内部 `_event`
- 向后兼容，现有代码继续工作

**替代方案**:
- 直接访问 `_event`: 破坏封装
- 使用 `anyio` 库：引入新依赖，不必要

### 3. 使用 `path.absolute()` 替代 `path.resolve()`
**决策**: 在路径安全校验中使用 `absolute()` 而非 `resolve()`。

**理由**:
- `resolve()` 跟随符号链接，可能被恶意利用逃逸工作目录
- `absolute()` 仅规范化路径而不解析链接
- 保持安全检查的有效性

**替代方案**:
- 完全禁用符号链接检查：过于复杂
- 使用 `os.path.realpath()`: 同样会跟随链接

### 4. 模块级预编译正则表达式
**决策**: 将 `silence_pip` 中的正则表达式移到模块级别编译。

**理由**:
- 避免每次调用重新编译正则
- 简单变更，无行为改变
- Python 的 `re` 模块会自动缓存，但显式编译更清晰

### 5. 使用浅拷贝替代深拷贝
**决策**: 在 `_propagate_reasoning_in_messages` 中使用 `[dict(m) for m in messages]` 替代 `copy.deepcopy(messages)`。

**理由**:
- 消息是简单的字典列表，不需要深拷贝
- 减少内存分配和 CPU 使用
- 假设：消息内容不会被递归修改（当前代码满足此假设）

**风险**: 如果未来添加嵌套可变对象，可能需要恢复深拷贝。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 基类提取引入回归 | 高 | 保持所有现有测试通过，添加新测试覆盖提取的基类 |
| `path.absolute()` 行为差异 | 中 | 在 Windows 和 Unix 上测试路径处理 |
| `CancellationToken.wait()` 命名冲突 | 低 | 检查是否已有 `wait` 方法或属性 |
| 性能优化改变时序 | 低 | 测试异步行为，确保取消仍然及时响应 |

## Migration Plan

无需迁移 - 所有变更都是内部实现优化，公共 API 保持不变。现有用户代码无需修改。

## Open Questions

1. 是否应该将 `_execute_command` 设计为 async generator 以支持流式输出？（未来扩展考虑）
2. 是否需要为 `CancellationToken` 添加超时支持？（当前未计划）
3. 基类提取后，是否需要将 `LocalCommandLineCodeExecutor` 标记为 `@final` 以防止进一步继承？
