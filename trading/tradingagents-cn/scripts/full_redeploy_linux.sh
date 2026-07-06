#!/bin/bash
# TradingAgents-CN 完整重新部署脚本（Linux服务器）
# 包含：代码更新 -> 镜像构建 -> 推送 -> 部署 -> 初始化

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数检查
if [ $# -lt 1 ]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    echo "使用方法: $0 <dockerhub-username> [version] [branch]"
    echo "示例: $0 hsliup v1.0.0-preview v1.0.0-preview"
    exit 1
fi

DOCKERHUB_USERNAME=$1
VERSION=${2:-"v1.0.0-preview"}
BRANCH=${3:-"v1.0.0-preview"}

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}TradingAgents-CN 完整重新部署${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${BLUE}Docker Hub用户名: ${DOCKERHUB_USERNAME}${NC}"
echo -e "${BLUE}版本: ${VERSION}${NC}"
echo -e "${BLUE}分支: ${BRANCH}${NC}"
echo ""

# 步骤1: 更新代码
echo -e "${YELLOW}步骤1: 更新代码...${NC}"
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
echo -e "${GREEN}  ✅ 代码更新完成${NC}"
echo ""

# 步骤2: 停止旧服务
echo -e "${YELLOW}步骤2: 停止旧服务...${NC}"
if [ -f "docker-compose.hub.yml" ]; then
    docker-compose -f docker-compose.hub.yml down || true
    echo -e "${GREEN}  ✅ 旧服务已停止${NC}"
else
    echo -e "${YELLOW}  ⚠️  docker-compose.hub.yml 不存在，跳过停止服务${NC}"
fi
echo ""

# 步骤3: 构建和推送镜像
echo -e "${YELLOW}步骤3: 构建和推送镜像...${NC}"
if [ -f "scripts/build-and-publish-linux.sh" ]; then
    chmod +x scripts/build-and-publish-linux.sh
    ./scripts/build-and-publish-linux.sh $DOCKERHUB_USERNAME $VERSION
    echo -e "${GREEN}  ✅ 镜像构建和推送完成${NC}"
else
    echo -e "${RED}  ❌ 构建脚本不存在！${NC}"
    exit 1
fi
echo ""

# 步骤4: 检查环境配置
echo -e "${YELLOW}步骤4: 检查环境配置...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}  ⚠️  已从 .env.example 创建 .env 文件${NC}"
        echo -e "${YELLOW}  ⚠️  请编辑 .env 文件填入您的API密钥${NC}"
        echo -e "${YELLOW}  ⚠️  按任意键继续...${NC}"
        read -n 1 -s
    else
        echo -e "${RED}  ❌ .env.example 文件不存在！${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✅ .env 文件已存在${NC}"
fi
echo ""

# 步骤5: 启动新服务
echo -e "${YELLOW}步骤5: 启动新服务...${NC}"
docker-compose -f docker-compose.hub.yml pull
docker-compose -f docker-compose.hub.yml up -d
echo -e "${GREEN}  ✅ 服务启动完成${NC}"
echo ""

# 步骤6: 等待服务就绪
echo -e "${YELLOW}步骤6: 等待服务就绪...${NC}"
echo -e "${BLUE}  等待MongoDB启动（60秒）...${NC}"
sleep 60

# 检查服务状态
echo -e "${BLUE}  检查服务状态...${NC}"
docker-compose -f docker-compose.hub.yml ps

# 检查MongoDB连接
echo -e "${BLUE}  检查MongoDB连接...${NC}"
if docker exec tradingagents-mongodb mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ MongoDB连接正常${NC}"
else
    echo -e "${RED}  ❌ MongoDB连接失败${NC}"
    echo -e "${YELLOW}  查看MongoDB日志:${NC}"
    docker-compose -f docker-compose.hub.yml logs mongodb
    exit 1
fi
echo ""

# 步骤7: 系统初始化
echo -e "${YELLOW}步骤7: 系统初始化...${NC}"

# 等待后端容器完全启动
echo -e "${BLUE}  等待后端容器启动...${NC}"
sleep 30

# 检查后端容器是否运行
if ! docker ps | grep -q "tradingagents-backend"; then
    echo -e "${RED}  ❌ 后端容器未运行！${NC}"
    docker-compose -f docker-compose.hub.yml logs backend
    exit 1
fi

# 在容器内运行初始化脚本
echo -e "${BLUE}  在后端容器内运行快速登录修复...${NC}"
if docker exec tradingagents-backend test -f scripts/quick_login_fix.py; then
    docker exec tradingagents-backend python scripts/quick_login_fix.py
    echo -e "${GREEN}  ✅ 快速登录修复完成${NC}"
else
    echo -e "${YELLOW}  ⚠️  快速登录修复脚本不存在，跳过${NC}"
fi

echo -e "${BLUE}  在后端容器内运行认证系统迁移...${NC}"
if docker exec tradingagents-backend test -f scripts/simple_auth_migration.py; then
    docker exec tradingagents-backend python scripts/simple_auth_migration.py
    echo -e "${GREEN}  ✅ 认证系统迁移完成${NC}"
else
    echo -e "${YELLOW}  ⚠️  认证系统迁移脚本不存在，跳过${NC}"
fi
echo ""

# 步骤8: 验证部署
echo -e "${YELLOW}步骤8: 验证部署...${NC}"

# 检查后端API
echo -e "${BLUE}  检查后端API...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}  ✅ 后端API正常${NC}"
else
    echo -e "${RED}  ❌ 后端API异常${NC}"
    echo -e "${YELLOW}  查看后端日志:${NC}"
    docker-compose -f docker-compose.hub.yml logs backend
fi

# 检查前端
echo -e "${BLUE}  检查前端...${NC}"
if curl -s -I http://localhost:80 | grep -q "200 OK"; then
    echo -e "${GREEN}  ✅ 前端正常${NC}"
else
    echo -e "${RED}  ❌ 前端异常${NC}"
    echo -e "${YELLOW}  查看前端日志:${NC}"
    docker-compose -f docker-compose.hub.yml logs frontend
fi
echo ""

# 完成
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "${GREEN}  前端: http://$(hostname -I | awk '{print $1}'):80${NC}"
echo -e "${GREEN}  后端API: http://$(hostname -I | awk '{print $1}'):8000${NC}"
echo -e "${GREEN}  API文档: http://$(hostname -I | awk '{print $1}'):8000/docs${NC}"
echo ""
echo -e "${BLUE}默认登录信息:${NC}"
echo -e "${GREEN}  用户名: admin${NC}"
echo -e "${GREEN}  密码: admin123 或 1234567${NC}"
echo ""
echo -e "${YELLOW}建议:${NC}"
echo -e "${YELLOW}  1. 立即登录并修改默认密码${NC}"
echo -e "${YELLOW}  2. 检查 .env 文件中的API密钥配置${NC}"
echo -e "${YELLOW}  3. 查看服务日志: docker-compose -f docker-compose.hub.yml logs -f${NC}"
echo ""
