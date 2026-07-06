#!/bin/bash
# 快速获取TradingAgents Docker容器日志

echo "🚀 TradingAgents Docker日志获取工具"
echo "=================================="

# 查找容器
CONTAINER_NAMES=("tradingagents-data-service" "tradingagents_data-service_1" "data-service" "tradingagents-cn-data-service-1")
CONTAINER=""

for name in "${CONTAINER_NAMES[@]}"; do
    if docker ps --filter "name=$name" --format "{{.Names}}" | grep -q "$name"; then
        CONTAINER="$name"
        echo "✅ 找到容器: $CONTAINER"
        break
    fi
done

if [ -z "$CONTAINER" ]; then
    echo "❌ 未找到TradingAgents容器"
    echo "📋 当前运行的容器:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    echo ""
    read -p "请输入容器名称: " CONTAINER
    if [ -z "$CONTAINER" ]; then
        echo "❌ 未提供容器名称，退出"
        exit 1
    fi
fi

# 创建时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo ""
echo "📋 获取日志信息..."

# 1. 获取Docker标准日志
echo "1️⃣ 获取Docker标准日志..."
docker logs "$CONTAINER" > "docker_logs_${TIMESTAMP}.log" 2>&1
echo "✅ Docker日志已保存到: docker_logs_${TIMESTAMP}.log"

# 2. 查找容器内日志文件
echo ""
echo "2️⃣ 查找容器内日志文件..."
LOG_FILES=$(docker exec "$CONTAINER" find /app -name "*.log" -type f 2>/dev/null || true)

if [ -n "$LOG_FILES" ]; then
    echo "📄 找到以下日志文件:"
    echo "$LOG_FILES"
    
    # 复制每个日志文件
    echo ""
    echo "3️⃣ 复制日志文件到本地..."
    while IFS= read -r log_file; do
        if [ -n "$log_file" ]; then
            filename=$(basename "$log_file")
            local_file="${filename}_${TIMESTAMP}"
            
            echo "📤 复制: $log_file -> $local_file"
            if docker cp "$CONTAINER:$log_file" "$local_file"; then
                echo "✅ 成功复制: $local_file"
                
                # 显示文件信息
                if [ -f "$local_file" ]; then
                    size=$(wc -c < "$local_file")
                    lines=$(wc -l < "$local_file")
                    echo "   📊 文件大小: $size 字节, $lines 行"
                fi
            else
                echo "❌ 复制失败: $log_file"
            fi
        fi
    done <<< "$LOG_FILES"
else
    echo "⚠️ 未在容器中找到.log文件"
fi

# 3. 获取容器内应用目录信息
echo ""
echo "4️⃣ 检查应用目录结构..."
echo "📂 /app 目录内容:"
docker exec "$CONTAINER" ls -la /app/ 2>/dev/null || echo "❌ 无法访问/app目录"

echo ""
echo "📂 查找所有可能的日志文件:"
docker exec "$CONTAINER" find /app -name "*log*" -type f 2>/dev/null || echo "❌ 未找到包含'log'的文件"

# 4. 检查环境变量和配置
echo ""
echo "5️⃣ 检查日志配置..."
echo "🔧 环境变量:"
docker exec "$CONTAINER" env | grep -i log || echo "❌ 未找到日志相关环境变量"

# 5. 获取最近的应用输出
echo ""
echo "6️⃣ 获取最近的应用输出 (最后50行):"
echo "=================================="
docker logs --tail 50 "$CONTAINER" 2>&1
echo "=================================="

echo ""
echo "🎉 日志获取完成!"
echo "📁 生成的文件:"
ls -la *_${TIMESTAMP}* 2>/dev/null || echo "   (无额外文件生成)"

echo ""
echo "💡 使用建议:"
echo "   - 如果源码目录的tradingagents.log为空，说明日志可能输出到stdout"
echo "   - Docker标准日志包含了应用的所有输出"
echo "   - 检查应用的日志配置，确保日志写入到文件"
echo ""
echo "📧 发送日志文件:"
echo "   请将 docker_logs_${TIMESTAMP}.log 文件发送给开发者"
if [ -f "tradingagents.log_${TIMESTAMP}" ]; then
    echo "   以及 tradingagents.log_${TIMESTAMP} 文件"
fi
