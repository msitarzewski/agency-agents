#!/bin/bash
# Docker镜像发布脚本 - 发布到Docker Hub
# 使用方法: ./scripts/publish-docker-images.sh <dockerhub-username> [version]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -lt 1 ]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    echo "使用方法: $0 <dockerhub-username> [version]"
    echo "示例: $0 myusername v1.0.1"
    exit 1
fi

DOCKERHUB_USERNAME=$1
VERSION=${2:-"v1.0.1"}
SKIP_BUILD=${SKIP_BUILD:-false}
PUSH_LATEST=${PUSH_LATEST:-true}

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Docker镜像发布到Docker Hub${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 配置
BACKEND_IMAGE_LOCAL="tradingagents-backend:$VERSION"
FRONTEND_IMAGE_LOCAL="tradingagents-frontend:$VERSION"
BACKEND_IMAGE_REMOTE="$DOCKERHUB_USERNAME/tradingagents-backend"
FRONTEND_IMAGE_REMOTE="$DOCKERHUB_USERNAME/tradingagents-frontend"

# 步骤1: 登录Docker Hub
echo -e "${YELLOW}步骤1: 登录Docker Hub...${NC}"
docker login -u $DOCKERHUB_USERNAME
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 登录失败！请检查用户名和密码是否正确。${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 登录成功！${NC}"
echo ""

# 步骤2: 构建镜像（如果需要）
if [ "$SKIP_BUILD" != "true" ]; then
    echo -e "${YELLOW}步骤2: 构建Docker镜像...${NC}"
    
    echo -e "${CYAN}  构建后端镜像...${NC}"
    docker build -f Dockerfile.backend -t $BACKEND_IMAGE_LOCAL .
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 后端镜像构建失败！${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ 后端镜像构建成功！${NC}"
    
    echo -e "${CYAN}  构建前端镜像...${NC}"
    docker build -f Dockerfile.frontend -t $FRONTEND_IMAGE_LOCAL .
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 前端镜像构建失败！${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ 前端镜像构建成功！${NC}"
    echo ""
else
    echo -e "${YELLOW}步骤2: 跳过构建（使用现有镜像）${NC}"
    echo ""
fi

# 步骤3: 标记镜像
echo -e "${YELLOW}步骤3: 标记镜像...${NC}"

echo -e "${CYAN}  标记后端镜像: $BACKEND_IMAGE_REMOTE:$VERSION${NC}"
docker tag $BACKEND_IMAGE_LOCAL "$BACKEND_IMAGE_REMOTE:$VERSION"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 后端镜像标记失败！${NC}"
    exit 1
fi

if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "${CYAN}  标记后端镜像: $BACKEND_IMAGE_REMOTE:latest${NC}"
    docker tag $BACKEND_IMAGE_LOCAL "$BACKEND_IMAGE_REMOTE:latest"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 后端镜像标记失败！${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}  标记前端镜像: $FRONTEND_IMAGE_REMOTE:$VERSION${NC}"
docker tag $FRONTEND_IMAGE_LOCAL "$FRONTEND_IMAGE_REMOTE:$VERSION"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 前端镜像标记失败！${NC}"
    exit 1
fi

if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "${CYAN}  标记前端镜像: $FRONTEND_IMAGE_REMOTE:latest${NC}"
    docker tag $FRONTEND_IMAGE_LOCAL "$FRONTEND_IMAGE_REMOTE:latest"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 前端镜像标记失败！${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 镜像标记成功！${NC}"
echo ""

# 步骤4: 推送镜像
echo -e "${YELLOW}步骤4: 推送镜像到GitHub Container Registry...${NC}"

echo -e "${CYAN}  推送后端镜像: $BACKEND_IMAGE_REMOTE:$VERSION${NC}"
docker push "$BACKEND_IMAGE_REMOTE:$VERSION"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 后端镜像推送失败！${NC}"
    exit 1
fi

if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "${CYAN}  推送后端镜像: $BACKEND_IMAGE_REMOTE:latest${NC}"
    docker push "$BACKEND_IMAGE_REMOTE:latest"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 后端镜像推送失败！${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}  推送前端镜像: $FRONTEND_IMAGE_REMOTE:$VERSION${NC}"
docker push "$FRONTEND_IMAGE_REMOTE:$VERSION"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 前端镜像推送失败！${NC}"
    exit 1
fi

if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "${CYAN}  推送前端镜像: $FRONTEND_IMAGE_REMOTE:latest${NC}"
    docker push "$FRONTEND_IMAGE_REMOTE:latest"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 前端镜像推送失败！${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 镜像推送成功！${NC}"
echo ""

# 完成
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}🎉 Docker镜像发布完成！${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}已发布的镜像：${NC}"
echo -e "${CYAN}  后端: $BACKEND_IMAGE_REMOTE:$VERSION${NC}"
if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "${CYAN}  后端: $BACKEND_IMAGE_REMOTE:latest${NC}"
fi
echo -e "${CYAN}  前端: $FRONTEND_IMAGE_REMOTE:$VERSION${NC}"
if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "${CYAN}  前端: $FRONTEND_IMAGE_REMOTE:latest${NC}"
fi
echo ""
echo -e "${YELLOW}用户可以通过以下命令拉取镜像：${NC}"
echo -e "${CYAN}  docker pull $BACKEND_IMAGE_REMOTE:latest${NC}"
echo -e "${CYAN}  docker pull $FRONTEND_IMAGE_REMOTE:latest${NC}"
echo ""
echo -e "${YELLOW}或使用docker-compose启动：${NC}"
echo -e "${CYAN}  docker-compose -f docker-compose.hub.yml up -d${NC}"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo "  1. 访问 https://hub.docker.com/repositories/$DOCKERHUB_USERNAME"
echo "  2. 查看已发布的镜像"
echo "  3. 更新docker-compose.hub.yml中的镜像地址（替换YOUR_DOCKERHUB_USERNAME）"
echo ""

