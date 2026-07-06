#!/usr/bin/env python3
"""
测试 AKShare 与 curl_cffi 集成
"""
import sys
sys.path.insert(0, '/app')

# 先 patch requests
import requests
import time
from curl_cffi import requests as curl_requests

original_get = requests.get
last_request_time = {'time': 0}

def patched_get(url, **kwargs):
    """Patch requests.get 使用 curl_cffi"""
    if 'eastmoney.com' in url:
        current_time = time.time()
        time_since_last_request = current_time - last_request_time['time']
        if time_since_last_request < 0.5:
            time.sleep(0.5 - time_since_last_request)
        last_request_time['time'] = time.time()
        
        try:
            print(f"使用 curl_cffi 请求: {url[:80]}...")
            response = curl_requests.get(
                url,
                params=kwargs.get('params'),
                timeout=kwargs.get('timeout', 10),
                impersonate="chrome120"
            )
            print(f"  状态码: {response.status_code}")
            print(f"  响应长度: {len(response.text)} 字符")
            print(f"  响应类型: {type(response)}")
            print(f"  响应前100字符: {response.text[:100]}")
            return response
        except Exception as e:
            print(f"  curl_cffi 失败: {e}")
            # 回退到标准 requests
    
    return original_get(url, **kwargs)

# 应用 patch
requests.get = patched_get

# 现在导入 akshare
import akshare as ak

print("=" * 80)
print("测试 AKShare stock_news_em 与 curl_cffi")
print("=" * 80)

test_symbols = ["600089", "000001"]

for symbol in test_symbols:
    print(f"\n测试股票: {symbol}")
    print("-" * 80)
    
    try:
        df = ak.stock_news_em(symbol=symbol)
        print(f"✅ 成功！数据形状: {df.shape}")
        if not df.empty:
            print(f"列名: {list(df.columns)}")
            print(f"第一条新闻: {df.iloc[0]['新闻标题'] if '新闻标题' in df.columns else 'N/A'}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    time.sleep(1)

