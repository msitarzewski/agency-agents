"""
检查旧版 MongoDB 数据卷中的数据

这个脚本会：
1. 临时启动一个 MongoDB 容器，挂载旧数据卷
2. 连接到 MongoDB 并查看数据
3. 显示所有集合和数据统计
"""

import subprocess
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, shell=True):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def check_old_volume():
    """检查旧版数据卷"""
    
    print("=" * 80)
    print("🔍 检查旧版 MongoDB 数据卷")
    print("=" * 80)
    
    # 旧数据卷名称
    old_volume = "tradingagents_mongodb_data"
    temp_container = "temp_mongodb_check"
    
    print(f"\n📋 旧数据卷: {old_volume}")
    
    # 1. 检查数据卷是否存在
    print(f"\n1️⃣ 检查数据卷是否存在...")
    code, stdout, stderr = run_command(f"docker volume inspect {old_volume}")
    
    if code != 0:
        print(f"❌ 数据卷 {old_volume} 不存在")
        print(f"错误: {stderr}")
        return
    
    print(f"✅ 数据卷 {old_volume} 存在")
    
    # 2. 停止并删除可能存在的临时容器
    print(f"\n2️⃣ 清理旧的临时容器...")
    run_command(f"docker stop {temp_container}", shell=True)
    run_command(f"docker rm {temp_container}", shell=True)
    
    # 3. 启动临时 MongoDB 容器，挂载旧数据卷
    print(f"\n3️⃣ 启动临时 MongoDB 容器...")
    cmd = f"""docker run -d \
        --name {temp_container} \
        -v {old_volume}:/data/db \
        -p 27018:27017 \
        mongo:4.4"""
    
    code, stdout, stderr = run_command(cmd)
    
    if code != 0:
        print(f"❌ 启动容器失败")
        print(f"错误: {stderr}")
        return
    
    print(f"✅ 临时容器已启动: {temp_container}")
    print(f"📍 端口映射: 27018 -> 27017")
    
    # 4. 等待 MongoDB 启动
    print(f"\n4️⃣ 等待 MongoDB 启动...")
    for i in range(30):
        time.sleep(1)
        code, stdout, stderr = run_command(
            f"docker exec {temp_container} mongosh --eval 'db.runCommand({{ping: 1}})'",
            shell=True
        )
        if code == 0:
            print(f"✅ MongoDB 已启动 (耗时 {i+1} 秒)")
            break
        print(f"⏳ 等待中... ({i+1}/30)")
    else:
        print(f"❌ MongoDB 启动超时")
        run_command(f"docker stop {temp_container}", shell=True)
        run_command(f"docker rm {temp_container}", shell=True)
        return
    
    # 5. 查看数据库列表
    print(f"\n5️⃣ 查看数据库列表...")
    cmd = f"docker exec {temp_container} mongosh --quiet --eval 'db.adminCommand({{listDatabases: 1}})'"
    code, stdout, stderr = run_command(cmd, shell=True)
    
    if code == 0:
        print(f"\n📊 数据库列表:")
        print(stdout)
    else:
        print(f"❌ 查询失败: {stderr}")
    
    # 6. 查看 tradingagents 数据库的集合
    print(f"\n6️⃣ 查看 tradingagents 数据库的集合...")
    cmd = f"docker exec {temp_container} mongosh tradingagents --quiet --eval 'db.getCollectionNames()'"
    code, stdout, stderr = run_command(cmd, shell=True)
    
    if code == 0:
        print(f"\n📋 集合列表:")
        print(stdout)
    else:
        print(f"❌ 查询失败: {stderr}")
    
    # 7. 查看 system_configs 集合
    print(f"\n7️⃣ 查看 system_configs 集合...")
    cmd = f"""docker exec {temp_container} mongosh tradingagents --quiet --eval '
        var count = db.system_configs.countDocuments();
        print("文档数量: " + count);
        if (count > 0) {{
            print("\\n最新配置:");
            var config = db.system_configs.findOne({{is_active: true}}, {{sort: {{version: -1}}}});
            if (config) {{
                print("  _id: " + config._id);
                print("  config_name: " + config.config_name);
                print("  version: " + config.version);
                print("  is_active: " + config.is_active);
                print("  LLM配置数量: " + (config.llm_configs ? config.llm_configs.length : 0));
                print("  数据源配置数量: " + (config.data_source_configs ? config.data_source_configs.length : 0));
                print("  系统设置数量: " + (config.system_settings ? Object.keys(config.system_settings).length : 0));
                
                if (config.llm_configs && config.llm_configs.length > 0) {{
                    print("\\n  启用的 LLM:");
                    config.llm_configs.forEach(function(llm) {{
                        if (llm.enabled) {{
                            print("    - " + llm.provider + ": " + llm.model_name);
                        }}
                    }});
                }}
                
                if (config.data_source_configs && config.data_source_configs.length > 0) {{
                    print("\\n  启用的数据源:");
                    config.data_source_configs.forEach(function(ds) {{
                        if (ds.enabled) {{
                            print("    - " + ds.type + ": " + ds.name);
                        }}
                    }});
                }}
            }} else {{
                print("\\n⚠️  未找到激活的配置");
            }}
        }}
    '"""
    code, stdout, stderr = run_command(cmd, shell=True)
    
    if code == 0:
        print(stdout)
    else:
        print(f"❌ 查询失败: {stderr}")
    
    # 8. 查看其他重要集合的数据量
    print(f"\n8️⃣ 查看其他集合的数据量...")
    collections = [
        "users",
        "stock_basic_info",
        "market_quotes",
        "analysis_tasks",
        "analysis_reports",
        "favorites",
        "tags",
        "token_usage"
    ]
    
    for coll in collections:
        cmd = f"docker exec {temp_container} mongosh tradingagents --quiet --eval 'db.{coll}.countDocuments()'"
        code, stdout, stderr = run_command(cmd, shell=True)
        if code == 0:
            count = stdout.strip()
            print(f"  {coll}: {count} 条数据")
    
    # 9. 提示用户
    print(f"\n" + "=" * 80)
    print(f"✅ 检查完成")
    print("=" * 80)
    print(f"\n📍 临时容器信息:")
    print(f"  容器名: {temp_container}")
    print(f"  端口: localhost:27018")
    print(f"  数据卷: {old_volume}")
    
    print(f"\n🔧 您可以使用以下命令连接到旧数据库:")
    print(f"  mongosh mongodb://localhost:27018/tradingagents")
    
    print(f"\n🔧 或使用 MongoDB Compass 连接:")
    print(f"  连接字符串: mongodb://localhost:27018/tradingagents")
    
    print(f"\n⚠️  查看完成后，请运行以下命令停止并删除临时容器:")
    print(f"  docker stop {temp_container}")
    print(f"  docker rm {temp_container}")
    
    print(f"\n💡 提示:")
    print(f"  - 临时容器会一直运行，直到您手动停止")
    print(f"  - 您可以使用 MongoDB 客户端工具查看详细数据")
    print(f"  - 如果需要迁移数据，请参考 docs/docker_volumes_analysis.md")


if __name__ == "__main__":
    try:
        check_old_volume()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

