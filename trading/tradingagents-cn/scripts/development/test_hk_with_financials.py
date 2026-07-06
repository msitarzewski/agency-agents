"""
测试港股数据接口（包含财务指标和 PE、PB 计算）

测试目标：
1. 测试财务指标获取功能
2. 测试历史数据中的 PE、PB 计算
3. 验证数据完整性
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def test_financial_indicators():
    """测试财务指标获取"""
    print("=" * 80)
    print("测试 1: 港股财务指标获取")
    print("=" * 80)
    
    test_symbols = ["00005", "00700", "01810"]  # 汇丰控股、腾讯、小米
    
    try:
        from tradingagents.dataflows.providers.hk.improved_hk import get_hk_financial_indicators
        
        for symbol in test_symbols:
            print(f"\n📊 测试股票: {symbol}")
            
            try:
                indicators = get_hk_financial_indicators(symbol)
                
                if indicators:
                    print(f"   ✅ 成功获取财务指标")
                    print(f"   📅 报告期: {indicators.get('report_date')}")
                    print(f"   📈 关键指标:")
                    print(f"      - EPS (基本): {indicators.get('eps_basic'):.2f} 港元")
                    print(f"      - EPS (TTM): {indicators.get('eps_ttm'):.2f} 港元")
                    print(f"      - BPS: {indicators.get('bps'):.2f} 港元")
                    print(f"      - ROE: {indicators.get('roe_avg'):.2f}%")
                    print(f"      - ROA: {indicators.get('roa'):.2f}%")
                    print(f"      - 营业收入: {indicators.get('operate_income') / 1e8:.2f} 亿港元")
                    print(f"      - 营收同比: {indicators.get('operate_income_yoy'):.2f}%")
                    print(f"      - 资产负债率: {indicators.get('debt_asset_ratio'):.2f}%")
                else:
                    print(f"   ⚠️ 未获取到财务指标")
                    
            except Exception as e:
                print(f"   ❌ 获取失败: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_historical_data_with_pe_pb():
    """测试历史数据（包含 PE、PB 计算）"""
    print("\n" + "=" * 80)
    print("测试 2: 港股历史数据（包含 PE、PB）")
    print("=" * 80)
    
    test_symbol = "00005"  # 汇丰控股
    
    try:
        from tradingagents.dataflows.providers.hk.improved_hk import get_hk_stock_data_akshare
        from datetime import datetime, timedelta
        
        # 获取最近30天数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"\n📊 测试股票: {test_symbol}")
        print(f"📅 日期范围: {start_date} ~ {end_date}")
        
        result = get_hk_stock_data_akshare(test_symbol, start_date, end_date)
        
        print(f"\n✅ 数据获取成功")
        print(f"\n{'='*80}")
        print("返回数据预览（前2000字符）:")
        print(f"{'='*80}")
        print(result[:2000])
        print(f"\n... (总长度: {len(result)} 字符)")
        
        # 检查是否包含 PE、PB 信息
        if 'PE (市盈率)' in result:
            print(f"\n✅ 包含 PE (市盈率) 信息")
        else:
            print(f"\n⚠️ 未找到 PE (市盈率) 信息")
        
        if 'PB (市净率)' in result:
            print(f"✅ 包含 PB (市净率) 信息")
        else:
            print(f"⚠️ 未找到 PB (市净率) 信息")
        
        if '财务指标' in result:
            print(f"✅ 包含财务指标部分")
        else:
            print(f"⚠️ 未找到财务指标部分")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_pe_pb_calculation():
    """测试 PE、PB 计算准确性"""
    print("\n" + "=" * 80)
    print("测试 3: PE、PB 计算准确性验证")
    print("=" * 80)
    
    test_symbol = "00700"  # 腾讯控股
    
    try:
        from tradingagents.dataflows.providers.hk.improved_hk import (
            get_hk_financial_indicators,
            get_hk_stock_data_akshare
        )
        from datetime import datetime, timedelta
        import re
        
        print(f"\n📊 测试股票: {test_symbol} (腾讯控股)")
        
        # 1. 获取财务指标
        print(f"\n1️⃣ 获取财务指标:")
        indicators = get_hk_financial_indicators(test_symbol)
        
        if not indicators:
            print(f"   ❌ 未获取到财务指标")
            return
        
        eps_ttm = indicators.get('eps_ttm')
        bps = indicators.get('bps')
        
        print(f"   ✅ EPS_TTM: {eps_ttm:.2f} 港元")
        print(f"   ✅ BPS: {bps:.2f} 港元")
        
        # 2. 获取历史数据
        print(f"\n2️⃣ 获取历史数据:")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        result = get_hk_stock_data_akshare(test_symbol, start_date, end_date)
        
        # 3. 提取当前价格
        price_match = re.search(r'最新价: HK\$(\d+\.?\d*)', result)
        if price_match:
            current_price = float(price_match.group(1))
            print(f"   ✅ 当前价格: {current_price:.2f} 港元")
        else:
            print(f"   ❌ 未找到当前价格")
            return
        
        # 4. 提取 PE、PB
        pe_match = re.search(r'PE \(市盈率\): (\d+\.?\d*)', result)
        pb_match = re.search(r'PB \(市净率\): (\d+\.?\d*)', result)
        
        if pe_match:
            pe_from_result = float(pe_match.group(1))
            print(f"   ✅ 报告中的 PE: {pe_from_result:.2f}")
        else:
            print(f"   ⚠️ 未找到 PE 数据")
            pe_from_result = None
        
        if pb_match:
            pb_from_result = float(pb_match.group(1))
            print(f"   ✅ 报告中的 PB: {pb_from_result:.2f}")
        else:
            print(f"   ⚠️ 未找到 PB 数据")
            pb_from_result = None
        
        # 5. 手动计算验证
        print(f"\n3️⃣ 手动计算验证:")
        
        if eps_ttm and eps_ttm > 0:
            pe_calculated = current_price / eps_ttm
            print(f"   计算的 PE: {pe_calculated:.2f} (= {current_price:.2f} / {eps_ttm:.2f})")
            
            if pe_from_result:
                diff = abs(pe_calculated - pe_from_result)
                if diff < 0.01:
                    print(f"   ✅ PE 计算正确！(误差: {diff:.4f})")
                else:
                    print(f"   ⚠️ PE 计算有误差: {diff:.2f}")
        
        if bps and bps > 0:
            pb_calculated = current_price / bps
            print(f"   计算的 PB: {pb_calculated:.2f} (= {current_price:.2f} / {bps:.2f})")
            
            if pb_from_result:
                diff = abs(pb_calculated - pb_from_result)
                if diff < 0.01:
                    print(f"   ✅ PB 计算正确！(误差: {diff:.4f})")
                else:
                    print(f"   ⚠️ PB 计算有误差: {diff:.2f}")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("港股数据接口测试（包含财务指标和 PE、PB）")
    print("=" * 80)
    
    # 测试 1: 财务指标获取
    test_financial_indicators()
    
    # 测试 2: 历史数据（包含 PE、PB）
    test_historical_data_with_pe_pb()
    
    # 测试 3: PE、PB 计算准确性
    test_pe_pb_calculation()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

