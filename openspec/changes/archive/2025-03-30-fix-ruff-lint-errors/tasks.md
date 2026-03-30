## 1. 修复源代码中的lint错误

- [x] 1.1 修复 `base.py` SIM102错误 - 合并嵌套if条件
- [x] 1.2 修复 `executor.py` SIM105错误 - 使用contextlib.suppress
- [x] 1.3 修复 `_reasoning_content.py` SIM108错误 - 使用三元运算符
- [x] 1.4 修复 `_reasoning_content.py` SIM102错误 - 合并嵌套if条件

## 2. 修复测试文件中的lint错误

- [x] 2.1 修复 `test_init.py` F401/F811错误 - 清理未使用和重复导入
- [x] 2.2 修复 `test_response_format.py` F401错误 - 删除未使用导入
- [x] 2.3 修复 `test_response_format.py` B017错误 - 使用具体异常类型

## 3. 启用CI检查

- [x] 3.1 取消 `.github/workflows/release.yml` 中ruff check的注释

## 4. 验证

- [x] 4.1 本地运行 `uv run ruff check .` 确认无错误
- [x] 4.2 运行 `uv run pytest` 确认测试通过
