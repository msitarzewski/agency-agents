"""
测试 AKShare 请求频率限制
验证东方财富接口的最佳请求间隔
"""

import time
import akshare as ak
from datetime import datetime
import sys


def test_single_request():
    """测试单次请求"""
    print("=" * 70)
    print("📊 测试单次请求")
    print("=" * 70)
    
    try:
        start_time = time.time()
        df = ak.stock_zh_a_spot_em()
        elapsed = time.time() - start_time
        
        if df is not None and not df.empty:
            print(f"✅ 请求成功")
            print(f"   数据量: {len(df)} 条")
            print(f"   耗时: {elapsed:.2f} 秒")
            return True, elapsed
        else:
            print(f"❌ 请求失败: 返回空数据")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 请求失败: {e}")
        return False, elapsed


def test_continuous_requests(count=10, interval=0):
    """测试连续请求"""
    print("\n" + "=" * 70)
    print(f"📊 测试连续请求 (次数: {count}, 间隔: {interval}秒)")
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    total_time = 0
    results = []
    
    for i in range(count):
        print(f"\n[{i+1}/{count}] {datetime.now().strftime('%H:%M:%S')} - 发起请求...")
        
        try:
            start_time = time.time()
            df = ak.stock_zh_a_spot_em()
            elapsed = time.time() - start_time
            total_time += elapsed
            
            if df is not None and not df.empty:
                success_count += 1
                print(f"   ✅ 成功 - 数据量: {len(df)} 条, 耗时: {elapsed:.2f}秒")
                results.append(("success", elapsed))
            else:
                fail_count += 1
                print(f"   ❌ 失败 - 返回空数据, 耗时: {elapsed:.2f}秒")
                results.append(("fail_empty", elapsed))
        except Exception as e:
            elapsed = time.time() - start_time
            fail_count += 1
            error_type = type(e).__name__
            error_msg = str(e)
            
            # 判断错误类型
            if "Connection aborted" in error_msg or "RemoteDisconnected" in error_msg:
                print(f"   ❌ 失败 - 连接中断, 耗时: {elapsed:.2f}秒")
                results.append(("fail_disconnect", elapsed))
            elif "SSL" in error_msg:
                print(f"   ❌ 失败 - SSL错误, 耗时: {elapsed:.2f}秒")
                results.append(("fail_ssl", elapsed))
            elif "Proxy" in error_msg:
                print(f"   ❌ 失败 - 代理错误, 耗时: {elapsed:.2f}秒")
                results.append(("fail_proxy", elapsed))
            else:
                print(f"   ❌ 失败 - {error_type}: {error_msg[:50]}..., 耗时: {elapsed:.2f}秒")
                results.append(("fail_other", elapsed))
        
        # 等待间隔
        if i < count - 1 and interval > 0:
            print(f"   ⏳ 等待 {interval} 秒...")
            time.sleep(interval)
    
    # 统计结果
    print("\n" + "=" * 70)
    print("📊 测试结果统计")
    print("=" * 70)
    print(f"总请求次数: {count}")
    print(f"成功次数: {success_count} ({success_count/count*100:.1f}%)")
    print(f"失败次数: {fail_count} ({fail_count/count*100:.1f}%)")
    
    if success_count > 0:
        success_times = [r[1] for r in results if r[0] == "success"]
        avg_time = sum(success_times) / len(success_times)
        print(f"平均响应时间: {avg_time:.2f} 秒")
    
    # 失败原因统计
    if fail_count > 0:
        print("\n失败原因统计:")
        fail_types = {}
        for result_type, _ in results:
            if result_type.startswith("fail_"):
                fail_types[result_type] = fail_types.get(result_type, 0) + 1
        
        for fail_type, count in fail_types.items():
            fail_name = {
                "fail_disconnect": "连接中断",
                "fail_ssl": "SSL错误",
                "fail_proxy": "代理错误",
                "fail_empty": "返回空数据",
                "fail_other": "其他错误"
            }.get(fail_type, fail_type)
            print(f"  • {fail_name}: {count} 次")
    
    return success_count, fail_count


