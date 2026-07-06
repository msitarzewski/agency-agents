#!/bin/bash
# Docker 环境报告导出功能测试脚本

set -e

echo "=========================================="
echo "Docker 环境报告导出功能测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 容器名称
CONTAINER_NAME="tradingagents-backend"

# 检查容器是否运行
echo "1. 检查容器状态..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}❌ 容器 $CONTAINER_NAME 未运行${NC}"
    echo "请先启动容器："
    echo "  docker-compose -f docker-compose.hub.nginx.yml up -d backend"
    exit 1
fi
echo -e "${GREEN}✅ 容器正在运行${NC}"
echo ""

# 检查 pandoc
echo "2. 检查 pandoc 安装..."
if docker exec "$CONTAINER_NAME" which pandoc > /dev/null 2>&1; then
    PANDOC_VERSION=$(docker exec "$CONTAINER_NAME" pandoc --version | head -n 1)
    echo -e "${GREEN}✅ Pandoc 已安装: $PANDOC_VERSION${NC}"
else
    echo -e "${RED}❌ Pandoc 未安装${NC}"
    echo "请重新构建 Docker 镜像"
    exit 1
fi
echo ""

# 检查 wkhtmltopdf
echo "3. 检查 wkhtmltopdf 安装..."
if docker exec "$CONTAINER_NAME" which wkhtmltopdf > /dev/null 2>&1; then
    WKHTMLTOPDF_VERSION=$(docker exec "$CONTAINER_NAME" wkhtmltopdf --version 2>&1 | head -n 1)
    echo -e "${GREEN}✅ wkhtmltopdf 已安装: $WKHTMLTOPDF_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  wkhtmltopdf 未安装（PDF 导出可能失败）${NC}"
fi
echo ""

# 检查中文字体
echo "4. 检查中文字体..."
FONT_COUNT=$(docker exec "$CONTAINER_NAME" fc-list :lang=zh 2>/dev/null | wc -l)
if [ "$FONT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ 中文字体已安装 ($FONT_COUNT 个字体)${NC}"
    echo "字体列表："
    docker exec "$CONTAINER_NAME" fc-list :lang=zh | head -n 5
else
    echo -e "${YELLOW}⚠️  未检测到中文字体（PDF 中文可能显示异常）${NC}"
fi
echo ""

# 检查 Python 依赖
echo "5. 检查 Python 依赖..."
if docker exec "$CONTAINER_NAME" python -c "import pypandoc; print('pypandoc:', pypandoc.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✅ pypandoc 已安装${NC}"
else
    echo -e "${RED}❌ pypandoc 未安装${NC}"
    exit 1
fi

if docker exec "$CONTAINER_NAME" python -c "import markdown; print('markdown:', markdown.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✅ markdown 已安装${NC}"
else
    echo -e "${RED}❌ markdown 未安装${NC}"
    exit 1
fi
echo ""

# 检查报告导出模块
echo "6. 检查报告导出模块..."
if docker exec "$CONTAINER_NAME" python -c "from app.utils.report_exporter import report_exporter; print('Export available:', report_exporter.export_available); print('Pandoc available:', report_exporter.pandoc_available)" 2>/dev/null; then
    echo -e "${GREEN}✅ 报告导出模块加载成功${NC}"
else
    echo -e "${RED}❌ 报告导出模块加载失败${NC}"
    exit 1
fi
echo ""

# 测试 API 端点
echo "7. 测试 API 端点..."
echo "请手动测试以下功能："
echo ""
echo "  a) 访问前端报告列表页面"
echo "  b) 找到一个已完成的报告"
echo "  c) 点击'下载'按钮，应该看到下拉菜单："
echo "     - Markdown"
echo "     - Word 文档"
echo "     - PDF"
echo "     - JSON (原始数据)"
echo "  d) 分别测试每种格式的下载"
echo ""

# 总结
echo "=========================================="
echo "测试总结"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ 系统依赖检查完成${NC}"
echo ""
echo "支持的导出格式："
echo "  ✅ Markdown - 无需额外依赖"
echo "  ✅ JSON - 无需额外依赖"
if docker exec "$CONTAINER_NAME" which pandoc > /dev/null 2>&1; then
    echo "  ✅ Word (DOCX) - pandoc 已安装"
else
    echo "  ❌ Word (DOCX) - pandoc 未安装"
fi
if docker exec "$CONTAINER_NAME" which wkhtmltopdf > /dev/null 2>&1; then
    echo "  ✅ PDF - wkhtmltopdf 已安装"
else
    echo "  ⚠️  PDF - wkhtmltopdf 未安装（可能使用备用引擎）"
fi
echo ""
echo "如需重新构建镜像："
echo "  docker build -t hsliup/tradingagents-backend:latest -f Dockerfile.backend ."
echo "  docker push hsliup/tradingagents-backend:latest"
echo ""
echo "=========================================="

