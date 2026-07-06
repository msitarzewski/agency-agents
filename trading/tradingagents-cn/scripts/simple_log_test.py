#!/usr/bin/env python3
"""
简单的日志测试 - 避免复杂导入
"""

import os
import logging
import logging.handlers
from pathlib import Path

def simple_log_test():
    """简单的日志测试"""
    print("🧪 简单日志测试")
    
    # 创建日志目录
    log_dir = Path("/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建简单的日志配置
    logger = logging.getLogger("simple_test")
    logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器
    try:
        log_file = log_dir / "simple_test.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        print(f"✅ 文件处理器创建成功: {log_file}")
    except Exception as e:
        print(f"❌ 文件处理器创建失败: {e}")
        return False
    
    # 测试日志写入
    try:
        logger.debug("🔍 DEBUG级别测试日志")
        logger.info("ℹ️ INFO级别测试日志")
        logger.warning("⚠️ WARNING级别测试日志")
        logger.error("❌ ERROR级别测试日志")
        
        print("✅ 日志写入测试完成")
        
        # 检查文件是否生成
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"📄 日志文件大小: {size} 字节")
            
            if size > 0:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"📄 日志文件行数: {len(lines)}")
                    if lines:
                        print("📄 最后一行:")
                        print(f"   {lines[-1].strip()}")
                return True
            else:
                print("⚠️ 日志文件为空")
                return False
        else:
            print("❌ 日志文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ 日志写入失败: {e}")
        return False

if __name__ == "__main__":
    success = simple_log_test()
    exit(0 if success else 1)