def test_different_intervals():
    """测试不同的请求间隔"""
    print("\n" + "=" * 70)
    print("🧪 测试不同的请求间隔")
    print("=" * 70)
    
    intervals = [0, 0.5, 1, 2, 3, 5]
    results = {}
    
    for interval in intervals:
        print(f"\n{'='*70}")
        print(f"测试间隔: {interval} 秒")
        print(f"{'='*70}")
        
        success, fail = test_continuous_requests(count=5, interval=interval)
        results[interval] = (success, fail)
        
        # 等待一段时间再测试下一个间隔
        if interval != intervals[-1]:
            print(f"\n⏳ 等待 10 秒后测试下一个间隔...")
            time.sleep(10)
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 不同间隔的测试结果汇总")
    print("=" * 70)
    print(f"{'间隔(秒)':<10} {'成功次数':<10} {'失败次数':<10} {'成功率':<10}")
    print("-" * 70)
    
    for interval, (success, fail) in results.items():
        success_rate = success / (success + fail) * 100
        print(f"{interval:<10} {success:<10} {fail:<10} {success_rate:.1f}%")
    
    # 推荐间隔
    print("\n" + "=" * 70)
    print("💡 推荐配置")
    print("=" * 70)
    
    best_interval = None
    for interval, (success, fail) in results.items():
        if success == 5:  # 全部成功
            best_interval = interval
            break
    
    if best_interval is not None:
        print(f"✅ 推荐请求间隔: {best_interval} 秒")
        print(f"   在此间隔下，所有请求都成功")
        
        if best_interval == 0:
            print(f"\n   配置建议:")
            print(f"   QUOTES_INGESTION_INTERVAL=30  # 30秒间隔（默认）")
        else:
            # 计算建议的同步间隔
            # 假设每次同步需要多次请求（分页）
            suggested_interval = max(30, int(best_interval * 10))
            print(f"\n   配置建议:")
            print(f"   QUOTES_INGESTION_INTERVAL={suggested_interval}  # {suggested_interval}秒间隔")
    else:
        # 找到成功率最高的间隔
        best_interval = max(results.items(), key=lambda x: x[1][0])[0]
        success, fail = results[best_interval]
        success_rate = success / (success + fail) * 100
        
        print(f"⚠️  没有找到100%成功的间隔")
        print(f"   成功率最高的间隔: {best_interval} 秒 (成功率: {success_rate:.1f}%)")
        
        suggested_interval = max(60, int(best_interval * 10))
        print(f"\n   配置建议:")
        print(f"   QUOTES_INGESTION_INTERVAL={suggested_interval}  # {suggested_interval}秒间隔")
        print(f"   或者考虑使用 Tushare 数据源（更稳定）")


def main():
    """主函数"""
    print("🚀 AKShare 请求频率限制测试")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 检查代理配置
    import os
    http_proxy = os.environ.get('HTTP_PROXY', '')
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    no_proxy = os.environ.get('NO_PROXY', '')

    print("\n📋 当前环境变量代理配置:")
    print(f"   HTTP_PROXY: {http_proxy or '(未设置)'}")
    print(f"   HTTPS_PROXY: {https_proxy or '(未设置)'}")
    print(f"   NO_PROXY: {no_proxy or '(未设置)'}")

    # 检查系统代理（Windows）
    try:
        import winreg
        internet_settings = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
            0,
            winreg.KEY_READ
        )
        proxy_enable, _ = winreg.QueryValueEx(internet_settings, 'ProxyEnable')
        if proxy_enable:
            proxy_server, _ = winreg.QueryValueEx(internet_settings, 'ProxyServer')
            print(f"\n⚠️  检测到系统代理（System Proxy）:")
            print(f"   代理服务器: {proxy_server}")
            print(f"   Python requests 库会自动使用系统代理")

            # 提示用户设置 NO_PROXY
            if not no_proxy:
                print(f"\n💡 建议设置 NO_PROXY 环境变量以绕过国内数据源:")
                print(f"   NO_PROXY=localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,82.push2.eastmoney.com,82.push2delay.eastmoney.com,gtimg.cn,sinaimg.cn,api.tushare.pro,baostock.com")

                # 询问是否自动设置
                try:
                    choice = input("\n是否自动设置 NO_PROXY？(y/n，默认y): ").strip().lower() or "y"
                    if choice == "y":
                        os.environ['NO_PROXY'] = "localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,82.push2.eastmoney.com,82.push2delay.eastmoney.com,gtimg.cn,sinaimg.cn,api.tushare.pro,baostock.com"
                        print(f"✅ 已设置 NO_PROXY 环境变量")
                        no_proxy = os.environ['NO_PROXY']
                except:
                    pass
        winreg.CloseKey(internet_settings)
    except Exception as e:
        pass

    if http_proxy or https_proxy:
        if no_proxy:
            print(f"\n✅ 已配置代理和 NO_PROXY")
            print(f"   国内数据源应该直连")
        else:
            print(f"\n⚠️  已配置代理但未配置 NO_PROXY")
            print(f"   可能会通过代理访问国内数据源，导致 SSL 错误")
    else:
        if no_proxy:
            print(f"\n✅ 已配置 NO_PROXY（用于绕过系统代理）")
        else:
            print(f"\n✅ 未配置代理，直连所有服务")
    
    # 选择测试模式
    print("\n" + "=" * 70)
    print("请选择测试模式:")
    print("=" * 70)
    print("1. 快速测试 (单次请求)")
    print("2. 标准测试 (10次连续请求，无间隔)")
    print("3. 完整测试 (测试不同间隔，推荐最佳配置)")
    print("=" * 70)
    
    try:
        choice = input("请输入选项 (1/2/3，默认3): ").strip() or "3"
        
        if choice == "1":
            test_single_request()
        elif choice == "2":
            test_continuous_requests(count=10, interval=0)
        elif choice == "3":
            test_different_intervals()
        else:
            print("❌ 无效选项")
            sys.exit(1)
        
        print("\n" + "=" * 70)
        print(f"✅ 测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

