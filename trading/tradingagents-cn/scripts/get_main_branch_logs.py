#!/usr/bin/env python3
"""
获取TradingAgents主分支Docker容器日志
适用于当前main分支的单体应用架构
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(cmd, capture_output=True):
    """执行命令"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def find_tradingagents_container():
    """查找TradingAgents Web容器"""
    print("🔍 查找TradingAgents Web容器...")
    
    # 根据docker-compose.yml，容器名应该是 TradingAgents-web
    container_names = [
        "TradingAgents-web",
        "tradingagents-web", 
        "tradingagents_web_1",
        "tradingagents-cn_web_1"
    ]
    
    for name in container_names:
        success, output, error = run_command(f"docker ps --filter name={name} --format '{{{{.Names}}}}'")
        if success and output.strip():
            print(f"✅ 找到容器: {output.strip()}")
            return output.strip()
    
    # 如果没找到，列出所有容器
    print("⚠️ 未找到预期的容器，列出所有运行中的容器:")
    success, output, error = run_command("docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'")
    if success:
        print(output)
        container_name = input("\n请输入TradingAgents Web容器名称: ").strip()
        if container_name:
            return container_name
    
    return None

def get_container_info(container_name):
    """获取容器基本信息"""
    print(f"\n📊 容器信息: {container_name}")
    print("-" * 50)
    
    # 容器状态
    success, output, error = run_command(f"docker inspect {container_name} --format '{{{{.State.Status}}}}'")
    if success:
        print(f"   状态: {output.strip()}")
    
    # 容器启动时间
    success, output, error = run_command(f"docker inspect {container_name} --format '{{{{.State.StartedAt}}}}'")
    if success:
        print(f"   启动时间: {output.strip()}")
    
    # 容器镜像
    success, output, error = run_command(f"docker inspect {container_name} --format '{{{{.Config.Image}}}}'")
    if success:
        print(f"   镜像: {output.strip()}")

