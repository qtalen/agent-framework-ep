## Requirements

### Requirement: PR 触发 CI 工作流
当开发者创建或更新 Pull Request 时，系统 SHALL 自动触发 CI 工作流。

#### Scenario: PR 创建时触发 CI
- **WHEN** 开发者向仓库提交 Pull Request
- **THEN** GitHub Actions SHALL 自动启动 ci.yml 工作流

#### Scenario: PR 更新时重新触发 CI
- **WHEN** 开发者向已存在的 PR 推送新的 commit
- **THEN** GitHub Actions SHALL 重新运行 ci.yml 工作流

### Requirement: 代码质量检查
CI 工作流 SHALL 依次执行 ruff lint、ruff format check、mypy type-check。

#### Scenario: Lint 检查失败阻止合并
- **WHEN** 代码存在 lint 错误
- **THEN** ruff check SHALL 返回非零退出码
- **AND** PR 合并按钮 SHALL 被禁用

#### Scenario: 格式检查失败阻止合并
- **WHEN** 代码未通过 ruff format 格式化
- **THEN** ruff format --check SHALL 返回非零退出码
- **AND** PR 合并按钮 SHALL 被禁用

#### Scenario: 类型检查失败阻止合并
- **WHEN** 代码存在类型错误
- **THEN** mypy SHALL 返回非零退出码
- **AND** PR 合并按钮 SHALL 被禁用

### Requirement: 测试执行
CI 工作流 SHALL 运行 pytest 测试套件，排除 Docker 相关测试。

#### Scenario: 测试失败阻止合并
- **WHEN** 任意测试用例失败
- **THEN** pytest SHALL 返回非零退出码
- **AND** PR 合并按钮 SHALL 被禁用

#### Scenario: 测试成功允许合并
- **WHEN** 所有测试用例通过
- **THEN** pytest SHALL 返回零退出码
- **AND** PR 合并按钮保持可用

### Requirement: 多版本 Python 支持
CI 工作流 SHALL 在 Python 3.12 和 Python 3.13 上运行所有检查。

#### Scenario: 双版本矩阵测试
- **WHEN** CI 工作流启动
- **THEN** 系统 SHALL 分别在 Python 3.12 和 3.13 环境中执行检查
- **AND** 任一版本失败 SHALL 阻止合并

### Requirement: 任务串行执行
CI 工作流中的质量检查任务 SHALL 串行执行，避免资源浪费。

#### Scenario: 快速失败机制
- **WHEN** lint 检查失败
- **THEN** 后续 type-check 和 test 任务 SHALL 被跳过
- **AND** 开发者 SHALL 尽快收到失败反馈
