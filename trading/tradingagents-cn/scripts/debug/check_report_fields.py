"""
检查分析报告的字段数量和内容
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from app.core.config import settings

async def check_report_fields():
    """检查报告字段"""
    # 使用配置中的 MongoDB URI
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 获取最新的一条报告
    doc = await db.analysis_reports.find_one(
        {},
        sort=[("created_at", -1)]
    )
    
    if not doc:
        print("❌ 没有找到任何报告")
        return
    
    print(f"\n📊 最新报告信息:")
    print(f"  - analysis_id: {doc.get('analysis_id', 'N/A')}")
    print(f"  - stock_symbol: {doc.get('stock_symbol', 'N/A')}")
    print(f"  - stock_name: {doc.get('stock_name', 'N/A')}")
    print(f"  - analysis_date: {doc.get('analysis_date', 'N/A')}")
    print(f"  - research_depth: {doc.get('research_depth', 'N/A')}")
    print(f"  - source: {doc.get('source', 'N/A')}")
    
    reports = doc.get("reports", {})
    print(f"\n📋 reports 字段 (共 {len(reports)} 个):")
    
    # 按照预期的13个报告顺序显示
    expected_fields = [
        # 分析师团队 (4个)
        ('market_report', '📈 市场技术分析'),
        ('sentiment_report', '💭 市场情绪分析'),
        ('news_report', '📰 新闻事件分析'),
        ('fundamentals_report', '💰 基本面分析'),
        
        # 研究团队 (3个)
        ('bull_researcher', '🐂 多头研究员'),
        ('bear_researcher', '🐻 空头研究员'),
        ('research_team_decision', '🔬 研究经理决策'),
        
        # 交易团队 (1个)
        ('trader_investment_plan', '💼 交易员计划'),
        
        # 风险管理团队 (4个)
        ('risky_analyst', '⚡ 激进分析师'),
        ('safe_analyst', '🛡️ 保守分析师'),
        ('neutral_analyst', '⚖️ 中性分析师'),
        ('risk_management_decision', '👔 投资组合经理'),
        
        # 最终决策 (1个)
        ('final_trade_decision', '🎯 最终交易决策'),
    ]
    
    print("\n预期的13个字段:")
    for field_key, field_name in expected_fields:
        if field_key in reports:
            content = reports[field_key]
            if isinstance(content, str):
                print(f"  ✅ {field_name} ({field_key}): {len(content)} 字符")
            else:
                print(f"  ⚠️ {field_name} ({field_key}): {type(content).__name__}")
        else:
            print(f"  ❌ {field_name} ({field_key}): 缺失")
    
    print("\n实际存在的字段:")
    for key in reports.keys():
        content = reports[key]
        if isinstance(content, str):
            print(f"  - {key}: {len(content)} 字符")
        else:
            print(f"  - {key}: {type(content).__name__}")
    
    # 检查是否有 investment_debate_state 和 risk_debate_state
    print(f"\n🔍 检查辩论状态字段:")
    if 'investment_debate_state' in doc:
        print(f"  ✅ investment_debate_state 存在")
        debate_state = doc['investment_debate_state']
        if isinstance(debate_state, dict):
            print(f"     - bull_history: {len(debate_state.get('bull_history', []))} 条")
            print(f"     - bear_history: {len(debate_state.get('bear_history', []))} 条")
            print(f"     - judge_decision: {len(str(debate_state.get('judge_decision', '')))} 字符")
    else:
        print(f"  ❌ investment_debate_state 不存在")
    
    if 'risk_debate_state' in doc:
        print(f"  ✅ risk_debate_state 存在")
        risk_state = doc['risk_debate_state']
        if isinstance(risk_state, dict):
            print(f"     - risky_history: {len(risk_state.get('risky_history', []))} 条")
            print(f"     - safe_history: {len(risk_state.get('safe_history', []))} 条")
            print(f"     - neutral_history: {len(risk_state.get('neutral_history', []))} 条")
            print(f"     - judge_decision: {len(str(risk_state.get('judge_decision', '')))} 字符")
    else:
        print(f"  ❌ risk_debate_state 不存在")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_report_fields())

