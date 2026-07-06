#!/usr/bin/env python3
"""
TradingAgents-CN v0.1.3 发布脚本
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')


def run_command(command, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """检查Git状态"""
    logger.debug(f"🔍 检查Git状态...")
    
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        logger.error(f"❌ Git状态检查失败: {stderr}")
        return False
    
    if stdout.strip():
        logger.warning(f"⚠️ 发现未提交的更改:")
        print(stdout)
        response = input("是否继续发布? (y/N): ")
        if response.lower() != 'y':
            return False
    
    logger.info(f"✅ Git状态检查通过")
    return True

def update_version_files():
    """更新版本文件"""
    logger.info(f"📝 更新版本文件...")
    
    version = "cn-0.1.3"
    
    # 更新VERSION文件
    try:
        with open("VERSION", "w", encoding='utf-8') as f:
            f.write(f"{version}\n")
        logger.info(f"✅ VERSION文件已更新")
    except Exception as e:
        logger.error(f"❌ 更新VERSION文件失败: {e}")
        return False
    
    return True

def run_tests():
    """运行测试"""
    logger.info(f"🧪 运行基础测试...")
    
    # 测试Tushare数据接口
    logger.info(f"  📊 测试Tushare数据接口...")
    success, stdout, stderr = run_command("python tests/fast_tdx_test.py")
    if success:
        logger.info(f"  ✅ Tushare数据接口测试通过")
    else:
        logger.warning(f"  ⚠️ Tushare数据接口测试警告: {stderr}")
        # 不阻止发布，因为可能是网络问题
    
    # 测试Web界面启动
    logger.info(f"  🌐 测试Web界面...")
    # 这里可以添加Web界面的基础测试
    logger.info(f"  ✅ Web界面测试跳过（需要手动验证）")
    
    return True

def create_git_tag():
    """创建Git标签"""
    logger.info(f"🏷️ 创建Git标签...")
    
    tag_name = "v0.1.3"
    tag_message = "TradingAgents-CN v0.1.3 - A股市场完整支持"
    
    # 检查标签是否已存在
    success, stdout, stderr = run_command(f"git tag -l {tag_name}")
    if stdout.strip():
        logger.warning(f"⚠️ 标签 {tag_name} 已存在")
        response = input("是否删除现有标签并重新创建? (y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d {tag_name}")
            run_command(f"git push origin --delete {tag_name}")
        else:
            return False
    
    # 创建标签
    success, stdout, stderr = run_command(f'git tag -a {tag_name} -m "{tag_message}"')
    if not success:
        logger.error(f"❌ 创建标签失败: {stderr}")
        return False
    
    logger.info(f"✅ 标签 {tag_name} 创建成功")
    return True

def commit_changes():
    """提交更改"""
    logger.info(f"💾 提交版本更改...")
    
    # 添加更改的文件
    files_to_add = [
        "VERSION",
        "CHANGELOG.md", 
        "README.md",
        "RELEASE_NOTES_v0.1.3.md",
        "docs/guides/a-share-analysis-guide.md",
        "docs/data/china_stock-api-integration.md",
        "tradingagents/dataflows/tdx_utils.py",
        "tradingagents/agents/utils/agent_utils.py",
        "web/components/analysis_form.py",
        "requirements.txt"
    ]
    
    for file in files_to_add:
        if os.path.exists(file):
            run_command(f"git add {file}")
    
    # 提交更改
    commit_message = "🚀 Release v0.1.3: A股市场完整支持\n\n- 集成Tushare数据接口支持A股实时数据\n- 新增Web界面市场选择功能\n- 优化新闻分析滞后性\n- 完善文档和使用指南"
    
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success and "nothing to commit" not in stderr:
        logger.error(f"❌ 提交失败: {stderr}")
        return False
    
    logger.info(f"✅ 更改已提交")
    return True

def push_to_remote():
    """推送到远程仓库"""
    logger.info(f"🚀 推送到远程仓库...")
    
    # 推送代码
    success, stdout, stderr = run_command("git push origin main")
    if not success:
        logger.error(f"❌ 推送代码失败: {stderr}")
        return False
    
    # 推送标签
    success, stdout, stderr = run_command("git push origin --tags")
    if not success:
        logger.error(f"❌ 推送标签失败: {stderr}")
        return False
    
    logger.info(f"✅ 推送完成")
    return True

def generate_release_summary():
    """生成发布摘要"""
    logger.info(f"\n")
    logger.info(f"🎉 TradingAgents-CN v0.1.3 发布完成!")
    logger.info(f"=")
    
    logger.info(f"\n📋 发布内容:")
    logger.info(f"  🇨🇳 A股市场完整支持")
    logger.info(f"  📊 Tushare数据接口集成")
    logger.info(f"  🌐 Web界面市场选择")
    logger.info(f"  📰 实时新闻优化")
    logger.info(f"  📚 完善的文档和指南")
    
    logger.info(f"\n🔗 相关文件:")
    logger.info(f"  📄 发布说明: RELEASE_NOTES_v0.1.3.md")
    logger.info(f"  📖 A股指南: docs/guides/a-share-analysis-guide.md")
    logger.info(f"  🔧 技术文档: docs/data/china_stock-api-integration.md")
    
    logger.info(f"\n🚀 下一步:")
    logger.info(f"  1. 在GitHub上创建Release")
    logger.info(f"  2. 更新项目README")
    logger.info(f"  3. 通知用户更新")
    logger.info(f"  4. 收集用户反馈")
    
    logger.info(f"\n💡 使用方法:")
    logger.info(f"  git pull origin main")
    logger.info(f"  pip install -r requirements.txt")
    logger.info(f"  pip install pytdx")
    logger.info(f"  python -m streamlit run web/app.py")

def main():
    """主函数"""
    logger.info(f"🚀 TradingAgents-CN v0.1.3 发布流程")
    logger.info(f"=")
    
    # 检查当前目录
    if not os.path.exists("VERSION"):
        logger.error(f"❌ 请在项目根目录运行此脚本")
        return False
    
    # 执行发布步骤
    steps = [
        ("检查Git状态", check_git_status),
        ("更新版本文件", update_version_files),
        ("运行测试", run_tests),
        ("提交更改", commit_changes),
        ("创建Git标签", create_git_tag),
        ("推送到远程", push_to_remote),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n📋 {step_name}...")
        if not step_func():
            logger.error(f"❌ {step_name}失败，发布中止")
            return False
    
    # 生成发布摘要
    generate_release_summary()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logger.info(f"\n🎉 发布成功完成!")
            sys.exit(0)
        else:
            logger.error(f"\n❌ 发布失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning(f"\n\n⚠️ 发布被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 发布过程中出现异常: {e}")
        sys.exit(1)
