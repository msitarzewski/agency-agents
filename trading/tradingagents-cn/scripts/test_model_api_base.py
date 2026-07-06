"""
测试脚本：验证模型级别的 API 基础 URL 是否生效
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    print("=" * 80)
    print("🧪 测试：验证模型级别的 API 基础 URL 配置")
    print("=" * 80)
    
    from pymongo import MongoClient
    from app.core.config import settings
    from app.services.simple_analysis_service import get_provider_and_url_by_model_sync
    
    # 连接数据库
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 1. 查看当前数据库中的配置
    print("\n📊 1. 查看数据库中的配置")
    print("-" * 80)
    
    configs_collection = db.system_configs
    doc = configs_collection.find_one({"is_active": True}, sort=[("version", -1)])
    
    if doc and "llm_configs" in doc:
        llm_configs = doc["llm_configs"]
        
        print(f"\n找到 {len(llm_configs)} 个模型配置：\n")
        
        for i, config in enumerate(llm_configs, 1):
            model_name = config.get("model_name", "未知")
            provider = config.get("provider", "未知")
            api_base = config.get("api_base", "")
            display_name = config.get("display_name", "")
            
            print(f"{i}. 模型: {model_name}")
            print(f"   显示名称: {display_name}")
            print(f"   供应商: {provider}")
            print(f"   API基础URL: {api_base if api_base else '(未配置，使用厂家默认)'}")
            print()
    else:
        print("❌ 未找到活跃的系统配置")
        client.close()
        return
    
    # 2. 查看厂家的默认 URL
    print("\n📊 2. 查看厂家的默认 URL")
    print("-" * 80)
    
    providers_collection = db.llm_providers
    providers = list(providers_collection.find())
    
    print(f"\n找到 {len(providers)} 个厂家配置：\n")
    
    for provider in providers:
        name = provider.get("name", "未知")
        default_base_url = provider.get("default_base_url", "")
        
        print(f"厂家: {name}")
        print(f"  默认URL: {default_base_url if default_base_url else '(未配置)'}")
        print()
    
    # 3. 测试配置优先级
    print("\n📊 3. 测试配置优先级")
    print("-" * 80)
    
    # 找一个配置了 api_base 的模型
    model_with_api_base = None
    model_without_api_base = None
    
    for config in llm_configs:
        if config.get("api_base"):
            model_with_api_base = config.get("model_name")
        elif not model_without_api_base:
            model_without_api_base = config.get("model_name")
    
    # 测试有 api_base 的模型
    if model_with_api_base:
        print(f"\n✅ 测试有 API基础URL 的模型: {model_with_api_base}")
        print("-" * 40)
        
        # 获取期望的 URL
        expected_url = None
        for config in llm_configs:
            if config.get("model_name") == model_with_api_base:
                expected_url = config.get("api_base")
                break
        
        # 调用函数获取实际 URL
        result = get_provider_and_url_by_model_sync(model_with_api_base)
        actual_url = result.get("backend_url")
        
        print(f"期望的 URL: {expected_url}")
        print(f"实际的 URL: {actual_url}")
        
        if actual_url == expected_url:
            print(f"🎯 ✅ 正确！模型级别的 API基础URL 已生效")
        else:
            print(f"❌ 错误！URL 不匹配")
    else:
        print("\n⚠️ 没有找到配置了 API基础URL 的模型")
    
    # 测试没有 api_base 的模型
    if model_without_api_base:
        print(f"\n✅ 测试没有 API基础URL 的模型: {model_without_api_base}")
        print("-" * 40)
        
        # 获取期望的 URL（应该是厂家的 default_base_url）
        provider = None
        for config in llm_configs:
            if config.get("model_name") == model_without_api_base:
                provider = config.get("provider")
                break
        
        expected_url = None
        if provider:
            provider_doc = providers_collection.find_one({"name": provider})
            if provider_doc:
                expected_url = provider_doc.get("default_base_url")
        
        # 调用函数获取实际 URL
        result = get_provider_and_url_by_model_sync(model_without_api_base)
        actual_url = result.get("backend_url")
        
        print(f"供应商: {provider}")
        print(f"期望的 URL (厂家默认): {expected_url}")
        print(f"实际的 URL: {actual_url}")
        
        if actual_url == expected_url:
            print(f"🎯 ✅ 正确！使用了厂家的默认 URL")
        else:
            print(f"⚠️ URL 不匹配（可能使用了硬编码的默认值）")
    
    # 4. 模拟添加一个测试模型配置
    print("\n\n📊 4. 模拟测试：添加一个带有自定义 API基础URL 的模型")
    print("-" * 80)
    
    test_model_name = "qwen-test-custom-url"
    test_api_base = "https://test-custom-api.example.com/v1"
    
    print(f"\n添加测试模型配置：")
    print(f"  模型名称: {test_model_name}")
    print(f"  供应商: dashscope")
    print(f"  API基础URL: {test_api_base}")
    
    # 添加到数据库
    if doc:
        llm_configs.append({
            "model_name": test_model_name,
            "display_name": "测试模型 - 自定义URL",
            "provider": "dashscope",
            "api_base": test_api_base,
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60,
            "retry_times": 3,
            "enabled": True
        })
        
        configs_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"llm_configs": llm_configs}}
        )
        
        print(f"\n✅ 测试模型已添加到数据库")
        
        # 测试查询
        print(f"\n测试查询...")
        result = get_provider_and_url_by_model_sync(test_model_name)
        actual_url = result.get("backend_url")
        
        print(f"期望的 URL: {test_api_base}")
        print(f"实际的 URL: {actual_url}")
        
        if actual_url == test_api_base:
            print(f"\n🎯 ✅ 完美！模型级别的 API基础URL 功能正常工作")
        else:
            print(f"\n❌ 错误！URL 不匹配")
        
        # 清理测试数据
        print(f"\n清理测试数据...")
        llm_configs = [c for c in llm_configs if c.get("model_name") != test_model_name]
        configs_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"llm_configs": llm_configs}}
        )
        print(f"✅ 测试数据已清理")
    
    client.close()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    
    print("\n💡 总结：")
    print("配置优先级（从高到低）：")
    print("  1️⃣ 模型级别的 API基础URL (system_configs.llm_configs[].api_base)")
    print("  2️⃣ 厂家级别的 默认API地址 (llm_providers.default_base_url)")
    print("  3️⃣ 硬编码的默认值")
    print("\n如果你在界面上配置了模型的 API基础URL，它会优先于厂家的默认URL。")

if __name__ == "__main__":
    main()

