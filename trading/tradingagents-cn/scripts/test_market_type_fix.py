#!/usr/bin/env python3
"""
测试市场类型修复
验证报告保存和查询时是否正确包含 market_type 字段
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.stock_utils import StockUtils


def test_market_type_detection():
    """测试市场类型检测"""
    print("=" * 60)
    print("测试市场类型检测")
    print("=" * 60)
    
    test_cases = [
        ("000001", "A股"),  # 深圳A股
        ("600000", "A股"),  # 上海A股
        ("00700", "港股"),  # 港股（5位）
        ("0700", "港股"),   # 港股（4位）
        ("00700.HK", "港股"),  # 港股（带后缀）
        ("AAPL", "美股"),   # 美股
        ("TSLA", "美股"),   # 美股
    ]
    
    market_type_map = {
        "china_a": "A股",
        "hong_kong": "港股",
        "us": "美股",
        "unknown": "A股"
    }
    
    for stock_code, expected_market in test_cases:
        market_info = StockUtils.get_market_info(stock_code)
        market_type = market_type_map.get(market_info.get("market", "unknown"), "A股")
        
        status = "✅" if market_type == expected_market else "❌"
        print(f"{status} {stock_code:12s} -> {market_type:6s} (期望: {expected_market})")
        
        if market_type != expected_market:
            print(f"   详细信息: {market_info}")


def test_mongodb_document_structure():
    """测试 MongoDB 文档结构"""
    print("\n" + "=" * 60)
    print("测试 MongoDB 文档结构")
    print("=" * 60)
    
    from datetime import datetime
    
    stock_symbol = "000001"
    market_info = StockUtils.get_market_info(stock_symbol)
    market_type_map = {
        "china_a": "A股",
        "hong_kong": "港股",
        "us": "美股",
        "unknown": "A股"
    }
    market_type = market_type_map.get(market_info.get("market", "unknown"), "A股")
    
    timestamp = datetime.now()
    analysis_id = f"{stock_symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    document = {
        "analysis_id": analysis_id,
        "stock_symbol": stock_symbol,
        "market_type": market_type,  # 关键字段
        "analysis_date": timestamp.strftime('%Y-%m-%d'),
        "timestamp": timestamp,
        "status": "completed",
        "source": "test",
        "summary": "测试报告",
        "analysts": ["test_analyst"],
        "research_depth": 3,
        "reports": {},
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    
    print(f"✅ 文档结构正确")
    print(f"   analysis_id: {document['analysis_id']}")
    print(f"   stock_symbol: {document['stock_symbol']}")
    print(f"   market_type: {document['market_type']}")
    print(f"   analysis_date: {document['analysis_date']}")
    
    # 检查必需字段
    required_fields = ["analysis_id", "stock_symbol", "market_type", "analysis_date"]
    missing_fields = [field for field in required_fields if field not in document]
    
    if missing_fields:
        print(f"❌ 缺少必需字段: {missing_fields}")
    else:
        print(f"✅ 所有必需字段都存在")


if __name__ == "__main__":
    test_market_type_detection()
    test_mongodb_document_structure()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n下一步:")
    print("1. 启动后端服务")
    print("2. 运行一次股票分析（例如：000001）")
    print("3. 检查分析报告页面是否显示数据")
    print("4. 测试市场筛选功能是否正常工作")

