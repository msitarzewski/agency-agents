#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一新闻工具集成效果
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek

def test_unified_news_tool():
    """测试统一新闻工具的集成效果"""
    
    print("🚀 开始测试统一新闻工具集成...")
    
    # 测试股票列表 - 包含A股、港股、美股
    test_stocks = [
        ("000001", "平安银行 - A股"),
        ("00700", "腾讯控股 - 港股"), 
        ("AAPL", "苹果公司 - 美股")
    ]
    
    try:
        # 初始化工具包
        print("📦 初始化工具包...")
        from tradingagents.default_config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config=config)
        
        # 创建LLM实例（使用DeepSeek）
        print("🤖 创建LLM实例...")
        llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1
        )
        
        # 创建新闻分析师
        print("📰 创建新闻分析师...")
        news_analyst = create_news_analyst(llm, toolkit)
        
        # 测试每个股票
        for stock_code, description in test_stocks:
            print(f"\n{'='*60}")
            print(f"🔍 测试股票: {stock_code} ({description})")
            print(f"{'='*60}")
            
            try:
                # 调用新闻分析师
                result = news_analyst({
                    "messages": [],
                    "company_of_interest": stock_code,
                    "trade_date": "2025-07-28",
                    "session_id": f"test_{stock_code}"
                })
                
                # 检查结果
                if result and "messages" in result and len(result["messages"]) > 0:
                    final_message = result["messages"][-1]
                    if hasattr(final_message, 'content'):
                        report = final_message.content
                        print(f"✅ 成功获取新闻分析报告")
                        print(f"📊 报告长度: {len(report)} 字符")
                        
                        # 显示报告摘要
                        if len(report) > 200:
                            print(f"📝 报告摘要: {report[:200]}...")
                        else:
                            print(f"📝 完整报告: {report}")
                            
                        # 检查是否包含真实新闻特征
                        news_indicators = ['发布时间', '新闻标题', '文章来源', '东方财富', '财联社', '证券时报']
                        has_real_news = any(indicator in report for indicator in news_indicators)
                        print(f"🔍 包含真实新闻特征: {'是' if has_real_news else '否'}")
                    else:
                        print("❌ 消息内容为空")
                else:
                    print("❌ 未获取到新闻分析报告")
                    
            except Exception as e:
                print(f"❌ 测试股票 {stock_code} 时出错: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"\n{'='*60}")
        print("🎉 统一新闻工具测试完成!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unified_news_tool()