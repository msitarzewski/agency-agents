import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.basics_sync.utils import fetch_latest_roe_map

print("🔍 测试获取 ROE 数据...")
try:
    roe_map = fetch_latest_roe_map()
    print(f"✅ 成功获取 ROE 数据，共 {len(roe_map)} 条记录")
    
    # 显示前5条数据
    count = 0
    for ts_code, data in roe_map.items():
        print(f"  {ts_code}: ROE = {data.get('roe')}")
        count += 1
        if count >= 5:
            break
    
    # 检查特定股票
    test_codes = ['601398.SH', '300033.SZ', '000001.SZ']
    print("\n🔍 检查特定股票的 ROE:")
    for ts_code in test_codes:
        if ts_code in roe_map:
            print(f"  {ts_code}: ROE = {roe_map[ts_code].get('roe')}")
        else:
            print(f"  {ts_code}: 未找到数据")
            
except Exception as e:
    print(f"❌ 获取 ROE 数据失败: {e}")
    import traceback
    traceback.print_exc()

