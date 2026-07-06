#!/usr/bin/env python3
"""
环境变量诊断脚本
用于排查 Docker 容器内环境变量读取问题
"""

import os
import sys

def diagnose_env_vars():
    """诊断环境变量"""
    print("=" * 80)
    print("🔍 环境变量诊断")
    print("=" * 80)
    print()
    
    # 1. 检查关键环境变量
    print("📋 关键环境变量检查:")
    print("-" * 80)
    
    env_vars = [
        "DASHSCOPE_API_KEY",
        "DASHSCOPE_ENABLED",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_ENABLED",
        "OPENAI_API_KEY",
        "OPENAI_ENABLED",
        "GOOGLE_API_KEY",
        "GOOGLE_ENABLED",
        "TUSHARE_TOKEN",
        "TUSHARE_ENABLED",
        "DOCKER_CONTAINER",
        "MONGODB_URL",
        "REDIS_URL",
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 对敏感信息进行脱敏
            if "KEY" in var or "TOKEN" in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else value[:10] + "..."
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: (未设置)")
    
    print()
    
    # 2. 检查所有环境变量
    print("📋 所有环境变量 (前20个):")
    print("-" * 80)
    all_env = dict(os.environ)
    for i, (key, value) in enumerate(list(all_env.items())[:20]):
        # 对敏感信息进行脱敏
        if any(keyword in key.upper() for keyword in ["KEY", "TOKEN", "PASSWORD", "SECRET"]):
            display_value = f"{value[:10]}..." if len(value) > 10 else "***"
        else:
            display_value = value[:50] + "..." if len(value) > 50 else value
        print(f"  {key}: {display_value}")
    
    print(f"\n  总共 {len(all_env)} 个环境变量")
    print()
    
    # 3. 测试导入模块
    print("📦 模块导入测试:")
    print("-" * 80)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI
        print("  ✅ ChatDashScopeOpenAI 导入成功")
        
        # 尝试创建实例
        try:
            llm = ChatDashScopeOpenAI(model="qwen-turbo")
            print("  ✅ ChatDashScopeOpenAI 实例创建成功")
            print(f"     模型: {llm.model_name if hasattr(llm, 'model_name') else 'unknown'}")
        except ValueError as e:
            print(f"  ❌ ChatDashScopeOpenAI 实例创建失败: {e}")
        except Exception as e:
            print(f"  ❌ ChatDashScopeOpenAI 实例创建异常: {e}")
            
    except ImportError as e:
        print(f"  ❌ ChatDashScopeOpenAI 导入失败: {e}")
    except Exception as e:
        print(f"  ❌ 模块导入异常: {e}")
    
    print()
    
    # 4. 测试 .env 文件
    print("📄 .env 文件检查:")
    print("-" * 80)
    
    env_file_paths = [
        "/app/.env",
        ".env",
        "../.env",
    ]
    
    for path in env_file_paths:
        if os.path.exists(path):
            print(f"  ✅ 找到 .env 文件: {path}")
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                print(f"     文件行数: {len(lines)}")
                
                # 显示前10行（脱敏）
                print("     前10行内容:")
                for i, line in enumerate(lines[:10]):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if any(keyword in key.upper() for keyword in ["KEY", "TOKEN", "PASSWORD", "SECRET"]):
                                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
                            else:
                                display_value = value[:30] + "..." if len(value) > 30 else value
                            print(f"       {key}={display_value}")
                        else:
                            print(f"       {line[:50]}")
                    elif line.startswith('#'):
                        print(f"       {line[:50]}")
            except Exception as e:
                print(f"     ❌ 读取文件失败: {e}")
        else:
            print(f"  ❌ 未找到 .env 文件: {path}")
    
    print()
    
    # 5. 测试 dotenv 加载
    print("🔄 python-dotenv 测试:")
    print("-" * 80)
    
    try:
        from dotenv import load_dotenv
        print("  ✅ python-dotenv 已安装")
        
        # 尝试加载 .env 文件
        for path in env_file_paths:
            if os.path.exists(path):
                print(f"  🔄 尝试加载: {path}")
                load_dotenv(path, override=True)
                
                # 重新检查环境变量
                dashscope_key = os.getenv("DASHSCOPE_API_KEY")
                if dashscope_key:
                    print(f"  ✅ 加载后 DASHSCOPE_API_KEY: {dashscope_key[:10]}...")
                else:
                    print(f"  ❌ 加载后 DASHSCOPE_API_KEY 仍然为空")
                break
    except ImportError:
        print("  ❌ python-dotenv 未安装")
    except Exception as e:
        print(f"  ❌ dotenv 加载异常: {e}")
    
    print()
    
    # 6. 系统信息
    print("💻 系统信息:")
    print("-" * 80)
    print(f"  Python 版本: {sys.version}")
    print(f"  Python 路径: {sys.executable}")
    print(f"  工作目录: {os.getcwd()}")
    print(f"  DOCKER_CONTAINER: {os.getenv('DOCKER_CONTAINER', 'false')}")
    
    print()
    print("=" * 80)
    print("✅ 诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    diagnose_env_vars()

