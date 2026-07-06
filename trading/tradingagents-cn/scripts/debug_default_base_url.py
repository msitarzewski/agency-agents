"""
调试脚本：检查为什么 default_base_url 没有生效
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from app.core.config import settings

def main():
    print("=" * 80)
    print("🔍 调试：检查 default_base_url 配置")
    print("=" * 80)
    
    # 连接数据库
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 1. 检查厂家配置
    print("\n📊 1. 检查厂家配置（llm_providers）")
    print("-" * 80)
    providers_collection = db.llm_providers
    providers = list(providers_collection.find({}))
    
    for provider in providers:
        print(f"\n厂家名称: {provider.get('name')}")
        print(f"  default_base_url: {provider.get('default_base_url', '未配置')}")
        print(f"  api_key: {'已配置' if provider.get('api_key') else '未配置'}")
    
    # 2. 检查系统配置中的模型配置
    print("\n\n📊 2. 检查系统配置中的模型配置（system_configs.llm_configs）")
    print("-" * 80)
    configs_collection = db.system_configs
    doc = configs_collection.find_one({"is_active": True}, sort=[("version", -1)])
    
    if doc and "llm_configs" in doc:
        llm_configs = doc["llm_configs"]
        print(f"\n找到 {len(llm_configs)} 个模型配置：\n")
        
        for config in llm_configs:
            model_name = config.get("model_name")
            provider = config.get("provider")
            api_base = config.get("api_base")
            enabled = config.get("enabled", False)
            
            print(f"模型: {model_name}")
            print(f"  厂家: {provider}")
            print(f"  api_base: {api_base if api_base else '未配置（将使用厂家的 default_base_url）'}")
            print(f"  启用状态: {'✅ 启用' if enabled else '❌ 禁用'}")
            print()
    else:
        print("⚠️ 未找到活跃的系统配置")
    
    # 3. 模拟查询过程
    print("\n📊 3. 模拟查询过程（以 qwen-turbo 为例）")
    print("-" * 80)
    
    model_name = "qwen-turbo"
    print(f"\n查询模型: {model_name}")
    
    # 步骤1：在 system_configs.llm_configs 中查找
    if doc and "llm_configs" in doc:
        found_in_configs = False
        for config in doc["llm_configs"]:
            if config.get("model_name") == model_name:
                found_in_configs = True
                provider = config.get("provider")
                api_base = config.get("api_base")
                
                print(f"\n✅ 在 system_configs.llm_configs 中找到模型配置")
                print(f"   厂家: {provider}")
                print(f"   api_base: {api_base}")
                
                if api_base:
                    print(f"\n🎯 结果: 使用模型配置的 api_base: {api_base}")
                    print(f"   ⚠️ 这就是为什么厂家的 default_base_url 没有生效！")
                else:
                    print(f"\n🔍 模型配置中没有 api_base，继续查询厂家配置...")
                    
                    # 步骤2：查询厂家的 default_base_url
                    provider_doc = providers_collection.find_one({"name": provider})
                    if provider_doc and provider_doc.get("default_base_url"):
                        print(f"✅ 找到厂家 {provider} 的 default_base_url: {provider_doc['default_base_url']}")
                        print(f"\n🎯 结果: 使用厂家的 default_base_url: {provider_doc['default_base_url']}")
                    else:
                        print(f"⚠️ 厂家 {provider} 没有配置 default_base_url")
                        print(f"\n🎯 结果: 使用硬编码的默认 URL")
                
                break
        
        if not found_in_configs:
            print(f"\n⚠️ 在 system_configs.llm_configs 中未找到模型 {model_name}")
            print(f"   将使用默认映射查找厂家...")
    
    # 4. 解决方案
    print("\n\n💡 解决方案")
    print("=" * 80)
    print("""
有两种方法可以让厂家的 default_base_url 生效：

方法1：清空模型配置中的 api_base 字段
--------------------------------------
如果模型配置（system_configs.llm_configs）中有 api_base 字段，
它的优先级高于厂家的 default_base_url。

解决方法：
1. 在"大模型配置"界面，编辑对应的模型
2. 清空"API地址"字段（或设置为空）
3. 保存配置

这样系统就会使用厂家的 default_base_url。

方法2：直接在模型配置中设置 api_base
--------------------------------------
如果您想为特定模型使用不同的 API 地址，
可以直接在模型配置中设置 api_base。

配置优先级：
1️⃣ 模型配置的 api_base（最高优先级）
2️⃣ 厂家配置的 default_base_url
3️⃣ 硬编码的默认 URL（最低优先级）
""")
    
    client.close()
    print("\n✅ 调试完成")

if __name__ == "__main__":
    main()

