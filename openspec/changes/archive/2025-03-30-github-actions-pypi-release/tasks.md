## 1. PyPI 外部配置（管理员操作）

- [ ] 1.1 访问 https://pypi.org/manage/account/publishing/ 添加 Trusted Publisher
- [ ] 1.2 配置 Publisher：Owner=`qtalen`，Repository=`agent-framework-ep`，Workflow=`release.yml`
- [ ] 1.3 （可选）配置 Environment 为 `pypi` 以增强安全性

## 2. 配置 hatch-vcs 版本管理

- [x] 2.1 修改 `pyproject.toml`：
  - 在 `[build-system] requires` 中添加 `"hatch-vcs"`
  - 添加 `dynamic = ["version"]` 到 `[project]`
  - 删除 `[project]` 中的 `version = "0.1.5"`
  - 添加 `[tool.hatch.version]` 配置 `source = "vcs"`
  - 添加 `[tool.hatch.build.hooks.vcs]` 配置 `version-file = "src/agent_framework_ep/_version.py"`
- [x] 2.2 更新 `.gitignore`，添加 `src/agent_framework_ep/_version.py`

## 3. 更新 __init__.py 使用动态版本

- [x] 3.1 修改 `src/agent_framework_ep/__init__.py`：
  - 删除硬编码 `__version__ = "0.1.5"`
  - 添加动态导入逻辑，try/except 从 `_version` 导入，失败时 fallback 到 `"0.0.0+dev"`
  - 保持 `__all__` 列表包含 `"__version__"`

## 4. 创建 GitHub Actions Workflow

- [x] 4.1 创建目录 `.github/workflows/`
- [x] 4.2 创建 `release.yml`：
  - 配置 trigger：`on.push.tags: ['v[0-9]+.[0-9]+.[0-9]+']`
  - 配置 permissions：`id-token: write`（用于 Trusted Publisher）
  - 创建 `build` job：checkout (fetch-depth: 0)，uv sync，uv build
  - 创建 `test` job：矩阵测试 Python 3.12 和 3.13，运行 pytest、ruff、mypy
  - 创建 `publish` job：依赖 build 和 test，使用 `pypa/gh-action-pypi-publish@release/v1`

## 5. 本地验证

- [x] 5.1 运行 `uv sync --prerelease=allow --all-extras` 安装 hatch-vcs
- [x] 5.2 运行 `uv build` 验证构建成功，检查生成的版本是否正确
- [x] 5.3 运行 `uv run pytest`、`uv run ruff check .`、`uv run mypy src/agent_framework_ep` 确保全部通过

## 6. 提交与发布测试

- [ ] 6.1 提交所有更改到 main 分支
- [ ] 6.2 本地创建测试 tag：`git tag v0.1.6`
- [ ] 6.3 推送 tag 触发 workflow：`git push origin v0.1.6`
- [ ] 6.4 在 GitHub Actions 页面观察 workflow 执行结果
- [ ] 6.5 验证 PyPI 上是否成功发布新版本
