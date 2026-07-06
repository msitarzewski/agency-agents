#!/bin/bash
# TradingAgents-CN 简化启动脚本 (Linux/Mac)
# 用于日常快速启动应用

echo ""
echo "========================================"
echo "  TradingAgents-CN 快速启动"
echo "========================================"
echo ""

# 检查虚拟环境
if [ ! -f ".venv/bin/activate" ]; then
    echo "[错误] 虚拟环境不存在"
    echo ""
    echo "请先运行安装脚本:"
    echo "  chmod +x scripts/easy_install.sh"
    echo "  ./scripts/easy_install.sh"
    echo ""
    exit 1
fi

# 激活虚拟环境
echo "[1/3] 激活虚拟环境..."
source .venv/bin/activate

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "[警告] 配置文件不存在"
    echo ""
    echo "请先运行安装脚本或手动创建 .env 文件"
    echo ""
    exit 1
fi

# 启动应用
echo "[2/3] 启动Web应用..."
echo ""
echo "========================================"
echo "  应用正在启动..."
echo "  浏览器将自动打开 http://localhost:8501"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止应用"
echo ""

python start_web.py

echo ""
echo "[3/3] 应用已停止"

