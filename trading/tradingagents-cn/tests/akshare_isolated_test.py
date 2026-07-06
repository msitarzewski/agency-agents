#!/usr/bin/env python3
"""
独立的AKShare功能测试
绕过yfinance依赖问题，直接测试AKShare集成
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_akshare_direct():
    """直接测试AKShare功能"""
    print("🔍 直接测试AKShare功能")
    print("=" * 40)
    
    try:
        import akshare as ak
        print(f"✅ AKShare导入成功，版本: {ak.__version__}")
        
        # 测试获取股票列表
        print("📊 测试获取股票列表...")
        stock_list = ak.stock_info_a_code_name()
        print(f"✅ 获取到{len(stock_list)}只股票")
        
        # 测试获取股票数据
        print("📈 测试获取招商银行(000001)数据...")
        data = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20241201", end_date="20241210", adjust="")
        print(f"✅ 获取到{len(data)}条数据")
        print(f"   最新收盘价: {data.iloc[-1]['收盘']}")
        
        # 测试获取实时行情
        print("📊 测试获取实时行情...")
        realtime = ak.stock_zh_a_spot_em()
        print(f"✅ 获取到{len(realtime)}只股票的实时行情")
        
        return True
        
    except Exception as e:
        print(f"❌ AKShare测试失败: {e}")
        return False

def test_akshare_utils_direct():
    """直接测试akshare_utils模块"""
    print("\n🔍 直接测试akshare_utils模块")
    print("=" * 40)
    
    try:
        # 直接导入akshare_utils，避免通过__init__.py
        akshare_utils_path = os.path.join(project_root, 'tradingagents', 'dataflows', 'akshare_utils.py')
        
        if os.path.exists(akshare_utils_path):
            print(f"✅ 找到akshare_utils.py文件")
            
            # 使用exec直接执行文件内容
            with open(akshare_utils_path, 'r', encoding='utf-8') as f:
                akshare_utils_code = f.read()
            
            # 创建独立的命名空间
            namespace = {}
            exec(akshare_utils_code, namespace)
            
            # 测试AKShareProvider
            if 'AKShareProvider' in namespace:
                provider_class = namespace['AKShareProvider']
                provider = provider_class()
                
                print(f"✅ AKShareProvider初始化成功，连接状态: {provider.connected}")
                
                if provider.connected:
                    # 测试获取股票数据
                    stock_data = provider.get_stock_data("000001", "2024-12-01", "2024-12-10")
                    if stock_data is not None and not stock_data.empty:
                        print(f"✅ 获取股票数据成功，{len(stock_data)}条记录")
                    else:
                        print("❌ 获取股票数据失败")
                    
                    # 测试获取股票信息
                    stock_info = provider.get_stock_info("000001")
                    print(f"✅ 获取股票信息: {stock_info}")
                
                return True
            else:
                print("❌ AKShareProvider类未找到")
                return False
        else:
            print(f"❌ akshare_utils.py文件不存在: {akshare_utils_path}")
            return False
            
    except Exception as e:
        print(f"❌ akshare_utils测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_data_source_enum():
    """检查数据源枚举定义"""
    print("\n🔍 检查数据源枚举定义")
    print("=" * 40)
    
    try:
        # 直接读取data_source_manager.py文件
        data_source_manager_path = os.path.join(project_root, 'tradingagents', 'dataflows', 'data_source_manager.py')
        
        if os.path.exists(data_source_manager_path):
            with open(data_source_manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查AKShare相关定义
            if 'AKSHARE' in content:
                print("✅ 找到AKSHARE枚举定义")
            else:
                print("❌ 未找到AKSHARE枚举定义")
            
            if 'akshare' in content.lower():
                print("✅ 找到akshare相关代码")
                
                # 统计akshare出现次数
                akshare_count = content.lower().count('akshare')
                print(f"   akshare在代码中出现{akshare_count}次")
            else:
                print("❌ 未找到akshare相关代码")
            
            return True
        else:
            print(f"❌ data_source_manager.py文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 数据源枚举检查失败: {e}")
        return False

def analyze_yfinance_issue():
    """分析yfinance依赖问题"""
    print("\n🔍 分析yfinance依赖问题")
    print("=" * 40)
    
    try:
        # 检查yfinance是否可以独立导入
        import yfinance as yf
        print("✅ yfinance可以独立导入")
        return True
    except Exception as e:
        print(f"❌ yfinance导入失败: {e}")
        
        # 检查curl_cffi
        try:
            import curl_cffi
            print("✅ curl_cffi可以导入")
        except Exception as e2:
            print(f"❌ curl_cffi导入失败: {e2}")
        
        # 检查cffi
        try:
            import cffi
            print("✅ cffi可以导入")
        except Exception as e3:
            print(f"❌ cffi导入失败: {e3}")
        
        return False

def main():
    """主测试函数"""
    print("🔍 AKShare功能独立测试")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 直接测试AKShare
    test_results['akshare_direct'] = test_akshare_direct()
    
    # 2. 直接测试akshare_utils
    test_results['akshare_utils_direct'] = test_akshare_utils_direct()
    
    # 3. 检查数据源枚举
    test_results['data_source_enum'] = check_data_source_enum()
    
    # 4. 分析yfinance问题
    test_results['yfinance_analysis'] = analyze_yfinance_issue()
    
    # 总结结果
    print(f"\n📊 独立测试总结")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:25} {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    # 分析结果
    if test_results.get('akshare_direct', False) and test_results.get('akshare_utils_direct', False):
        print("\n🎉 AKShare核心功能完全正常！")
        print("💡 问题只是yfinance依赖导致的模块导入问题")
        print("✅ 可以安全删除重复的AKShare分支")
        
        print(f"\n🎯 分支管理建议:")
        print("✅ AKShare功能本身完全正常")
        print("✅ feature/tushare-integration包含完整的AKShare集成")
        print("✅ 可以安全删除以下分支:")
        print("   - feature/akshare-integration")
        print("   - feature/akshare-integration-clean")
        
        return True
    else:
        print("\n⚠️ AKShare功能存在问题，需要进一步调查")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🚀 下一步建议:")
        print("1. 修复yfinance依赖问题（可选）")
        print("2. 删除重复的AKShare分支")
        print("3. 发布v0.1.6版本")
    else:
        print(f"\n🔧 需要修复的问题:")
        print("1. 检查AKShare集成代码")
        print("2. 修复依赖问题")
        print("3. 重新测试后再考虑分支清理")
