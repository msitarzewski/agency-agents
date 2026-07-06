#!/bin/bash
# Docker排查命令集合 - Linux/Mac版本

echo "=== Docker容器排查工具 ==="

# 1. 检查Docker服务状态
echo -e "\n1. 检查Docker服务状态:"
if docker version > /dev/null 2>&1; then
    echo "✅ Docker服务正常运行"
else
    echo "❌ Docker服务未运行或有问题"
    exit 1
fi

# 2. 检查容器状态
echo -e "\n2. 检查容器状态:"
docker-compose ps -a

# 3. 检查网络状态
echo -e "\n3. 检查Docker网络:"
docker network ls | grep tradingagents

# 4. 检查数据卷状态
echo -e "\n4. 检查数据卷:"
docker volume ls | grep tradingagents

# 5. 检查端口占用
echo -e "\n5. 检查端口占用:"
ports=(8501 27017 6379 8081 8082)
for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "端口 $port 被占用:"
        lsof -i :$port
    else
        echo "端口 $port 空闲"
    fi
done

# 6. 检查磁盘空间
echo -e "\n6. 检查磁盘空间:"
docker system df

echo -e "\n=== 排查完成 ==="
echo "如需查看详细日志，请运行:"
echo "docker-compose logs [服务名]"
echo "例如: docker-compose logs web"