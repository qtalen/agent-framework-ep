## Context

当前项目使用 GitHub Actions 进行发布管理（release.yml），但该工作流仅在打 tag 时触发。这导致代码质量问题可能在发布前才被发现，增加了修复成本和发布风险。

需要在 Pull Request 阶段建立质量门禁，确保所有合入主干的代码都通过基础质量检查。

## Goals / Non-Goals

**Goals:**
- 在 PR 阶段运行完整的质量检查流程
- 支持 Python 3.12 和 3.13 双版本矩阵
- 串行执行任务以节约 CI 资源并实现快速失败
- 与现有 release.yml 保持一致（使用 uv、排除 Docker 测试）

**Non-Goals:**
- 不修改现有的 release.yml
- 不添加代码覆盖率报告
- 不添加自动修复或自动格式化功能
- 不支持 Windows/macOS 测试矩阵

## Decisions

### 1. 使用 pull_request 事件触发
**决策**: 使用 `on: pull_request` 而非 `on: push`

**理由**:
- `pull_request` 事件在 PR 创建和更新时都会触发
- GitHub 会自动在 PR 页面显示检查状态
- 可以与 Branch protection rule 集成

**替代方案考虑**:
- `on: push` 会在任意 push 时触发，包括已合并的 commit，浪费资源
- `on: pull_request_target` 权限过大，有安全风险

### 2. 串行执行而非并行
**决策**: 使用 `needs` 关键字实现串行执行

```
lint → type-check → test
```

**理由**:
- 早期失败可以跳过后续任务，节约 CI 分钟数
- Lint 和 type-check 通常比测试快很多，早期发现问题

**替代方案考虑**:
- 并行执行可以更快获得反馈，但资源消耗翻倍
- 本项目规模适中，串行执行总时间可接受（预计 2-3 分钟）

### 3. 复用现有工具配置
**决策**: 直接使用 pyproject.toml 中已配置的 ruff 和 mypy 设置

**理由**:
- 避免重复配置和配置漂移
- 保持与本地开发环境一致

### 4. 使用 needs 作为合并门禁
**决策**: 依赖 `needs` 机制阻止合并，而非 `continue-on-error`

**理由**:
- GitHub 的 "Require status checks" 可以直接引用 job 名称
- 简单直观，无需额外的 status reporting

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| [风险] 新增 CI 会减慢 PR 合并速度 | [缓解] 串行执行快速失败，lint/type-check 通常 < 30 秒 |
| [风险] Python 3.13 测试矩阵增加 CI 分钟消耗 | [缓解] 仅使用 Ubuntu 单系统，不扩展其他系统 |
| [风险] 开发者不熟悉 GitHub Branch protection 配置 | [缓解] 在文档中提供配置步骤 |

## Migration Plan

1. **创建 ci.yml 文件** → 提交 PR
2. **验证工作流正常运行** → 检查 Actions 标签页
3. **配置 Branch protection rule**:
   - 进入 Settings → Branches
   - 添加规则保护 `main` 分支
   - 启用 "Require status checks to pass before merging"
   - 搜索并选择 `ci.yml` 中的 job 名称（如 `lint`, `type-check`, `test`）
4. **完成** → 后续 PR 必须通过 CI 才能合并

## Open Questions

无

