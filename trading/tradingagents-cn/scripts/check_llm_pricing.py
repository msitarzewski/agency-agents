"""检查数据库中的 LLM 定价配置"""
import asyncio
from app.core.database import init_database, get_mongo_db


async def check_pricing():
    """检查定价配置"""
    # 初始化数据库连接
    await init_database()

    db = get_mongo_db()
    
    # 获取最新的激活配置
    config = await db['system_configs'].find_one(
        {'is_active': True},
        sort=[('version', -1)]
    )
    
    if not config:
        print("❌ 未找到激活的配置")
        return
    
    print(f"📊 配置版本: {config.get('version')}")
    print(f"📊 LLM配置数量: {len(config.get('llm_configs', []))}")
    print("\n" + "="*80)
    print("LLM 定价配置:")
    print("="*80)
    
    for llm in config.get('llm_configs', []):
        provider = llm.get('provider')
        model_name = llm.get('model_name')
        input_price = llm.get('input_price_per_1k', 0)
        output_price = llm.get('output_price_per_1k', 0)
        enabled = llm.get('enabled', False)
        
        status = "✅" if enabled else "❌"
        print(f"{status} {provider}/{model_name}")
        print(f"   输入价格: ¥{input_price}/1k tokens")
        print(f"   输出价格: ¥{output_price}/1k tokens")
        print()


if __name__ == "__main__":
    asyncio.run(check_pricing())

