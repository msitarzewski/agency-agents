"""
检查688788股票信息
"""
from tradingagents.config.database_manager import get_mongodb_client
from datetime import datetime

client = get_mongodb_client()
db = client.get_database('tradingagents')

# 查询基础信息
doc = db.stock_basic_info.find_one({'code': '688788'})
if doc:
    print(f"股票代码: {doc.get('code')}")
    print(f"股票名称: {doc.get('name')}")
    print(f"上市日期: {doc.get('list_date')}")
    print(f"市场: {doc.get('market_info', {}).get('market')}")
    print(f"板块: {doc.get('board')}")
else:
    print("未找到688788的基础信息")

# 查询历史数据
count = db.stock_daily_quotes.count_documents({'symbol': '688788', 'period': 'daily'})
print(f"\n历史数据记录数: {count}")

# 查询日期范围
first = db.stock_daily_quotes.find_one({'symbol': '688788', 'period': 'daily'}, sort=[('trade_date', 1)])
last = db.stock_daily_quotes.find_one({'symbol': '688788', 'period': 'daily'}, sort=[('trade_date', -1)])

if first and last:
    print(f"最早日期: {first.get('trade_date')}")
    print(f"最新日期: {last.get('trade_date')}")
    
    # 计算交易日数量
    from datetime import datetime
    if doc and doc.get('list_date'):
        list_date = doc.get('list_date')
        if isinstance(list_date, str):
            list_date_obj = datetime.strptime(list_date, '%Y%m%d')
        else:
            list_date_obj = list_date
        
        today = datetime.now()
        days_since_listing = (today - list_date_obj).days
        print(f"\n上市天数: {days_since_listing}天")
        print(f"交易日数量: {count}条")
        print(f"交易日占比: {count / days_since_listing * 100:.1f}%")

