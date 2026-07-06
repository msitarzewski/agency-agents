#!/usr/bin/env python3
"""
禁用结构化日志，只保留主日志文件
"""

from pathlib import Path

def disable_structured_logging():
    """禁用结构化日志"""
    print("🔧 禁用结构化日志...")
    
    config_file = Path("config/logging_docker.toml")
    if not config_file.exists():
        print("❌ 配置文件不存在")
        return False
    
    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 禁用结构化日志
    new_content = content.replace(
        '[logging.handlers.structured]\nenabled = true',
        '[logging.handlers.structured]\nenabled = false'
    )
    
    # 写回文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 结构化日志已禁用")
    print("💡 现在只会生成 tradingagents.log 文件")
    print("🔄 需要重新构建Docker镜像: docker-compose build")
    
    return True

if __name__ == "__main__":
    disable_structured_logging()
