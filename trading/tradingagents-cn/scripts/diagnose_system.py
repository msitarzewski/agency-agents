#!/usr/bin/env python3
"""
系统诊断脚本
用于检查系统环境、配置和依赖是否正确
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
def print_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.END}")
def print_info(msg): print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")
def print_header(msg): print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}\n{msg}\n{'='*60}{Colors.END}\n")

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 10:
        return True, f"Python {version_str}"
    else:
        return False, f"Python {version_str} (需要3.10+)"

def check_pip_version() -> Tuple[bool, str]:
    """检查pip版本"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, "pip未正确安装"
    except Exception as e:
        return False, f"检查失败: {str(e)}"

def check_virtual_env() -> Tuple[bool, str]:
    """检查是否在虚拟环境中"""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        return True, f"虚拟环境: {sys.prefix}"
    else:
        return False, "未在虚拟环境中（建议使用虚拟环境）"

def check_required_packages() -> Tuple[bool, List[str]]:
    """检查必需的Python包"""
    required_packages = [
        "streamlit",
        "pandas",
        "openai",
        "langchain",
        "langgraph",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if not missing_packages:
        return True, []
    else:
        return False, missing_packages

def check_env_file() -> Tuple[bool, str]:
    """检查.env配置文件"""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        return False, "配置文件不存在"
    
    # 检查文件大小
    size = env_file.stat().st_size
    if size == 0:
        return False, "配置文件为空"
    
    return True, f"配置文件存在 ({size} 字节)"

def check_api_keys() -> Tuple[bool, List[str]]:
    """检查API密钥配置"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        return False, ["python-dotenv未安装"]
    
    api_keys = {
        "DEEPSEEK_API_KEY": "DeepSeek",
        "DASHSCOPE_API_KEY": "阿里百炼",
        "GOOGLE_API_KEY": "Google AI",
        "OPENAI_API_KEY": "OpenAI"
    }
    
    configured_keys = []
    
    for key, name in api_keys.items():
        value = os.getenv(key)
        if value and len(value) > 10:  # 简单验证
            configured_keys.append(name)
    
    if configured_keys:
        return True, configured_keys
    else:
        return False, []

def check_port_availability() -> Tuple[bool, str]:
    """检查端口是否可用"""
    import socket
    
    port = 8501
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True, f"端口 {port} 可用"
    except OSError:
        return False, f"端口 {port} 已被占用"

def check_network_connectivity() -> Tuple[bool, str]:
    """检查网络连接"""
    import socket
    
    test_hosts = [
        ("pypi.org", 443),
        ("api.deepseek.com", 443),
        ("dashscope.aliyun.com", 443)
    ]
    
    for host, port in test_hosts:
        try:
            socket.create_connection((host, port), timeout=5)
            return True, f"网络连接正常 (测试: {host})"
        except (socket.timeout, socket.error):
            continue
    
    return False, "网络连接可能存在问题"

def check_disk_space() -> Tuple[bool, str]:
    """检查磁盘空间"""
    import shutil
    
    try:
        stat = shutil.disk_usage(project_root)
        free_gb = stat.free / (1024**3)
        
        if free_gb > 5:
            return True, f"可用空间: {free_gb:.1f} GB"
        else:
            return False, f"可用空间不足: {free_gb:.1f} GB (建议至少5GB)"
    except Exception as e:
        return False, f"检查失败: {str(e)}"

def main():
    """主函数"""
    print_header("🔍 TradingAgents-CN 系统诊断工具")
    
    print_info(f"项目目录: {project_root}")
    print()
    
    # 执行所有检查
    checks = [
        ("Python版本", check_python_version),
        ("pip版本", check_pip_version),
        ("虚拟环境", check_virtual_env),
        ("配置文件", check_env_file),
        ("端口可用性", check_port_availability),
        ("网络连接", check_network_connectivity),
        ("磁盘空间", check_disk_space)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"🔍 检查 {name}...")
        is_ok, message = check_func()
        
        if is_ok:
            print_success(message)
        else:
            print_error(message)
        
        results.append((name, is_ok, message))
        print()
    
    # 检查Python包
    print("🔍 检查必需的Python包...")
    packages_ok, missing = check_required_packages()
    
    if packages_ok:
        print_success("所有必需包已安装")
    else:
        print_error(f"缺少以下包: {', '.join(missing)}")
        print_info("运行以下命令安装: pip install -e .")
    
    results.append(("Python包", packages_ok, ""))
    print()
    
    # 检查API密钥
    print("🔍 检查API密钥配置...")
    keys_ok, configured = check_api_keys()
    
    if keys_ok:
        print_success(f"已配置: {', '.join(configured)}")
    else:
        print_error("未配置任何API密钥")
        print_info("运行安装脚本配置: python scripts/easy_install.py")
    
    results.append(("API密钥", keys_ok, ""))
    print()
    
    # 显示总结
    print_header("📊 诊断结果总结")
    
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    
    print(f"{'检查项':<20} {'状态'}")
    print("-" * 40)
    
    for name, is_ok, _ in results:
        status = f"{Colors.GREEN}✅ 通过{Colors.END}" if is_ok else f"{Colors.RED}❌ 失败{Colors.END}"
        print(f"{name:<20} {status}")
    
    print()
    print(f"通过率: {passed}/{total} ({passed*100//total}%)")
    
    # 给出建议
    print()
    if passed == total:
        print_success("系统环境完全正常，可以开始使用！")
        print_info("运行以下命令启动应用:")
        print_info("  python start_web.py")
    elif passed >= total * 0.7:
        print_warning("系统环境基本正常，但有一些问题需要注意")
        print_info("建议修复上述问题以获得最佳体验")
    else:
        print_error("系统环境存在较多问题，建议先解决")
        print_info("运行一键安装脚本: python scripts/easy_install.py")
    
    print()
    print_info("如需帮助，请访问: https://github.com/hsliuping/TradingAgents-CN/issues")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  诊断已取消")
        sys.exit(0)
    except Exception as e:
        print_error(f"诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

