"""测试查询"""
from pymongo import MongoClient

# 连接 MongoDB
mongo_uri = "mongodb://admin:tradingagents123@localhost:27017/"
client = MongoClient(mongo_uri)

db = client["tradingagents"]

print("=" * 60)
print("🔍 测试查询 market_quotes")
print("=" * 60)

# 测试不同的查询条件
queries = [
    {"code": "300750"},
    {"symbol": "300750"},
    {"code": "300750", "symbol": "300750"},
]

for query in queries:
    print(f"\n查询条件: {query}")
    result = db.market_quotes.find_one(query, {"_id": 0})
    if result:
        print(f"  ✅ 找到数据")
        print(f"  - volume: {result.get('volume')}")
        print(f"  - amount: {result.get('amount')}")
        print(f"  - volume_ratio: {result.get('volume_ratio')}")
    else:
        print(f"  ❌ 未找到数据")

client.close()

