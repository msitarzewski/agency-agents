#!/usr/bin/env python3
"""
获取Docker容器内部日志文件的脚本
用于从运行中的TradingAgents容器获取实际的日志文件
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

def find_container():
    """查找TradingAgents容器"""
    print("🔍 查找TradingAgents容器...")
    
    # 可能的容器名称
    possible_names = [
        "tradingagents-data-service",
        "tradingagents_data-service_1",
        "data-service",
        "tradingagents-cn-data-service-1"
    ]
    
    for name in possible_names:
        success, output, error = run_command(f"docker ps --filter name={name} --format '{{{{.Names}}}}'")
        if success and output.strip():
            print(f"✅ 找到容器: {output.strip()}")
            return output.strip()
    
    # 如果没找到，列出所有容器让用户选择
    print("⚠️ 未找到预期的容器名称，列出所有运行中的容器:")
    success, output, error = run_command("docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'")
    if success:
        print(output)
        container_name = input("\n请输入容器名称: ").strip()
        if container_name:
            return container_name
    
    return None

def explore_container_filesystem(container_name):
    """探索容器文件系统，查找日志文件"""
    print(f"🔍 探索容器 {container_name} 的文件系统...")
    
    # 检查常见的日志位置
    log_locations = [
        "/app",
        "/app/logs",
        "/var/log",
        "/tmp",
        "."
    ]
    
    found_logs = []
    
    for location in log_locations:
        print(f"\n📂 检查目录: {location}")
        
        # 列出目录内容
        success, output, error = run_command(f"docker exec {container_name} ls -la {location}")
        if success:
            print(f"   目录内容:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
            
            # 查找.log文件
            success, output, error = run_command(f"docker exec {container_name} find {location} -maxdepth 2 -name '*.log' -type f 2>/dev/null")
            if success and output.strip():
                log_files = output.strip().split('\n')
                for log_file in log_files:
                    if log_file.strip():
                        found_logs.append(log_file.strip())
                        print(f"   📄 找到日志文件: {log_file.strip()}")
    
    return found_logs

def get_log_file_info(container_name, log_file):
    """获取日志文件信息"""
    print(f"\n📊 日志文件信息: {log_file}")
    
    # 文件大小和修改时间
    success, output, error = run_command(f"docker exec {container_name} ls -lh {log_file}")
    if success:
        print(f"   文件详情: {output.strip()}")
    
    # 文件行数
    success, output, error = run_command(f"docker exec {container_name} wc -l {log_file}")
    if success:
        lines = output.strip().split()[0]
        print(f"   总行数: {lines}")
    
    # 最后修改时间
    success, output, error = run_command(f"docker exec {container_name} stat -c '%y' {log_file}")
    if success:
        print(f"   最后修改: {output.strip()}")

def preview_log_file(container_name, log_file, lines=20):
    """预览日志文件内容"""
    print(f"\n👀 预览日志文件 {log_file} (最后{lines}行):")
    print("=" * 80)
    
    success, output, error = run_command(f"docker exec {container_name} tail -{lines} {log_file}")
    if success:
        print(output)
    else:
        print(f"❌ 无法读取日志文件: {error}")
    
    print("=" * 80)

def copy_log_file(container_name, log_file, local_path=None):
    """复制日志文件到本地"""
    if not local_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(log_file)
        local_path = f"{filename}_{timestamp}"
    
    print(f"\n📤 复制日志文件到本地: {local_path}")
    
    success, output, error = run_command(f"docker cp {container_name}:{log_file} {local_path}")
    if success:
        print(f"✅ 日志文件已复制到: {local_path}")
        
        # 检查本地文件大小
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            print(f"   文件大小: {size:,} 字节")
            
            # 显示文件的最后几行
            print(f"\n📋 文件内容预览 (最后10行):")
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(f"   {line.rstrip()}")
            except Exception as e:
                print(f"   ⚠️ 无法预览文件内容: {e}")
        
        return local_path
    else:
        print(f"❌ 复制失败: {error}")
        return None

def get_docker_logs(container_name):
    """获取Docker标准日志"""
    print(f"\n📋 获取Docker标准日志...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docker_log_file = f"docker_logs_{timestamp}.log"
    
    success, output, error = run_command(f"docker logs {container_name}")
    if success:
        with open(docker_log_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Docker日志已保存到: {docker_log_file}")
        print(f"   日志行数: {len(output.split(chr(10)))}")
        return docker_log_file
    else:
        print(f"❌ 获取Docker日志失败: {error}")
        return None

def main():
    """主函数"""
    print("🚀 TradingAgents Docker容器日志获取工具")
    print("=" * 60)
    
    # 1. 查找容器
    container_name = find_container()
    if not container_name:
        print("❌ 未找到容器，请确保TradingAgents容器正在运行")
        return
    
    # 2. 探索文件系统
    log_files = explore_container_filesystem(container_name)
    
    # 3. 获取Docker标准日志
    docker_log_file = get_docker_logs(container_name)
    
    if not log_files:
        print("\n⚠️ 未在容器中找到.log文件")
        print("💡 可能的原因:")
        print("   - 日志配置为输出到stdout/stderr (被Docker捕获)")
        print("   - 日志文件在其他位置")
        print("   - 应用尚未生成日志文件")
        
        if docker_log_file:
            print(f"\n✅ 但已获取到Docker标准日志: {docker_log_file}")
        return
    
    # 4. 处理找到的日志文件
    print(f"\n📋 找到 {len(log_files)} 个日志文件:")
    for i, log_file in enumerate(log_files, 1):
        print(f"   {i}. {log_file}")
    
    # 5. 让用户选择要处理的日志文件
    if len(log_files) == 1:
        selected_log = log_files[0]
        print(f"\n🎯 自动选择唯一的日志文件: {selected_log}")
    else:
        try:
            choice = input(f"\n请选择要获取的日志文件 (1-{len(log_files)}, 或按Enter获取所有): ").strip()
            if not choice:
                selected_logs = log_files
            else:
                index = int(choice) - 1
                if 0 <= index < len(log_files):
                    selected_logs = [log_files[index]]
                else:
                    print("❌ 无效选择")
                    return
        except ValueError:
            print("❌ 无效输入")
            return
        
        if len(selected_logs) == 1:
            selected_log = selected_logs[0]
        else:
            selected_log = None
    
    # 6. 处理选中的日志文件
    if selected_log:
        # 单个文件处理
        get_log_file_info(container_name, selected_log)
        preview_log_file(container_name, selected_log)
        
        copy_choice = input("\n是否复制此日志文件到本地? (y/N): ").strip().lower()
        if copy_choice in ['y', 'yes']:
            local_file = copy_log_file(container_name, selected_log)
            if local_file:
                print(f"\n🎉 日志文件获取完成!")
                print(f"📁 本地文件: {local_file}")
    else:
        # 多个文件处理
        print(f"\n📤 复制所有 {len(selected_logs)} 个日志文件...")
        copied_files = []
        for log_file in selected_logs:
            local_file = copy_log_file(container_name, log_file)
            if local_file:
                copied_files.append(local_file)
        
        if copied_files:
            print(f"\n🎉 成功复制 {len(copied_files)} 个日志文件:")
            for file in copied_files:
                print(f"   📁 {file}")
    
    print(f"\n📋 总结:")
    print(f"   容器名称: {container_name}")
    print(f"   找到日志文件: {len(log_files)} 个")
    if docker_log_file:
        print(f"   Docker日志: {docker_log_file}")
    print(f"   完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 操作被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
