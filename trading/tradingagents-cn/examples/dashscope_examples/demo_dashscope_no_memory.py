#!/usr/bin/env python3
"""
TradingAgents 演示脚本 - 使用阿里百炼大模型（禁用记忆功能）
这个脚本展示了如何使用阿里百炼大模型运行 TradingAgents 框架，临时禁用记忆功能
"""

import os
import sys
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 加载 .env 文件
load_dotenv()

def main():
    """主函数"""
    logger.info(f"🚀 TradingAgents 演示 - 阿里百炼版本（无记忆）")
    logger.info(f"=")
    
    # 检查API密钥
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    
    if not dashscope_key:
        logger.error(f"❌ 错误: 未找到 DASHSCOPE_API_KEY 环境变量")
        return
    
    if not finnhub_key:
        logger.error(f"❌ 错误: 未找到 FINNHUB_API_KEY 环境变量")
        return
    
    logger.info(f"✅ 阿里百炼 API 密钥: {dashscope_key[:10]}...")
    logger.info(f"✅ FinnHub API 密钥: {finnhub_key[:10]}...")
    print()
    
    # 创建阿里百炼配置
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "dashscope"
    config["deep_think_llm"] = "qwen-plus"      # 深度分析
    config["quick_think_llm"] = "qwen-turbo"    # 快速任务
    config["max_debate_rounds"] = 1             # 减少辩论轮次
    config["online_tools"] = False             # 暂时禁用在线工具
    config["use_memory"] = False               # 禁用记忆功能
    
    logger.info(f"📊 配置信息:")
    logger.info(f"  LLM 提供商: {config['llm_provider']}")
    logger.info(f"  深度思考模型: {config['deep_think_llm']} (通义千问Plus)")
    logger.info(f"  快速思考模型: {config['quick_think_llm']} (通义千问Turbo)")
    logger.info(f"  最大辩论轮次: {config['max_debate_rounds']}")
    logger.info(f"  在线工具: {config['online_tools']}")
    logger.info(f"  记忆功能: {config['use_memory']}")
    print()
    
    try:
        logger.info(f"🤖 正在初始化 TradingAgents...")
        
        # 临时修改记忆相关的环境变量，避免初始化错误
        original_openai_key = os.environ.get('OPENAI_API_KEY')
        if not original_openai_key:
            os.environ['OPENAI_API_KEY'] = 'dummy_key_for_initialization'
        
        ta = TradingAgentsGraph(debug=True, config=config)
        logger.info(f"✅ TradingAgents 初始化成功!")
        print()
        
        # 分析股票
        stock_symbol = "AAPL"  # 苹果公司
        analysis_date = "2024-05-10"
        
        logger.info(f"📈 开始分析股票: {stock_symbol}")
        logger.info(f"📅 分析日期: {analysis_date}")
        logger.info(f"⏳ 正在进行多智能体分析，请稍候...")
        logger.info(f"🧠 使用阿里百炼大模型进行智能分析...")
        logger.warning(f"⚠️  注意: 当前版本禁用了记忆功能以避免兼容性问题")
        print()
        
        # 执行分析
        state, decision = ta.propagate(stock_symbol, analysis_date)
        
        logger.info(f"🎯 分析结果:")
        logger.info(f"=")
        print(decision)
        logger.info(f"=")
        
        logger.info(f"✅ 分析完成!")
        print()
        logger.info(f"🌟 阿里百炼大模型特色:")
        logger.info(f"  - 中文理解能力强")
        logger.info(f"  - 金融领域知识丰富")
        logger.info(f"  - 推理能力出色")
        logger.info(f"  - 成本相对较低")
        print()
        logger.info(f"💡 提示:")
        logger.info(f"  - 当前版本为了兼容性暂时禁用了记忆功能")
        logger.info(f"  - 完整功能版本需要解决嵌入模型兼容性问题")
        logger.info(f"  - 您可以修改 stock_symbol 和 analysis_date 来分析其他股票")
        
    except Exception as e:
        logger.error(f"❌ 运行时错误: {str(e)}")
        print()
        # 显示详细的错误信息
        import traceback

        logger.error(f"🔍 详细错误信息:")
        traceback.print_exc()
        print()
        logger.info(f"🔧 可能的解决方案:")
        logger.info(f"1. 检查阿里百炼API密钥是否正确")
        logger.info(f"2. 确认已开通百炼服务并有足够额度")
        logger.info(f"3. 检查网络连接")
        logger.info(f"4. 尝试使用简化版本的演示脚本")

if __name__ == "__main__":
    main()
