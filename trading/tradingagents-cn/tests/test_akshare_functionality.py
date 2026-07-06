#!/usr/bin/env python3
"""
AKShare功能检查测试
检查当前分支中AKShare的可用性和功能完整性
"""

import sys
import os
import traceback
from typing import Dict, Any, List

def test_akshare_import():
    """测试AKShare库导入"""
    print("🔍 测试AKShare库导入...")
    try:
        import akshare as ak
        print(f"✅ AKShare导入成功，版本: {ak.__version__}")
        return True, ak
    except ImportError as e:
        print(f"❌ AKShare导入失败: {e}")
        return False, None

def test_data_source_manager():
    """测试数据源管理器中的AKShare支持"""
    print("\n🔍 测试数据源管理器...")
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
        
        # 检查AKShare是否在枚举中
        akshare_enum = ChinaDataSource.AKSHARE
        print(f"✅ AKShare枚举存在: {akshare_enum.value}")
        
        # 初始化数据源管理器
        manager = DataSourceManager()
        
        # 检查AKShare是否在可用数据源中
        available_sources = [s.value for s in manager.available_sources]
        if 'akshare' in available_sources:
            print("✅ AKShare在可用数据源列表中")
        else:
            print("⚠️ AKShare不在可用数据源列表中")
        
        return True, manager
    except Exception as e:
        print(f"❌ 数据源管理器测试失败: {e}")
        traceback.print_exc()
        return False, None

def test_akshare_adapter():
    """测试AKShare适配器"""
    print("\n🔍 测试AKShare适配器...")
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # 尝试获取AKShare适配器
        akshare_adapter = manager._get_akshare_adapter()
        
        if akshare_adapter is not None:
            print("✅ AKShare适配器获取成功")
            return True, akshare_adapter
        else:
            print("❌ AKShare适配器获取失败")
            return False, None
            
    except Exception as e:
        print(f"❌ AKShare适配器测试失败: {e}")
        traceback.print_exc()
        return False, None

def test_akshare_utils_file():
    """检查akshare_utils.py文件是否存在"""
    print("\n🔍 检查akshare_utils.py文件...")
    
    akshare_utils_path = "tradingagents/dataflows/akshare_utils.py"
    
    if os.path.exists(akshare_utils_path):
        print(f"✅ 找到AKShare工具文件: {akshare_utils_path}")
        
        try:
            from tradingagents.dataflows.akshare_utils import get_akshare_provider
            print("✅ get_akshare_provider函数导入成功")
            return True
        except ImportError as e:
            print(f"❌ 导入get_akshare_provider失败: {e}")
            return False
    else:
        print(f"❌ AKShare工具文件不存在: {akshare_utils_path}")
        return False

