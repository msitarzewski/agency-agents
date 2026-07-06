"""
简单测试脚本：验证 Google AI SDK 的基础功能

测试步骤：
1. 直接使用 google-generativeai SDK
2. 使用 langchain_google_genai.ChatGoogleGenerativeAI
3. 使用我们的 ChatGoogleOpenAI 适配器
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("=" * 80)
print("🧪 Google AI SDK 基础功能测试")
print("=" * 80)
print()

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    print("❌ 错误：未找到 GOOGLE_API_KEY 环境变量")
    print("   请在 .env 文件中设置 GOOGLE_API_KEY")
    sys.exit(1)

print(f"✅ 找到 GOOGLE_API_KEY: {google_api_key[:10]}...")
print()

# ============================================================================
# 测试 1: 直接使用 google-generativeai SDK
# ============================================================================
print("📊 测试 1: 直接使用 google-generativeai SDK")
print("-" * 80)

try:
    import google.generativeai as genai
    
    # 配置 API Key
    genai.configure(api_key=google_api_key)
    
    # 创建模型
    model = genai.GenerativeModel('gemini-2.5-flash')
    print(f"✅ 模型创建成功: {model.model_name}")
    
    # 发送测试消息
    print("📤 发送测试消息: 你好，请用一句话介绍你自己")
    response = model.generate_content("你好，请用一句话介绍你自己")
    
    print("✅ API 调用成功！")
    print(f"📥 响应: {response.text[:200]}...")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============================================================================
# 测试 2: 使用 langchain_google_genai.ChatGoogleGenerativeAI
# ============================================================================
print("📊 测试 2: 使用 langchain_google_genai.ChatGoogleGenerativeAI")
print("-" * 80)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # 创建 LLM（默认端点）
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.7,
        max_tokens=100
    )
    print(f"✅ LLM 创建成功: {llm.model}")
    
    # 发送测试消息
    print("📤 发送测试消息: 你好，请用一句话介绍你自己")
    response = llm.invoke("你好，请用一句话介绍你自己")
    
    print("✅ API 调用成功！")
    print(f"📥 响应: {response.content[:200]}...")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============================================================================
# 测试 3: 使用 langchain_google_genai + REST 模式
# ============================================================================
print("📊 测试 3: 使用 langchain_google_genai + REST 模式")
print("-" * 80)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # 创建 LLM（REST 模式）
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.7,
        max_tokens=100,
        transport="rest"  # 使用 REST 模式
    )
    print(f"✅ LLM 创建成功: {llm.model}")
    print("   传输模式: REST")
    
    # 发送测试消息
    print("📤 发送测试消息: 你好，请用一句话介绍你自己")
    response = llm.invoke("你好，请用一句话介绍你自己")
    
    print("✅ API 调用成功！")
    print(f"📥 响应: {response.content[:200]}...")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============================================================================
# 测试 4: 使用 langchain_google_genai + 自定义 client_options
# ============================================================================
print("📊 测试 4: 使用 langchain_google_genai + 自定义 client_options")
print("-" * 80)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # 创建 LLM（自定义 client_options）
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.7,
        max_tokens=100,
        transport="rest",
        client_options={"api_endpoint": "https://generativelanguage.googleapis.com"}
    )
    print(f"✅ LLM 创建成功: {llm.model}")
    print("   传输模式: REST")
    print("   自定义端点: https://generativelanguage.googleapis.com")
    
    # 发送测试消息
    print("📤 发送测试消息: 你好，请用一句话介绍你自己")
    response = llm.invoke("你好，请用一句话介绍你自己")
    
    print("✅ API 调用成功！")
    print(f"📥 响应: {response.content[:200]}...")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============================================================================
# 测试 5: 使用我们的 ChatGoogleOpenAI 适配器（不提供 base_url）
# ============================================================================
print("📊 测试 5: 使用我们的 ChatGoogleOpenAI 适配器（不提供 base_url）")
print("-" * 80)

try:
    from tradingagents.llm_adapters import ChatGoogleOpenAI
    
    # 创建 LLM（不提供 base_url）
    llm = ChatGoogleOpenAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.7,
        max_tokens=100,
        transport="rest"
    )
    print(f"✅ LLM 创建成功: {llm.model}")
    
    # 发送测试消息
    print("📤 发送测试消息: 你好，请用一句话介绍你自己")
    response = llm.invoke("你好，请用一句话介绍你自己")
    
    print("✅ API 调用成功！")
    print(f"📥 响应: {response.content[:200]}...")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============================================================================
# 测试 6: 使用我们的 ChatGoogleOpenAI 适配器（提供 base_url）
# ============================================================================
print("📊 测试 6: 使用我们的 ChatGoogleOpenAI 适配器（提供 base_url）")
print("-" * 80)

try:
    from tradingagents.llm_adapters import ChatGoogleOpenAI
    
    # 创建 LLM（提供 base_url）
    llm = ChatGoogleOpenAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        temperature=0.7,
        max_tokens=100,
        transport="rest"
    )
    print(f"✅ LLM 创建成功: {llm.model}")
    
    # 发送测试消息
    print("📤 发送测试消息: 你好，请用一句话介绍你自己")
    response = llm.invoke("你好，请用一句话介绍你自己")
    
    print("✅ API 调用成功！")
    print(f"📥 响应: {response.content[:200]}...")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("🎉 测试完成！")
print("=" * 80)
print()
print("📝 说明：")
print("   - 测试 1-3 验证基础 SDK 功能")
print("   - 测试 4 验证自定义 client_options")
print("   - 测试 5-6 验证我们的适配器")
print()
print("💡 如果某个测试失败，请检查：")
print("   1. 网络连接（需要能访问 Google API）")
print("   2. GOOGLE_API_KEY 是否正确")
print("   3. API 配额是否充足")

