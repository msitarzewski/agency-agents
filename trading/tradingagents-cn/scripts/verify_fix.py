"""
验证 trade_date 修复效果
检查最新同步的数据是否使用正确的日期格式
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_database, get_mongo_db, close_database


async def verify_fix():
    """验证修复效果"""
    
    print("=" * 80)
    print("🔍 验证 trade_date 修复效果")
    print("=" * 80)
    
    try:
        # 初始化数据库
        await init_database()
        db = get_mongo_db()
        collection = db.stock_daily_quotes
        
        # 查询最近更新的 AKShare 数据
        recent_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"\n📊 查询条件:")
        print(f"  - 数据源: akshare")
        print(f"  - 更新时间: >= {recent_date}")
        print(f"  - 周期: daily")
        
        # 查询最近更新的记录
        cursor = collection.find({
            "data_source": "akshare",
            "period": "daily",
            "updated_at": {"$gte": datetime.strptime(recent_date, '%Y-%m-%d')}
        }).sort("updated_at", -1).limit(10)
        
        records = await cursor.to_list(length=10)
        
        if not records:
            print(f"\n⚠️ 未找到最近更新的 AKShare 数据")
            print(f"   可能同步还在进行中，或者还没有新数据")
            return
        
        print(f"\n✅ 找到 {len(records)} 条最近更新的记录")
        
        # 检查 trade_date 格式
        print(f"\n📋 最新的 10 条记录:")
        print(f"{'序号':<4} {'股票代码':<8} {'trade_date':<12} {'格式':<8} {'收盘价':<10} {'更新时间':<20}")
        print("-" * 80)
        
        valid_count = 0
        invalid_count = 0
        
        for i, record in enumerate(records, 1):
            trade_date = record.get('trade_date', 'N/A')
            symbol = record.get('symbol', 'N/A')
            close = record.get('close', 0)
            updated_at = record.get('updated_at', 'N/A')
            
            # 检查格式
            if isinstance(trade_date, str) and len(trade_date) >= 8:
                format_status = "✅ 正确"
                valid_count += 1
            else:
                format_status = "❌ 错误"
                invalid_count += 1
            
            print(f"{i:<4} {symbol:<8} {trade_date:<12} {format_status:<8} {close:<10.2f} {str(updated_at):<20}")
        
        # 统计结果
        print("\n" + "=" * 80)
        print(f"📊 统计结果:")
        print(f"  ✅ 格式正确: {valid_count} 条")
        print(f"  ❌ 格式错误: {invalid_count} 条")
        
        if invalid_count == 0:
            print(f"\n🎉 修复成功！所有新同步的数据格式都正确！")
        else:
            print(f"\n⚠️ 仍有格式错误的数据，需要进一步检查")
        
        # 检查 000001 的最新数据
        print("\n" + "=" * 80)
        print("🔍 检查 000001 的最新数据")
        print("=" * 80)
        
        cursor = collection.find({
            "symbol": "000001",
            "period": "daily",
            "data_source": "akshare"
        }).sort("trade_date", -1).limit(5)
        
        records = await cursor.to_list(length=5)
        
        if records:
            print(f"\n✅ 找到 {len(records)} 条记录")
            print(f"\n{'序号':<4} {'trade_date':<12} {'收盘价':<10} {'成交量':<15}")
            print("-" * 50)
            
            for i, record in enumerate(records, 1):
                trade_date = record.get('trade_date', 'N/A')
                close = record.get('close', 0)
                volume = record.get('volume', 0)
                print(f"{i:<4} {trade_date:<12} {close:<10.2f} {volume:<15.0f}")
        else:
            print(f"\n⚠️ 未找到 000001 的 AKShare 数据")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await close_database()
    
    print("\n" + "=" * 80)
    print("✅ 验证完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(verify_fix())

