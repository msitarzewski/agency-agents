# Validation Scripts

## 目录说明

这个目录包含各种验证脚本，用于检查项目配置、依赖、Git设置等。

## 脚本列表

- `verify_gitignore.py` - 验证Git忽略配置，确保docs/contribution目录不被版本控制
- `check_dependencies.py` - 检查项目依赖是否正确安装
- `smart_config.py` - 智能配置检测和管理

## 使用方法

```bash
# 进入项目根目录
cd C:\code\TradingAgentsCN

# 运行验证脚本
python scripts/validation/verify_gitignore.py
python scripts/validation/check_dependencies.py
python scripts/validation/smart_config.py
```

## 验证脚本 vs 测试脚本的区别

### 验证脚本 (scripts/validation/)
- **目的**: 检查项目配置、环境设置、依赖状态
- **运行时机**: 开发环境设置、部署前检查、问题排查
- **特点**: 独立运行，提供详细的检查报告和修复建议

### 测试脚本 (tests/)
- **目的**: 验证代码功能正确性
- **运行时机**: 开发过程中、CI/CD流程
- **特点**: 使用pytest框架，专注于代码逻辑测试

## 注意事项

- 确保在项目根目录下运行脚本
- 验证脚本会检查系统状态并提供修复建议
- 某些验证可能需要网络连接或特定权限
- 验证失败时会提供详细的错误信息和解决方案
