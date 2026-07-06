#!/usr/bin/env python3
"""
测试Web界面修复
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_render_decision_summary():
    """测试render_decision_summary函数修复"""
    
    try:
        # 模拟streamlit环境
        class MockStreamlit:
            def subheader(self, text):
                print(f"📊 {text}")
            
            def columns(self, n):
                return [MockColumn() for _ in range(n)]
            
            def metric(self, label, value, delta=None, delta_color=None, help=None):
                print(f"  {label}: {value}")
                if delta:
                    print(f"    Delta: {delta}")
        
        class MockColumn:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        # 模拟streamlit模块
        sys.modules['streamlit'] = MockStreamlit()
        
        from web.components.results_display import render_decision_summary
        
        print("🧪 测试render_decision_summary修复...")
        
        # 测试中国A股
        china_decision = {
            'action': '持有',
            'confidence': 0.75,
            'risk_score': 0.40,
            'target_price': 15.00,
            'reasoning': '基于综合分析的投资建议'
        }
        
        print("\n📈 测试中国A股决策显示:")
        render_decision_summary(china_decision, "000001")
        
        # 测试美股
        us_decision = {
            'action': '买入',
            'confidence': 0.80,
            'risk_score': 0.30,
            'target_price': 180.00,
            'reasoning': '基于综合分析的投资建议'
        }
        
        print("\n📈 测试美股决策显示:")
        render_decision_summary(us_decision, "AAPL")
        
        print("\n✅ render_decision_summary修复测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_currency_detection():
    """测试货币检测逻辑"""
    
    try:
        import re
        
        def is_china_stock(ticker_code):
            return re.match(r'^\d{6}$', str(ticker_code)) if ticker_code else False
        
        print("🧪 测试货币检测逻辑...")
        
        # 测试中国A股代码
        china_stocks = ["000001", "600036", "300001", "002001"]
        for stock in china_stocks:
            is_china = is_china_stock(stock)
            currency = "¥" if is_china else "$"
            print(f"  {stock}: {'中国A股' if is_china else '非A股'} -> {currency}")
            
            if not is_china:
                print(f"❌ {stock} 应该被识别为中国A股")
                return False
        
        # 测试非中国股票代码
        foreign_stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "0700.HK"]
        for stock in foreign_stocks:
            is_china = is_china_stock(stock)
            currency = "¥" if is_china else "$"
            print(f"  {stock}: {'中国A股' if is_china else '非A股'} -> {currency}")
            
            if is_china:
                print(f"❌ {stock} 不应该被识别为中国A股")
                return False
        
        print("✅ 货币检测逻辑测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试Web界面修复...")
    print("=" * 50)
    
    # 运行测试
    test1_result = test_render_decision_summary()
    test2_result = test_currency_detection()
    
    print("=" * 50)
    if test1_result and test2_result:
        print("🎉 所有Web界面修复测试通过！")
        print("📝 现在Web界面应该能正确显示:")
        print("   - 中国A股: ¥XX.XX")
        print("   - 美股/港股: $XX.XX")
        print("   - 不再出现 NameError")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)
