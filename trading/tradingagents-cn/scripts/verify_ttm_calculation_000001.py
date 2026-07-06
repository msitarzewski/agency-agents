"""
验证 000001（平安银行）的 TTM 计算是否正确
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def main():
    # 连接数据库
    mongo_uri = os.getenv("MONGODB_CONNECTION_STRING")
    db_name = os.getenv("MONGODB_DATABASE_NAME") or os.getenv("MONGODB_DATABASE", "tradingagents")

    if not mongo_uri:
        mongo_host = os.getenv("MONGODB_HOST", "localhost")
        mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongo_uri = f"mongodb://{mongo_host}:{mongo_port}"

    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    print("=" * 100)
    print("验证 000001（平安银行）的 TTM 计算")
    print("=" * 100)
    
    # 查询财务数据
    financial_data = await db.stock_financial_data.find_one(
        {"code": "000001", "data_source": "tushare"},
        sort=[("report_period", -1)]
    )
    
    if not financial_data:
        print("❌ 未找到财务数据")
        return
    
    print(f"\n【最新财务数据】")
    print(f"报告期: {financial_data.get('report_period')}")
    print(f"营业收入（单期）: {financial_data.get('revenue', 0) / 100000000:.2f} 亿元")
    print(f"营业收入（TTM）: {financial_data.get('revenue_ttm', 0) / 100000000:.2f} 亿元")
    
    # 查询所有利润表数据
    print(f"\n【利润表历史数据】")
    raw_data = financial_data.get('raw_data', {})
    income_statements = raw_data.get('income_statement', [])
    
    if not income_statements:
        print("❌ 没有利润表数据")
        return
    
    print(f"共有 {len(income_statements)} 期数据：\n")
    
    # 按报告期排序（最新的在前）
    income_statements_sorted = sorted(
        income_statements, 
        key=lambda x: x.get('end_date', ''), 
        reverse=True
    )
    
    # 显示最近几期的数据
    for i, stmt in enumerate(income_statements_sorted[:8]):
        end_date = stmt.get('end_date', 'N/A')
        revenue = stmt.get('revenue', 0) / 100000000  # 转换为亿元
        print(f"{i+1}. {end_date}: {revenue:.2f} 亿元")
    
    # 手动计算 TTM
    print(f"\n【手动计算 TTM】")
    
    latest = income_statements_sorted[0]
    latest_period = latest.get('end_date')
    latest_revenue = latest.get('revenue', 0) / 100000000
    
    print(f"最新期: {latest_period} = {latest_revenue:.2f} 亿元")
    
    # 查找去年同期
    latest_year = latest_period[:4]
    last_year = str(int(latest_year) - 1)
    last_year_same_period = last_year + latest_period[4:]
    
    last_year_same = None
    for stmt in income_statements_sorted:
        if stmt.get('end_date') == last_year_same_period:
            last_year_same = stmt
            break
    
    if not last_year_same:
        print(f"❌ 未找到去年同期数据: {last_year_same_period}")
        return
    
    last_year_revenue = last_year_same.get('revenue', 0) / 100000000
    print(f"去年同期: {last_year_same_period} = {last_year_revenue:.2f} 亿元")
    
    # 查找基准年报
    base_period = None
    for stmt in income_statements_sorted:
        period = stmt.get('end_date')
        if period and period > last_year_same_period and period[4:8] == '1231':
            base_period = stmt
            break
    
    if not base_period:
        print(f"❌ 未找到基准年报（需要在 {last_year_same_period} 之后的年报）")
        return
    
    base_period_date = base_period.get('end_date')
    base_revenue = base_period.get('revenue', 0) / 100000000
    print(f"基准年报: {base_period_date} = {base_revenue:.2f} 亿元")
    
    # 计算 TTM
    ttm_calculated = base_revenue + (latest_revenue - last_year_revenue)
    
    print(f"\n【TTM 计算过程】")
    print(f"TTM = 基准年报 + (本期累计 - 去年同期累计)")
    print(f"    = {base_revenue:.2f} + ({latest_revenue:.2f} - {last_year_revenue:.2f})")
    print(f"    = {base_revenue:.2f} + {latest_revenue - last_year_revenue:.2f}")
    print(f"    = {ttm_calculated:.2f} 亿元")
    
    # 对比数据库中的 TTM
    db_ttm = financial_data.get('revenue_ttm', 0) / 100000000
    print(f"\n【对比结果】")
    print(f"数据库 TTM: {db_ttm:.2f} 亿元")
    print(f"手动计算 TTM: {ttm_calculated:.2f} 亿元")
    print(f"差异: {abs(db_ttm - ttm_calculated):.2f} 亿元")
    
    if abs(db_ttm - ttm_calculated) < 0.01:
        print(f"✅ TTM 计算正确！")
    else:
        print(f"❌ TTM 计算有误！")
    
    # 验证 TTM 的合理性
    print(f"\n【合理性验证】")
    print(f"单期数据（2025年1-9月）: {latest_revenue:.2f} 亿元")
    print(f"TTM数据（最近12个月）: {ttm_calculated:.2f} 亿元")
    print(f"TTM / 单期 = {ttm_calculated / latest_revenue:.2f} 倍")
    
    # 计算单季度数据
    print(f"\n【单季度数据推算】")
    
    # 找到 2025Q2
    q2_2025 = None
    for stmt in income_statements_sorted:
        if stmt.get('end_date') == '20250630':
            q2_2025 = stmt
            break
    
    if q2_2025:
        q2_revenue = q2_2025.get('revenue', 0) / 100000000
        q3_single = latest_revenue - q2_revenue  # 2025Q3单季 = 2025Q3累计 - 2025Q2累计
        print(f"2025Q2累计: {q2_revenue:.2f} 亿元")
        print(f"2025Q3单季 = 2025Q3累计 - 2025Q2累计 = {latest_revenue:.2f} - {q2_revenue:.2f} = {q3_single:.2f} 亿元")
        
        # 计算 Q4 2024 单季
        q3_2024 = None
        for stmt in income_statements_sorted:
            if stmt.get('end_date') == '20240930':
                q3_2024 = stmt
                break
        
        if q3_2024 and base_period:
            q3_2024_revenue = q3_2024.get('revenue', 0) / 100000000
            q4_2024_single = base_revenue - q3_2024_revenue
            print(f"2024Q3累计: {q3_2024_revenue:.2f} 亿元")
            print(f"2024Q4单季 = 2024年报 - 2024Q3累计 = {base_revenue:.2f} - {q3_2024_revenue:.2f} = {q4_2024_single:.2f} 亿元")
            
            print(f"\n最近4个单季度:")
            print(f"  2024Q4: {q4_2024_single:.2f} 亿元")
            print(f"  2025Q1: (需要2025Q1数据)")
            print(f"  2025Q2: (需要2025Q1数据)")
            print(f"  2025Q3: {q3_single:.2f} 亿元")
    
    client.close()
    print("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())

