## 说明

此变更不涉及功能规格的添加、修改或删除。

该变更仅在抽象基类 `CodeExecutor` 中添加 `execute_script` 方法的抽象声明，以统一现有子类 (`DockerCommandLineCodeExecutor`, `LocalCommandLineCodeExecutor`) 的接口契约。

具体的行为规格已在现有实现中定义，无需更改。
