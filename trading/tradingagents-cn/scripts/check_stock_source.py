"""
检查股票数据的 source 字段值
"""
import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_stock_source():
    """检查股票数据的 source 字段"""
    try:
        # 从环境变量读取 MongoDB 连接信息
        load_dotenv()
        
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongo_db_name = os.getenv("MONGO_DB", "tradingagents")
        
        print(f"连接 MongoDB: {mongo_uri}")
        print(f"数据库: {mongo_db_name}")
        print()
        
        # 创建同步 MongoDB 客户端
        client = MongoClient(mongo_uri)
        db = client[mongo_db_name]
        
        # 查询 300750 的所有记录
        print("=" * 80)
        print("📋 查询股票 300750 的所有记录")
        print("=" * 80)
        print()
        
        records = list(db.stock_basic_info.find({"code": "300750"}))
        
        if records:
            print(f"✅ 找到 {len(records)} 条记录")
            print()
            
            for idx, record in enumerate(records, 1):
                print(f"记录 {idx}:")
                print(f"  source: {record.get('source')}")
                print(f"  name: {record.get('name')}")
                print(f"  total_mv: {record.get('total_mv')}")
                print(f"  circ_mv: {record.get('circ_mv')}")
                print(f"  pe: {record.get('pe')}")
                print(f"  pb: {record.get('pb')}")
                print(f"  ps_ttm: {record.get('ps_ttm')}")
                print(f"  turnover_rate: {record.get('turnover_rate')}")
                print()
        else:
            print("❌ 没有找到记录")
        
        print()
        
        # 测试查询条件
        print("=" * 80)
        print("🔍 测试不同的查询条件")
        print("=" * 80)
        print()
        
        test_sources = ["tushare", "Tushare", "TUSHARE", "akshare", "AKShare", "AKSHARE"]
        
        for source in test_sources:
            count = db.stock_basic_info.count_documents({"code": "300750", "source": source})
            print(f"source = '{source}': {count} 条记录")
        
        print()
        
        # 查询所有不同的 source 值
        print("=" * 80)
        print("📊 数据库中所有不同的 source 值")
        print("=" * 80)
        print()
        
        distinct_sources = db.stock_basic_info.distinct("source")
        print(f"找到 {len(distinct_sources)} 个不同的 source 值:")
        for source in sorted(distinct_sources):
            count = db.stock_basic_info.count_documents({"source": source})
            print(f"  '{source}': {count} 条记录")
        
        print()
        
        # 检查数据源配置中的 type 字段
        print("=" * 80)
        print("📋 检查 system_configs 中的数据源 type 字段")
        print("=" * 80)
        print()
        
        config_data = db.system_configs.find_one(
            {"is_active": True},
            sort=[("version", -1)]
        )
        
        if config_data:
            data_source_configs = config_data.get('data_source_configs', [])
            
            # 按优先级排序
            sorted_configs = sorted(data_source_configs, key=lambda x: x.get('priority', 0), reverse=True)
            
            print("数据源配置（按优先级排序）:")
            print()
            
            for idx, ds in enumerate(sorted_configs, 1):
                if ds.get('enabled', False) and ds.get('type', '').lower() in ['tushare', 'akshare', 'baostock']:
                    print(f"{idx}. {ds.get('name', 'Unknown')}")
                    print(f"   type: '{ds.get('type', '')}'")
                    print(f"   type.lower(): '{ds.get('type', '').lower()}'")
                    print(f"   priority: {ds.get('priority', 0)}")
                    print()
            
            # 提取优先级最高的数据源
            enabled_sources = [
                ds.type.lower() if hasattr(ds, 'type') else ds.get('type', '').lower()
                for ds in sorted_configs
                if ds.get('enabled', False) and ds.get('type', '').lower() in ['tushare', 'akshare', 'baostock']
            ]
            
            if enabled_sources:
                print(f"✅ 优先级最高的数据源: '{enabled_sources[0]}'")
                print()
                
                # 测试用这个数据源查询
                source = enabled_sources[0]
                count = db.stock_basic_info.count_documents({"code": "300750", "source": source})
                print(f"使用 source = '{source}' 查询 300750: {count} 条记录")
                
                if count > 0:
                    record = db.stock_basic_info.find_one({"code": "300750", "source": source})
                    print()
                    print("查询到的记录:")
                    print(f"  source: {record.get('source')}")
                    print(f"  name: {record.get('name')}")
                    print(f"  total_mv: {record.get('total_mv')}")
                    print(f"  circ_mv: {record.get('circ_mv')}")
                    print(f"  pe: {record.get('pe')}")
                    print(f"  pb: {record.get('pb')}")
        
        print()
        print("=" * 80)
        print("✅ 检查完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_stock_source()

