## Why

当前项目仅在发布打 tag 时运行测试和 lint 检查，这导致潜在问题可能在代码合并后才被发现，回滚成本高。需要在 Pull Request 合并前建立质量门禁，确保代码质量符合标准。

## What Changes

- 新增 `.github/workflows/ci.yml` 工作流文件
- 在 PR 阶段运行完整的质量检查流程：ruff lint → mypy type-check → pytest
- 支持 Python 3.12 和 3.13 双版本矩阵测试
- 所有检查通过后方可合并分支

## Capabilities

### New Capabilities
- `pr-ci-gate`: PR 合并前的持续集成门禁系统，确保代码通过 lint、type-check 和测试

### Modified Capabilities
- （无）

## Non-goals

- 不修改 release.yml 的现有发布流程
- 不添加 Docker 测试（保持与 release.yml 一致，使用 `-m "not docker"`）
- 不添加代码覆盖率报告上传
- 不添加自动格式化或自动修复功能

## Impact

- 新增 GitHub Actions 工作流：`.github/workflows/ci.yml`
- 需要在 GitHub 仓库设置中配置 Branch protection rule，启用 "Require status checks to pass before merging"
- 所有现有和未来的 PR 都需要通过 CI 检查才能合并

