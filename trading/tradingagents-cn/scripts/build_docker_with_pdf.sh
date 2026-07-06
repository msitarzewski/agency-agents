#!/bin/bash
# Docker 镜像构建脚本（包含 PDF 导出支持）
# 用于构建支持 PDF 导出的 TradingAgents-CN Docker 镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_success "Docker 已安装"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_warning "Docker Compose 未安装，将跳过 docker-compose 相关操作"
        return 1
    fi
    print_success "Docker Compose 已安装"
    return 0
}

# 构建后端镜像
build_backend() {
    print_info "开始构建后端镜像（包含 PDF 导出支持）..."
    
    # 获取架构
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        PLATFORM="linux/amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        PLATFORM="linux/arm64"
    else
        print_error "不支持的架构: $ARCH"
        exit 1
    fi
    
    print_info "目标平台: $PLATFORM"
    
    # 构建镜像
    docker build \
        --platform "$PLATFORM" \
        -f Dockerfile.backend \
        -t tradingagents-backend:latest \
        -t tradingagents-backend:pdf-support \
        .
    
    if [ $? -eq 0 ]; then
        print_success "后端镜像构建成功"
    else
        print_error "后端镜像构建失败"
        exit 1
    fi
}

# 测试 PDF 导出功能
test_pdf_export() {
    print_info "测试 PDF 导出功能..."
    
    # 启动临时容器
    print_info "启动测试容器..."
    docker run --rm -d \
        --name tradingagents-pdf-test \
        -p 8000:8000 \
        tradingagents-backend:latest
    
    # 等待容器启动
    print_info "等待容器启动..."
    sleep 10
    
    # 检查 PDF 工具是否可用
    print_info "检查 PDF 工具..."
    
    # 检查 WeasyPrint
    docker exec tradingagents-pdf-test python -c "
import sys
try:
    import weasyprint
    print('✅ WeasyPrint 已安装')
    try:
        weasyprint.HTML(string='<html><body>test</body></html>').write_pdf()
        print('✅ WeasyPrint 可用')
        sys.exit(0)
    except Exception as e:
        print(f'❌ WeasyPrint 不可用: {e}')
        sys.exit(1)
except ImportError:
    print('❌ WeasyPrint 未安装')
    sys.exit(1)
" || print_warning "WeasyPrint 检测失败"
    
    # 检查 pdfkit
    docker exec tradingagents-pdf-test python -c "
import sys
try:
    import pdfkit
    print('✅ pdfkit 已安装')
    try:
        pdfkit.configuration()
        print('✅ pdfkit + wkhtmltopdf 可用')
        sys.exit(0)
    except Exception as e:
        print(f'❌ pdfkit 不可用: {e}')
        sys.exit(1)
except ImportError:
    print('❌ pdfkit 未安装')
    sys.exit(1)
" || print_warning "pdfkit 检测失败"
    
    # 检查 Pandoc
    docker exec tradingagents-pdf-test pandoc --version | head -n 1 || print_warning "Pandoc 检测失败"
    
    # 检查 wkhtmltopdf
    docker exec tradingagents-pdf-test wkhtmltopdf --version || print_warning "wkhtmltopdf 检测失败"
    
    # 停止测试容器
    print_info "停止测试容器..."
    docker stop tradingagents-pdf-test
    
    print_success "PDF 导出功能测试完成"
}

# 显示使用说明
show_usage() {
    cat << EOF
${GREEN}TradingAgents-CN Docker 构建脚本（PDF 导出支持）${NC}

用法:
    $0 [选项]

选项:
    -h, --help          显示此帮助信息
    -b, --build         仅构建镜像
    -t, --test          构建并测试 PDF 导出功能
    -c, --compose       使用 docker-compose 启动服务
    --no-cache          构建时不使用缓存

示例:
    # 构建镜像
    $0 --build

    # 构建并测试
    $0 --test

    # 使用 docker-compose 启动
    $0 --compose

    # 不使用缓存构建
    $0 --build --no-cache

EOF
}

# 使用 docker-compose 启动服务
start_with_compose() {
    print_info "使用 docker-compose 启动服务..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        print_success "服务已启动"
        print_info "查看日志: docker-compose logs -f backend"
    else
        print_error "docker-compose.yml 文件不存在"
        exit 1
    fi
}

# 主函数
main() {
    local BUILD_ONLY=false
    local TEST=false
    local USE_COMPOSE=false
    local NO_CACHE=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -b|--build)
                BUILD_ONLY=true
                shift
                ;;
            -t|--test)
                TEST=true
                shift
                ;;
            -c|--compose)
                USE_COMPOSE=true
                shift
                ;;
            --no-cache)
                NO_CACHE="--no-cache"
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 检查 Docker
    check_docker
    
    # 构建镜像
    if [ "$BUILD_ONLY" = true ] || [ "$TEST" = true ] || [ "$USE_COMPOSE" = true ]; then
        build_backend
    fi
    
    # 测试 PDF 导出
    if [ "$TEST" = true ]; then
        test_pdf_export
    fi
    
    # 使用 docker-compose 启动
    if [ "$USE_COMPOSE" = true ]; then
        if check_docker_compose; then
            start_with_compose
        else
            print_error "Docker Compose 不可用"
            exit 1
        fi
    fi
    
    # 如果没有指定任何选项，显示帮助
    if [ "$BUILD_ONLY" = false ] && [ "$TEST" = false ] && [ "$USE_COMPOSE" = false ]; then
        show_usage
        exit 0
    fi
    
    print_success "所有操作完成！"
    
    # 显示下一步提示
    cat << EOF

${GREEN}下一步:${NC}
1. 测试 PDF 导出功能:
   docker run --rm -p 8000:8000 tradingagents-backend:latest

2. 查看容器日志:
   docker logs -f <container_id>

3. 进入容器调试:
   docker exec -it <container_id> bash

4. 使用 docker-compose 启动完整服务:
   docker-compose up -d

EOF
}

# 运行主函数
main "$@"

