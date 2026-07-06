#!/bin/bash

# MongoDB 单独测试脚本
# 用于排查 MongoDB 初始化问题

set -e

echo "================================================================================"
echo "🧪 MongoDB 单独测试"
echo "================================================================================"
echo ""

# 清理旧容器和卷
echo "📋 步骤 1: 清理旧容器和卷"
echo "--------------------------------------------------------------------------------"
docker-compose -f docker-compose.mongodb-test.yml down -v 2>/dev/null || true
docker volume rm mongodb_test_data 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 启动 MongoDB
echo "📋 步骤 2: 启动 MongoDB 容器"
echo "--------------------------------------------------------------------------------"
docker-compose -f docker-compose.mongodb-test.yml up -d
echo "✅ MongoDB 容器已启动"
echo ""

# 等待 MongoDB 启动
echo "📋 步骤 3: 等待 MongoDB 初始化（30秒）"
echo "--------------------------------------------------------------------------------"
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""
echo "✅ 等待完成"
echo ""

# 查看容器状态
echo "📋 步骤 4: 检查容器状态"
echo "--------------------------------------------------------------------------------"
docker ps | grep mongodb-test
echo ""

# 查看 MongoDB 日志
echo "📋 步骤 5: 查看 MongoDB 初始化日志"
echo "--------------------------------------------------------------------------------"
echo "🔍 查找初始化脚本执行记录..."
docker logs mongodb-test 2>&1 | grep -A 20 "mongo-init.js" || echo "⚠️  未找到初始化脚本执行记录"
echo ""

echo "🔍 查找 TradingAgents 相关日志..."
docker logs mongodb-test 2>&1 | grep -i "tradingagents" || echo "⚠️  未找到 TradingAgents 相关日志"
echo ""

# 测试连接（不使用认证）
echo "📋 步骤 6: 测试连接（不使用认证）"
echo "--------------------------------------------------------------------------------"
if docker exec -it mongodb-test mongo --eval "db.version()" 2>/dev/null; then
    echo "✅ 无认证连接成功"
else
    echo "❌ 无认证连接失败（这是正常的，说明认证已启用）"
fi
echo ""

# 测试连接（使用 admin 用户）
echo "📋 步骤 7: 测试连接（使用 admin 用户）"
echo "--------------------------------------------------------------------------------"
if docker exec -it mongodb-test mongo -u admin -p tradingagents123 --authenticationDatabase admin --eval "db.version()" 2>/dev/null; then
    echo "✅ admin 用户认证成功"
    echo ""
    
    # 查看用户列表
    echo "📋 步骤 8: 查看用户列表"
    echo "--------------------------------------------------------------------------------"
    docker exec -it mongodb-test mongo -u admin -p tradingagents123 --authenticationDatabase admin --eval "
        use admin;
        print('=== Admin 数据库用户 ===');
        db.getUsers().forEach(function(user) {
            print('用户: ' + user.user);
            print('角色: ' + JSON.stringify(user.roles));
            print('');
        });
    "
    echo ""
    
    # 查看数据库列表
    echo "📋 步骤 9: 查看数据库列表"
    echo "--------------------------------------------------------------------------------"
    docker exec -it mongodb-test mongo -u admin -p tradingagents123 --authenticationDatabase admin --eval "
        print('=== 数据库列表 ===');
        db.adminCommand('listDatabases').databases.forEach(function(db) {
            print(db.name + ' (' + (db.sizeOnDisk / 1024 / 1024).toFixed(2) + ' MB)');
        });
    "
    echo ""
    
    # 查看 tradingagents 数据库
    echo "📋 步骤 10: 查看 tradingagents 数据库"
    echo "--------------------------------------------------------------------------------"
    docker exec -it mongodb-test mongo -u admin -p tradingagents123 --authenticationDatabase admin --eval "
        use tradingagents;
        print('=== TradingAgents 数据库 ===');
        print('集合数量: ' + db.getCollectionNames().length);
        print('集合列表:');
        db.getCollectionNames().forEach(function(coll) {
            print('  - ' + coll);
        });
    "
    echo ""
    
    # 测试 Python 连接
    echo "📋 步骤 11: 测试 Python 连接"
    echo "--------------------------------------------------------------------------------"
    python3 -c "
from pymongo import MongoClient
import sys

try:
    # 测试连接
    uri = 'mongodb://admin:tradingagents123@localhost:27017/tradingagents?authSource=admin'
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    # 测试 ping
    client.admin.command('ping')
    print('✅ Python 连接成功')
    
    # 获取服务器信息
    info = client.server_info()
    print(f'   MongoDB 版本: {info[\"version\"]}')
    
    # 列出数据库
    dbs = client.list_database_names()
    print(f'   数据库数量: {len(dbs)}')
    
    # 列出集合
    db = client['tradingagents']
    collections = db.list_collection_names()
    print(f'   集合数量: {len(collections)}')
    
    client.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ Python 连接失败: {e}')
    sys.exit(1)
"
    echo ""
    
else
    echo "❌ admin 用户认证失败"
    echo ""
    echo "🔍 可能的原因："
    echo "   1. MongoDB 初始化脚本未执行"
    echo "   2. MONGO_INITDB_ROOT_USERNAME/PASSWORD 环境变量未生效"
    echo "   3. 数据卷已存在，初始化脚本被跳过"
    echo ""
    echo "📋 完整的 MongoDB 日志："
    echo "--------------------------------------------------------------------------------"
    docker logs mongodb-test 2>&1
    echo ""
fi

echo "================================================================================"
echo "📝 测试完成"
echo "================================================================================"
echo ""
echo "💡 下一步："
echo "   1. 如果测试成功，说明 MongoDB 配置正确，问题可能在 docker-compose.hub.nginx.yml"
echo "   2. 如果测试失败，查看上面的日志找出原因"
echo "   3. 测试完成后，运行以下命令清理："
echo "      docker-compose -f docker-compose.mongodb-test.yml down -v"
echo ""

