## ADDED Requirements

### Requirement: BaseCommandLineCodeExecutor 抽象基类
系统 SHALL 提供 `BaseCommandLineCodeExecutor` 抽象基类，封装命令行代码执行器的公共逻辑。

#### Scenario: 子类继承基类
- **WHEN** 开发者创建 `DockerCommandLineCodeExecutor` 继承 `BaseCommandLineCodeExecutor`
- **THEN** 只需实现 `_execute_command` 抽象方法即可获得完整的代码执行功能

#### Scenario: 公共执行流程
- **WHEN** 调用基类的 `_execute_code_dont_check_setup`
- **THEN** 系统 SHALL 依次执行：提取文件名 → 写入代码文件 → 构建命令 → 调用 `_execute_command` → 收集输出

#### Scenario: 命令构建
- **WHEN** 基类构建执行命令
- **THEN** Docker 执行器 SHALL 使用 `timeout` 命令包装
- **THEN** Local 执行器 SHALL 直接调用解释器

### Requirement: 公共属性定义
`BaseCommandLineCodeExecutor` SHALL 定义公共属性接口供子类使用。

#### Scenario: 工作目录访问
- **WHEN** 访问 `work_dir` 属性
- **THEN** 返回已解析的 `Path` 对象，指向实际工作目录

#### Scenario: 超时配置
- **WHEN** 访问 `timeout` 属性
- **THEN** 返回配置的超时秒数（整数）

### Requirement: 文件处理逻辑
基类 SHALL 提供统一的文件处理功能。

#### Scenario: 文件名提取
- **WHEN** 代码首行包含 `# filename: xxx`
- **THEN** 使用该行指定的文件名
- **THEN** 执行路径安全检查（防止路径遍历）

#### Scenario: 临时文件生成
- **WHEN** 代码未指定文件名
- **THEN** 使用 `tmp_code_{hash}.{lang}` 格式生成文件名
- **THEN** 仅在实际需要时才计算 SHA256 哈希

#### Scenario: 文件清理
- **WHEN** `delete_tmp_files=True`
- **THEN** 执行完成后 SHALL 删除临时文件
- **THEN** 删除失败时记录 DEBUG 级别日志（不抛出异常）
