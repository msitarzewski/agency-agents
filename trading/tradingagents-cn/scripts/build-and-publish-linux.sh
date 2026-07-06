#!/bin/bash
# TradingAgents-CN Docker镜像构建和发布脚本（Linux服务器版 - 多架构支持）
# 使用方法: ./scripts/build-and-publish-linux.sh <dockerhub-username>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -lt 1 ]; then
    echo -e "${RED}错误: 缺少必需参数${NC}"
    echo "使用方法: $0 <dockerhub-username> [version] [platforms]"
    echo "示例: $0 myusername v1.0.0-preview"
    echo "示例: $0 myusername v1.0.0-preview linux/amd64,linux/arm64"
    exit 1
fi

DOCKERHUB_USERNAME=$1
VERSION=${2:-"v1.0.0-preview"}
PLATFORMS=${3:-"linux/amd64,linux/arm64"}

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}TradingAgents-CN Docker多架构构建和发布${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${BLUE}Docker Hub用户名: ${DOCKERHUB_USERNAME}${NC}"
echo -e "${BLUE}版本: ${VERSION}${NC}"
echo -e "${BLUE}目标架构: ${PLATFORMS}${NC}"
echo ""

# 配置
BACKEND_IMAGE_REMOTE="$DOCKERHUB_USERNAME/tradingagents-backend"
FRONTEND_IMAGE_REMOTE="$DOCKERHUB_USERNAME/tradingagents-frontend"
BUILDER_NAME="tradingagents-builder"

# 步骤1: 检查环境
echo -e "${YELLOW}步骤1: 检查环境...${NC}"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装！${NC}"
    echo "请先安装Docker: sudo apt-get install docker.io"
    exit 1
fi
echo -e "${GREEN}  ✅ Docker已安装: $(docker --version)${NC}"

# 检查Docker Buildx
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}❌ Docker Buildx未安装或不可用！${NC}"
    echo "请安装Docker Buildx: https://docs.docker.com/buildx/working-with-buildx/"
    exit 1
fi
echo -e "${GREEN}  ✅ Docker Buildx可用: $(docker buildx version | head -n1)${NC}"

# 检查Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git未安装！${NC}"
    echo "请先安装Git: sudo apt-get install git"
    exit 1
