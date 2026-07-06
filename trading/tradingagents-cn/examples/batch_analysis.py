#!/usr/bin/env python3
"""
批量股票分析脚本
一次性分析多只股票，生成对比报告
"""

import os
import sys
import time
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from tradingagents.llm_adapters import ChatDashScope
from langchain_core.messages import HumanMessage, SystemMessage


# 加载环境变量
load_dotenv()

def batch_stock_analysis():
    """批量分析股票"""
    
    # 🎯 在这里定义您要分析的股票组合
    stock_portfolio = {
        "科技股": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "AI芯片": ["NVDA", "AMD", "INTC"],
        "电动车": ["TSLA", "BYD", "NIO"],
        "ETF": ["SPY", "QQQ", "VTI"]
    }
    
    logger.info(f"🚀 TradingAgents-CN 批量股票分析")
    logger.info(f"=")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error(f"❌ 请设置 DASHSCOPE_API_KEY 环境变量")
        return
    
    try:
        # 初始化模型
        llm = ChatDashScope(
            model="qwen-turbo",  # 使用快速模型进行批量分析
            temperature=0.1,
            max_tokens=2000
        )
        
        all_results = {}
        
        for category, stocks in stock_portfolio.items():
            logger.info(f"\n📊 正在分析 {category} 板块...")
            category_results = {}
            
            for i, stock in enumerate(stocks, 1):
                logger.info(f"  [{i}/{len(stocks)}] 分析 {stock}...")
                
                # 简化的分析提示
                prompt = f"""
请对股票 {stock} 进行简要投资分析，包括：

1. 当前基本面状况（1-2句话）
2. 技术面趋势判断（1-2句话）
3. 主要机会和风险（各1-2句话）
4. 投资建议（买入/持有/卖出，目标价）

请保持简洁，用中文回答。
"""
                
                try:
                    response = llm.invoke([HumanMessage(content=prompt)])
                    category_results[stock] = response.content
                    logger.info(f"    ✅ {stock} 分析完成")
                    
                    # 添加延迟避免API限制
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"    ❌ {stock} 分析失败: {e}")
                    category_results[stock] = f"分析失败: {e}"
            
            all_results[category] = category_results
        
        # 生成汇总报告
        logger.info(f"\n📋 生成汇总报告...")
        generate_summary_report(all_results, llm)
        
    except Exception as e:
        logger.error(f"❌ 批量分析失败: {e}")

def generate_summary_report(results, llm):
    """生成汇总报告"""
    
    # 保存详细结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    detail_filename = f"batch_analysis_detail_{timestamp}.txt"
    
    with open(detail_filename, 'w', encoding='utf-8') as f:
        f.write("TradingAgents-CN 批量股票分析报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for category, stocks in results.items():
            f.write(f"\n{category} 板块分析\n")
            f.write("-" * 30 + "\n")
            
            for stock, analysis in stocks.items():
                f.write(f"\n【{stock}】\n")
                f.write(analysis + "\n")
    
    logger.info(f"✅ 详细报告已保存到: {detail_filename}")
    
    # 生成投资组合建议
    try:
        portfolio_prompt = f"""
基于以下股票分析结果，请提供投资组合建议：

{format_results_for_summary(results)}

请提供：
1. 推荐的投资组合配置（各板块权重）
2. 重点推荐的3-5只股票及理由
3. 需要规避的风险股票
4. 整体市场观点和策略建议

请用中文回答，保持专业和客观。
"""
        
        logger.info(f"⏳ 正在生成投资组合建议...")
        portfolio_response = llm.invoke([HumanMessage(content=portfolio_prompt)])
        
        # 保存投资组合建议
        summary_filename = f"portfolio_recommendation_{timestamp}.txt"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("投资组合建议报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(portfolio_response.content)
        
        logger.info(f"✅ 投资组合建议已保存到: {summary_filename}")
        
        # 显示简要建议
        logger.info(f"\n🎯 投资组合建议摘要:")
        logger.info(f"=")
        print(portfolio_response.content[:500] + "...")
        logger.info(f"=")
        
    except Exception as e:
        logger.error(f"❌ 生成投资组合建议失败: {e}")

def format_results_for_summary(results):
    """格式化结果用于汇总分析"""
    formatted = ""
    for category, stocks in results.items():
        formatted += f"\n{category}:\n"
        for stock, analysis in stocks.items():
            # 提取关键信息
            formatted += f"- {stock}: {analysis[:100]}...\n"
    return formatted

if __name__ == "__main__":
    batch_stock_analysis()
