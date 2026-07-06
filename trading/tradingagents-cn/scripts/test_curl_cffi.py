#!/usr/bin/env python3
"""
使用 curl_cffi 模拟真实浏览器的 TLS 指纹
这个库可以模拟 Chrome/Firefox 的 TLS/JA3 指纹，绕过更严格的反爬虫检测
"""
import json
import time

try:
    from curl_cffi import requests
    print("✅ curl_cffi 已安装")
except ImportError:
    print("❌ curl_cffi 未安装")
    print("安装命令: pip install curl-cffi")
    exit(1)


def get_stock_news_with_curl_cffi(symbol: str, page_size: int = 10):
    """
    使用 curl_cffi 获取股票新闻
    curl_cffi 可以模拟真实浏览器的 TLS 指纹
    """
    url = "https://search-api-web.eastmoney.com/search/jsonp"
    
    param = {
        "uid": "",
        "keyword": symbol,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": "default",
                "sort": "default",
                "pageIndex": 1,
                "pageSize": page_size,
                "preTag": "<em>",
                "postTag": "</em>"
            }
        }
    }
    
    params = {
        "cb": f"jQuery{int(time.time() * 1000)}",
        "param": json.dumps(param),
        "_": str(int(time.time() * 1000))
    }
    
    print(f"测试股票: {symbol}")
    print(f"URL: {url}")
    print(f"-" * 80)
    
    # 使用 curl_cffi 模拟 Chrome 浏览器
    # impersonate 参数可以模拟不同浏览器的 TLS 指纹
    try:
        print("尝试模拟 Chrome 120...")
        response = requests.get(
            url,
            params=params,
            impersonate="chrome120",  # 模拟 Chrome 120 的 TLS 指纹
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)} 字符")
        
        if response.status_code == 200:
            # 解析 JSONP
            text = response.text
            if text.startswith("jQuery"):
                text = text[text.find("(")+1:text.rfind(")")]
            
            data = json.loads(text)
            print(f"返回的键: {list(data.keys())}")
            
            if "result" in data:
                print(f"result 的键: {list(data['result'].keys())}")
                
                if "cmsArticleWebOld" in data["result"]:
                    articles = data["result"]["cmsArticleWebOld"]
                    print(f"✅ 成功获取 {len(articles)} 条新闻")
                    
                    if articles:
                        print(f"\n第一条新闻:")
                        first = articles[0]
                        print(f"  标题: {first.get('title', 'N/A')}")
                        print(f"  时间: {first.get('date', 'N/A')}")
                        print(f"  URL: {first.get('url', 'N/A')}")
                    
                    return articles
                else:
                    print(f"❌ 未找到 cmsArticleWebOld 字段")
                    print(f"可用字段: {list(data['result'].keys())}")
                    
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    return []


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 测试 curl_cffi 模拟浏览器 TLS 指纹")
    print("=" * 80)
    print()
    
    test_symbols = ["600089", "000001", "002533"]
    
    success_count = 0
    fail_count = 0
    
    for symbol in test_symbols:
        print(f"\n{'=' * 80}")
        news_list = get_stock_news_with_curl_cffi(symbol, page_size=5)
        
        if news_list:
            success_count += 1
            print(f"✅ 成功")
        else:
            fail_count += 1
            print(f"❌ 失败")
        
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n{'=' * 80}")
    print(f"📊 测试结果")
    print(f"  总计: {len(test_symbols)} 只股票")
    print(f"  成功: {success_count} 只")
    print(f"  失败: {fail_count} 只")
    print(f"  成功率: {success_count / len(test_symbols) * 100:.1f}%")
    print(f"{'=' * 80}")

