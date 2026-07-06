#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档一致性测试
Documentation Consistency Test

测试文档中的配置和说明是否一致
Test if configurations and descriptions in documentation are consistent
"""

import os
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_redis_commander_port_consistency():
    """
    测试 Redis Commander 端口配置的一致性
    Test Redis Commander port configuration consistency
    """
    print("🔍 测试 Redis Commander 端口配置一致性...")
    
    # 检查 .env.example 文件
    env_example_path = project_root / ".env.example"
    if env_example_path.exists():
        with open(env_example_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
            # 应该包含 8082 端口
            if "localhost:8082" in env_content and "Redis Commander" in env_content:
                print("✅ .env.example 中 Redis Commander 端口配置正确 (8082)")
            else:
                print("❌ .env.example 中 Redis Commander 端口配置不正确")
                return False
    
    # 检查 database_setup.md 文件
    db_setup_path = project_root / "docs" / "database_setup.md"
    if db_setup_path.exists():
        with open(db_setup_path, 'r', encoding='utf-8') as f:
            db_content = f.read()
            # 应该包含 8082 端口
            if "8082" in db_content and "Redis Commander" in db_content:
                print("✅ database_setup.md 中 Redis Commander 端口配置正确 (8082)")
            else:
                print("❌ database_setup.md 中 Redis Commander 端口配置不正确")
                return False
    
    return True


def test_cli_command_format_consistency():
    """
    测试 CLI 命令格式的一致性
    Test CLI command format consistency
    """
    print("\n🔍 测试 CLI 命令格式一致性...")
    
    # 检查主要文档文件
    docs_to_check = [
        "README-CN.md",
        "docs/configuration/google-ai-setup.md"
    ]
    
    for doc_file in docs_to_check:
        doc_path = project_root / doc_file
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查是否使用了推荐的 python -m cli.main 格式
                old_format_count = len(re.findall(r'python cli/main\.py', content))
                new_format_count = len(re.findall(r'python -m cli\.main', content))
                
                if old_format_count == 0:
                    print(f"✅ {doc_file} 中 CLI 命令格式正确")
                else:
                    print(f"❌ {doc_file} 中仍有 {old_format_count} 处使用旧格式")
                    return False
    
    return True


def test_cli_smart_suggestions():
    """
    测试 CLI 智能建议功能
    Test CLI smart suggestions feature
    """
    print("\n🔍 测试 CLI 智能建议功能...")
    
    # 检查 cli/main.py 是否包含智能建议代码
    cli_main_path = project_root / "cli" / "main.py"
    if cli_main_path.exists():
        with open(cli_main_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查是否包含智能建议相关代码
            if "get_close_matches" in content and "您是否想要使用以下命令之一" in content:
                print("✅ CLI 智能建议功能已实现")
                return True
            else:
                print("❌ CLI 智能建议功能未找到")
                return False
    
    return False


def test_documentation_structure():
    """
    测试文档结构的完整性
    Test documentation structure completeness
    """
    print("\n🔍 测试文档结构完整性...")
    
    # 检查关键文档是否存在
    key_docs = [
        "README.md",
        "docs/README.md",
        "docs/database_setup.md",
        "docs/overview/quick-start.md",
        "docs/configuration/data-directory-configuration.md"
    ]
    
    missing_docs = []
    for doc in key_docs:
        doc_path = project_root / doc
        if not doc_path.exists():
            missing_docs.append(doc)
    
    if not missing_docs:
        print("✅ 所有关键文档都存在")
        return True
    else:
        print(f"❌ 缺少文档: {', '.join(missing_docs)}")
        return False


def main():
    """
    主测试函数
    Main test function
    """
    print("🚀 开始文档一致性测试...")
    print("=" * 50)
    
    tests = [
        test_redis_commander_port_consistency,
        test_cli_command_format_consistency,
        test_cli_smart_suggestions,
        test_documentation_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 执行失败: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有文档一致性测试通过！")
        return True
    else:
        print("⚠️ 部分测试未通过，请检查上述问题")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)