fi
echo -e "${GREEN}  ✅ Git已安装: $(git --version)${NC}"

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ] || [ ! -f "Dockerfile.backend" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本！${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ 当前目录正确${NC}"

# 检查Git分支（可选）
if git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    echo -e "${BLUE}  当前分支: ${CURRENT_BRANCH}${NC}"
else
    echo -e "${YELLOW}  ⚠️  不是Git仓库，跳过分支检查${NC}"
fi

echo ""

# 步骤2: 配置Docker Buildx
echo -e "${YELLOW}步骤2: 配置Docker Buildx...${NC}"

# 检查builder是否存在
if docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    echo -e "${GREEN}  ✅ Builder '$BUILDER_NAME' 已存在${NC}"
else
    echo -e "${CYAN}  创建新的Builder '$BUILDER_NAME'...${NC}"
    docker buildx create --name "$BUILDER_NAME" --use --platform "$PLATFORMS"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Builder创建失败！${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ Builder创建成功${NC}"
fi

# 使用指定的builder
docker buildx use "$BUILDER_NAME"

# 启动builder
echo -e "${CYAN}  启动Builder...${NC}"
docker buildx inspect --bootstrap

# 显示支持的平台
echo -e "${BLUE}  支持的平台:${NC}"
docker buildx inspect "$BUILDER_NAME" | grep "Platforms:" | head -n1

echo ""

# 步骤3: 登录Docker Hub
echo -e "${YELLOW}步骤3: 登录Docker Hub...${NC}"
docker login -u $DOCKERHUB_USERNAME
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 登录失败！请检查用户名和密码是否正确。${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 登录成功！${NC}"
echo ""

# 步骤4: 构建并推送后端镜像（多架构）
echo -e "${YELLOW}步骤4: 构建并推送后端镜像（多架构）...${NC}"
echo -e "${CYAN}  镜像名称: ${BACKEND_IMAGE_REMOTE}${NC}"
echo -e "${CYAN}  目标架构: ${PLATFORMS}${NC}"
echo -e "${CYAN}  开始时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

START_TIME=$(date +%s)

# 构建并推送版本标签
echo -e "${CYAN}  构建并推送: ${BACKEND_IMAGE_REMOTE}:${VERSION}${NC}"
docker buildx build \
  --platform "$PLATFORMS" \
  -f Dockerfile.backend \
  -t "${BACKEND_IMAGE_REMOTE}:${VERSION}" \
  -t "${BACKEND_IMAGE_REMOTE}:latest" \
  --push \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 后端镜像构建失败！${NC}"
    exit 1
fi

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

echo -e "${GREEN}  ✅ 后端镜像构建并推送成功！${NC}"
echo -e "${BLUE}  构建耗时: ${BUILD_TIME}秒 ($(($BUILD_TIME / 60))分钟)${NC}"
echo ""

# 步骤5: 构建并推送前端镜像（多架构）
echo -e "${YELLOW}步骤5: 构建并推送前端镜像（多架构）...${NC}"
echo -e "${CYAN}  镜像名称: ${FRONTEND_IMAGE_REMOTE}${NC}"
echo -e "${CYAN}  目标架构: ${PLATFORMS}${NC}"
echo -e "${CYAN}  开始时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

START_TIME=$(date +%s)

# 构建并推送版本标签
echo -e "${CYAN}  构建并推送: ${FRONTEND_IMAGE_REMOTE}:${VERSION}${NC}"
docker buildx build \
  --platform "$PLATFORMS" \
  -f Dockerfile.frontend \
  -t "${FRONTEND_IMAGE_REMOTE}:${VERSION}" \
  -t "${FRONTEND_IMAGE_REMOTE}:latest" \
  --push \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 前端镜像构建失败！${NC}"
    exit 1
fi

END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))

echo -e "${GREEN}  ✅ 前端镜像构建并推送成功！${NC}"
echo -e "${BLUE}  构建耗时: ${BUILD_TIME}秒 ($(($BUILD_TIME / 60))分钟)${NC}"
echo ""

# 步骤6: 验证镜像
echo -e "${YELLOW}步骤6: 验证镜像架构...${NC}"

echo -e "${CYAN}  验证后端镜像: ${BACKEND_IMAGE_REMOTE}:${VERSION}${NC}"
docker buildx imagetools inspect "${BACKEND_IMAGE_REMOTE}:${VERSION}" | grep "Platform:" || true

echo ""
echo -e "${CYAN}  验证前端镜像: ${FRONTEND_IMAGE_REMOTE}:${VERSION}${NC}"
docker buildx imagetools inspect "${FRONTEND_IMAGE_REMOTE}:${VERSION}" | grep "Platform:" || true

echo ""

# 步骤7: 清理本地镜像和缓存
echo -e "${YELLOW}步骤7: 清理本地镜像和缓存...${NC}"

# 清理本地镜像（如果存在）
echo -e "${CYAN}  清理本地镜像...${NC}"
docker images | grep "tradingagents-backend" | grep "$VERSION" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
docker images | grep "tradingagents-frontend" | grep "$VERSION" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
docker images | grep "$DOCKERHUB_USERNAME/tradingagents-backend" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
docker images | grep "$DOCKERHUB_USERNAME/tradingagents-frontend" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# 清理悬空镜像
echo -e "${CYAN}  清理悬空镜像...${NC}"
docker image prune -f > /dev/null 2>&1 || true

# 清理buildx缓存
echo -e "${CYAN}  清理buildx缓存...${NC}"
docker buildx prune -f > /dev/null 2>&1 || true

echo -e "${GREEN}  ✅ 本地镜像和缓存已清理${NC}"
echo ""

# 完成
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}🎉 Docker多架构镜像构建和发布完成！${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}已发布的镜像（支持 ${PLATFORMS}）：${NC}"
echo -e "${CYAN}  后端: $BACKEND_IMAGE_REMOTE:$VERSION${NC}"
echo -e "${CYAN}  后端: $BACKEND_IMAGE_REMOTE:latest${NC}"
echo -e "${CYAN}  前端: $FRONTEND_IMAGE_REMOTE:$VERSION${NC}"
echo -e "${CYAN}  前端: $FRONTEND_IMAGE_REMOTE:latest${NC}"
echo ""
echo -e "${YELLOW}用户可以通过以下命令拉取镜像（Docker会自动选择匹配的架构）：${NC}"
echo -e "${CYAN}  docker pull $BACKEND_IMAGE_REMOTE:latest${NC}"
echo -e "${CYAN}  docker pull $FRONTEND_IMAGE_REMOTE:latest${NC}"
echo ""
echo -e "${YELLOW}或使用docker-compose启动：${NC}"
echo -e "${CYAN}  docker-compose -f docker-compose.hub.yml up -d${NC}"
echo ""
echo -e "${YELLOW}验证镜像架构：${NC}"
echo -e "${CYAN}  docker buildx imagetools inspect $BACKEND_IMAGE_REMOTE:latest${NC}"
echo -e "${CYAN}  docker buildx imagetools inspect $FRONTEND_IMAGE_REMOTE:latest${NC}"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo "  1. 访问 https://hub.docker.com/repositories/$DOCKERHUB_USERNAME"
echo "  2. 查看已发布的镜像（应该显示多个架构）"
echo "  3. 更新README.md添加多架构镜像拉取说明"
echo "  4. 在GitHub Release中添加Docker镜像信息"
echo ""
echo -e "${GREEN}✅ 本地镜像已清理，服务器磁盘空间已释放${NC}"
echo ""

