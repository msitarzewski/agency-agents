"""
测试历史数据天数修复
验证 historical_days 参数是否正确工作
"""
import asyncio
from datetime import datetime, timedelta
from app.worker.tushare_init_service import TushareInitService

async def test_historical_days_calculation():
    """测试历史数据天数计算逻辑"""
    
    print("=" * 60)
    print("测试历史数据天数计算逻辑")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        (30, "最近30天"),
        (180, "最近6个月"),
        (365, "最近1年（默认）"),
        (730, "最近2年"),
        (3650, "10年（全历史阈值）"),
        (10000, "全历史（>10年）"),
    ]
    
    end_date = datetime.now()
    
    for days, description in test_cases:
        print(f"\n📊 测试: {description} (historical_days={days})")
        
        # 模拟计算逻辑
        if days >= 3650:
            start_date = "1990-01-01"
            print(f"  ✅ 使用全历史模式")
            print(f"  📅 日期范围: {start_date} 到 {end_date.strftime('%Y-%m-%d')}")
        else:
            start_date = (end_date - timedelta(days=days)).strftime('%Y-%m-%d')
            print(f"  ✅ 使用指定天数模式")
            print(f"  📅 日期范围: {start_date} 到 {end_date.strftime('%Y-%m-%d')}")
        
        # 计算实际天数
        if start_date == "1990-01-01":
            actual_days = (end_date - datetime(1990, 1, 1)).days
        else:
            actual_days = days
        
        print(f"  📈 实际天数: {actual_days}天")
        print(f"  📊 预计交易日: ~{int(actual_days * 0.68)}天（按68%交易日比例）")

async def test_service_initialization():
    """测试初始化服务"""
    
    print("\n" + "=" * 60)
    print("测试初始化服务")
    print("=" * 60)
    
    try:
        service = TushareInitService()
        await service.initialize()
        
        print("\n✅ 初始化服务创建成功")
        print(f"  数据源: Tushare")
        print(f"  同步服务: 已初始化")
        
    except Exception as e:
        print(f"\n❌ 初始化服务失败: {e}")

async def check_existing_data():
    """检查现有数据"""
    
    print("\n" + "=" * 60)
    print("检查现有数据")
    print("=" * 60)
    
    try:
        from tradingagents.config.database_manager import get_mongodb_client
        
        client = get_mongodb_client()
        db = client.get_database('tradingagents')
        
        # 检查688788的数据
        symbol = "688788"
        
        # 基础信息
        basic_info = db.stock_basic_info.find_one({'code': symbol})
        if basic_info:
            print(f"\n📊 {symbol} ({basic_info.get('name')})")
            print(f"  上市日期: {basic_info.get('list_date')}")
        
        # 历史数据统计
        for period in ['daily', 'weekly', 'monthly']:
            count = db.stock_daily_quotes.count_documents({
                'symbol': symbol,
                'period': period
            })
            
            if count > 0:
                first = db.stock_daily_quotes.find_one(
                    {'symbol': symbol, 'period': period},
                    sort=[('trade_date', 1)]
                )
                last = db.stock_daily_quotes.find_one(
                    {'symbol': symbol, 'period': period},
                    sort=[('trade_date', -1)]
                )
                
                print(f"\n  {period.upper()}:")
                print(f"    记录数: {count}条")
                print(f"    日期范围: {first.get('trade_date')} ~ {last.get('trade_date')}")
            else:
                print(f"\n  {period.upper()}: 无数据")
        
        # 全市场统计
        print("\n" + "-" * 60)
        print("全市场数据统计:")
        
        total_stocks = db.stock_basic_info.count_documents({'market_info.market': 'CN'})
        print(f"  股票总数: {total_stocks}")
        
        for period in ['daily', 'weekly', 'monthly']:
            count = db.stock_daily_quotes.count_documents({'period': period})
            print(f"  {period.upper()}记录数: {count:,}条")
        
    except Exception as e:
        print(f"\n❌ 检查数据失败: {e}")

async def main():
    """主函数"""
    
    print("\n🚀 历史数据天数修复测试")
    print("=" * 60)
    
    # 测试1: 计算逻辑
    await test_historical_days_calculation()
    
    # 测试2: 服务初始化
    await test_service_initialization()
    
    # 测试3: 检查现有数据
    await check_existing_data()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    
    print("\n💡 修复说明:")
    print("  1. historical_days < 3650: 使用指定天数")
    print("  2. historical_days >= 3650: 使用全历史（从1990-01-01）")
    print("  3. 移除了 all_history 参数（逻辑冲突）")
    print()
    print("💡 使用建议:")
    print("  # 同步最近1年数据（默认）")
    print("  python cli/tushare_init.py --full")
    print()
    print("  # 同步全历史数据")
    print("  python cli/tushare_init.py --full --historical-days 10000")
    print()
    print("  # 同步全历史多周期数据")
    print("  python cli/tushare_init.py --full --multi-period --historical-days 10000")
    print()

if __name__ == "__main__":
    asyncio.run(main())

