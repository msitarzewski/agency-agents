#!/usr/bin/env python3
"""
完成脚本文件的最终整理
将剩余的脚本文件移动到合适的分类目录
"""

import os
import shutil
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

def finalize_script_organization():
    """完成脚本文件的最终整理"""
    
    # 项目根目录
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / "scripts"
    
    logger.info(f"📁 完成TradingAgentsCN脚本文件的最终整理")
    logger.info(f"=")
    logger.info(f"📍 项目根目录: {project_root}")
    
    # 定义剩余文件的移动规则
    remaining_moves = {
        # 设置和数据库脚本 -> scripts/setup/
        "setup_databases.py": "setup/setup_databases.py",
        "init_database.py": "setup/init_database.py",
        "migrate_env_to_config.py": "setup/migrate_env_to_config.py",
        
        # 开发和贡献脚本 -> scripts/development/
        "prepare_upstream_contribution.py": "development/prepare_upstream_contribution.py",
        "download_finnhub_sample_data.py": "development/download_finnhub_sample_data.py",
        "fix_streamlit_watcher.py": "development/fix_streamlit_watcher.py",
        
        # 发布和版本管理 -> scripts/deployment/
        "create_github_release.py": "deployment/create_github_release.py",
        "release_v0.1.2.py": "deployment/release_v0.1.2.py",
        "release_v0.1.3.py": "deployment/release_v0.1.3.py",
        
        # 维护和管理脚本 -> scripts/maintenance/
        "branch_manager.py": "maintenance/branch_manager.py",
        "version_manager.py": "maintenance/version_manager.py",
        
        # Docker脚本 -> scripts/docker/
        "docker-compose-start.bat": "docker/docker-compose-start.bat",
        "start_docker_services.bat": "docker/start_docker_services.bat",
        "start_docker_services.sh": "docker/start_docker_services.sh",
        "stop_docker_services.bat": "docker/stop_docker_services.bat",
        "stop_docker_services.sh": "docker/stop_docker_services.sh",
        "start_services_alt_ports.bat": "docker/start_services_alt_ports.bat",
        "start_services_simple.bat": "docker/start_services_simple.bat",
        "mongo-init.js": "docker/mongo-init.js",
        
        # Git工具 -> scripts/git/
        "upstream_git_workflow.sh": "git/upstream_git_workflow.sh",
        "setup_fork_environment.sh": "git/setup_fork_environment.sh",
    }
    
    # 创建必要的目录
    directories_to_create = [
        "deployment",
        "docker", 
        "git"
    ]
    
    logger.info(f"\n📁 创建必要的目录...")
    for dir_name in directories_to_create:
        dir_path = scripts_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 确保目录存在: scripts/{dir_name}")
    
    # 移动文件
    logger.info(f"\n📦 移动剩余脚本文件...")
    moved_count = 0
    
    for source_file, target_path in remaining_moves.items():
        source_path = scripts_dir / source_file
        target_full_path = scripts_dir / target_path
        
        if source_path.exists():
            try:
                # 确保目标目录存在
                target_full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                shutil.move(str(source_path), str(target_full_path))
                logger.info(f"✅ 移动: {source_file} -> scripts/{target_path}")
                moved_count += 1
                
            except Exception as e:
                logger.error(f"❌ 移动失败 {source_file}: {e}")
        else:
            logger.info(f"ℹ️ 文件不存在: {source_file}")
    
    # 创建各目录的README文件
    logger.info(f"\n📝 创建README文件...")
    
    readme_contents = {
        "deployment": {
            "title": "Deployment Scripts",
            "description": "部署和发布相关脚本",
            "scripts": [
                "create_github_release.py - 创建GitHub发布",
                "release_v0.1.2.py - 发布v0.1.2版本",
                "release_v0.1.3.py - 发布v0.1.3版本"
            ]
        },
        "docker": {
            "title": "Docker Scripts", 
            "description": "Docker容器管理脚本",
            "scripts": [
                "docker-compose-start.bat - 启动Docker Compose",
                "start_docker_services.* - 启动Docker服务",
                "stop_docker_services.* - 停止Docker服务",
                "mongo-init.js - MongoDB初始化脚本"
            ]
        },
        "git": {
            "title": "Git Tools",
            "description": "Git工具和工作流脚本", 
            "scripts": [
                "upstream_git_workflow.sh - 上游Git工作流",
                "setup_fork_environment.sh - 设置Fork环境"
            ]
        }
    }
    
    for dir_name, info in readme_contents.items():
        readme_path = scripts_dir / dir_name / "README.md"
        
        content = f"""# {info['title']}

## 目录说明

{info['description']}

## 脚本列表

"""
        for script in info['scripts']:
            content += f"- `{script}`\n"
        
        content += f"""
## 使用方法

```bash
# 进入项目根目录
cd C:\\code\\TradingAgentsCN

# 运行脚本
python scripts/{dir_name}/script_name.py
```

## 注意事项

- 确保在项目根目录下运行脚本
- 检查脚本的依赖要求
- 某些脚本可能需要特殊权限
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✅ 创建README: scripts/{dir_name}/README.md")
    
    # 更新主README
    logger.info(f"\n📝 更新主README...")
    main_readme_path = scripts_dir / "README.md"
    
    main_content = """# Scripts Directory

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
- 上游同步
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
cd C:\\code\\TradingAgentsCN

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
"""
    
    with open(main_readme_path, 'w', encoding='utf-8') as f:
        f.write(main_content)
    logger.info(f"✅ 更新主README: scripts/README.md")
    
    # 检查最终状态
    logger.info(f"\n📊 检查最终状态...")
    
    # 统计各目录的脚本数量
    subdirs = ["setup", "validation", "maintenance", "development", "deployment", "docker", "git"]
    total_scripts = 0
    
    for subdir in subdirs:
        subdir_path = scripts_dir / subdir
        if subdir_path.exists():
            script_files = [f for f in subdir_path.iterdir() 
                          if f.is_file() and f.suffix in ['.py', '.ps1', '.sh', '.bat', '.js']]
            script_count = len(script_files)
            total_scripts += script_count
            logger.info(f"📁 scripts/{subdir}: {script_count} 个脚本")
    
    # 检查根级别剩余脚本
    root_scripts = [f for f in scripts_dir.iterdir() 
                   if f.is_file() and f.suffix in ['.py', '.ps1', '.sh', '.bat', '.js']]
    
    if root_scripts:
        logger.warning(f"\n⚠️ scripts根目录仍有 {len(root_scripts)} 个脚本:")
        for script in root_scripts:
            logger.info(f"  - {script.name}")
    else:
        logger.info(f"\n✅ scripts根目录已清理完成")
    
    logger.info(f"\n📊 整理结果:")
    logger.info(f"✅ 总共整理: {total_scripts} 个脚本")
    logger.info(f"✅ 分类目录: {len(subdirs)} 个")
    logger.info(f"✅ 本次移动: {moved_count} 个文件")
    
    return moved_count > 0

def main():
    """主函数"""
    try:
        success = finalize_script_organization()
        
        if success:
            logger.info(f"\n🎉 脚本整理完成!")
            logger.info(f"\n💡 建议:")
            logger.info(f"1. 检查移动后的脚本是否正常工作")
            logger.info(f"2. 更新相关文档中的路径引用")
            logger.info(f"3. 提交这些目录结构变更")
            logger.info(f"4. 验证各分类目录的脚本功能")
        else:
            logger.info(f"\n✅ 脚本已经整理完成，无需移动")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 整理失败: {e}")
        import traceback

        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
