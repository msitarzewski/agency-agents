#!/usr/bin/env python3
"""
TradingAgents-CN v1.0.0-preview API服务启动脚本
同时启动FastAPI服务和Worker进程
"""

import asyncio
import subprocess
import sys
import signal
import time
import os
from pathlib import Path
from typing import List, Optional

# 确保项目根目录在路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n🛑 收到信号 {signum}，正在关闭所有服务...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)
    
    def start_service(self, name: str, command: List[str], cwd: Optional[str] = None) -> bool:
        """启动单个服务"""
        try:
            print(f"🚀 启动 {name}...")
            
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = str(project_root)
            
            process = subprocess.Popen(
                command,
                cwd=cwd or str(project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(process)
            print(f"✅ {name} 已启动 (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ 启动 {name} 失败: {e}")
            return False
    
    def stop_all_services(self):
        """停止所有服务"""
        print("🔄 正在停止所有服务...")
        
        for process in self.processes:
            try:
                if process.poll() is None:  # 进程仍在运行
                    print(f"🛑 停止进程 {process.pid}...")
                    process.terminate()
                    
                    # 等待进程优雅退出
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"⚡ 强制杀死进程 {process.pid}...")
                        process.kill()
                        process.wait()
                    
                    print(f"✅ 进程 {process.pid} 已停止")
            except Exception as e:
                print(f"❌ 停止进程失败: {e}")
        
        self.processes.clear()
        print("✅ 所有服务已停止")
    
    def check_services(self):
        """检查服务状态"""
        running_count = 0
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                running_count += 1
            else:
                print(f"⚠️  服务 {i+1} 已退出 (返回码: {process.returncode})")
        
        return running_count
    
    def monitor_services(self):
        """监控服务状态"""
        print("👀 开始监控服务状态...")
        self.running = True
        
        try:
            while self.running:
                running_count = self.check_services()
                
                if running_count == 0:
                    print("❌ 所有服务都已停止")
                    break
                
                time.sleep(5)  # 每5秒检查一次
                
        except KeyboardInterrupt:
            print("\n🛑 收到中断信号...")
        finally:
            self.stop_all_services()


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'motor',
        'redis',
        'pydantic',
        'python-jose',
        'passlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # 特殊处理python-jose包的导入名称
            if package == 'python-jose':
                __import__('jose')
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有依赖已安装")
    return True


def check_services():
    """检查外部服务"""
    print("🔍 检查外部服务...")
    
    # 检查Redis
    try:
        import redis
        from app.core.config import settings
        
        # 使用配置中的Redis连接信息
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        r.ping()
        print("✅ Redis 连接正常")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print("请确保Redis服务正在运行并配置正确")
        return False
    
    # 检查MongoDB
    try:
        from app.core.config import settings
        from pymongo import MongoClient
        
        # 使用配置中的MongoDB连接信息
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB 连接正常")
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        print("请确保MongoDB服务正在运行并配置正确")
        return False
    
    return True


def main():
    """主函数"""
    print("🚀 TradingAgents-CN v1.0.0-preview API服务启动器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查外部服务
    if not check_services():
        print("\n💡 提示: 可以使用以下命令快速启动外部服务:")
        print("docker run -d --name redis -p 6379:6379 redis:alpine")
        print("docker run -d --name mongodb -p 27017:27017 mongo:latest")
        sys.exit(1)
    
    # 创建日志目录
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 创建服务管理器
    manager = ServiceManager()
    
    print("\n🎯 启动服务...")
    
    # 启动FastAPI服务
    api_success = manager.start_service(
        "FastAPI服务",
        [sys.executable, "-m", "uvicorn", "webapi.main:app", 
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(project_root)
    )
    
    if not api_success:
        print("❌ FastAPI服务启动失败")
        sys.exit(1)
    
    # 等待API服务启动
    time.sleep(3)
    
    # 启动Worker进程
    worker_success = manager.start_service(
        "分析Worker",
        [sys.executable, "scripts/start_worker.py"],
        cwd=str(project_root)
    )
    
    if not worker_success:
        print("❌ Worker进程启动失败")
        manager.stop_all_services()
        sys.exit(1)
    
    print("\n🎉 所有服务启动成功!")
    print("📍 服务地址:")
    print("  - API服务: http://localhost:8000")
    print("  - API文档: http://localhost:8000/docs")
    print("  - 健康检查: http://localhost:8000/api/health")
    print("\n💡 提示:")
    print("  - 按 Ctrl+C 停止所有服务")
    print("  - 查看日志: tail -f logs/tradingagents.log")
    print("  - 运行测试: python scripts/quick_test.py")
    
    # 监控服务
    manager.monitor_services()


if __name__ == "__main__":
    main()
