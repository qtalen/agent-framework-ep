## Context

当前项目使用 `hatchling` 作为构建后端，版本号在 `pyproject.toml` 和 `src/agent_framework_ep/__init__.py` 中硬编码。发布流程完全手动，容易出错且无法审计。

需要建立一套自动化 CI/CD 流程：
- 通过 git tag 触发发布
- 使用 hatch-vcs 从 tag 自动推导版本
- 使用 GitHub Actions 执行构建和测试
- 使用 PyPI Trusted Publisher 进行安全认证

## Goals / Non-Goals

**Goals:**
- 推送语义化版本标签时自动触发 PyPI 发布
- 版本号唯一来源为 git tag，消除多处维护的不一致
- 发布前在 Python 3.12 和 3.13 上通过完整测试
- 使用 Trusted Publisher 替代长期 API token，提升安全性
- `__version__` 在运行时正确反映当前版本

**Non-Goals:**
- 支持手动触发发布 (workflow_dispatch)
- 自动生成 CHANGELOG 或 GitHub Release
- 支持预发布版本 (alpha/beta/rc) 的特殊流程
- 实现回滚机制（PyPI 不支持删除已发布版本）

## Decisions

### Decision 1: 使用 hatch-vcs 进行版本管理

**选择**: 集成 `hatch-vcs` 插件，从 git tag 自动推导版本。

**理由**:
- 与 hatchling 构建后端原生集成
- 自动生成 `_version.py` 文件，无需手动维护
- 支持本地开发 fallback（`0.0.0+dev`）

**替代方案**: 
- `setuptools-scm`: 需要切换到 setuptools，与现有 hatchling 配置冲突
- 手动更新版本: 容易出错，无法保证 tag 与代码版本一致

### Decision 2: Trusted Publisher (OIDC) 而非 API Token

**选择**: 使用 PyPI Trusted Publisher 机制，通过 OIDC 令牌认证。

**理由**:
- 无需在 GitHub Secrets 中存储长期有效的 API token
- 令牌临时生成，仅限单次 workflow 运行
- PyPI 官方推荐的安全最佳实践

**配置要求**:
- PyPI 项目页面配置 Trusted Publisher，指定仓库、workflow 文件名
- GitHub workflow 需要 `permissions: id-token: write`

### Decision 3: 矩阵测试 Python 3.12 和 3.13

**选择**: 在发布前并行测试 Python 3.12 和 3.13。

**理由**:
- `pyproject.toml` 声明支持 `>=3.12`
- 确保在声明支持的版本上都通过测试
- 矩阵测试发现版本特定问题

### Decision 4: __version__ 动态导入 + fallback

**选择**: 运行时从 hatch-vcs 生成的 `_version.py` 导入，失败时使用 `0.0.0+dev`。

**理由**:
- 发布后版本准确反映 git tag
- 开发环境无需构建即可导入包
- 避免 `importlib.metadata` 在开发环境的导入错误

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| 误推送错误 tag 导致错误版本发布 | Tag 推送即触发，无人工确认环节。确保本地测试通过后再打 tag；错误版本无法删除，只能发布新版本覆盖 |
| hatch-vcs 版本推导失败 | 确保 `fetch-depth: 0` 拉取完整 git 历史；使用明确的语义化标签格式 `v*.*.*` |
| Trusted Publisher 配置错误导致发布失败 | 在测试发布前先在 PyPI 完成配置；首次发布前可先用 TestPyPI 验证 |
| 测试失败但 tag 已推送 | Workflow 会阻止发布；修复问题后需要新建 tag 重新触发 |
| 开发环境 `_version.py` 不存在导致导入错误 | 使用 try/except fallback 到 `0.0.0+dev` |

## Migration Plan

1. **准备阶段**（管理员操作）:
   - 在 PyPI 项目页面添加 Trusted Publisher 配置
   - 确认 GitHub 仓库 Settings → Actions → General 中 Workflow 权限正确

2. **实施阶段**:
   - 修改 `pyproject.toml` 添加 hatch-vcs 配置
   - 修改 `src/agent_framework_ep/__init__.py` 使用动态版本
   - 更新 `.gitignore` 忽略 `_version.py`
   - 创建 `.github/workflows/release.yml`

3. **验证阶段**:
   - 本地测试 `uv build` 成功
   - 提交并推送修改到 main
   - 打测试 tag（可选：使用 TestPySI 验证）
   - 观察 workflow 执行结果

4. **回滚策略**:
   - PyPI 不支持删除已发布版本
   - 如发现问题，修复后发布新版本（patch 版本号递增）
   - 可在 PyPI 中 yank（标记为不可用）有问题的版本
