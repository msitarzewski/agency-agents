"""
测试 Google API 连接（使用代理）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("测试 Google API 连接（使用代理）")
print("=" * 80)

# 1. 配置代理
print("\n配置代理设置...")
print("请输入您的代理地址（例如: http://127.0.0.1:7890）")
print("如果不需要代理，直接按回车跳过")

proxy_url = input("代理地址: ").strip()

if proxy_url:
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    print(f"✅ 已设置代理: {proxy_url}")
else:
    print("⚠️ 未设置代理，将直接连接")

# 2. 检查 API Key
google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    print("\n❌ 未找到 GOOGLE_API_KEY 环境变量")
    print("请在 .env 文件中设置：GOOGLE_API_KEY=your-api-key")
    sys.exit(1)

print(f"\n✅ 找到 GOOGLE_API_KEY: {google_api_key[:10]}...{google_api_key[-4:]}")

# 3. 测试网络连接
print("\n" + "=" * 80)
print("测试网络连接")
print("=" * 80)

import socket
import time

def test_connection(host, port=443, timeout=5):
    """测试 TCP 连接"""
    try:
        start_time = time.time()
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        elapsed = time.time() - start_time
        return True, elapsed
    except Exception as e:
        return False, str(e)

# 测试连接
host = "generativelanguage.googleapis.com"
success, result = test_connection(host, timeout=10)
if success:
    print(f"✅ {host}: 连接成功 ({result:.2f}秒)")
else:
    print(f"❌ {host}: 连接失败 - {result}")
    print("\n⚠️ 网络连接失败，但仍然尝试调用 API（可能通过代理成功）")

# 4. 测试 Google AI API
print("\n" + "=" * 80)
print("测试 Google AI API (gemini-2.5-flash)")
print("=" * 80)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    print("📝 创建 ChatGoogleGenerativeAI 实例...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.7,
        max_tokens=500,  # 增加到 500
        timeout=30  # 30秒超时
    )
    
    print("✅ LLM 实例创建成功")
    print(f"   模型: {llm.model}")
    
    # 发送测试消息
    print("\n📤 发送测试消息: '你好，请用一句话介绍你自己'")
    print("⏳ 等待响应（最多30秒）...")
    
    start_time = time.time()
    
    response = llm.invoke("你好，请用一句话介绍你自己")
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ API 调用成功！耗时: {elapsed:.2f}秒")
    print(f"\n📥 响应内容:")
    print(f"   {response.content}")
    
    print("\n" + "=" * 80)
    print("✅ 测试通过！Google API 连接正常")
    print("=" * 80)
    
    if proxy_url:
        print(f"\n💡 提示: 您的代理 {proxy_url} 工作正常")
        print("建议在后端服务启动时也配置相同的代理")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    print("\n详细错误信息:")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("故障排查建议:")
    print("=" * 80)
    
    if "timed out" in str(e).lower() or "timeout" in str(e).lower():
        print("\n🔍 连接超时问题:")
        print("1. 确认代理地址是否正确")
        print("2. 检查代理工具是否正在运行")
        print("3. 尝试在浏览器中访问: https://generativelanguage.googleapis.com")
        print("4. 常见代理端口:")
        print("   - Clash: http://127.0.0.1:7890")
        print("   - V2Ray: http://127.0.0.1:10809")
        print("   - Shadowsocks: http://127.0.0.1:1080")
    elif "api key" in str(e).lower():
        print("\n🔍 API Key 问题:")
        print("1. 访问 https://aistudio.google.com/app/apikey 检查 API Key")
        print("2. 确认 API Key 是否有效且未过期")
        print("3. 检查 API Key 是否有足够的配额")
    else:
        print("\n🔍 其他问题:")
        print("1. 检查网络连接")
        print("2. 尝试重启代理工具")
        print("3. 查看防火墙设置")

