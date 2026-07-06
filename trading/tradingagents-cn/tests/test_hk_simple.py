"""
简单的港股功能测试
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_basic():
    """基本测试"""
    print("🧪 开始基本港股功能测试...")
    
    try:
        # 测试股票工具类
        from tradingagents.utils.stock_utils import StockUtils
        
        # 测试港股代码识别
        test_cases = [
            "0700.HK",  # 腾讯
            "9988.HK",  # 阿里巴巴
            "3690.HK",  # 美团
            "000001",   # 平安银行
            "AAPL"      # 苹果
        ]
        
        for ticker in test_cases:
            market_info = StockUtils.get_market_info(ticker)
            print(f"  {ticker}: {market_info['market_name']} ({market_info['currency_name']} {market_info['currency_symbol']})")
        
        print("✅ 基本测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic()
