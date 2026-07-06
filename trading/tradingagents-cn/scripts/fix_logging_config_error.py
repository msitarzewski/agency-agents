#!/usr/bin/env python3
"""
修复日志配置KeyError错误
"""

import os
from pathlib import Path

def fix_logging_docker_config():
    """修复Docker日志配置文件"""
    print("🔧 修复Docker日志配置文件...")
    
    docker_config_content = '''# Docker环境专用日志配置 - 完整修复版
# 解决KeyError: 'file'错误

[logging]
level = "INFO"

[logging.format]
# 必须包含所有格式配置
console = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
file = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"
structured = "json"

[logging.handlers]

# 控制台输出
[logging.handlers.console]
enabled = true
colored = false
level = "INFO"

# 文件输出 - 完整配置
[logging.handlers.file]
enabled = true
level = "DEBUG"
max_size = "100MB"
backup_count = 5
directory = "/app/logs"

# 结构化日志
[logging.handlers.structured]
enabled = true
level = "INFO"
directory = "/app/logs"

[logging.loggers]
[logging.loggers.tradingagents]
level = "INFO"

[logging.loggers.web]
level = "INFO"

[logging.loggers.dataflows]
level = "INFO"

[logging.loggers.llm_adapters]
level = "INFO"

[logging.loggers.streamlit]
level = "WARNING"

[logging.loggers.urllib3]
level = "WARNING"

[logging.loggers.requests]
level = "WARNING"

[logging.loggers.matplotlib]
level = "WARNING"

[logging.loggers.pandas]
level = "WARNING"

# Docker配置 - 修复版
[logging.docker]
enabled = true
stdout_only = false  # 同时输出到文件和stdout
disable_file_logging = false  # 启用文件日志

[logging.development]
enabled = false
debug_modules = ["tradingagents.graph", "tradingagents.llm_adapters"]
save_debug_files = true

[logging.production]
enabled = false
structured_only = false
error_notification = true
max_log_size = "100MB"

[logging.performance]
enabled = true
log_slow_operations = true
slow_threshold_seconds = 10.0
log_memory_usage = false

[logging.security]
enabled = true
log_api_calls = true
log_token_usage = true
mask_sensitive_data = true

[logging.business]
enabled = true
log_analysis_events = true
log_user_actions = true
log_export_events = true
'''
    
    # 确保config目录存在
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # 写入修复后的配置文件
    docker_config_file = config_dir / "logging_docker.toml"
    with open(docker_config_file, 'w', encoding='utf-8') as f:
        f.write(docker_config_content)
    
    print(f"✅ 修复Docker日志配置: {docker_config_file}")

def fix_main_logging_config():
    """修复主日志配置文件"""
    print("🔧 检查主日志配置文件...")
    
    main_config_file = Path("config/logging.toml")
    if main_config_file.exists():
        with open(main_config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含file格式配置
        if 'file = "' not in content:
            print("⚠️ 主配置文件缺少file格式配置，正在修复...")
            
            # 在format部分添加file配置
            if '[logging.format]' in content:
                content = content.replace(
                    'console = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"',
                    'console = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"\nfile = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"'
                )
                
                with open(main_config_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ 主配置文件已修复")
            else:
                print("❌ 主配置文件格式异常")
        else:
            print("✅ 主配置文件正常")
    else:
        print("⚠️ 主配置文件不存在")

def create_simple_test():
    """创建简单的日志测试"""
    print("📝 创建简单日志测试...")
    
    test_content = '''#!/usr/bin/env python3
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
'''
    
    test_file = Path("simple_log_test.py")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ 创建简单测试: {test_file}")

def main():
    """主函数"""
    print("🚀 修复日志配置KeyError错误")
    print("=" * 60)
    
    # 1. 修复Docker配置
    fix_logging_docker_config()
    
    # 2. 修复主配置
    fix_main_logging_config()
    
    # 3. 创建简单测试
    create_simple_test()
    
    print("\n" + "=" * 60)
    print("🎉 日志配置修复完成！")
    print("\n💡 接下来的步骤:")
    print("1. 重新构建Docker镜像: docker-compose build")
    print("2. 重启容器: docker-compose down && docker-compose up -d")
    print("3. 简单测试: docker exec TradingAgents-web python simple_log_test.py")
    print("4. 检查日志: ls -la logs/")
    print("5. 查看容器日志: docker-compose logs web")
    
    print("\n🔧 如果还有问题:")
    print("- 检查容器启动日志: docker-compose logs web")
    print("- 进入容器调试: docker exec -it TradingAgents-web bash")
    print("- 检查配置文件: docker exec TradingAgents-web cat /app/config/logging_docker.toml")

if __name__ == "__main__":
    main()
