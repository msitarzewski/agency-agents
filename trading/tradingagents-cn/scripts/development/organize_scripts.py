#!/usr/bin/env python3
"""
整理TradingAgentsCN项目的scripts目录结构
将现有脚本按功能分类到子目录中
"""

import os
import shutil
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')


def create_scripts_structure():
    """创建scripts子目录结构"""
    
    project_path = Path("C:/code/TradingAgentsCN")
    scripts_path = project_path / "scripts"
    
    logger.info(f"📁 整理TradingAgentsCN项目的scripts目录")
    logger.info(f"=")
    
    # 定义目录结构和脚本分类
    script_categories = {
        "setup": {
            "description": "安装和配置脚本",
            "scripts": [
                "setup_databases.py",
                "init_database.py", 
                "setup_fork_environment.sh",
                "migrate_env_to_config.py"
            ]
        },
        "validation": {
            "description": "验证和检查脚本", 
            "scripts": [
                # 这里会放置验证脚本
            ]
        },
        "maintenance": {
            "description": "维护和管理脚本",
            "scripts": [
                "branch_manager.py",
                "version_manager.py"
            ]
        },
        "development": {
            "description": "开发辅助脚本",
            "scripts": [
                "prepare_upstream_contribution.py",
                "download_finnhub_sample_data.py",
                "fix_streamlit_watcher.py"
            ]
        },
        "deployment": {
            "description": "部署和发布脚本",
            "scripts": [
                "create_github_release.py",
                "release_v0.1.2.py", 
                "release_v0.1.3.py"
            ]
        },
        "docker": {
            "description": "Docker相关脚本",
            "scripts": [
                "docker-compose-start.bat",
                "start_docker_services.bat",
                "start_docker_services.sh", 
                "stop_docker_services.bat",
                "stop_docker_services.sh",
                "start_services_alt_ports.bat",
                "start_services_simple.bat",
                "mongo-init.js"
            ]
        },
        "git": {
            "description": "Git相关脚本",
            "scripts": [
                "upstream_git_workflow.sh"
            ]
        }
    }
    
    # 创建子目录
    logger.info(f"📁 创建子目录...")
    for category, info in script_categories.items():
        category_path = scripts_path / category
        category_path.mkdir(exist_ok=True)
        logger.info(f"✅ 创建目录: scripts/{category} - {info['description']}")
        
        # 创建README文件
        readme_path = category_path / "README.md"
        readme_content = f"""# {category.title()} Scripts

## 目录说明

{info['description']}

## 脚本列表

"""
        for script in info['scripts']:
            readme_content += f"- `{script}` - 脚本功能说明\n"
        
        readme_content += f"""
## 使用方法

```bash
# 进入项目根目录
cd C:\\code\\TradingAgentsCN

# 运行脚本
python scripts/{category}/script_name.py
```

## 注意事项

- 确保在项目根目录下运行脚本
- 检查脚本的依赖要求
- 某些脚本可能需要管理员权限
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        logger.info(f"📝 创建README: scripts/{category}/README.md")
    
    # 移动现有脚本到对应目录
    logger.info(f"\n📦 移动现有脚本...")
    
    for category, info in script_categories.items():
        category_path = scripts_path / category
        
        for script_name in info['scripts']:
            source_path = scripts_path / script_name
            target_path = category_path / script_name
            
            if source_path.exists():
                try:
                    shutil.move(str(source_path), str(target_path))
                    logger.info(f"✅ 移动: {script_name} -> scripts/{category}/")
                except Exception as e:
                    logger.error(f"⚠️ 移动失败 {script_name}: {e}")
            else:
                logger.info(f"ℹ️ 脚本不存在: {script_name}")
    
    # 创建主README
    logger.info(f"\n📝 创建主README...")
    main_readme_path = scripts_path / "README.md"
    main_readme_content = """# Scripts Directory

这个目录包含TradingAgentsCN项目的各种脚本工具。

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

### 🛠️ development/ - 开发辅助脚本
- 代码分析
- 性能基准测试
- 文档生成
- 贡献准备

### 🚀 deployment/ - 部署脚本
- Web应用部署
- 发布打包
- GitHub发布

### 🐳 docker/ - Docker脚本
- Docker服务管理
- 容器启动停止
- 数据库初始化

### 📋 git/ - Git工具脚本
- 上游同步
- 分支管理
- 贡献工作流

## 使用原则

### 脚本分类
- **tests/** - 单元测试和集成测试（pytest运行）
- **scripts/** - 工具脚本和验证脚本（独立运行）
- **tools/** - 复杂的独立工具程序

### 运行方式
```bash
# 从项目根目录运行
cd C:\\code\\TradingAgentsCN

# Python脚本
python scripts/validation/verify_gitignore.py

# PowerShell脚本  
powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup.ps1
```

## 注意事项

- 所有脚本应该从项目根目录运行
- 检查脚本的依赖要求
- 某些脚本可能需要特殊权限
- 保持脚本的独立性和可重用性
"""
    
    with open(main_readme_path, 'w', encoding='utf-8') as f:
        f.write(main_readme_content)
    logger.info(f"📝 创建主README: scripts/README.md")
    
    # 显示剩余的未分类脚本
    logger.info(f"\n📊 检查未分类的脚本...")
    remaining_scripts = []
    for item in scripts_path.iterdir():
        if item.is_file() and item.suffix in ['.py', '.sh', '.bat', '.js']:
            if item.name not in ['README.md']:
                remaining_scripts.append(item.name)
    
    if remaining_scripts:
        logger.warning(f"⚠️ 未分类的脚本:")
        for script in remaining_scripts:
            logger.info(f"  - {script}")
        logger.info(f"建议手动将这些脚本移动到合适的分类目录中")
    else:
        logger.info(f"✅ 所有脚本都已分类")
    
    logger.info(f"\n🎉 Scripts目录整理完成！")
    
    return True

def main():
    """主函数"""
    try:
        success = create_scripts_structure()
        
        if success:
            logger.info(f"\n🎯 整理结果:")
            logger.info(f"✅ 创建了分类子目录")
            logger.info(f"✅ 移动了现有脚本")
            logger.info(f"✅ 生成了README文档")
            logger.info(f"\n💡 建议:")
            logger.info(f"1. 验证脚本放在 scripts/validation/")
            logger.info(f"2. 测试代码放在 tests/")
            logger.info(f"3. 新脚本按功能放在对应分类目录")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 整理失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
