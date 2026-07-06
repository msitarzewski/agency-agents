#!/bin/bash

################################################################################
# TradingAgents 演示系统一键部署脚本
#
# 功能：
# - 检查系统要求
# - 安装 Docker 和 Docker Compose
# - 下载项目文件
# - 配置环境变量
# - 拉取并启动服务
# - 导入配置数据
# - 创建默认管理员账号
#
# 使用方法：
#   curl -fsSL https://raw.githubusercontent.com/your-org/TradingAgents-CN/main/scripts/deploy_demo.sh | bash
#   或
#   bash deploy_demo.sh
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_NAME="TradingAgents-Demo"
GITHUB_REPO="https://github.com/your-org/TradingAgents-CN"
GITHUB_RAW="https://raw.githubusercontent.com/your-org/TradingAgents-CN/main"

################################################################################
# 工具函数
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ 错误: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  警告: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

################################################################################
# 检查系统要求
################################################################################

check_system() {
    print_header "检查系统要求"
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "操作系统: Linux"
    else
        print_error "不支持的操作系统: $OSTYPE"
        print_info "本脚本仅支持 Linux 系统"
        exit 1
    fi
    
    # 检查是否为 root 或有 sudo 权限
    if [[ $EUID -eq 0 ]]; then
        SUDO=""
        print_warning "正在以 root 用户运行"
    elif check_command sudo; then
        SUDO="sudo"
        print_success "检测到 sudo 权限"
    else
        print_error "需要 root 权限或 sudo 权限"
        exit 1
    fi
    
    # 检查内存
    total_mem=$(free -m | awk '/^Mem:/{print $2}')
    if [ $total_mem -lt 3800 ]; then
        print_warning "内存不足 4GB (当前: ${total_mem}MB)，可能影响性能"
    else
        print_success "内存: ${total_mem}MB"
    fi
    
    # 检查磁盘空间
    available_space=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $available_space -lt 20 ]; then
        print_warning "磁盘空间不足 20GB (当前: ${available_space}GB)"
    else
        print_success "磁盘空间: ${available_space}GB"
    fi
}

################################################################################
# 安装 Docker
################################################################################

install_docker() {
    print_header "安装 Docker"
    
    if check_command docker; then
        docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker 已安装: $docker_version"
        return 0
    fi
    
    print_info "开始安装 Docker..."
    
    # 检测发行版
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        print_error "无法检测操作系统"
        exit 1
    fi
    
    case $OS in
        ubuntu|debian)
            print_info "检测到 Ubuntu/Debian 系统"
            
            # 更新包索引
            $SUDO apt-get update
            
            # 安装依赖
            $SUDO apt-get install -y ca-certificates curl gnupg
            
            # 添加 Docker GPG 密钥
            $SUDO install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
            
            # 设置 Docker 仓库
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
              $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
              $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # 安装 Docker
            $SUDO apt-get update
            $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
            
        centos|rhel)
            print_info "检测到 CentOS/RHEL 系统"
            
            # 安装依赖
            $SUDO yum install -y yum-utils
            
            # 添加 Docker 仓库
            $SUDO yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # 安装 Docker
            $SUDO yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
            
        *)
            print_error "不支持的发行版: $OS"
            exit 1
            ;;
    esac
    
    # 启动 Docker
    $SUDO systemctl start docker
    $SUDO systemctl enable docker
    
    # 添加当前用户到 docker 组
    if [[ $EUID -ne 0 ]]; then
        $SUDO usermod -aG docker $USER
        print_warning "已将用户添加到 docker 组，请重新登录或运行: newgrp docker"
    fi
    
    print_success "Docker 安装完成"
}

################################################################################
# 下载项目文件
################################################################################

download_files() {
    print_header "下载项目文件"
    
    # 创建项目目录
    if [ -d "$PROJECT_NAME" ]; then
        print_warning "目录 $PROJECT_NAME 已存在"
        read -p "是否删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_NAME"
        else
            print_error "部署已取消"
            exit 1
        fi
    fi
    
    mkdir -p "$PROJECT_NAME"
    cd "$PROJECT_NAME"
    
    # 创建必要的目录
    mkdir -p install scripts
    
    print_info "下载 docker-compose 文件..."
    curl -fsSL -o docker-compose.hub.yml "$GITHUB_RAW/docker-compose.hub.yml"
    
    print_info "下载环境变量模板..."
    curl -fsSL -o .env.example "$GITHUB_RAW/.env.example"
    
    print_info "下载配置数据..."
    curl -fsSL -o install/database_export_config_2025-10-16.json "$GITHUB_RAW/install/database_export_config_2025-10-16.json"
    
    print_info "下载导入脚本..."
    curl -fsSL -o scripts/import_config_and_create_user.py "$GITHUB_RAW/scripts/import_config_and_create_user.py"
    
    print_success "项目文件下载完成"
}

################################################################################
# 配置环境变量
################################################################################

