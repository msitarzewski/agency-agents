#!/usr/bin/env python3
"""
修复版AKShare功能检查
添加路径设置以解决模块导入问题
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_akshare_import():
    """检查AKShare导入"""
    try:
        import akshare as ak
        print(f"✅ AKShare导入成功，版本: {ak.__version__}")
        return True
    except ImportError as e:
        print(f"❌ AKShare导入失败: {e}")
        return False

def check_akshare_utils():
    """检查akshare_utils.py"""
    try:
        from tradingagents.dataflows.akshare_utils import get_akshare_provider
        provider = get_akshare_provider()
        print(f"✅ AKShare工具模块正常，连接状态: {provider.connected}")
        return True, provider
    except Exception as e:
        print(f"❌ AKShare工具模块异常: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def check_data_source_manager():
    """检查数据源管理器"""
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
        
        # 检查AKShare枚举
        akshare_enum = ChinaDataSource.AKSHARE
        print(f"✅ AKShare枚举: {akshare_enum.value}")
        
        # 初始化管理器
        manager = DataSourceManager()
        
        # 检查可用数据源
        available = [s.value for s in manager.available_sources]
        if 'akshare' in available:
            print("✅ AKShare在可用数据源中")
        else:
            print("⚠️ AKShare不在可用数据源中")
        
        return True, manager
    except Exception as e:
        print(f"❌ 数据源管理器检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_akshare_adapter():
    """测试AKShare适配器"""
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # 获取AKShare适配器
        akshare_adapter = manager._get_akshare_adapter()
        
        if akshare_adapter is not None:
            print("✅ AKShare适配器获取成功")
            
            # 测试获取股票数据
            test_data = akshare_adapter.get_stock_data("000001", "2024-12-01", "2024-12-10")
            if test_data is not None and not test_data.empty:
                print(f"✅ AKShare适配器数据获取成功，{len(test_data)}条记录")
                return True
            else:
                print("❌ AKShare适配器数据获取失败")
                return False
        else:
            print("❌ AKShare适配器获取失败")
            return False
            
    except Exception as e:
        print(f"❌ AKShare适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_source_switching():
    """测试数据源切换"""
    try:
        from tradingagents.dataflows.interface import switch_china_data_source
        
        # 切换到AKShare
        result = switch_china_data_source("akshare")
        print(f"数据源切换结果: {result}")
        
        if "成功" in result or "✅" in result or "akshare" in result.lower():
            print("✅ 数据源切换到AKShare成功")
            return True
        else:
            print("❌ 数据源切换到AKShare失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据源切换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_interface():
    """测试统一数据接口"""
    try:
        from tradingagents.dataflows.interface import get_china_stock_data_unified, switch_china_data_source
        
        # 先切换到AKShare
        switch_china_data_source("akshare")
        
        # 测试获取数据
        data = get_china_stock_data_unified("000001", "2024-12-01", "2024-12-10")
        
        if data and len(data) > 100:  # 假设返回的是字符串格式的数据
            print("✅ 统一数据接口测试成功")
            print(f"   数据长度: {len(data)} 字符")
            return True
        else:
            print("❌ 统一数据接口测试失败")
            print(f"   返回数据: {data}")
            return False
            
    except Exception as e:
        print(f"❌ 统一数据接口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_akshare():
    """测试基本AKShare功能"""
    try:
        import akshare as ak
        
        # 测试获取股票列表
        print("📊 测试获取股票列表...")
        stock_list = ak.stock_info_a_code_name()
        print(f"✅ 获取到{len(stock_list)}只股票")
        
        # 测试获取股票数据
        print("📈 测试获取股票数据...")
        data = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20241201", end_date="20241210", adjust="")
        print(f"✅ 获取到{len(data)}条数据")
        
        return True
    except Exception as e:
        print(f"❌ AKShare基本功能测试失败: {e}")
        return False

def main():
    """主检查函数"""
    print("🔍 AKShare功能完整检查（修复版）")
    print("=" * 50)
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path[0]}")
    print("=" * 50)
    
    test_results = {}
    
    # 1. 基本AKShare功能
    print("\n1️⃣ 基本AKShare功能测试")
    test_results['basic_akshare'] = test_basic_akshare()
    
    # 2. AKShare工具模块
    print("\n2️⃣ AKShare工具模块测试")
    success, provider = check_akshare_utils()
    test_results['akshare_utils'] = success
    
    # 3. 数据源管理器
    print("\n3️⃣ 数据源管理器测试")
    success, manager = check_data_source_manager()
    test_results['data_source_manager'] = success
    
    # 4. AKShare适配器
    print("\n4️⃣ AKShare适配器测试")
    test_results['akshare_adapter'] = test_akshare_adapter()
    
    # 5. 数据源切换
    print("\n5️⃣ 数据源切换测试")
    test_results['data_source_switching'] = test_data_source_switching()
    
    # 6. 统一数据接口
    print("\n6️⃣ 统一数据接口测试")
    test_results['unified_interface'] = test_unified_interface()
    
    # 总结结果
    print(f"\n📊 AKShare功能检查总结")
    print("=" * 50)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:25} {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 AKShare功能完全可用！")
        print("💡 可以安全删除重复的AKShare分支")
    elif passed >= total * 0.7:
        print("⚠️ AKShare功能基本可用，但有部分问题")
        print("💡 建议修复问题后再删除重复分支")
    else:
        print("❌ AKShare功能存在严重问题")
        print("💡 不建议删除AKShare分支，需要先修复问题")
    
    return passed >= total * 0.7

if __name__ == "__main__":
    success = main()
    
    print(f"\n🎯 分支管理建议:")
    if success:
        print("✅ AKShare功能基本正常，可以考虑删除重复分支")
        print("   - feature/akshare-integration")
        print("   - feature/akshare-integration-clean")
        print("   - 保留 feature/tushare-integration（包含完整功能）")
    else:
        print("⚠️ 建议先修复AKShare功能问题，再考虑分支清理")
