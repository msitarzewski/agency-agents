#!/usr/bin/env python3
"""
Token使用统计和成本跟踪演示

本演示展示如何使用TradingAgents的Token统计功能：
1. 自动记录LLM调用的token使用量
2. 计算使用成本
3. 查看统计信息
4. MongoDB存储支持
"""

import os
import sys
import time
from datetime import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# 确保使用正确的dashscope模块
if 'dashscope' in sys.modules:
    del sys.modules['dashscope']

from tradingagents.llm_adapters.dashscope_adapter import ChatDashScope
from tradingagents.config.config_manager import config_manager, token_tracker
from langchain_core.messages import HumanMessage, SystemMessage



def print_separator(title=""):
    """打印分隔线"""
    logger.info(f"\n")
    if title:
        logger.info(f" {title} ")
        logger.info(f"=")


def display_config_status():
    """显示配置状态"""
    print_separator("配置状态")
    
    # 检查环境配置
    env_status = config_manager.get_env_config_status()
    logger.info(f"📋 环境配置:")
    logger.info(f"   ✅ .env文件存在: {env_status['env_file_exists']}")
    logger.info(f"   ✅ DashScope API: {'已配置' if env_status['api_keys']['dashscope'] else '未配置'}")
    
    # 检查MongoDB配置
    use_mongodb = os.getenv("USE_MONGODB_STORAGE", "false").lower() == "true"
    logger.info(f"   📦 MongoDB存储: {'启用' if use_mongodb else '未启用（使用JSON文件）'}")
    
    if use_mongodb:
        if config_manager.mongodb_storage and config_manager.mongodb_storage.is_connected():
            logger.info(f"   ✅ MongoDB连接: 正常")
        else:
            logger.error(f"   ❌ MongoDB连接: 失败")
    
    # 显示成本跟踪设置
    settings = config_manager.load_settings()
    cost_tracking = settings.get("enable_cost_tracking", True)
    cost_threshold = settings.get("cost_alert_threshold", 100.0)
    
    logger.info(f"   💰 成本跟踪: {'启用' if cost_tracking else '禁用'}")
    logger.warning(f"   ⚠️ 成本警告阈值: ¥{cost_threshold}")


def display_current_statistics():
    """显示当前统计信息"""
    print_separator("当前使用统计")
    
    # 获取不同时间段的统计
    periods = [(1, "今日"), (7, "本周"), (30, "本月")]
    
    for days, period_name in periods:
        stats = config_manager.get_usage_statistics(days)
        logger.info(f"📊 {period_name}统计:")
        logger.info(f"   💰 总成本: ¥{stats['total_cost']:.4f}")
        logger.info(f"   📞 总请求: {stats['total_requests']}")
        logger.info(f"   📥 输入tokens: {stats['total_input_tokens']:,}")
        logger.info(f"   📤 输出tokens: {stats['total_output_tokens']:,}")
        
        # 显示供应商统计
        provider_stats = stats.get('provider_stats', {})
        if provider_stats:
            logger.info(f"   📈 供应商统计:")
            for provider, pstats in provider_stats.items():
                logger.info(f"      {provider}: ¥{pstats['cost']:.4f} ({pstats['requests']}次请求)")
        print()