configure_env() {
    print_header "配置环境变量"
    
    # 复制环境变量文件
    cp .env.example .env
    
    # 生成随机密钥
    print_info "生成随机密钥..."
    JWT_SECRET=$(openssl rand -base64 32 | tr -d '\n')
    MONGO_PASSWORD=$(openssl rand -base64 16 | tr -d '\n')
    REDIS_PASSWORD=$(openssl rand -base64 16 | tr -d '\n')
    
    # 获取服务器 IP
    SERVER_IP=$(curl -s ifconfig.me || echo "localhost")
    
    # 更新 .env 文件
    sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=production/" .env
    sed -i "s/SERVER_HOST=.*/SERVER_HOST=$SERVER_IP/" .env
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    sed -i "s/MONGO_PASSWORD=.*/MONGO_PASSWORD=$MONGO_PASSWORD/" .env
    sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
    sed -i "s|MONGO_URI=.*|MONGO_URI=mongodb://admin:$MONGO_PASSWORD@mongodb:27017/tradingagents?authSource=admin|" .env
    
    print_success "环境变量配置完成"
    print_info "服务器地址: $SERVER_IP"
}

################################################################################
# 启动服务
################################################################################

start_services() {
    print_header "启动服务"
    
    print_info "拉取 Docker 镜像..."
    docker compose -f docker-compose.hub.yml pull
    
    print_info "启动容器..."
    docker compose -f docker-compose.hub.yml up -d
    
    print_info "等待服务启动..."
    sleep 15
    
    # 检查容器状态
    if docker compose -f docker-compose.hub.yml ps | grep -q "Up"; then
        print_success "服务启动成功"
    else
        print_error "服务启动失败"
        docker compose -f docker-compose.hub.yml logs
        exit 1
    fi
}

################################################################################
# 导入配置数据
################################################################################

import_data() {
    print_header "导入配置数据"
    
    # 安装 Python 依赖
    print_info "安装 Python 依赖..."
    if check_command pip3; then
        pip3 install pymongo --quiet
    elif check_command pip; then
        pip install pymongo --quiet
    else
        print_error "未找到 pip，请手动安装 pymongo"
        exit 1
    fi
    
    # 运行导入脚本
    print_info "导入配置数据并创建默认用户..."
    python3 scripts/import_config_and_create_user.py
    
    # 重启后端服务
    print_info "重启后端服务..."
    docker restart tradingagents-backend
    sleep 5
    
    print_success "配置数据导入完成"
}

################################################################################
# 验证部署
################################################################################

verify_deployment() {
    print_header "验证部署"
    
    # 检查容器状态
    print_info "检查容器状态..."
    docker compose -f docker-compose.hub.yml ps
    
    # 测试后端 API
    print_info "测试后端 API..."
    if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
        print_success "后端 API 正常"
    else
        print_warning "后端 API 可能未就绪，请稍后检查"
    fi
    
    print_success "部署验证完成"
}

################################################################################
# 显示部署信息
################################################################################

show_info() {
    print_header "部署完成"
    
    SERVER_IP=$(curl -s ifconfig.me || echo "localhost")
    
    echo ""
    echo -e "${GREEN}🎉 TradingAgents 演示系统部署成功！${NC}"
    echo ""
    echo -e "${BLUE}访问信息:${NC}"
    echo -e "  前端地址: ${GREEN}http://$SERVER_IP:3000${NC}"
    echo -e "  后端地址: ${GREEN}http://$SERVER_IP:8000${NC}"
    echo ""
    echo -e "${BLUE}登录信息:${NC}"
    echo -e "  用户名: ${GREEN}admin${NC}"
    echo -e "  密码: ${GREEN}admin123${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  重要提示:${NC}"
    echo -e "  1. 请立即登录并修改默认密码"
    echo -e "  2. 配置 LLM API 密钥以使用分析功能"
    echo -e "  3. 建议配置防火墙和 HTTPS"
    echo ""
    echo -e "${BLUE}常用命令:${NC}"
    echo -e "  查看日志: ${GREEN}docker compose -f docker-compose.hub.yml logs -f${NC}"
    echo -e "  重启服务: ${GREEN}docker compose -f docker-compose.hub.yml restart${NC}"
    echo -e "  停止服务: ${GREEN}docker compose -f docker-compose.hub.yml stop${NC}"
    echo ""
    echo -e "${BLUE}文档:${NC}"
    echo -e "  完整文档: ${GREEN}https://github.com/your-org/TradingAgents-CN/blob/main/docs/deploy_demo_system.md${NC}"
    echo ""
}

################################################################################
# 主函数
################################################################################

main() {
    print_header "TradingAgents 演示系统一键部署"
    
    echo "本脚本将自动完成以下操作:"
    echo "  1. 检查系统要求"
    echo "  2. 安装 Docker 和 Docker Compose"
    echo "  3. 下载项目文件"
    echo "  4. 配置环境变量"
    echo "  5. 启动服务"
    echo "  6. 导入配置数据"
    echo "  7. 创建默认管理员账号"
    echo ""
    read -p "是否继续? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
        print_error "部署已取消"
        exit 1
    fi
    
    check_system
    install_docker
    download_files
    configure_env
    start_services
    import_data
    verify_deployment
    show_info
}

# 运行主函数
main

