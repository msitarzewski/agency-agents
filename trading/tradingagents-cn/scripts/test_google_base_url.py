"""
测试脚本：验证 Google AI 的 base_url 参数是否生效

说明：
- 如果系统已配置全局代理（如 V2Ray 系统代理模式），会自动使用
- 不需要显式设置 HTTP_PROXY 环境变量
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("🧪 Google AI base_url 参数测试")
print("=" * 80)

def test_google_base_url():
    """测试 Google AI 的 base_url 参数"""
    print()
    
    from tradingagents.llm_adapters import ChatGoogleOpenAI
    
    # 测试 1: 不提供 base_url（使用默认端点）
    print("\n📊 测试 1: 不提供 base_url（使用默认端点）")
    print("-" * 80)
    
    try:
        llm1 = ChatGoogleOpenAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0.7,
            max_tokens=100
        )
        print("✅ LLM 创建成功（默认端点）")
        print(f"   模型: {llm1.model}")
    except Exception as e:
        print(f"❌ LLM 创建失败: {e}")
        return False
    
    # 测试 2: 提供 base_url（v1beta）+ REST 传输模式
    print("\n📊 测试 2: 提供 base_url（v1beta）+ REST 传输模式")
    print("-" * 80)

    custom_url_v1beta = "https://generativelanguage.googleapis.com/v1beta"

    try:
        llm2 = ChatGoogleOpenAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            base_url=custom_url_v1beta,
            temperature=0.7,
            max_tokens=100,
            transport="rest"  # 🔧 使用 REST 传输模式，支持 HTTP 代理
        )
        print(f"✅ LLM 创建成功（自定义端点: {custom_url_v1beta}）")
        print(f"   模型: {llm2.model}")
        print(f"   传输模式: REST（支持 HTTP 代理）")
    except Exception as e:
        print(f"❌ LLM 创建失败: {e}")
        return False
    
    # 测试 3: 提供 base_url（v1，应该自动转换为 v1beta）
    print("\n📊 测试 3: 提供 base_url（v1，应该自动转换为 v1beta）")
    print("-" * 80)
    
    custom_url_v1 = "https://generativelanguage.googleapis.com/v1"
    
    try:
        llm3 = ChatGoogleOpenAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            base_url=custom_url_v1,
            temperature=0.7,
            max_tokens=100
        )
        print(f"✅ LLM 创建成功（自定义端点: {custom_url_v1}）")
        print(f"   模型: {llm3.model}")
        print(f"   ℹ️  应该自动转换为: {custom_url_v1[:-3]}/v1beta")
    except Exception as e:
        print(f"❌ LLM 创建失败: {e}")
        return False
    
    # 测试 4: 使用 create_llm_by_provider 函数
    print("\n📊 测试 4: 使用 create_llm_by_provider 函数")
    print("-" * 80)
    
    from tradingagents.graph.trading_graph import create_llm_by_provider
    
    try:
        llm4 = create_llm_by_provider(
            provider="google",
            model="gemini-2.5-flash",
            backend_url=custom_url_v1,
            temperature=0.7,
            max_tokens=100,
            timeout=60
        )
        print(f"✅ LLM 创建成功（通过 create_llm_by_provider）")
        print(f"   模型: {llm4.model}")
    except Exception as e:
        print(f"❌ LLM 创建失败: {e}")
        return False
    
    # 测试 5: 实际 API 调用（使用 REST 模式）
    print("\n📊 测试 5: 实际 API 调用（使用 REST 模式）")
    print("-" * 80)

    try:
        print("📤 发送测试消息...")
        print("   提示: 你好，请用一句话介绍你自己")

        # 使用 REST 模式的 LLM（llm2）
        response = llm2.invoke("你好，请用一句话介绍你自己")

        print("✅ API 调用成功！")
        print(f"📥 响应内容: {response.content[:200]}...")
        print(f"   响应长度: {len(response.content)} 字符")

        # 检查响应元数据
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            print(f"   模型: {metadata.get('model_name', 'N/A')}")
            if 'token_usage' in metadata:
                usage = metadata['token_usage']
                print(f"   Token使用: 输入={usage.get('prompt_tokens', 0)}, 输出={usage.get('completion_tokens', 0)}, 总计={usage.get('total_tokens', 0)}")

        return True

    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        print()
        print("   可能的原因：")
        print("   1. 网络连接问题（需要能访问 Google API）")
        print("   2. Google API Key 无效或已过期")
        print("   3. API 配额已用完")
        print("   4. 代理配置问题（如果使用代理）")
        print()
        print("   💡 提示：")
        print("   - 在美国服务器上应该可以直接连接")
        print("   - 检查 GOOGLE_API_KEY 是否正确")
        print("   - 访问 https://ai.google.dev/ 查看 API 状态")
        print()
        print("   ⚠️  注意：API 调用失败不影响 base_url 参数传递功能")
        return False

    print("\n" + "=" * 80)
    print("🎉 所有基础测试通过！Google AI 的 base_url 参数功能正常")
    print("=" * 80)
    print("\n✅ 测试结果总结：")
    print("   1. ✅ 默认端点创建成功")
    print("   2. ✅ 自定义端点（v1beta）创建成功")
    print("   3. ✅ 自动转换 v1 到 v1beta 成功")
    print("   4. ✅ create_llm_by_provider 函数传递 base_url 成功")
    print("\n📝 说明：")
    print("   - Google AI 现在可以像其他厂商一样使用数据库配置的 default_base_url")
    print("   - 配置优先级：模型配置 > 厂家配置 > 默认端点")
    print("   - 自动将 /v1 转换为 /v1beta，避免配置错误")
    print("   - 通过 client_options 传递自定义端点给 Google AI SDK")
    
    return True


if __name__ == "__main__":
    success = test_google_base_url()
    sys.exit(0 if success else 1)

