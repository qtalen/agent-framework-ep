## Why

当前项目需要手动执行 `uv build && uv publish` 来发布新版本到 PyPI，这不仅繁琐还容易出错（如忘记更新版本号、环境不一致等）。通过 GitHub Actions 实现 tag 触发的自动化发布，可以确保每次发布流程一致、可审计，并减少人为错误。

## What Changes

- **新增**: GitHub Actions workflow (`.github/workflows/release.yml`)，在推送语义化版本标签 (v*.*.*) 时自动触发
- **修改**: `pyproject.toml` 集成 `hatch-vcs`，实现从 git tag 自动推导版本号，移除硬编码 version
- **修改**: `src/agent_framework_ep/__init__.py` 中的 `__version__` 改为从 hatch-vcs 生成的版本文件动态导入
- **新增**: `.gitignore` 条目，忽略自动生成的 `_version.py` 文件
- **配置**: PyPI Trusted Publisher（OIDC），无需存储 API token 即可安全发布

## Capabilities

### New Capabilities
- `ci-cd-pypi-release`: GitHub Actions 自动化发布到 PyPI，支持 tag 触发、多 Python 版本测试、Trusted Publisher 认证

### Modified Capabilities
<!-- 此变更为基础设施配置，不涉及业务功能需求变更 -->

## Impact

- **发布流程**: 开发者只需 `git tag v0.1.6 && git push origin v0.1.6`，无需本地执行发布命令
- **版本管理**: 版本号唯一来源为 git tag，消除多处维护版本号的不一致性
- **安全性**: 使用 PyPI Trusted Publisher 替代长期有效的 API token
- **测试覆盖**: 发布前自动在 Python 3.12 和 3.13 上运行完整测试套件
- **外部依赖**: 需要仓库管理员在 PyPI 网站配置 Trusted Publisher

## Non-goals

- 不支持手动触发发布 (workflow_dispatch)
- 不自动生成 CHANGELOG 或 GitHub Release 页面
- 不支持预发布版本 (alpha/beta/rc) 的特殊处理
- 不实现多包仓库的复杂发布场景
