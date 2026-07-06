#!/bin/bash
# TradingAgents-CN 智能Docker启动脚本 (Linux/Mac Bash版本)
# 功能：自动判断是否需要重新构建Docker镜像
# 使用：chmod +x scripts/smart_start.sh && ./scripts/smart_start.sh
# 
# 判断逻辑：
# 1. 检查是否存在tradingagents-cn镜像
# 2. 如果镜像不存在 -> 执行构建启动
# 3. 如果镜像存在但代码有变化 -> 执行构建启动  
# 4. 如果镜像存在且代码无变化 -> 快速启动

echo "=== TradingAgents-CN Docker 智能启动脚本 ==="
echo "适用环境: Linux/Mac Bash"

# 检查是否有镜像
if docker images | grep -q "tradingagents-cn"; then
    echo "✅ 发现现有镜像"
    
    # 检查代码是否有变化
    if git diff --quiet HEAD~1 HEAD -- . ':!*.md' ':!docs/' ':!scripts/'; then
        echo "📦 代码无变化，使用快速启动"
        docker-compose up -d
    else
        echo "🔄 检测到代码变化，重新构建"
        docker-compose up -d --build
    fi
else
    echo "🏗️ 首次运行，构建镜像"
    docker-compose up -d --build
fi

echo "🚀 启动完成！"
echo "Web界面: http://localhost:8501"
echo "Redis管理: http://localhost:8081"