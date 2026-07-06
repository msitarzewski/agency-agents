#!/bin/bash
# 检查Docker构建上下文的脚本

echo "=========================================="
echo "检查Docker构建上下文"
echo "=========================================="
echo ""

# 检查当前目录
echo "当前目录: $(pwd)"
echo ""

# 检查必需的文件
echo "检查必需的文件："
echo ""

files=(
    "pyproject.toml"
    "Dockerfile.backend"
    "Dockerfile.frontend"
    "frontend/package.json"
    "frontend/yarn.lock"
    "frontend/src/main.ts"
    "frontend/vite.config.ts"
    "app/main.py"
    "tradingagents/__init__.py"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (不存在)"
        all_exist=false
    fi
done

echo ""

if [ "$all_exist" = true ]; then
    echo "✅ 所有必需文件都存在，可以开始构建"
    echo ""
    echo "构建命令："
    echo "  后端: docker build -f Dockerfile.backend -t tradingagents-backend:v1.0.0-preview ."
    echo "  前端: docker build -f Dockerfile.frontend -t tradingagents-frontend:v1.0.0-preview ."
else
    echo "❌ 缺少必需文件，请确保在项目根目录执行此脚本"
    exit 1
fi

echo ""
echo "检查frontend目录结构："
if [ -d "frontend" ]; then
    echo "frontend/"
    ls -la frontend/ | head -20
else
    echo "❌ frontend目录不存在！"
    exit 1
fi

