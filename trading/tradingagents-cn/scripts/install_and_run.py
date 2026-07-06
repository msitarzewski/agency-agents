#!/usr/bin/env python3
"""
TradingAgents-CN 安装和启动脚本
解决模块导入问题，提供一键安装和启动
"""

import os
import sys
import subprocess
from pathlib import Path

def check_virtual_env():
    """检查是否在虚拟环境中"""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if not in_venv:
        print("❌ 请先激活虚拟环境:")
        print("   Windows: .\\env\\Scripts\\activate")
        print("   Linux/macOS: source env/bin/activate")
        return False
    
    print("✅ 虚拟环境已激活")
    return True

def install_project():
    """安装项目到虚拟环境"""
    print("\n📦 安装项目到虚拟环境...")
    
    project_root = Path(__file__).parent.parent
    
    try:
        # 开发模式安装
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], cwd=project_root, check=True, capture_output=True, text=True)
        
        print("✅ 项目安装成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 项目安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def install_web_dependencies():
    """安装Web界面依赖"""
    print("\n🌐 安装Web界面依赖...")
    
    web_deps = [
        "streamlit>=1.28.0",
        "plotly>=5.15.0", 
        "altair>=5.0.0"
    ]
    
    try:
        for dep in web_deps:
            print(f"   安装 {dep}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
        
        print("✅ Web依赖安装成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Web依赖安装失败: {e}")
        return False

def check_env_file():
    """检查.env文件"""
    print("\n🔑 检查环境配置...")
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env_example"
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️ .env文件不存在，正在从.env_example创建...")
            try:
                import shutil
                shutil.copy(env_example, env_file)
                print("✅ .env文件已创建")
                print("💡 请编辑.env文件，配置您的API密钥")
            except Exception as e:
                print(f"❌ 创建.env文件失败: {e}")
                return False
        else:
            print("❌ 找不到.env_example文件")
            return False
    else:
        print("✅ .env文件存在")
    
    return True

def start_web_app():
    """启动Web应用"""
    print("\n🚀 启动Web应用...")
    
    project_root = Path(__file__).parent.parent
    web_dir = project_root / "web"
    app_file = web_dir / "app.py"
    
    if not app_file.exists():
        print(f"❌ 找不到应用文件: {app_file}")
        return False
    
    # 构建启动命令
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_file),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("📱 Web应用启动中...")
    print("🌐 浏览器将自动打开 http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        # 启动应用
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n⏹️ Web应用已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🔧 TradingAgents-CN 安装和启动工具")
    print("=" * 50)
    
    # 检查虚拟环境
    if not check_virtual_env():
        return
    
    # 安装项目
    if not install_project():
        return
    
    # 安装Web依赖
    if not install_web_dependencies():
        return
    
    # 检查环境文件
    if not check_env_file():
        return
    
    # 启动Web应用
    start_web_app()

if __name__ == "__main__":
    main()