def test_akshare_basic_functionality():
    """测试AKShare基本功能"""
    print("\n🔍 测试AKShare基本功能...")
    
    success, ak = test_akshare_import()
    if not success:
        return False
    
    try:
        # 测试获取股票列表
        print("📊 测试获取A股股票列表...")
        stock_list = ak.stock_info_a_code_name()
        if stock_list is not None and not stock_list.empty:
            print(f"✅ 获取股票列表成功，共{len(stock_list)}只股票")
            print(f"   示例: {stock_list.head(3).to_dict('records')}")
        else:
            print("❌ 获取股票列表失败")
            return False
        
        # 测试获取股票历史数据
        print("\n📈 测试获取股票历史数据...")
        stock_data = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20241201", end_date="20241210", adjust="")
        if stock_data is not None and not stock_data.empty:
            print(f"✅ 获取股票数据成功，共{len(stock_data)}条记录")
            print(f"   最新数据: {stock_data.tail(1).to_dict('records')}")
        else:
            print("❌ 获取股票数据失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ AKShare基本功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_source_switching():
    """测试数据源切换功能"""
    print("\n🔍 测试数据源切换功能...")
    
    try:
        from tradingagents.dataflows.interface import switch_china_data_source
        
        # 尝试切换到AKShare
        result = switch_china_data_source("akshare")
        print(f"切换结果: {result}")
        
        if "成功" in result or "✅" in result:
            print("✅ 数据源切换到AKShare成功")
            return True
        else:
            print("❌ 数据源切换到AKShare失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据源切换测试失败: {e}")
        traceback.print_exc()
        return False

def test_unified_data_interface():
    """测试统一数据接口"""
    print("\n🔍 测试统一数据接口...")
    
    try:
        from tradingagents.dataflows.interface import get_china_stock_data_unified
        
        # 设置使用AKShare数据源
        from tradingagents.dataflows.interface import switch_china_data_source
        switch_china_data_source("akshare")
        
        # 测试获取股票数据
        data = get_china_stock_data_unified("000001", "2024-12-01", "2024-12-10")
        
        if data and "股票代码" in data:
            print("✅ 统一数据接口测试成功")
            print(f"   数据预览: {data[:200]}...")
            return True
        else:
            print("❌ 统一数据接口测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 统一数据接口测试失败: {e}")
        traceback.print_exc()
        return False

def create_missing_akshare_utils():
    """如果缺失，创建基本的akshare_utils.py文件"""
    print("\n🔧 检查是否需要创建akshare_utils.py...")
    
    akshare_utils_path = "tradingagents/dataflows/akshare_utils.py"
    
    if not os.path.exists(akshare_utils_path):
        print("📝 创建基本的akshare_utils.py文件...")
        
        akshare_utils_content = '''#!/usr/bin/env python3
"""
AKShare数据源工具
提供AKShare数据获取的统一接口
"""

import pandas as pd
from typing import Optional, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class AKShareProvider:
    """AKShare数据提供器"""
    
    def __init__(self):
        """初始化AKShare提供器"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True
            print("✅ AKShare初始化成功")
        except ImportError:
            self.ak = None
            self.connected = False
            print("❌ AKShare未安装")
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        if not self.connected:
            return None
        
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                symbol = symbol
            else:
                symbol = symbol.replace('.SZ', '').replace('.SS', '')
            
            # 获取数据
            data = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', '') if start_date else "20240101",
                end_date=end_date.replace('-', '') if end_date else "20241231",
                adjust=""
            )
            
            return data
            
        except Exception as e:
            print(f"❌ AKShare获取股票数据失败: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        if not self.connected:
            return {}
        
        try:
            # 获取股票基本信息
            stock_list = self.ak.stock_info_a_code_name()
            stock_info = stock_list[stock_list['code'] == symbol]
            
            if not stock_info.empty:
                return {
                    'symbol': symbol,
                    'name': stock_info.iloc[0]['name'],
                    'source': 'akshare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}
                
        except Exception as e:
            print(f"❌ AKShare获取股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

def get_akshare_provider() -> AKShareProvider:
    """获取AKShare提供器实例"""
    return AKShareProvider()
'''
        
        try:
            with open(akshare_utils_path, 'w', encoding='utf-8') as f:
                f.write(akshare_utils_content)
            print(f"✅ 创建akshare_utils.py成功: {akshare_utils_path}")
            return True
        except Exception as e:
            print(f"❌ 创建akshare_utils.py失败: {e}")
            return False
    else:
        print("✅ akshare_utils.py文件已存在")
        return True

def main():
    """主测试函数"""
    print("🔍 AKShare功能完整性检查")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 测试AKShare库导入
    test_results['akshare_import'] = test_akshare_import()[0]
    
    # 2. 检查akshare_utils.py文件
    test_results['akshare_utils_file'] = test_akshare_utils_file()
    
    # 3. 如果文件不存在，尝试创建
    if not test_results['akshare_utils_file']:
        test_results['create_akshare_utils'] = create_missing_akshare_utils()
    
    # 4. 测试数据源管理器
    test_results['data_source_manager'] = test_data_source_manager()[0]
    
    # 5. 测试AKShare适配器
    test_results['akshare_adapter'] = test_akshare_adapter()[0]
    
    # 6. 测试AKShare基本功能
    test_results['akshare_basic'] = test_akshare_basic_functionality()
    
    # 7. 测试数据源切换
    test_results['data_source_switching'] = test_data_source_switching()
    
    # 8. 测试统一数据接口
    test_results['unified_interface'] = test_unified_data_interface()
    
    # 总结结果
    print(f"\n📊 AKShare功能检查总结")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:25} {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 AKShare功能完全可用！")
    elif passed >= total * 0.7:
        print("⚠️ AKShare功能基本可用，但有部分问题需要修复")
    else:
        print("❌ AKShare功能存在严重问题，需要修复")
    
    return passed == total

if __name__ == "__main__":
    main()
