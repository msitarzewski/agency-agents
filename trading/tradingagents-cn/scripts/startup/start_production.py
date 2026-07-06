#!/usr/bin/env python3
"""
TradingAgents-CN Backend Production Launcher
生产环境启动脚本
"""

import uvicorn
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def main():
    """生产环境启动函数"""
    print("🚀 Starting TradingAgents-CN Backend (Production Mode)")
    print(f"📍 Host: {settings.HOST}")
    print(f"🔌 Port: {settings.PORT}")
    print("🔒 Production Mode: Enabled")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            log_level="warning",
            access_log=False,
            workers=4,  # 多进程
            loop="uvloop",  # 高性能事件循环
            http="httptools",  # 高性能HTTP解析器
            # 生产环境优化
            backlog=2048,
            limit_concurrency=1000,
            limit_max_requests=10000,
            timeout_keep_alive=5
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 设置生产环境变量
    os.environ["DEBUG"] = "False"
    main()
