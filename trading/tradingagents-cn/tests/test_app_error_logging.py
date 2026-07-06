#!/usr/bin/env python3
"""
测试 app 目录的错误日志配置
验证 app/core/logging_config.py 中的错误日志处理器是否正确配置
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging_config import setup_logging


def test_error_logging_toml_config():
    """测试从 TOML 配置读取错误日志处理器"""
    print("\n" + "=" * 60)
    print("测试1: TOML 配置中的错误日志处理器")
    print("=" * 60)
    
    # 设置日志
    setup_logging(log_level="INFO")
    
    # 获取日志器
    webapi_logger = logging.getLogger("webapi")
    worker_logger = logging.getLogger("worker")
    
    # 检查处理器
    print("\n✅ webapi 日志器处理器:")
    for handler in webapi_logger.handlers:
        print(f"  - {handler.__class__.__name__}: {getattr(handler, 'baseFilename', 'N/A')}")
        if hasattr(handler, 'level'):
            print(f"    级别: {logging.getLevelName(handler.level)}")
    
    print("\n✅ worker 日志器处理器:")
    for handler in worker_logger.handlers:
        print(f"  - {handler.__class__.__name__}: {getattr(handler, 'baseFilename', 'N/A')}")
        if hasattr(handler, 'level'):
            print(f"    级别: {logging.getLevelName(handler.level)}")
    
    # 验证错误日志处理器存在
    error_handlers = [h for h in webapi_logger.handlers 
                     if hasattr(h, 'baseFilename') and 'error.log' in h.baseFilename]
    
    if error_handlers:
        print("\n✅ 错误日志处理器已正确配置！")
        for handler in error_handlers:
            print(f"  文件: {handler.baseFilename}")
            print(f"  级别: {logging.getLevelName(handler.level)}")
            print(f"  最大大小: {handler.maxBytes} 字节")
            print(f"  备份数: {handler.backupCount}")
    else:
        print("\n❌ 错误日志处理器未找到！")
        return False
    
    return True


def test_error_logging_functionality():
    """测试错误日志的实际功能"""
    print("\n" + "=" * 60)
    print("测试2: 错误日志功能测试")
    print("=" * 60)
    
    # 清除现有日志器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 重新设置日志
    setup_logging(log_level="INFO")
    
    # 获取日志器
    logger = logging.getLogger("webapi")
    
    # 记录不同级别的日志
    print("\n📝 记录测试日志:")
    logger.debug("这是 DEBUG 级别的日志（不应该出现在 error.log）")
    logger.info("这是 INFO 级别的日志（不应该出现在 error.log）")
    logger.warning("这是 WARNING 级别的日志（应该出现在 error.log）")
    logger.error("这是 ERROR 级别的日志（应该出现在 error.log）")
    logger.critical("这是 CRITICAL 级别的日志（应该出现在 error.log）")
    
    print("✅ 日志已记录")
    
    # 检查 error.log 文件
    error_log_path = Path("logs/error.log")
    if error_log_path.exists():
        print(f"\n✅ error.log 文件已创建: {error_log_path.absolute()}")
        
        # 读取文件内容
        with open(error_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查内容
        print(f"\n📄 error.log 文件内容（最后 500 字符）:")
        print("-" * 60)
        print(content[-500:] if len(content) > 500 else content)
        print("-" * 60)
        
        # 验证内容
        if "WARNING" in content or "ERROR" in content or "CRITICAL" in content:
            print("\n✅ error.log 包含预期的错误级别日志！")
            return True
        else:
            print("\n⚠️ error.log 文件存在但内容不符合预期")
            return False
    else:
        print(f"\n❌ error.log 文件未创建: {error_log_path.absolute()}")
        return False


def test_webapi_and_worker_loggers():
    """测试 webapi 和 worker 日志器都有错误日志处理器"""
    print("\n" + "=" * 60)
    print("测试3: webapi 和 worker 日志器验证")
    print("=" * 60)
    
    # 清除现有日志器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 重新设置日志
    setup_logging(log_level="INFO")
    
    loggers_to_check = ["webapi", "worker", "uvicorn", "fastapi"]
    all_ok = True
    
    for logger_name in loggers_to_check:
        logger = logging.getLogger(logger_name)
        error_handlers = [h for h in logger.handlers 
                         if hasattr(h, 'baseFilename') and 'error.log' in h.baseFilename]
        
        if error_handlers:
            print(f"✅ {logger_name:10s} - 有错误日志处理器")
        else:
            print(f"❌ {logger_name:10s} - 缺少错误日志处理器")
            all_ok = False
    
    return all_ok


if __name__ == "__main__":
    print("=" * 60)
    print("app 目录错误日志配置测试")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("TOML 配置测试", test_error_logging_toml_config()))
    except Exception as e:
        print(f"\n❌ TOML 配置测试失败: {e}")
        results.append(("TOML 配置测试", False))
    
    try:
        results.append(("错误日志功能测试", test_error_logging_functionality()))
    except Exception as e:
        print(f"\n❌ 错误日志功能测试失败: {e}")
        results.append(("错误日志功能测试", False))
    
    try:
        results.append(("日志器验证测试", test_webapi_and_worker_loggers()))
    except Exception as e:
        print(f"\n❌ 日志器验证测试失败: {e}")
        results.append(("日志器验证测试", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} - {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ 所有测试通过！app 目录的错误日志配置已正确修复。")
    else:
        print("\n❌ 部分测试失败，请检查配置。")
    
    sys.exit(0 if all_passed else 1)

