#!/bin/bash
# Docker环境初始化脚本 - TradingAgents-CN v1.0.0-preview

set -e

echo "=========================================="
echo "TradingAgents-CN Docker 初始化"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到.env文件，从.env.example复制...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env文件创建成功${NC}"
    echo -e "${YELLOW}⚠️  请编辑.env文件，配置你的API密钥${NC}"
    exit 1
fi

# 检查必需的环境变量
echo ""
echo "检查环境变量..."

required_vars=("DEEPSEEK_API_KEY" "JWT_SECRET")
missing_vars=()

for var in "${required_vars[@]}"; do
    value=$(grep "^${var}=" .env | cut -d '=' -f2)
    if [ -z "$value" ] || [ "$value" == "your_${var,,}_here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}❌ 缺少必需的环境变量:${NC}"
    for var in "${missing_vars[@]}"; do
        echo -e "${RED}   - $var${NC}"
    done
    echo -e "${YELLOW}请编辑.env文件，配置这些变量${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 环境变量检查通过${NC}"

# 创建必需的目录
echo ""
echo "创建必需的目录..."

directories=(
    "logs"
    "data/cache"
    "data/exports"
    "data/reports"
    "data/progress"
    "config"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓ 创建目录: $dir${NC}"
    fi
done

# 设置目录权限
chmod -R 755 logs data config

# 停止现有容器
echo ""
echo "停止现有容器..."
docker-compose down 2>/dev/null || true

# 拉取最新镜像
echo ""
echo "拉取Docker镜像..."
docker-compose pull

# 构建自定义镜像
echo ""
echo "构建应用镜像..."
docker-compose build

# 启动数据库服务
echo ""
echo "启动数据库服务..."
docker-compose up -d mongodb redis

# 等待数据库就绪
echo ""
echo "等待数据库就绪..."
sleep 10

# 检查MongoDB
echo "检查MongoDB..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T mongodb mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB就绪${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待MongoDB启动... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ MongoDB启动超时${NC}"
    exit 1
fi

# 检查Redis
echo "检查Redis..."
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis就绪${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待Redis启动... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Redis启动超时${NC}"
    exit 1
fi

# 初始化数据库
echo ""
echo "初始化数据库..."
docker-compose exec -T mongodb mongo tradingagents /docker-entrypoint-initdb.d/mongo-init.js

# 启动应用服务
echo ""
echo "启动应用服务..."
docker-compose up -d

# 等待应用就绪
echo ""
echo "等待应用就绪..."
sleep 15

# 检查后端服务
echo "检查后端服务..."
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务就绪${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待后端服务启动... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${YELLOW}⚠️  后端服务启动超时，请检查日志${NC}"
fi

# 检查前端服务
echo "检查前端服务..."
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务就绪${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "等待前端服务启动... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${YELLOW}⚠️  前端服务启动超时，请检查日志${NC}"
fi

# 显示服务状态
echo ""
echo "=========================================="
echo "服务状态"
echo "=========================================="
docker-compose ps

# 显示访问信息
echo ""
echo "=========================================="
echo "✅ 初始化完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端界面: http://localhost:5173"
echo "  后端API:  http://localhost:8000"
echo "  API文档:  http://localhost:8000/docs"
echo ""
echo "默认账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo -e "${YELLOW}⚠️  重要: 请在首次登录后立即修改密码！${NC}"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""
echo "=========================================="

