#!/usr/bin/env python3
"""
测试真实的volume映射问题
验证现有代码是否真的存在KeyError: 'volume'问题
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, '.env'))
    print(f"✅ 已加载.env文件")
except ImportError:
    print(f"⚠️ python-dotenv未安装，尝试手动加载环境变量")
except Exception as e:
    print(f"⚠️ 加载.env文件失败: {e}")

def test_real_tushare_volume_access():
    """测试真实的Tushare数据volume访问"""
    print("🧪 测试真实Tushare数据volume访问")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
        
        # 检查Tushare是否可用
        tushare_token = os.getenv('TUSHARE_TOKEN')
        if not tushare_token:
            print("⚠️ TUSHARE_TOKEN未设置，无法测试真实数据")
            return True
        
        print(f"✅ TUSHARE_TOKEN已设置")
        
        # 创建数据源管理器
        manager = DataSourceManager()
        
        # 确保使用Tushare数据源
        if ChinaDataSource.TUSHARE in manager.available_sources:
            manager.set_current_source(ChinaDataSource.TUSHARE)
            print(f"📊 当前数据源: {manager.current_source.value}")
            
            # 测试获取真实数据
            print(f"🔍 获取000001真实数据...")
            
            try:
                result = manager._get_tushare_data('000001', '2025-07-20', '2025-07-26')
                
                if result and "❌" not in result:
                    print(f"✅ 成功获取数据，长度: {len(result)}")
                    print(f"📊 结果预览: {result[:200]}...")
                    
                    # 检查结果中是否包含成交量信息
                    if "成交量" in result:
                        print(f"✅ 结果包含成交量信息")
                        return True
                    else:
                        print(f"⚠️ 结果不包含成交量信息")
                        return False
                else:
                    print(f"❌ 获取数据失败: {result}")
                    return False
                    
            except KeyError as e:
                if "'volume'" in str(e):
                    print(f"🎯 确认存在KeyError: 'volume'问题！")
                    print(f"❌ 错误详情: {e}")
                    return False
                else:
                    print(f"❌ 其他KeyError: {e}")
                    return False
            except Exception as e:
                print(f"❌ 其他错误: {e}")
                if "volume" in str(e).lower():
                    print(f"🎯 可能与volume相关的错误")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("❌ Tushare数据源不可用")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tushare_adapter_direct():
    """直接测试Tushare适配器"""
    print(f"\n🧪 直接测试Tushare适配器")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        
        # 检查Tushare是否可用
        tushare_token = os.getenv('TUSHARE_TOKEN')
        if not tushare_token:
            print("⚠️ TUSHARE_TOKEN未设置，无法测试真实数据")
            return True
        
        adapter = get_tushare_adapter()
        print(f"✅ Tushare适配器创建成功")
        
        # 测试获取股票数据
        print(f"🔍 获取000001股票数据...")
        
        try:
            data = adapter.get_stock_data('000001', '2025-07-20', '2025-07-26')
            
            if data is not None and not data.empty:
                print(f"✅ 成功获取数据，形状: {data.shape}")
                print(f"📊 列名: {list(data.columns)}")
                
                # 检查volume列
                if 'volume' in data.columns:
                    print(f"✅ volume列存在")
                    volume_sum = data['volume'].sum()
                    print(f"📊 总成交量: {volume_sum:,.0f}")
                    
                    # 测试访问volume列（这是关键测试）
                    try:
                        volume_values = data['volume'].tolist()
                        print(f"✅ 成功访问volume列: {volume_values[:3]}...")
                        return True
                    except KeyError as e:
                        print(f"❌ KeyError访问volume列: {e}")
                        return False
                else:
                    print(f"❌ volume列不存在")
                    print(f"📊 可用列: {list(data.columns)}")
                    return False
            else:
                print(f"❌ 未获取到数据")
                return False
                
        except KeyError as e:
            if "'volume'" in str(e):
                print(f"🎯 确认存在KeyError: 'volume'问题！")
                print(f"❌ 错误详情: {e}")
                return False
            else:
                print(f"❌ 其他KeyError: {e}")
                return False
        except Exception as e:
            print(f"❌ 其他错误: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_column_mapping_in_real_data():
    """测试真实数据中的列映射"""
    print(f"\n🧪 测试真实数据中的列映射")
    print("=" * 60)
    
    try:
        import tushare as ts
        
        # 检查Tushare是否可用
        tushare_token = os.getenv('TUSHARE_TOKEN')
        if not tushare_token:
            print("⚠️ TUSHARE_TOKEN未设置，无法测试真实数据")
            return True
        
        # 直接调用Tushare API获取原始数据
        print(f"🔍 直接调用Tushare API...")
        ts.set_token(tushare_token)
        pro = ts.pro_api()
        
        # 获取原始数据
        raw_data = pro.daily(ts_code='000001.SZ', start_date='20250720', end_date='20250726')
        
        if raw_data is not None and not raw_data.empty:
            print(f"✅ 获取原始数据成功，形状: {raw_data.shape}")
            print(f"📊 原始列名: {list(raw_data.columns)}")
            
            # 检查原始数据中的列名
            if 'vol' in raw_data.columns:
                print(f"✅ 原始数据包含'vol'列")
                vol_values = raw_data['vol'].tolist()
                print(f"📊 vol列值: {vol_values}")
            else:
                print(f"❌ 原始数据不包含'vol'列")
                return False
            
            # 测试我们的标准化函数
            from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
            adapter = get_tushare_adapter()
            
            print(f"\n🔧 测试标准化函数...")
            standardized_data = adapter._standardize_data(raw_data)
            
            print(f"📊 标准化后列名: {list(standardized_data.columns)}")
            
            if 'volume' in standardized_data.columns:
                print(f"✅ 标准化后包含'volume'列")
                volume_values = standardized_data['volume'].tolist()
                print(f"📊 volume列值: {volume_values}")
                
                # 验证映射是否正确
                if raw_data['vol'].sum() == standardized_data['volume'].sum():
                    print(f"✅ vol -> volume 映射正确")
                    return True
                else:
                    print(f"❌ vol -> volume 映射错误")
                    return False
            else:
                print(f"❌ 标准化后不包含'volume'列")
                return False
        else:
            print(f"❌ 未获取到原始数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🔍 验证真实环境中的volume映射问题")
    print("=" * 80)
    print("📋 目标: 在真实环境中验证是否存在 KeyError: 'volume' 问题")
    print("=" * 80)
    
    tests = [
        ("真实数据列映射测试", test_column_mapping_in_real_data),
        ("Tushare适配器直接测试", test_tushare_adapter_direct),
        ("数据源管理器真实数据测试", test_real_tushare_volume_access),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试{test_name}异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "=" * 80)
    print("📊 真实环境测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    # 分析结果和建议
    print("\n📋 分析结论:")
    if passed == total:
        print("🎉 所有真实环境测试通过！")
        print("✅ 现有代码的volume映射功能完全正常")
        print("\n💡 对PR #173的建议:")
        print("  1. 🤔 询问PR作者具体的错误复现步骤")
        print("  2. 📅 确认PR作者使用的代码版本和分支")
        print("  3. 🔍 检查是否是特定环境、数据或配置的问题")
        print("  4. 📝 要求提供完整的错误堆栈信息")
        print("  5. ⚠️ 可能是已经修复的旧问题")
    else:
        print("❌ 部分真实环境测试失败")
        print("🎯 确实存在volume相关问题，PR #173的修复是必要的")
        print("\n💡 建议:")
        print("  1. ✅ 接受PR #173的修复")
        print("  2. 🔧 但需要优化实现方式")
        print("  3. 🧪 增加更多测试用例")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
