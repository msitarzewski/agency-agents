#!/usr/bin/env python3
"""
数据库环境设置脚本
自动安装和配置MongoDB + Redis
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

def run_command(command, description=""):
    """运行命令并处理错误"""
    logger.info(f"🔄 {description}")
    logger.info(f"   执行: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        logger.info(f"✅ {description} 成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} 失败")
        logger.error(f"   错误: {e.stderr}")
        return False

def install_python_packages():
    """安装Python依赖包"""
    logger.info(f"\n📦 安装Python数据库依赖包...")
    
    packages = [
        "pymongo>=4.6.0",
        "redis>=5.0.0", 
        "hiredis>=2.2.0"
    ]
    
    for package in packages:
        success = run_command(
            f"pip install {package}",
            f"安装 {package}"
        )
        if not success:
            logger.error(f"⚠️ {package} 安装失败，请手动安装")

def setup_mongodb_windows():
    """Windows环境MongoDB设置"""
    logger.info(f"\n🍃 Windows MongoDB 设置指南:")
    print("""
    请按以下步骤手动安装MongoDB:
    
    1. 下载MongoDB Community Server:
       https://www.mongodb.com/try/download/community
    
    2. 安装MongoDB:
       - 选择 "Complete" 安装
       - 勾选 "Install MongoDB as a Service"
       - 勾选 "Install MongoDB Compass" (可选的图形界面)
    
    3. 启动MongoDB服务:
       - 打开服务管理器 (services.msc)
       - 找到 "MongoDB" 服务并启动
       
    4. 验证安装:
       - 打开命令行，运行: mongosh
       - 如果连接成功，说明安装正确
    
    默认连接地址: mongodb://localhost:27017
    """)

def setup_redis_windows():
    """Windows环境Redis设置"""
    logger.info(f"\n🔴 Windows Redis 设置指南:")
    print("""
    请按以下步骤手动安装Redis:
    
    1. 下载Redis for Windows:
       https://github.com/microsoftarchive/redis/releases
       
    2. 解压到目录 (如 C:\\Redis)
    
    3. 启动Redis服务器:
       - 打开命令行，进入Redis目录
       - 运行: redis-server.exe
       
    4. 测试Redis连接:
       - 新开命令行窗口
       - 运行: redis-cli.exe
       - 输入: ping
       - 应该返回: PONG
    
    或者使用Docker:
    docker run -d -p 6379:6379 --name redis redis:latest
    
    默认连接地址: redis://localhost:6379
    """)

def setup_mongodb_linux():
    """Linux环境MongoDB设置"""
    logger.info(f"\n🍃 Linux MongoDB 设置...")
    
    # 检测Linux发行版
    if os.path.exists("/etc/ubuntu-release") or os.path.exists("/etc/debian_version"):
        # Ubuntu/Debian
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y mongodb",
            "sudo systemctl start mongodb",
            "sudo systemctl enable mongodb"
        ]
    elif os.path.exists("/etc/redhat-release") or os.path.exists("/etc/centos-release"):
        # CentOS/RHEL
        commands = [
            "sudo yum install -y mongodb-server",
            "sudo systemctl start mongod",
            "sudo systemctl enable mongod"
        ]
    else:
        logger.warning(f"⚠️ 未识别的Linux发行版，请手动安装MongoDB")
        return
    
    for cmd in commands:
        run_command(cmd, f"执行: {cmd}")

def setup_redis_linux():
    """Linux环境Redis设置"""
    logger.info(f"\n🔴 Linux Redis 设置...")
    
    # 检测Linux发行版
    if os.path.exists("/etc/ubuntu-release") or os.path.exists("/etc/debian_version"):
        # Ubuntu/Debian
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y redis-server",
            "sudo systemctl start redis-server",
            "sudo systemctl enable redis-server"
        ]
    elif os.path.exists("/etc/redhat-release") or os.path.exists("/etc/centos-release"):
        # CentOS/RHEL
        commands = [
            "sudo yum install -y redis",
            "sudo systemctl start redis",
            "sudo systemctl enable redis"
        ]
    else:
        logger.warning(f"⚠️ 未识别的Linux发行版，请手动安装Redis")
        return
    
    for cmd in commands:
        run_command(cmd, f"执行: {cmd}")

def setup_docker_option():
    """Docker方式设置"""
    logger.info(f"\n🐳 Docker 方式设置 (推荐):")
    print("""
    如果您已安装Docker，可以使用以下命令快速启动:
    
    # 启动MongoDB
    docker run -d \\
      --name mongodb \\
      -p 27017:27017 \\
      -v mongodb_data:/data/db \\
      mongo:latest
    
    # 启动Redis
    docker run -d \\
      --name redis \\
      -p 6379:6379 \\
      -v redis_data:/data \\
      redis:latest
    
    # 查看运行状态
    docker ps
    
    # 停止服务
    docker stop mongodb redis
    
    # 重新启动
    docker start mongodb redis
    """)

def create_env_template():
    """创建环境变量模板"""
    logger.info(f"📄 数据库配置已整合到主要的 .env 文件中")
    logger.info(f"请参考 .env.example 文件进行配置")

def test_connections():
    """测试数据库连接"""
    logger.debug(f"\n🔍 测试数据库连接...")
    
    try:
        from tradingagents.config.database_manager import get_database_manager


        db_manager = get_database_manager()
        
        # 测试基本功能
        if db_manager.is_mongodb_available() and db_manager.is_redis_available():
            logger.info(f"🎉 MongoDB + Redis 连接成功！")

            # 获取统计信息
            stats = db_manager.get_cache_stats()
            logger.info(f"📊 缓存统计: {stats}")

        elif db_manager.is_mongodb_available():
            logger.info(f"✅ MongoDB 连接成功，Redis 未连接")
        elif db_manager.is_redis_available():
            logger.info(f"✅ Redis 连接成功，MongoDB 未连接")
        else:
            logger.error(f"❌ 数据库连接失败")
            
        db_manager.close()
        
    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.info(f"请先安装依赖包: pip install -r requirements_db.txt")
    except Exception as e:
        logger.error(f"❌ 连接测试失败: {e}")

def main():
    """主函数"""
    logger.info(f"🚀 TradingAgents 数据库环境设置")
    logger.info(f"=")
    
    # 检测操作系统
    system = platform.system().lower()
    logger.info(f"🖥️ 检测到操作系统: {system}")
    
    # 安装Python依赖
    install_python_packages()
    
    # 根据操作系统提供设置指南
    if system == "windows":
        setup_mongodb_windows()
        setup_redis_windows()
    elif system == "linux":
        setup_mongodb_linux()
        setup_redis_linux()
    else:
        logger.warning(f"⚠️ 不支持的操作系统: {system}")
    
    # Docker选项
    setup_docker_option()
    
    # 创建配置文件
    create_env_template()
    
    logger.info(f"\n")
    logger.info(f"📋 设置完成后，请运行以下命令测试连接:")
    logger.info(f"python scripts/setup_databases.py --test")
    
    # 如果指定了测试参数
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_connections()

if __name__ == "__main__":
    main()
