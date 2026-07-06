#!/usr/bin/env python3
"""
测试日志修复效果的脚本
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def test_logging_fix():
    """测试日志修复效果"""
    print("🔍 测试日志修复效果")
    print("=" * 60)
    
    try:
        # 初始化TradingAgents日志系统
        from tradingagents.utils.logging_init import init_logging, get_logger
        init_logging()
        
        # 获取日志器
        logger = get_logger('test')
        logger.info("🧪 测试日志系统初始化成功")
        
        # 导入TradingAgents
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = False  # 使用离线模式避免API调用
        config["llm_provider"] = "dashscope"
        config["debug"] = True  # 启用调试模式
        
        logger.info(f"✅ 配置创建成功")
        logger.info(f"   LLM提供商: {config['llm_provider']}")
        logger.info(f"   在线工具: {config['online_tools']}")
        logger.info(f"   调试模式: {config['debug']}")
        
        # 创建分析图
        graph = TradingAgentsGraph(
            selected_analysts=["market"],  # 只使用市场分析师进行快速测试
            debug=True,
            config=config
        )
        
        logger.info(f"✅ TradingAgentsGraph创建成功")
        
        # 测试市场分析师是否能正确记录日志
        print(f"\n🚀 开始测试市场分析师日志...")
        
        # 检查日志文件
        log_file = Path("logs/tradingagents.log")
        if log_file.exists():
            print(f"✅ 日志文件存在: {log_file}")
            
            # 读取最后几行日志
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 0:
                    print(f"📊 日志文件最后5行:")
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
                else:
                    print(f"⚠️ 日志文件为空")
        else:
            print(f"❌ 日志文件不存在: {log_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_logging_fix()
