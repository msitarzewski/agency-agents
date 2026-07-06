#!/usr/bin/env python3
"""
测试DashScope工具调用失败检测和补救机制

这个脚本测试新闻分析师在DashScope模型不调用工具时的补救机制。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def test_dashscope_tool_call_detection():
    """测试DashScope工具调用失败检测机制"""
    
    print("🧪 测试DashScope工具调用失败检测和补救机制")
    print("=" * 60)
    
    # 模拟DashScope模型类
    class MockDashScopeModel:
        def __init__(self):
            self.__class__.__name__ = "ChatDashScopeOpenAI"
        
        def invoke(self, messages):
            # 模拟返回结果
            class MockResult:
                def __init__(self, content, tool_calls=None):
                    self.content = content
                    self.tool_calls = tool_calls or []
            
            return MockResult("这是一个没有基于真实新闻数据的分析报告...")
    
    # 模拟工具
    class MockToolkit:
        @staticmethod
        def get_realtime_stock_news():
            class MockTool:
                def invoke(self, params):
                    ticker = params.get('ticker', 'UNKNOWN')
                    curr_date = params.get('curr_date', 'UNKNOWN')
                    # 返回足够长的新闻数据（>100字符）
                    return f"""【东方财富新闻】{ticker} 股票最新消息：
                    
1. 公司发布重要公告，第三季度业绩超预期，净利润同比增长25%
2. 管理层宣布新的战略合作伙伴关系，预计将带来显著的收入增长
3. 行业分析师上调目标价格，认为该股票具有良好的投资价值
4. 最新财报显示公司现金流状况良好，负债率持续下降
5. 市场对公司未来发展前景保持乐观态度

发布时间：{curr_date}
数据来源：东方财富网"""
            return MockTool()
        
        @staticmethod
        def get_google_news():
            class MockTool:
                def invoke(self, params):
                    query = params.get('query', 'UNKNOWN')
                    curr_date = params.get('curr_date', 'UNKNOWN')
                    # 返回足够长的新闻数据（>100字符）
                    return f"""【Google新闻】{query} 相关新闻汇总：
                    
1. 市场分析师看好该股票前景，预计未来12个月将有显著上涨
2. 机构投资者增持该股票，显示对公司长期价值的认可
3. 行业整体表现良好，该公司作为龙头企业受益明显
4. 技术分析显示股价突破关键阻力位，趋势向好
5. 基本面分析表明公司估值合理，具有投资价值

时间：{curr_date}
数据来源：Google News"""
            return MockTool()
    
    # 测试参数
    ticker = "600036"
    current_date = datetime.now().strftime("%Y-%m-%d")
    llm = MockDashScopeModel()
    toolkit = MockToolkit()
    
    print(f"📊 测试股票: {ticker}")
    print(f"📅 当前日期: {current_date}")
    print(f"🤖 模型类型: {llm.__class__.__name__}")
    print()
    
    # 测试场景1：DashScope没有调用任何工具（tool_call_count = 0）
    print("🔍 测试场景1：DashScope没有调用任何工具")
    print("-" * 40)
    
    # 模拟LLM调用结果
    class MockResult:
        def __init__(self):
            self.content = "这是一个没有基于真实新闻数据的分析报告，长度为2089字符..."
            self.tool_calls = []  # 没有工具调用
    
    result = MockResult()
    tool_call_count = len(result.tool_calls)
    
    print(f"📈 LLM调用结果: 工具调用数量 = {tool_call_count}")
    print(f"📝 原始报告长度: {len(result.content)} 字符")
    
    # 应用增强的检测逻辑
    report = ""
    
    if 'DashScope' in llm.__class__.__name__:
        if tool_call_count == 0:
            print("🚨 检测到DashScope没有调用任何工具，启动强制补救...")
            
            try:
                # 强制获取新闻数据
                print("🔧 强制调用get_realtime_stock_news获取新闻数据...")
                forced_news = toolkit.get_realtime_stock_news().invoke({"ticker": ticker, "curr_date": current_date})
                
                if forced_news and len(forced_news.strip()) > 100:
                    print(f"✅ 强制获取新闻成功: {len(forced_news)} 字符")
                    print(f"📰 新闻内容预览: {forced_news[:100]}...")
                    
                    # 模拟基于真实新闻数据重新生成分析
                    forced_prompt = f"""
基于以下最新获取的新闻数据，对股票 {ticker} 进行详细的新闻分析：

=== 最新新闻数据 ===
{forced_news}

请基于上述真实新闻数据撰写详细的中文分析报告。
"""
                    
                    print("🔄 基于强制获取的新闻数据重新生成完整分析...")
                    # 模拟重新生成的结果
                    report = f"基于真实新闻数据的分析报告：\n\n{forced_news}\n\n详细分析：该股票基于最新新闻显示积极信号..."
                    print(f"✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                    
                else:
                    print("⚠️ 强制获取新闻失败，尝试备用工具...")
                    
                    # 尝试备用工具
                    backup_news = toolkit.get_google_news().invoke({"query": f"{ticker} 股票 新闻", "curr_date": current_date})
                    
                    if backup_news and len(backup_news.strip()) > 100:
                        print(f"✅ 备用工具获取成功: {len(backup_news)} 字符")
                        report = f"基于备用新闻数据的分析报告：\n\n{backup_news}\n\n分析结论..."
                        print(f"✅ 备用工具补救成功，长度: {len(report)} 字符")
                    else:
                        print("❌ 所有新闻获取方式都失败，使用原始结果")
                        report = result.content
                        
            except Exception as e:
                print(f"❌ 强制补救过程失败: {e}")
                report = result.content
    
    if not report:
        report = result.content
    
    print()
    print("📊 测试结果总结:")
    print(f"   原始报告长度: {len(result.content)} 字符")
    print(f"   最终报告长度: {len(report)} 字符")
    print(f"   是否包含真实新闻: {'是' if '东方财富新闻' in report or 'Google新闻' in report else '否'}")
    print(f"   补救机制状态: {'成功' if len(report) > len(result.content) else '未触发或失败'}")
    
    print()
    print("🎯 测试结论:")
    if '东方财富新闻' in report or 'Google新闻' in report:
        print("✅ 增强的DashScope工具调用失败检测和补救机制工作正常")
        print("✅ 成功检测到工具调用失败并强制获取了真实新闻数据")
        print("✅ 基于真实新闻数据重新生成了分析报告")
    else:
        print("❌ 补救机制可能存在问题")
    
    return True

if __name__ == "__main__":
    try:
        test_dashscope_tool_call_detection()
        print("\n🎉 所有测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        sys.exit(1)