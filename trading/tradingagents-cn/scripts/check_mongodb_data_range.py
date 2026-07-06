"""
检查MongoDB中已同步数据的实际时间范围
"""
from tradingagents.config.database_manager import get_mongodb_client


def check_data_range():
    """检查MongoDB中的数据范围"""
    
    client = get_mongodb_client()
    db = client['tradingagents']
    collection = db['stock_daily_quotes']
    
    print("=" * 80)
    print("检查MongoDB中历史数据的实际时间范围")
    print("=" * 80)
    
    # 测试几只老股票
    test_symbols = [
        '000001',  # 平安银行
        '600000',  # 浦发银行
        '000002',  # 万科A
    ]
    
    for symbol in test_symbols:
        print(f"\n📊 {symbol}")
        print("-" * 80)
        
        # 查询该股票的数据
        docs = list(collection.find(
            {'symbol': symbol, 'period': 'daily'},
            {'trade_date': 1, 'open': 1, 'close': 1, 'volume': 1}
        ).sort('trade_date', 1).limit(10))
        
        if docs:
            # 统计总数
            total_count = collection.count_documents({'symbol': symbol, 'period': 'daily'})
            
            # 获取最早和最晚的日期
            earliest = collection.find_one(
                {'symbol': symbol, 'period': 'daily'},
                sort=[('trade_date', 1)]
            )
            latest = collection.find_one(
                {'symbol': symbol, 'period': 'daily'},
                sort=[('trade_date', -1)]
            )
            
            print(f"  总记录数: {total_count}")
            print(f"  最早日期: {earliest['trade_date']}")
            print(f"  最晚日期: {latest['trade_date']}")
            
            # 显示最早的几条记录
            print(f"\n  最早的10条记录:")
            for doc in docs:
                print(f"    {doc['trade_date']}: 开盘={doc.get('open', 'N/A')}, "
                      f"收盘={doc.get('close', 'N/A')}, 成交量={doc.get('volume', 'N/A')}")
        else:
            print(f"  ❌ 无数据")
    
    # 统计所有股票的最早日期分布
    print("\n" + "=" * 80)
    print("所有股票的最早日期分布")
    print("=" * 80)
    
    pipeline = [
        {'$match': {'period': 'daily'}},
        {'$group': {
            '_id': '$symbol',
            'earliest_date': {'$min': '$trade_date'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'earliest_date': 1}},
        {'$limit': 20}
    ]
    
    results = list(collection.aggregate(pipeline))
    
    print(f"\n最早的20只股票:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['_id']}: {result['earliest_date']} ({result['count']}条记录)")
    
    # 统计年份分布
    print("\n" + "=" * 80)
    print("数据年份分布统计")
    print("=" * 80)
    
    year_pipeline = [
        {'$match': {'period': 'daily'}},
        {'$group': {
            '_id': '$symbol',
            'earliest_date': {'$min': '$trade_date'}
        }},
        {'$project': {
            'year': {'$substr': ['$earliest_date', 0, 4]}
        }},
        {'$group': {
            '_id': '$year',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    
    year_results = list(collection.aggregate(year_pipeline))
    
    print(f"\n按年份统计股票数量:")
    for result in year_results:
        print(f"  {result['_id']}年: {result['count']}只股票")
    
    print("\n" + "=" * 80)
    print("结论:")
    print("=" * 80)
    print("根据上述统计，可以确定Tushare数据的实际起始时间范围。")
    print()


if __name__ == "__main__":
    check_data_range()

