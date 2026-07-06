"""
测试Google工具处理器的改进
"""
import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler
from tradingagents.agents.utils.agent_utils import Toolkit
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

# 配置日志
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('data', 'logs', f"google_tool_handler_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    ]
)
logger = logging.getLogger("test_google_tool_handler")

def test_google_tool_handler_improvements():
    """测试Google工具处理器的改进"""
    logger.info("开始测试Google工具处理器的改进...")
    
    # 创建Google模型
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.1)
    
    # 创建工具集
    tools = [Toolkit.get_stock_market_data_unified]
    
    # 测试场景1: 检查是否为Google模型
    logger.info("测试场景1: 检查是否为Google模型")
    try:
        is_google = GoogleToolCallHandler.is_google_model(llm)
        logger.info(f"场景1结果: 是否为Google模型: {is_google}")
    except Exception as e:
        logger.error(f"场景1异常: {e}")
    
    # 测试场景2: 模拟空工具调用的AIMessage
    logger.info("测试场景2: 模拟空工具调用的AIMessage")
    try:
        # 创建一个没有工具调用的AIMessage
        ai_message = AIMessage(content="我需要获取股票数据来进行分析")
        
        state = {
            "messages": [HumanMessage(content="请分析贵州茅台(600519)的市场情况")],
            "trade_date": "2023-12-31",
            "company_of_interest": "贵州茅台",
            "ticker": "600519"
        }
        
        result, messages = GoogleToolCallHandler.handle_google_tool_calls(
            result=ai_message,
            llm=llm,
            tools=tools,
            state=state,
            analysis_prompt_template="请基于以上数据生成详细的市场分析报告",
            analyst_name="市场分析师"
        )
        logger.info(f"场景2结果: {result[:100]}...")
    except Exception as e:
        logger.error(f"场景2异常: {e}")
    
    # 测试场景3: 模拟有工具调用的AIMessage
    logger.info("测试场景3: 模拟有工具调用的AIMessage")
    try:
        # 创建一个有工具调用的AIMessage
        ai_message = AIMessage(
            content="我需要获取股票数据",
            tool_calls=[{
                'id': 'test_tool_call_1',
                'name': 'get_stock_market_data_unified',
                'args': {
                    'ticker': '600519',
                    'start_date': '2023-01-01',
                    'end_date': '2023-12-31'
                }
            }]
        )
        
        state = {
            "messages": [HumanMessage(content="请分析贵州茅台(600519)的市场情况")],
            "trade_date": "2023-12-31",
            "company_of_interest": "贵州茅台",
            "ticker": "600519"
        }
        
        result, messages = GoogleToolCallHandler.handle_google_tool_calls(
            result=ai_message,
            llm=llm,
            tools=tools,
            state=state,
            analysis_prompt_template="请基于以上数据生成详细的市场分析报告",
            analyst_name="市场分析师"
        )
        logger.info(f"场景3结果: {result[:100]}...")
    except Exception as e:
        logger.error(f"场景3异常: {e}")
    
    logger.info("Google工具处理器改进测试完成")

if __name__ == "__main__":
    test_google_tool_handler_improvements()