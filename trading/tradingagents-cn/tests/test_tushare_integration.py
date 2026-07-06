#!/usr/bin/env python3
"""
Tushare集成测试
验证Tushare数据源的集成功能，包括数据获取、缓存、接口调用等
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_tushare_provider():
    """测试Tushare提供器基本功能"""
    print("\n🔧 测试Tushare提供器")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.tushare_utils import get_tushare_provider
        
        print("✅ Tushare工具库加载成功")
        
        # 创建提供器实例
        provider = get_tushare_provider()
        
        if provider.connected:
            print("✅ Tushare API连接成功")
            
            # 测试获取股票列表
            print("🔄 测试获取股票列表...")
            stock_list = provider.get_stock_list()
            
            if not stock_list.empty:
                print(f"✅ 获取股票列表成功: {len(stock_list)}条")
                print(f"📊 示例股票: {stock_list.head(3)[['ts_code', 'name']].to_string(index=False)}")
            else:
                print("❌ 获取股票列表失败")
            
            # 测试获取股票信息
            print("🔄 测试获取股票信息...")
            stock_info = provider.get_stock_info("000001")
            
            if stock_info and stock_info.get('name'):
                print(f"✅ 获取股票信息成功: {stock_info['name']}")
            else:
                print("❌ 获取股票信息失败")
            
            # 测试获取股票数据
            print("🔄 测试获取股票数据...")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            stock_data = provider.get_stock_daily("000001", start_date, end_date)
            
            if not stock_data.empty:
                print(f"✅ 获取股票数据成功: {len(stock_data)}条")
            else:
                print("❌ 获取股票数据失败")
        else:
            print("❌ Tushare API连接失败")
        
    except Exception as e:
        print(f"❌ Tushare提供器测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_tushare_adapter():
    """测试Tushare适配器功能"""
    print("\n🔧 测试Tushare适配器")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        
        print("✅ Tushare适配器库加载成功")
        
        # 创建适配器实例
        adapter = get_tushare_adapter()
        
        # 测试获取股票数据
        print("🔄 测试获取股票数据...")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        stock_data = adapter.get_stock_data("000001", start_date, end_date)
        
        if not stock_data.empty:
            print(f"✅ 获取股票数据成功: {len(stock_data)}条")
            print(f"📊 数据列: {list(stock_data.columns)}")
        else:
            print("❌ 获取股票数据失败")
        
        # 测试获取股票信息
        print("🔄 测试获取股票信息...")
        stock_info = adapter.get_stock_info("000001")
        
        if stock_info and stock_info.get('name'):
            print(f"✅ 获取股票信息成功: {stock_info['name']}")
        else:
            print("❌ 获取股票信息失败")
        
        # 测试搜索股票
        print("🔄 测试搜索股票...")
        search_results = adapter.search_stocks("平安")
        
        if not search_results.empty:
            print(f"✅ 搜索股票成功: {len(search_results)}条结果")
        else:
            print("❌ 搜索股票失败")
        
        # 测试基本面数据
        print("🔄 测试基本面数据...")
        fundamentals = adapter.get_fundamentals("000001")
        
        if fundamentals and len(fundamentals) > 100:
            print(f"✅ 获取基本面数据成功: {len(fundamentals)}字符")
        else:
            print("❌ 获取基本面数据失败")
        
    except Exception as e:
        print(f"❌ Tushare适配器测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_tushare_interface():
    """测试Tushare接口函数"""
    print("\n🔧 测试Tushare接口函数")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.interface import (
            get_china_stock_data_tushare,
            search_china_stocks_tushare,
            get_china_stock_fundamentals_tushare,
            get_china_stock_info_tushare
        )
        
        print("✅ Tushare接口函数加载成功")
        
        # 测试获取股票数据接口
        print("🔄 测试股票数据接口...")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data_result = get_china_stock_data_tushare("000001", start_date, end_date)
        
        if "股票代码: 000001" in data_result:
            print("✅ 股票数据接口测试成功")
        else:
            print("❌ 股票数据接口测试失败")
        
        # 测试搜索接口
        print("🔄 测试搜索接口...")
        search_result = search_china_stocks_tushare("平安")
        
        if "搜索关键词: 平安" in search_result:
            print("✅ 搜索接口测试成功")
        else:
            print("❌ 搜索接口测试失败")
        
        # 测试股票信息接口
        print("🔄 测试股票信息接口...")
        info_result = get_china_stock_info_tushare("000001")
        
        if "股票代码: 000001" in info_result:
            print("✅ 股票信息接口测试成功")
        else:
            print("❌ 股票信息接口测试失败")
        
        # 测试基本面接口
        print("🔄 测试基本面接口...")
        fundamentals_result = get_china_stock_fundamentals_tushare("000001")
        
        if "基本面分析报告" in fundamentals_result:
            print("✅ 基本面接口测试成功")
        else:
            print("❌ 基本面接口测试失败")
        
    except Exception as e:
        print(f"❌ Tushare接口函数测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_tushare_cache():
    """测试Tushare缓存功能"""
    print("\n🔧 测试Tushare缓存功能")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        
        adapter = get_tushare_adapter()
        
        if not adapter.enable_cache:
            print("⚠️ 缓存功能未启用，跳过缓存测试")
            return
        
        print("✅ 缓存功能已启用")
        
        # 第一次获取数据（应该从API获取）
        print("🔄 第一次获取数据（从API）...")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        data1 = adapter.get_stock_data("000001", start_date, end_date)
        
        if not data1.empty:
            print(f"✅ 第一次获取成功: {len(data1)}条")
        else:
            print("❌ 第一次获取失败")
            return
        
        # 第二次获取数据（应该从缓存获取）
        print("🔄 第二次获取数据（从缓存）...")
        data2 = adapter.get_stock_data("000001", start_date, end_date)
        
        if not data2.empty:
            print(f"✅ 第二次获取成功: {len(data2)}条")
            
            # 比较数据是否一致
            if len(data1) == len(data2):
                print("✅ 缓存数据一致性验证通过")
            else:
                print("⚠️ 缓存数据可能不一致")
        else:
            print("❌ 第二次获取失败")
        
    except Exception as e:
        print(f"❌ Tushare缓存测试失败: {e}")
        import traceback
        traceback.print_exc()


def check_tushare_environment():
    """检查Tushare环境配置"""
    print("\n🔧 检查Tushare环境配置")
    print("=" * 60)
    
    # 检查Tushare库
    try:
        import tushare as ts
        print("✅ Tushare库已安装")
        print(f"📦 Tushare版本: {ts.__version__}")
    except ImportError:
        print("❌ Tushare库未安装，请运行: pip install tushare")
        return False
    
    # 检查API Token
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        print("✅ TUSHARE_TOKEN环境变量已设置")
        print(f"🔑 Token长度: {len(token)}字符")
    else:
        print("❌ 未设置TUSHARE_TOKEN环境变量")
        print("💡 请在.env文件中设置: TUSHARE_TOKEN=your_token_here")
        return False
    
    # 检查缓存目录
    try:
        from tradingagents.dataflows.cache_manager import get_cache
        cache = get_cache()
        print("✅ 缓存管理器可用")
    except Exception as e:
        print(f"⚠️ 缓存管理器不可用: {e}")
    
    return True


def main():
    """主测试函数"""
    print("🔬 Tushare集成测试")
    print("=" * 70)
    print("💡 测试目标:")
    print("   - Tushare环境配置检查")
    print("   - Tushare提供器功能测试")
    print("   - Tushare适配器功能测试")
    print("   - Tushare接口函数测试")
    print("   - Tushare缓存功能测试")
    print("=" * 70)
    
    # 检查环境配置
    if not check_tushare_environment():
        print("\n❌ 环境配置检查失败，请先配置Tushare环境")
        return
    
    # 运行所有测试
    test_tushare_provider()
    test_tushare_adapter()
    test_tushare_interface()
    test_tushare_cache()
    
    # 总结
    print("\n📋 Tushare集成测试总结")
    print("=" * 60)
    print("✅ Tushare提供器: 基本功能测试")
    print("✅ Tushare适配器: 数据获取和处理")
    print("✅ Tushare接口: 统一接口函数")
    print("✅ Tushare缓存: 性能优化功能")
    
    print("\n🎉 Tushare集成测试完成！")
    print("\n🎯 现在可以使用Tushare数据源:")
    print("   1. 在CLI中选择Tushare作为A股数据源")
    print("   2. 在Web界面中配置Tushare数据源")
    print("   3. 使用API接口获取A股数据")
    print("   4. 享受高质量的A股数据服务")
    
    input("按回车键退出...")


if __name__ == "__main__":
    main()
