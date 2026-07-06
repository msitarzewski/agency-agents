#!/usr/bin/env python3
"""
简单股票分析演示
展示如何快速使用TradingAgents-CN进行投资分析
"""

import os
import sys
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def quick_analysis_demo():
    """快速分析演示"""
    
    logger.info(f"🚀 TradingAgents-CN 快速投资分析演示")
    logger.info(f"=")
    
    # 检查环境
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error(f"❌ 请先设置 DASHSCOPE_API_KEY 环境变量")
        logger.info(f"💡 在 .env 文件中添加: DASHSCOPE_API_KEY=your_api_key")
        return
    
    logger.info(f"✅ 环境检查通过")
    
    # 演示不同类型的分析
    analysis_examples = {
        "技术面分析": {
            "description": "分析价格趋势、技术指标、支撑阻力位",
            "suitable_for": "短期交易者、技术分析爱好者",
            "example_stocks": ["AAPL", "TSLA", "NVDA"]
        },
        "基本面分析": {
            "description": "分析财务状况、业务模式、竞争优势",
            "suitable_for": "长期投资者、价值投资者",
            "example_stocks": ["MSFT", "GOOGL", "BRK.B"]
        },
        "风险评估": {
            "description": "识别各类风险因素，制定风险控制策略",
            "suitable_for": "风险管理、投资组合管理",
            "example_stocks": ["SPY", "QQQ", "VTI"]
        },
        "行业比较": {
            "description": "对比同行业公司的相对优势",
            "suitable_for": "行业研究、选股决策",
            "example_stocks": ["AAPL vs MSFT", "TSLA vs F", "AMZN vs WMT"]
        }
    }
    
    logger.info(f"\n📊 支持的分析类型:")
    for i, (analysis_type, info) in enumerate(analysis_examples.items(), 1):
        logger.info(f"\n{i}. {analysis_type}")
        logger.info(f"   📝 描述: {info['description']}")
        logger.info(f"   👥 适合: {info['suitable_for']}")
        logger.info(f"   📈 示例: {', '.join(info['example_stocks'])}")
    
    logger.info(f"\n")
    logger.info(f"🎯 使用方法:")
    logger.info(f"\n1. 预设示例分析:")
    logger.info(f"   python examples/dashscope/demo_dashscope_chinese.py")
    logger.info(f"   python examples/dashscope/demo_dashscope_simple.py")
    
    logger.info(f"\n2. 交互式CLI工具:")
    logger.info(f"   python -m cli.main analyze")
    
    logger.info(f"\n3. 自定义分析脚本:")
    logger.info(f"   修改示例程序中的股票代码和分析参数")
    
    logger.info(f"\n")
    logger.info(f"💡 实用技巧:")
    
    tips = [
        "选择qwen-plus模型平衡性能和成本",
        "使用qwen-max获得最高质量的分析",
        "分析前先查看最新的财报和新闻",
        "结合多个时间框架进行分析",
        "设置合理的止损和目标价位",
        "定期回顾和调整投资策略"
    ]
    
    for i, tip in enumerate(tips, 1):
        logger.info(f"{i}. {tip}")
    
    logger.info(f"\n")
    logger.warning(f"⚠️ 重要提醒:")
    logger.info(f"• 分析结果仅供参考，不构成投资建议")
    logger.info(f"• 投资有风险，决策需谨慎")
    logger.info(f"• 建议结合多方信息进行验证")
    logger.info(f"• 重大投资决策请咨询专业财务顾问")

def show_analysis_workflow():
    """展示分析工作流程"""
    
    logger.info(f"\n🔄 投资分析工作流程:")
    logger.info(f"=")
    
    workflow_steps = [
        {
            "step": "1. 选择分析目标",
            "details": [
                "确定要分析的股票代码",
                "明确分析目的（短期交易 vs 长期投资）",
                "选择分析重点（技术面 vs 基本面）"
            ]
        },
        {
            "step": "2. 收集基础信息", 
            "details": [
                "查看最新股价和成交量",
                "了解最近的重要新闻和公告",
                "检查财报发布时间和业绩预期"
            ]
        },
        {
            "step": "3. 运行AI分析",
            "details": [
                "选择合适的分析程序",
                "配置分析参数",
                "等待AI生成分析报告"
            ]
        },
        {
            "step": "4. 验证和补充",
            "details": [
                "对比其他分析师观点",
                "查证关键数据和事实",
                "补充最新市场信息"
            ]
        },
        {
            "step": "5. 制定投资策略",
            "details": [
                "确定买入/卖出时机",
                "设置目标价位和止损点",
                "规划仓位管理策略"
            ]
        },
        {
            "step": "6. 执行和监控",
            "details": [
                "按计划执行交易",
                "定期监控投资表现",
                "根据市场变化调整策略"
            ]
        }
    ]
    
    for workflow in workflow_steps:
        logger.info(f"\n📋 {workflow['step']}")
        for detail in workflow['details']:
            logger.info(f"   • {detail}")

def show_model_comparison():
    """展示不同模型的特点"""
    
    logger.info(f"\n🧠 阿里百炼模型对比:")
    logger.info(f"=")
    
    models = {
        "qwen-turbo": {
            "特点": "响应速度快，成本低",
            "适用场景": "快速查询，批量分析",
            "分析质量": "⭐⭐⭐",
            "响应速度": "⭐⭐⭐⭐⭐",
            "成本效益": "⭐⭐⭐⭐⭐"
        },
        "qwen-plus": {
            "特点": "平衡性能和成本，推荐日常使用",
            "适用场景": "日常分析，投资决策",
            "分析质量": "⭐⭐⭐⭐",
            "响应速度": "⭐⭐⭐⭐",
            "成本效益": "⭐⭐⭐⭐"
        },
        "qwen-max": {
            "特点": "最高质量，深度分析",
            "适用场景": "重要决策，深度研究",
            "分析质量": "⭐⭐⭐⭐⭐",
            "响应速度": "⭐⭐⭐",
            "成本效益": "⭐⭐⭐"
        }
    }
    
    for model, info in models.items():
        logger.info(f"\n🤖 {model}")
        for key, value in info.items():
            logger.info(f"   {key}: {value}")

def main():
    """主函数"""
    
    # 加载环境变量
    from dotenv import load_dotenv

    load_dotenv()
    
    quick_analysis_demo()
    show_analysis_workflow()
    show_model_comparison()
    
    logger.info(f"\n")
    logger.info(f"🚀 开始您的投资分析之旅!")
    logger.info(f"💡 建议从简单示例开始: python examples/dashscope/demo_dashscope_simple.py")

if __name__ == "__main__":
    main()
