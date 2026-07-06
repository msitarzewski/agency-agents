#!/usr/bin/env python3
"""
整理根目录下的脚本文件
将测试和验证脚本移动到对应的目录中
"""

import os
import shutil
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

def organize_root_scripts():
    """整理根目录下的脚本文件"""
    
    # 项目根目录
    project_root = Path(__file__).parent.parent.parent
    
    logger.info(f"📁 整理TradingAgentsCN根目录下的脚本文件")
    logger.info(f"=")
    logger.info(f"📍 项目根目录: {project_root}")
    
    # 定义文件移动规则
    file_moves = {
        # 验证脚本 -> scripts/validation/
        "check_dependencies.py": "scripts/validation/check_dependencies.py",
        "verify_gitignore.py": "scripts/validation/verify_gitignore.py",
        "smart_config.py": "scripts/validation/smart_config.py",
        
        # 测试脚本 -> tests/
        "quick_test.py": "tests/quick_test.py",
        "test_smart_system.py": "tests/test_smart_system.py",
        "demo_fallback_system.py": "tests/demo_fallback_system.py",
        
        # 开发脚本 -> scripts/development/
        "adaptive_cache_manager.py": "scripts/development/adaptive_cache_manager.py",
        "organize_scripts.py": "scripts/development/organize_scripts.py",
        
        # 设置脚本 -> scripts/setup/
        "setup_fork_environment.ps1": "scripts/setup/setup_fork_environment.ps1",
        
        # 维护脚本 -> scripts/maintenance/
        "remove_contribution_from_git.ps1": "scripts/maintenance/remove_contribution_from_git.ps1",
        "analyze_differences.ps1": "scripts/maintenance/analyze_differences.ps1",
        "debug_integration.ps1": "scripts/maintenance/debug_integration.ps1",
        "integrate_cache_improvements.ps1": "scripts/maintenance/integrate_cache_improvements.ps1",
        "migrate_first_contribution.ps1": "scripts/maintenance/migrate_first_contribution.ps1",
        "create_scripts_structure.ps1": "scripts/maintenance/create_scripts_structure.ps1",
    }
    
    # 创建必要的目录
    directories_to_create = [
        "scripts/validation",
        "scripts/setup", 
        "scripts/maintenance",
        "scripts/development",
        "tests/integration",
        "tests/validation"
    ]
    
    logger.info(f"\n📁 创建必要的目录...")
    for dir_path in directories_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 确保目录存在: {dir_path}")
    
    # 移动文件
    logger.info(f"\n📦 移动脚本文件...")
    moved_count = 0
    skipped_count = 0
    
    for source_file, target_path in file_moves.items():
        source_path = project_root / source_file
        target_full_path = project_root / target_path
        
        if source_path.exists():
            try:
                # 确保目标目录存在
                target_full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                shutil.move(str(source_path), str(target_full_path))
                logger.info(f"✅ 移动: {source_file} -> {target_path}")
                moved_count += 1
                
            except Exception as e:
                logger.error(f"❌ 移动失败 {source_file}: {e}")
        else:
            logger.info(f"ℹ️ 文件不存在: {source_file}")
            skipped_count += 1
    
    # 检查剩余的脚本文件
    logger.debug(f"\n🔍 检查剩余的脚本文件...")
    remaining_scripts = []
    
    script_extensions = ['.py', '.ps1', '.sh', '.bat']
    for item in project_root.iterdir():
        if item.is_file() and item.suffix in script_extensions:
            # 排除主要的项目文件
            if item.name not in ['main.py', 'setup.py', 'start_web.bat', 'start_web.ps1']:
                remaining_scripts.append(item.name)
    
    if remaining_scripts:
        logger.warning(f"⚠️ 根目录下仍有脚本文件:")
        for script in remaining_scripts:
            logger.info(f"  - {script}")
        logger.info(f"\n💡 建议手动检查这些文件是否需要移动")
    else:
        logger.info(f"✅ 根目录下没有剩余的脚本文件")
    
    # 创建README文件
    logger.info(f"\n📝 更新README文件...")
    
    # 更新scripts/validation/README.md
    validation_readme = project_root / "scripts/validation/README.md"
    validation_content = """# Validation Scripts

## 目录说明

这个目录包含各种验证脚本，用于检查项目配置、依赖、Git设置等。

## 脚本列表

- `verify_gitignore.py` - 验证Git忽略配置，确保docs/contribution目录不被版本控制
- `check_dependencies.py` - 检查项目依赖是否正确安装
- `smart_config.py` - 智能配置检测和管理

## 使用方法

```bash
# 进入项目根目录
cd C:\\code\\TradingAgentsCN

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
"""
    
    with open(validation_readme, 'w', encoding='utf-8') as f:
        f.write(validation_content)
    logger.info(f"✅ 更新: scripts/validation/README.md")
    
    # 更新tests/README.md
    tests_readme = project_root / "tests/README.md"
    if tests_readme.exists():
        with open(tests_readme, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # 添加新移动的测试文件说明
        additional_content = """

## 新增的测试文件

### 集成测试
- `quick_test.py` - 快速集成测试，验证基本功能
- `test_smart_system.py` - 智能系统完整测试
- `demo_fallback_system.py` - 降级系统演示和测试

### 运行方法
```bash
# 快速测试
python tests/quick_test.py

# 智能系统测试
python tests/test_smart_system.py

# 降级系统演示
python tests/demo_fallback_system.py
```
"""
        
        if "新增的测试文件" not in existing_content:
            with open(tests_readme, 'a', encoding='utf-8') as f:
                f.write(additional_content)
            logger.info(f"✅ 更新: tests/README.md")
    
    # 统计结果
    logger.info(f"\n📊 整理结果统计:")
    logger.info(f"✅ 成功移动: {moved_count} 个文件")
    logger.info(f"ℹ️ 跳过文件: {skipped_count} 个文件")
    logger.warning(f"⚠️ 剩余脚本: {len(remaining_scripts)} 个文件")
    
    logger.info(f"\n🎯 目录结构优化完成!")
    logger.info(f"📁 验证脚本: scripts/validation/")
    logger.info(f"🧪 测试脚本: tests/")
    logger.info(f"🔧 工具脚本: scripts/对应分类/")
    
    return moved_count > 0

def main():
    """主函数"""
    try:
        success = organize_root_scripts()
        
        if success:
            logger.info(f"\n🎉 脚本整理完成!")
            logger.info(f"\n💡 建议:")
            logger.info(f"1. 检查移动后的脚本是否正常工作")
            logger.info(f"2. 更新相关文档中的路径引用")
            logger.info(f"3. 提交这些目录结构变更")
        else:
            logger.warning(f"\n⚠️ 没有文件被移动")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 整理失败: {e}")
        import traceback

        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