def explore_log_locations(container_name):
    """探索容器内的日志位置"""
    print(f"\n🔍 探索容器 {container_name} 的日志位置...")
    print("-" * 50)
    
    # 检查预期的日志目录
    log_locations = [
        "/app/logs",
        "/app", 
        "/app/tradingagents",
        "/tmp",
        "/var/log"
    ]
    
    found_logs = []
    
    for location in log_locations:
        print(f"\n📂 检查目录: {location}")
        
        # 检查目录是否存在
        success, output, error = run_command(f"docker exec {container_name} test -d {location}")
        if not success:
            print(f"   ❌ 目录不存在")
            continue
        
        # 列出目录内容
        success, output, error = run_command(f"docker exec {container_name} ls -la {location}")
        if success:
            print(f"   📋 目录内容:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        # 查找日志文件
        success, output, error = run_command(f"docker exec {container_name} find {location} -maxdepth 2 -name '*.log' -type f 2>/dev/null")
        if success and output.strip():
            log_files = [f.strip() for f in output.strip().split('\n') if f.strip()]
            for log_file in log_files:
                found_logs.append(log_file)
                print(f"   📄 找到日志文件: {log_file}")
                
                # 获取文件信息
                success2, output2, error2 = run_command(f"docker exec {container_name} ls -lh {log_file}")
                if success2:
                    print(f"      详情: {output2.strip()}")
    
    return found_logs

def get_docker_logs(container_name):
    """获取Docker标准日志"""
    print(f"\n📋 获取Docker标准日志...")
    print("-" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docker_log_file = f"tradingagents_docker_logs_{timestamp}.log"
    
    success, output, error = run_command(f"docker logs {container_name}")
    if success:
        with open(docker_log_file, 'w', encoding='utf-8') as f:
            f.write(output)
        
        # 统计信息
        lines = len(output.split('\n'))
        size = len(output.encode('utf-8'))
        
        print(f"✅ Docker日志已保存到: {docker_log_file}")
        print(f"   📊 日志行数: {lines:,}")
        print(f"   📊 文件大小: {size:,} 字节")
        
        # 显示最后几行
        print(f"\n👀 最后10行日志预览:")
        print("=" * 60)
        last_lines = output.split('\n')[-11:-1]  # 最后10行
        for line in last_lines:
            if line.strip():
                print(line)
        print("=" * 60)
        
        return docker_log_file
    else:
        print(f"❌ 获取Docker日志失败: {error}")
        return None

def copy_log_files(container_name, log_files):
    """复制容器内的日志文件"""
    if not log_files:
        print("\n⚠️ 未找到容器内的日志文件")
        return []
    
    print(f"\n📤 复制容器内的日志文件...")
    print("-" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    copied_files = []
    
    for log_file in log_files:
        filename = os.path.basename(log_file)
        local_file = f"{filename}_{timestamp}"
        
        print(f"📄 复制: {log_file} -> {local_file}")
        
        success, output, error = run_command(f"docker cp {container_name}:{log_file} {local_file}")
        if success:
            print(f"   ✅ 复制成功")
            
            # 检查本地文件
            if os.path.exists(local_file):
                size = os.path.getsize(local_file)
                print(f"   📊 文件大小: {size:,} 字节")
                
                # 预览文件内容
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print(f"   📊 文件行数: {len(lines):,}")
                        
                        if lines:
                            print(f"   👀 最后3行预览:")
                            for line in lines[-3:]:
                                print(f"      {line.rstrip()}")
                except Exception as e:
                    print(f"   ⚠️ 无法预览文件: {e}")
                
                copied_files.append(local_file)
        else:
            print(f"   ❌ 复制失败: {error}")
    
    return copied_files

def check_log_configuration(container_name):
    """检查日志配置"""
    print(f"\n🔧 检查日志配置...")
    print("-" * 50)
    
    # 检查环境变量
    print("📋 日志相关环境变量:")
    success, output, error = run_command(f"docker exec {container_name} env | grep -i log")
    if success and output.strip():
        for line in output.split('\n'):
            if line.strip():
                print(f"   {line}")
    else:
        print("   ❌ 未找到日志相关环境变量")
    
    # 检查Python日志配置
    print("\n🐍 检查Python日志配置:")
    python_check = '''
import os
import logging
print("Python日志配置:")
print(f"  日志级别: {os.getenv('TRADINGAGENTS_LOG_LEVEL', 'NOT_SET')}")
print(f"  日志目录: {os.getenv('TRADINGAGENTS_LOG_DIR', 'NOT_SET')}")
print(f"  当前工作目录: {os.getcwd()}")
print(f"  日志目录是否存在: {os.path.exists('/app/logs')}")
if os.path.exists('/app/logs'):
    print(f"  日志目录内容: {os.listdir('/app/logs')}")
'''
    
    success, output, error = run_command(f"docker exec {container_name} python -c \"{python_check}\"")
    if success:
        print(output)
    else:
        print(f"   ❌ 检查失败: {error}")

def get_recent_activity(container_name):
    """获取最近的活动日志"""
    print(f"\n⏰ 获取最近的活动日志...")
    print("-" * 50)
    
    # 最近1小时的Docker日志
    print("📋 最近1小时的Docker日志:")
    success, output, error = run_command(f"docker logs --since 1h {container_name}")
    if success:
        lines = output.split('\n')
        recent_lines = [line for line in lines if line.strip()][-20:]  # 最后20行
        
        if recent_lines:
            print("   最近20行:")
            for line in recent_lines:
                print(f"   {line}")
        else:
            print("   ❌ 最近1小时无日志输出")
    else:
        print(f"   ❌ 获取失败: {error}")

def main():
    """主函数"""
    print("🚀 TradingAgents 主分支日志获取工具")
    print("=" * 60)
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 查找容器
    container_name = find_tradingagents_container()
    if not container_name:
        print("❌ 未找到TradingAgents容器，请确保容器正在运行")
        print("\n💡 启动容器的命令:")
        print("   docker-compose up -d")
        return False
    
    # 2. 获取容器信息
    get_container_info(container_name)
    
    # 3. 检查日志配置
    check_log_configuration(container_name)
    
    # 4. 探索日志位置
    log_files = explore_log_locations(container_name)
    
    # 5. 获取Docker标准日志
    docker_log_file = get_docker_logs(container_name)
    
    # 6. 复制容器内日志文件
    copied_files = copy_log_files(container_name, log_files)
    
    # 7. 获取最近活动
    get_recent_activity(container_name)
    
    # 8. 生成总结报告
    print("\n" + "=" * 60)
    print("📋 日志获取总结报告")
    print("=" * 60)
    
    print(f"🐳 容器名称: {container_name}")
    print(f"📄 找到容器内日志文件: {len(log_files)} 个")
    print(f"📤 成功复制文件: {len(copied_files)} 个")
    
    if docker_log_file:
        print(f"📋 Docker标准日志: {docker_log_file}")
    
    if copied_files:
        print(f"📁 复制的日志文件:")
        for file in copied_files:
            print(f"   - {file}")
    
    print(f"\n💡 建议:")
    if not log_files:
        print("   - 应用可能将日志输出到stdout，已通过Docker日志捕获")
        print("   - 检查应用的日志配置，确保写入到文件")
        print("   - 考虑在docker-compose.yml中添加日志目录挂载")
    
    print("   - 将获取到的日志文件发送给开发者进行问题诊断")
    
    if docker_log_file:
        print(f"\n📧 主要发送文件: {docker_log_file}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
