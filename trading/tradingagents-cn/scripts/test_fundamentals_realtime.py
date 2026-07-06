"""
测试基本面接口是否使用实时市值计算PS
"""
import asyncio
from app.core.database import get_mongo_db
from app.routers.stocks import get_fundamentals


async def test():
    """测试基本面数据"""
    code = "688146"
    
    # 模拟用户认证
    mock_user = {"username": "test"}
    
    # 调用基本面接口
    result = await get_fundamentals(code, mock_user)
    
    if result.get("success"):
        data = result["data"]
        print("=" * 60)
        print("📊 基本面数据测试")
        print("=" * 60)
        print(f"股票代码: {data.get('code')}")
        print(f"股票名称: {data.get('name')}")
        print(f"行业: {data.get('industry')}")
        print()
        print("--- 估值指标 ---")
        print(f"PE(TTM): {data.get('pe_ttm')}")
        print(f"PB: {data.get('pb')}")
        print(f"PS(TTM): {data.get('ps_ttm')}")
        print()
        print("--- 市值信息 ---")
        print(f"总市值: {data.get('total_mv')}亿元")
        print(f"流通市值: {data.get('circ_mv')}亿元")
        print(f"市值是否实时: {data.get('mv_is_realtime')}")
        print()
        print("--- 数据来源 ---")
        print(f"PE数据来源: {data.get('pe_source')}")
        print(f"PE是否实时: {data.get('pe_is_realtime')}")
        print(f"更新时间: {data.get('pe_updated_at')}")
        print()
        print("--- 财务指标 ---")
        print(f"ROE: {data.get('roe')}")
        print(f"负债率: {data.get('debt_ratio')}")
        print("=" * 60)
    else:
        print(f"❌ 获取基本面数据失败: {result.get('message')}")


if __name__ == "__main__":
    asyncio.run(test())

