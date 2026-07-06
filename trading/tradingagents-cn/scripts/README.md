# Scripts Directory

这个目录包含TradingAgentsCN项目的各种脚本工具，按功能分类组织。

## 目录结构

### 📦 setup/ - 安装和配置脚本
- 环境设置
- 依赖安装  
- API配置
- 数据库设置

### 🔍 validation/ - 验证脚本
- Git配置验证
- 依赖检查
- 配置验证
- API连接测试

### 🔧 maintenance/ - 维护脚本
- 缓存清理
- 数据备份
- 依赖更新
- 分支管理

### 🛠️ development/ - 开发辅助脚本
- 代码分析
- 性能基准测试
- 文档生成
- 贡献准备
- 数据下载

### 🚀 deployment/ - 部署脚本
- GitHub发布
- 版本发布
- 打包部署

### 🐳 docker/ - Docker脚本
- Docker服务管理
- 容器启动停止
- 数据库初始化

### 📋 git/ - Git工具脚本
- 上游同步
- Fork环境设置
- 贡献工作流

## 使用原则

### 脚本分类
- **tests/** - 单元测试和集成测试（pytest运行）
- **scripts/** - 工具脚本和验证脚本（独立运行）
- **utils/** - 实用工具脚本

### 运行方式
```bash
# 从项目根目录运行
cd C:\code\TradingAgentsCN

# Python脚本
python scripts/validation/verify_gitignore.py

# PowerShell脚本  
powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup.ps1

# Bash脚本
bash scripts/git/upstream_git_workflow.sh
```

## 目录说明

| 目录 | 用途 | 示例脚本 |
|------|------|----------|
| `setup/` | 环境配置和初始化 | setup_databases.py |
| `validation/` | 验证和检查 | verify_gitignore.py |
| `maintenance/` | 维护和管理 | branch_manager.py |
| `development/` | 开发辅助 | prepare_upstream_contribution.py |
| `deployment/` | 部署发布 | create_github_release.py |
| `docker/` | 容器管理 | start_docker_services.bat |
| `git/` | Git工具 | upstream_git_workflow.sh |

## 注意事项

- 所有脚本应该从项目根目录运行
- 检查脚本的依赖要求
- 某些脚本可能需要特殊权限
- 保持脚本的独立性和可重用性

## 开发指南

### 添加新脚本
1. 确定脚本类型和目标目录
2. 创建脚本文件
3. 添加适当的文档注释
4. 更新相应目录的README
5. 测试脚本功能

### 脚本模板
每个脚本应包含：
- 文件头注释说明用途
- 使用方法说明
- 依赖要求
- 错误处理
- 日志输出
