## 1. 创建 CI 工作流文件

- [x] 1.1 创建 `.github/workflows/ci.yml` 文件
- [x] 1.2 配置 `on: pull_request` 触发器
- [x] 1.3 添加 `lint` job（ruff check）
- [x] 1.4 添加 `format-check` job（ruff format --check）
- [x] 1.5 添加 `type-check` job（mypy）
- [x] 1.6 添加 `test` job（pytest -m "not docker"）
- [x] 1.7 配置 Python 版本矩阵（3.12, 3.13）
- [x] 1.8 使用 `needs` 关键字实现串行执行

## 2. 配置工具和环境

- [x] 2.1 配置 uv 安装步骤
- [x] 2.2 配置 Python 环境设置
- [x] 2.3 配置依赖安装（uv sync --prerelease=allow --all-extras）
- [x] 2.4 验证与 release.yml 的工具版本一致性

## 3. 测试和验证

- [ ] 3.1 提交 PR 测试 ci.yml 是否能正常触发
- [ ] 3.2 验证 lint 失败时是否正确阻止合并
- [ ] 3.3 验证所有检查通过时 PR 可以正常合并
- [ ] 3.4 验证 Python 3.12 和 3.13 矩阵都正确运行

## 4. 配置 GitHub Branch Protection

- [ ] 4.1 进入仓库 Settings → Branches
- [ ] 4.2 添加规则保护 `main` 分支
- [ ] 4.3 启用 "Require status checks to pass before merging"
- [ ] 4.4 添加 `lint` 作为 required check
- [ ] 4.5 添加 `format-check` 作为 required check
- [ ] 4.6 添加 `type-check` 作为 required check
- [ ] 4.7 添加 `test` 作为 required check

## 5. 文档和清理

- [x] 5.1 在 README.md 中添加 CI 状态徽章
- [ ] 5.2 更新开发文档说明 CI 流程
- [ ] 5.3 验证所有任务完成并归档变更

