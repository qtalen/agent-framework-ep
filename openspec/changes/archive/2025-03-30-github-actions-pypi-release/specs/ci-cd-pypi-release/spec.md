## ADDED Requirements

### Requirement: GitHub Actions 在 tag 推送时触发发布流程
GitHub Actions workflow SHALL 在推送匹配语义化版本模式的 tag (`v[0-9]+.[0-9]+.[0-9]+`) 时自动触发。

#### Scenario: 推送 v0.1.6 tag 触发 workflow
- **WHEN** 开发者执行 `git tag v0.1.6 && git push origin v0.1.6`
- **THEN** GitHub Actions workflow `release.yml` 开始执行

#### Scenario: 推送非版本 tag 不触发发布
- **WHEN** 开发者推送标签 `release-candidate` 或 `test-tag`
- **THEN** 不触发 release workflow

### Requirement: Workflow 使用 Trusted Publisher 认证发布到 PyPI
Workflow SHALL 使用 PyPI Trusted Publisher (OIDC) 机制进行认证，无需存储 API token。

#### Scenario: 成功配置 Trusted Publisher 后发布
- **GIVEN** PyPI 项目已配置 Trusted Publisher，指定仓库为 `qtalen/agent-framework-ep`，workflow 为 `release.yml`
- **WHEN** workflow 执行到 publish 步骤
- **THEN** 使用 OIDC 令牌成功认证并发布到 PyPI

### Requirement: 发布前执行完整测试套件
Workflow SHALL 在发布前执行完整的测试、代码检查和类型检查，且所有检查必须通过。

#### Scenario: 所有测试通过
- **GIVEN** 代码变更已提交到 main 分支
- **WHEN** workflow 执行测试步骤
- **THEN** pytest、ruff、mypy 全部通过

#### Scenario: 测试失败阻止发布
- **GIVEN** 代码存在导致测试失败的 bug
- **WHEN** workflow 执行到测试步骤
- **THEN** 测试失败，publish 步骤被跳过，不发布到 PyPI

### Requirement: 支持多 Python 版本矩阵测试
Workflow SHALL 在 Python 3.12 和 3.13 上并行运行测试。

#### Scenario: Python 3.12 和 3.13 矩阵测试
- **WHEN** workflow 执行测试 job
- **THEN** 使用矩阵策略在 Python 3.12 和 3.13 上各运行一次完整测试套件

### Requirement: hatch-vcs 从 git tag 自动推导版本号
项目 SHALL 使用 hatch-vcs 从 git tag 自动推导版本号，无需在代码中硬编码版本。

#### Scenario: 从 v0.1.6 tag 构建
- **GIVEN** 当前 git tag 为 `v0.1.6`
- **WHEN** 执行 `uv build`
- **THEN** 生成的 wheel 和 sdist 版本为 `0.1.6`

#### Scenario: 开发环境无 tag 时的 fallback
- **GIVEN** 开发环境没有 git tag 或 hatch-vcs 未生成版本文件
- **WHEN** 导入 `agent_framework_ep`
- **THEN** `__version__` 返回 `0.0.0+dev`

### Requirement: __version__ 正确反映当前版本
`agent_framework_ep.__version__` SHALL 在发布后正确反映当前版本号。

#### Scenario: 导入已发布的包获取版本
- **GIVEN** 从 PyPI 安装了 `agent-framework-ep==0.1.6`
- **WHEN** 执行 `from agent_framework_ep import __version__`
- **THEN** `__version__` 等于 `"0.1.6"`
