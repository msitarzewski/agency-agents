import requests
import json

# 配置
API_KEY = "AIzaSy0000000000000000000000000000000"  # 请替换为您的真实API密钥
MODEL_NAME = "gemini-2.0-flash"  # 指定使用的模型
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

# 请求头
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": API_KEY
}

# 请求数据
data = {
    "contents": [{
        "parts": [{
            "text": "请用一句话解释人工智能。"
        }]
    }]
}

# 发送请求
response = requests.post(url, headers=headers, data=json.dumps(data))

# 处理响应
if response.status_code == 200:
    result = response.json()
    print(result['candidates'][0]['content']['parts'][0]['text'])
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)