def demo_basic_usage():
    """演示基本使用"""
    print_separator("基本使用演示")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error(f"❌ 未找到DASHSCOPE_API_KEY")
        logger.info(f"请在.env文件中配置DashScope API密钥")
        return False
    
    try:
        # 初始化LLM
        logger.info(f"🤖 初始化DashScope LLM...")
        llm = ChatDashScope(
            model="qwen-turbo",
            api_key=api_key,
            temperature=0.7,
            max_tokens=200
        )
        
        # 生成唯一会话ID
        session_id = f"demo_session_{int(time.time())}"
        logger.info(f"📝 会话ID: {session_id}")
        
        # 测试消息
        messages = [
            SystemMessage(content="你是一个专业的股票分析师，请提供简洁准确的分析。"),
            HumanMessage(content="请简单分析一下当前A股市场的整体趋势，不超过150字。")
        ]
        
        logger.info(f"🚀 发送分析请求...")
        
        # 调用LLM（自动记录token使用）
        response = llm.invoke(
            messages,
            session_id=session_id,
            analysis_type="market_analysis"
        )
        
        logger.info(f"✅ 收到分析结果:")
        logger.info(f"   {response.content}")
        
        # 等待记录保存
        time.sleep(0.5)
        
        # 查看会话成本
        session_cost = token_tracker.get_session_cost(session_id)
        logger.info(f"💰 本次分析成本: ¥{session_cost:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        return False


def demo_cost_estimation():
    """演示成本估算"""
    print_separator("成本估算演示")
    
    logger.info(f"💡 成本估算功能可以帮助您预算LLM使用成本")
    
    # 不同场景的估算
    scenarios = [
        ("简单查询", "qwen-turbo", 100, 50),
        ("详细分析", "qwen-turbo", 500, 300),
        ("深度研究", "qwen-plus-latest", 1000, 800),
        ("复杂报告", "qwen-plus-latest", 2000, 1500)
    ]
    
    logger.info(f"📊 不同使用场景的成本估算:")
    for scenario, model, input_tokens, output_tokens in scenarios:
        cost = token_tracker.estimate_cost(
            provider="dashscope",
            model_name=model,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens
        )
        logger.info(f"   {scenario:8} ({model:15}): ¥{cost:.4f} ({input_tokens:4}+{output_tokens:4} tokens)")


def demo_mongodb_features():
    """演示MongoDB功能"""
    print_separator("MongoDB存储功能")
    
    if not config_manager.mongodb_storage:
        logger.info(f"ℹ️ MongoDB存储未启用")
        logger.info(f"要启用MongoDB存储，请:")
        logger.info(f"   1. 安装pymongo: pip install pymongo")
        logger.info(f"   2. 在.env文件中设置: USE_MONGODB_STORAGE=true")
        logger.info(f"   3. 配置MongoDB连接字符串")
        return
    
    if not config_manager.mongodb_storage.is_connected():
        logger.error(f"❌ MongoDB连接失败")
        return
    
    logger.info(f"✅ MongoDB存储功能演示")
    
    try:
        # 获取MongoDB统计
        stats = config_manager.mongodb_storage.get_usage_statistics(30)
        logger.info(f"📊 MongoDB统计 (最近30天):")
        logger.info(f"   💰 总成本: ¥{stats.get('total_cost', 0):.4f}")
        logger.info(f"   📞 总请求: {stats.get('total_requests', 0)}")
        
        # 获取供应商统计
        provider_stats = config_manager.mongodb_storage.get_provider_statistics(30)
        if provider_stats:
            logger.info(f"   📈 供应商统计:")
            for provider, pstats in provider_stats.items():
                logger.info(f"      {provider}: ¥{pstats['cost']:.4f}")
        
        # 演示清理功能
        logger.info(f"\n🧹 数据清理功能:")
        logger.info(f"   MongoDB支持自动清理旧记录以节省存储空间")
        
        # 清理超过90天的记录（演示用）
        # deleted_count = config_manager.mongodb_storage.cleanup_old_records(90)
        # print(f"   清理了 {deleted_count} 条超过90天的记录")
        
    except Exception as e:
        logger.error(f"❌ MongoDB功能演示失败: {e}")


def display_pricing_info():
    """显示定价信息"""
    print_separator("定价信息")
    
    pricing_configs = config_manager.load_pricing()
    
    logger.info(f"💰 当前定价配置:")
    
    # 按供应商分组显示
    providers = {}
    for pricing in pricing_configs:
        if pricing.provider not in providers:
            providers[pricing.provider] = []
        providers[pricing.provider].append(pricing)
    
    for provider, models in providers.items():
        logger.info(f"\n📦 {provider.upper()}:")
        for model in models:
            logger.info(f"   {model.model_name:20} | 输入: ¥{model.input_price_per_1k:.4f}/1K | 输出: ¥{model.output_price_per_1k:.4f}/1K")


def main():
    """主演示函数"""
    logger.info(f"🎯 TradingAgents Token使用统计和成本跟踪演示")
    logger.info(f"本演示将展示完整的Token统计和成本跟踪功能")
    
    # 1. 显示配置状态
    display_config_status()
    
    # 2. 显示当前统计
    display_current_statistics()
    
    # 3. 显示定价信息
    display_pricing_info()
    
    # 4. 演示基本使用
    if demo_basic_usage():
        logger.info(f"\n⏳ 等待统计更新...")
        time.sleep(1)
        
        # 显示更新后的统计
        print_separator("更新后的统计")
        stats = config_manager.get_usage_statistics(1)
        logger.info(f"📊 今日最新统计:")
        logger.info(f"   💰 总成本: ¥{stats['total_cost']:.4f}")
        logger.info(f"   📞 总请求: {stats['total_requests']}")
    
    # 5. 演示成本估算
    demo_cost_estimation()
    
    # 6. 演示MongoDB功能
    demo_mongodb_features()
    
    print_separator("演示完成")
    logger.info(f"🎉 Token统计和成本跟踪功能演示完成！")
    logger.info(f"\n📚 更多信息请参考:")
    logger.info(f"   - 文档: docs/configuration/token-tracking-guide.md")
    logger.info(f"   - 测试: tests/test_dashscope_token_tracking.py")
    logger.info(f"   - 配置示例: .env.example")


if __name__ == "__main__":
    main()