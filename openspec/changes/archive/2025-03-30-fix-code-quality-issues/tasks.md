## 1. CancellationToken 优化

- [x] 1.1 在 `CancellationToken` 类中添加 `wait()` 方法，包装 `self._event.wait()`
- [x] 1.2 更新 `LocalCommandLineCodeExecutor._execute_command` 使用 `await cancellation_token.wait()` 替代轮询循环
- [x] 1.3 运行测试验证取消功能正常工作

## 2. 修复已弃用的 asyncio API

- [x] 2.1 在 `DockerCommandLineCodeExecutor.stop()` 中，将 `asyncio.wrap_future(f, loop=self._loop)` 改为 `asyncio.wrap_future(f)`
- [x] 2.2 移除 `DockerCommandLineCodeExecutor.__init__` 中 `self._loop = None` 的初始化
- [x] 2.3 移除 `DockerCommandLineCodeExecutor.start()` 中的 `self._loop = asyncio.get_running_loop()`
- [x] 2.4 更新 `stop()` 方法中访问 loop 的代码，改用 `asyncio.get_running_loop()` 或检查 Future 状态

## 3. 提取 BaseCommandLineCodeExecutor 基类

- [x] 3.1 创建 `BaseCommandLineCodeExecutor` 抽象基类，定义 `_execute_command` 抽象方法
- [x] 3.2 将 `SUPPORTED_LANGUAGES`、`_timeout`、`_work_dir`、`_delete_tmp_files`、`_temp_dir`、`_running` 属性移到基类
- [x] 3.3 将 `work_dir`、`timeout` 属性移到基类
- [x] 3.4 将 `_execute_code_dont_check_setup` 方法移到基类
- [x] 3.5 将 `execute_code_blocks` 公共逻辑移到基类（状态检查 + 调用基类方法）
- [x] 3.6 将文件名处理逻辑（`get_file_name_from_content` 调用和 SHA256 计算）移到基类
- [x] 3.7 将文件清理逻辑移到基类

## 4. 重构 DockerCommandLineCodeExecutor

- [x] 4.1 修改 `DockerCommandLineCodeExecutor` 继承 `BaseCommandLineCodeExecutor`
- [x] 4.2 移除已移到基类的属性，保留 Docker 特有属性（`_image`、`_container_name`、`_container` 等）
- [x] 4.3 实现 `_execute_command` 方法，包含 Docker 容器内命令执行逻辑
- [x] 4.4 移除冗余的容器状态检查（`_wait_for_ready` 后的检查）
- [x] 4.5 运行 Docker 执行器测试验证功能正常

## 5. 重构 LocalCommandLineCodeExecutor

- [x] 5.1 修改 `LocalCommandLineCodeExecutor` 继承 `BaseCommandLineCodeExecutor`
- [x] 5.2 移除已移到基类的属性和方法
- [x] 5.3 实现 `_execute_command` 方法，包含子进程执行逻辑
- [x] 5.4 移除未使用的私有方法 `_wait_for_cancellation` 和 `_kill_process_if_cancelled`
- [x] 5.5 运行 Local 执行器测试验证功能正常

## 6. 修复安全漏洞和性能优化

- [x] 6.1 在 `base.py` 的 `get_file_name_from_content` 中，将 `path.resolve()` 改为 `path.absolute()`
- [x] 6.2 在模块级别预编译 `silence_pip` 函数中的正则表达式
- [x] 6.3 延迟计算 SHA256 哈希（仅在需要时计算）
- [x] 6.4 优化异常处理：为文件删除失败添加 DEBUG 级别日志

## 7. 优化 reasoning_content 处理

- [x] 7.1 在 `_reasoning_content.py` 的 `_propagate_reasoning_in_messages` 中，将 `copy.deepcopy(messages)` 改为 `[dict(m) for m in messages]`
- [x] 7.2 运行 reasoning_content 测试验证功能正常

## 8. 代码清理和类型优化

- [x] 8.1 移除 `LocalCommandLineCodeExecutor.__aexit__` 中 `exc_tb` 参数类型从 `object` 改为 `TracebackType | None` 以与基类一致
- [x] 8.2 审查并减少 `Any` 类型的使用（如果适用）
- [x] 8.3 添加/更新文档字符串

## 9. 测试验证

- [x] 9.1 运行所有现有测试确保没有回归
- [x] 9.2 运行类型检查 (`mypy`) 确保类型正确
- [x] 9.3 运行代码格式化 (`ruff format`) 确保格式一致
- [x] 9.4 运行代码检查 (`ruff check`) 确保无警告
- [ ] 9.5 为新的 `BaseCommandLineCodeExecutor` 添加单元测试
