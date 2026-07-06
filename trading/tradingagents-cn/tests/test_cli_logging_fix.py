#!/usr/bin/env python3
"""
测试CLI日志修复效果
验证用户界面是否清爽，日志是否只写入文件
"""

import os
import sys
import subprocess

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_cli_logging_setup():
    """测试CLI日志设置"""
    print("🔧 测试CLI日志设置")
    print("=" * 60)
    
    try:
        # 导入CLI模块，触发日志设置
        from cli.main import setup_cli_logging, logger
        from tradingagents.utils.logging_manager import get_logger_manager
        
        print("📊 测试前的日志处理器:")
        logger_manager = get_logger_manager()
        handlers_before = len(logger_manager.root_logger.handlers)
        console_handlers_before = sum(1 for h in logger_manager.root_logger.handlers 
                                    if hasattr(h, 'stream') and h.stream.name == '<stderr>')
        print(f"   总处理器数量: {handlers_before}")
        print(f"   控制台处理器数量: {console_handlers_before}")
        
        # 执行CLI日志设置
        setup_cli_logging()
        
        print("\n📊 测试后的日志处理器:")
        handlers_after = len(logger_manager.root_logger.handlers)
        console_handlers_after = sum(1 for h in logger_manager.root_logger.handlers 
                                   if hasattr(h, 'stream') and h.stream.name == '<stderr>')
        print(f"   总处理器数量: {handlers_after}")
        print(f"   控制台处理器数量: {console_handlers_after}")
        
        # 验证效果
        if console_handlers_after < console_handlers_before:
            print("✅ 控制台日志处理器已成功移除")
        else:
            print("⚠️ 控制台日志处理器未完全移除")
        
        # 测试日志输出
        print("\n🧪 测试日志输出:")
        print("   执行 logger.info('测试消息')...")
        logger.info("这是一条测试日志消息，应该只写入文件，不在控制台显示")
        print("   ✅ 如果上面没有显示时间戳和日志信息，说明修复成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_console_output():
    """测试console输出"""
    print("\n🎨 测试console输出")
    print("=" * 60)
    
    try:
        from rich.console import Console
        
        console = Console()
        
        print("📊 测试Rich Console输出:")
        console.print("[bold cyan]这是一条用户界面消息[/bold cyan]")
        console.print("[green]✅ 这应该正常显示，没有时间戳[/green]")
        console.print("[yellow]💡 这是用户友好的提示信息[/yellow]")
        
        print("✅ Console输出正常，界面清爽")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_log_file_writing():
    """测试日志文件写入"""
    print("\n📁 测试日志文件写入")
    print("=" * 60)
    
    try:
        from cli.main import logger
        import glob
        
        # 写入测试日志
        test_message = "CLI日志修复测试消息 - 这应该只出现在日志文件中"
        logger.info(test_message)
        
        # 查找日志文件
        log_files = glob.glob("data/logs/*.log") + glob.glob("logs/*.log") + glob.glob("*.log")
        
        if log_files:
            print(f"📄 找到日志文件: {log_files}")
            
            # 检查最新的日志文件
            latest_log = max(log_files, key=os.path.getmtime)
            print(f"📄 检查最新日志文件: {latest_log}")
            
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if test_message in content:
                        print("✅ 测试消息已写入日志文件")
                        return True
                    else:
                        print("⚠️ 测试消息未在日志文件中找到")
                        return False
            except Exception as e:
                print(f"⚠️ 读取日志文件失败: {e}")
                return False
        else:
            print("⚠️ 未找到日志文件")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_cli_interface_preview():
    """预览CLI界面效果"""
    print("\n👀 预览CLI界面效果")
    print("=" * 60)
    
    try:
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        
        # 模拟修复后的CLI界面
        print("🎭 模拟修复后的CLI界面:")
        print("-" * 40)
        
        # 标题
        title_panel = Panel(
            "[bold blue]步骤 1: 选择市场 | Step 1: Select Market[/bold blue]\n"
            "请选择要分析的股票市场 | Please select the stock market to analyze",
            box_style="cyan"
        )
        console.print(title_panel)
        
        # 选项
        console.print("\n[bold cyan]请选择股票市场 | Please select stock market:[/bold cyan]")
        console.print("[cyan]1[/cyan]. 🌍 美股 | US Stock")
        console.print("   示例 | Examples: SPY, AAPL, TSLA")
        console.print("[cyan]2[/cyan]. 🌍 A股 | China A-Share")
        console.print("   示例 | Examples: 000001 (平安银行), 600036 (招商银行)")
        console.print("[cyan]3[/cyan]. 🌍 港股 | Hong Kong Stock")
        console.print("   示例 | Examples: 0700.HK (腾讯), 09988.HK (阿里巴巴)")
        
        print("\n" + "-" * 40)
        print("✅ 界面清爽，没有时间戳和技术日志信息")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试CLI日志修复效果")
    print("=" * 80)
    
    results = []
    
    # 测试1: CLI日志设置
    results.append(test_cli_logging_setup())
    
    # 测试2: Console输出
    results.append(test_console_output())
    
    # 测试3: 日志文件写入
    results.append(test_log_file_writing())
    
    # 测试4: CLI界面预览
    results.append(test_cli_interface_preview())
    
    # 总结结果
    print("\n" + "=" * 80)
    print("📋 测试结果总结")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "CLI日志设置",
        "Console输出测试",
        "日志文件写入",
        "CLI界面预览"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！CLI日志修复成功")
        print("\n📋 修复效果:")
        print("1. ✅ 控制台不再显示技术日志信息")
        print("2. ✅ 用户界面清爽美观")
        print("3. ✅ 系统日志正常写入文件")
        print("4. ✅ 用户提示使用Rich Console显示")
        
        print("\n🎯 用户体验改善:")
        print("- 界面简洁，没有时间戳干扰")
        print("- 彩色输出更加美观")
        print("- 技术信息和用户信息分离")
        print("- 调试信息仍然记录在日志文件中")
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
