#!/usr/bin/env python3
"""
测试 Docker 容器内 AKShare 新闻接口 - 检查请求头和反爬虫
"""
import akshare as ak
import json
import traceback
import requests

def test_with_different_headers():
    """测试不同请求头的效果"""
    symbol = "000001"

    print(f"=" * 80)
    print(f"测试 AKShare 新闻接口 - 请求头对比")
    print(f"=" * 80)

    # 测试1：默认请求头
    print(f"\n【测试1】使用默认请求头")
    print(f"-" * 80)
    try:
        df = ak.stock_news_em(symbol=symbol)
        print(f"✅ 成功！数据形状: {df.shape}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试2：直接请求，查看默认请求头
    print(f"\n【测试2】查看 requests 默认请求头")
    print(f"-" * 80)
    url = "https://search-api-web.eastmoney.com/search/jsonp"

    # 默认请求头
    print("默认请求头:")
    session = requests.Session()
    print(f"  User-Agent: {session.headers.get('User-Agent', 'None')}")

    # 测试3：使用浏览器请求头
    print(f"\n【测试3】使用浏览器 User-Agent")
    print(f"-" * 80)

    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.eastmoney.com/',
        'Connection': 'keep-alive',
    }

    params = {
        "cb": "jQuery",
        "param": json.dumps({
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
                    "pageSize": 10,
                    "preTag": "<em>",
                    "postTag": "</em>"
                }
            }
        })
    }

    try:
        response = requests.get(url, params=params, headers=browser_headers, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)} 字符")
        print(f"响应内容（前500字符）:")
        print(response.text[:500])

        # 尝试解析 JSON
        if response.status_code == 200:
            # 移除 JSONP 包装
            text = response.text
            if text.startswith("jQuery"):
                text = text[text.find("(")+1:text.rfind(")")]

            data = json.loads(text)
            print(f"\n✅ JSON 解析成功")
            print(f"返回的键: {list(data.keys())}")

            if "result" in data:
                print(f"result 的键: {list(data['result'].keys())}")
                if "cmsArticleWebOld" in data["result"]:
                    print(f"✅ 找到 cmsArticleWebOld 字段")
                    articles = data["result"]["cmsArticleWebOld"]
                    print(f"文章数量: {len(articles)}")
                else:
                    print(f"❌ 未找到 cmsArticleWebOld 字段")
                    print(f"可用字段: {list(data['result'].keys())}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_with_different_headers()

