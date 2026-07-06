#!/usr/bin/env python3
"""
测试LLM工具调用问题的详细脚本
专门分析为什么LLM声称调用了工具但实际没有执行
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'test_tool_call_issue.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_tool_call_mechanism():
    """测试工具调用机制"""
    logger.info("=" * 60)
    logger.info("开始测试LLM工具调用机制问题")
    logger.info("=" * 60)
    
    try:
        # 1. 导入必要模块
        logger.info("1. 导入模块...")
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.utils.realtime_news_utils import get_realtime_stock_news
        from langchain_core.messages import HumanMessage
        from langchain_core.tools import tool
        os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
        
        # 2. 创建LLM实例
        logger.info("2. 创建LLM实例...")
        llm = ChatDashScopeOpenAI(
            model="qwen-plus-latest",
            temperature=0.1,
            max_tokens=1000
        )
        logger.info(f"   LLM类型: {llm.__class__.__name__}")
        
        # 3. 创建Toolkit
        logger.info("3. 创建Toolkit...")
        toolkit = Toolkit()
        logger.info(f"   Toolkit创建成功")
        
        # 4. 获取工具
        logger.info("4. 获取工具...")
        realtime_news_tool = toolkit.get_realtime_stock_news
        logger.info(f"   工具名称: {realtime_news_tool.name}")
        logger.info(f"   工具描述: {realtime_news_tool.description}")
        
        # 5. 绑定工具到LLM
        logger.info("5. 绑定工具到LLM...")
        llm_with_tools = llm.bind_tools([realtime_news_tool])
        logger.info(f"   工具绑定完成")
        
        # 6. 测试工具调用
        logger.info("6. 测试工具调用...")
        test_message = HumanMessage(
            content="请调用get_realtime_stock_news工具获取000001.SZ的最新新闻"
        )
        
        logger.info("   开始LLM调用...")
        result = llm_with_tools.invoke([test_message])
        logger.info("   LLM调用完成")
        
        # 7. 分析结果
        logger.info("7. 分析结果...")
        logger.info(f"   结果类型: {type(result)}")
        logger.info(f"   是否有tool_calls属性: {hasattr(result, 'tool_calls')}")
        
        if hasattr(result, 'tool_calls'):
            tool_calls = result.tool_calls
            logger.info(f"   工具调用数量: {len(tool_calls)}")
            
            if len(tool_calls) > 0:
                logger.info("   工具调用详情:")
                for i, call in enumerate(tool_calls):
                    logger.info(f"     调用 {i+1}:")
                    logger.info(f"       类型: {type(call)}")
                    if hasattr(call, 'name'):
                        logger.info(f"       名称: {call.name}")
                    if hasattr(call, 'args'):
                        logger.info(f"       参数: {call.args}")
                    if isinstance(call, dict):
                        logger.info(f"       字典内容: {call}")
                        
                # 8. 尝试手动执行工具调用
                logger.info("8. 尝试手动执行工具调用...")
                for i, call in enumerate(tool_calls):
                    try:
                        logger.info(f"   执行工具调用 {i+1}...")
                        
                        # 获取参数
                        if hasattr(call, 'args'):
                            args = call.args
                        elif isinstance(call, dict) and 'args' in call:
                            args = call['args']
                        else:
                            logger.error(f"     无法获取参数: {call}")
                            continue
                            
                        logger.info(f"     参数: {args}")
                        
                        # 执行工具
                        if 'ticker' in args:
                            ticker = args['ticker']
                            logger.info(f"     调用 get_realtime_stock_news(ticker='{ticker}')")
                            
                            # 直接调用函数
                            news_result = get_realtime_stock_news(ticker)
                            logger.info(f"     函数调用成功，结果长度: {len(news_result)} 字符")
                            logger.info(f"     结果前100字符: {news_result[:100]}...")
                            
                        else:
                            logger.error(f"     参数中缺少ticker: {args}")
                            
                    except Exception as e:
                        logger.error(f"     工具执行失败: {e}")
                        import traceback
                        logger.error(f"     错误详情: {traceback.format_exc()}")
            else:
                logger.warning("   LLM没有调用任何工具")
        else:
            logger.warning("   结果没有tool_calls属性")
            
        # 9. 检查响应内容
        logger.info("9. 检查响应内容...")
        if hasattr(result, 'content'):
            content = result.content
            logger.info(f"   响应内容长度: {len(content)} 字符")
            logger.info(f"   响应内容前200字符: {content[:200]}...")
        else:
            logger.warning("   结果没有content属性")
            
        logger.info("=" * 60)
        logger.info("测试完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_tool_call_mechanism()