## Context

当前CI流程中的ruff lint检查被注释掉了（`.github/workflows/release.yml`第75-77行），原因是存在11处pre-existing的lint错误。这些错误都是代码风格问题，不涉及功能缺陷。

## Goals / Non-Goals

**Goals:**
- 修复所有11处ruff lint错误
- 重新启用CI中的ruff check
- 确保CI通过

**Non-Goals:**
- 不修改任何功能逻辑
- 不添加新的lint规则
- 不改变测试行为

## Decisions

### 修复策略

使用ruff的自动修复功能处理简单的import问题，手动修复需要逻辑判断的问题：

1. **自动修复（--fix）**：F401未使用导入、F811重复定义
2. **手动修复**：
   - SIM102：合并嵌套if条件
   - SIM105：使用contextlib.suppress替换try-except-pass
   - SIM108：使用三元运算符简化赋值
   - B017：使用具体的异常类型而非泛化的Exception

### 文件变更清单

| 文件 | 错误类型 | 修复方式 |
|------|----------|----------|
| `src/agent_framework_ep/code_executor/base.py:172` | SIM102 | 合并if条件 |
| `src/agent_framework_ep/code_executor/docker/executor.py:255` | SIM105 | 使用suppress |
| `src/agent_framework_ep/openai_like/_reasoning_content.py:60` | SIM108 | 三元运算符 |
| `src/agent_framework_ep/openai_like/_reasoning_content.py:80` | SIM102 | 合并if条件 |
| `tests/openai_like/test_init.py:3,6,10` | F401 | 删除未使用导入 |
| `tests/openai_like/test_init.py:236` | F811 | 删除重复导入（保留函数内导入用于测试） |
| `tests/openai_like/test_response_format.py:3,5` | F401 | 删除未使用导入 |
| `tests/openai_like/test_response_format.py:150` | B017 | 使用具体异常类型 |

## Risks / Trade-offs

无重大风险。所有变更都是代码风格改进，经过ruff自动检查确保正确性。
