#!/bin/bash
# ChromaDB 问题诊断和修复脚本 (Linux/Mac版本)
# 用于解决 "Configuration error: An instance of Chroma already exists for ephemeral with different settings" 错误

echo "=== ChromaDB 问题诊断和修复工具 ==="
echo "适用环境: Linux/Mac Bash"
echo ""

# 1. 检查Python进程中的ChromaDB实例
echo "1. 检查Python进程..."
python_pids=$(pgrep -f python)
if [ ! -z "$python_pids" ]; then
    echo "发现Python进程:"
    ps aux | grep python | grep -v grep
    echo ""
    read -p "是否终止所有Python进程? (y/N): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        pkill -f python
        echo "✅ 已终止所有Python进程"
        sleep 2
    fi
else
    echo "✅ 未发现Python进程"
fi

# 2. 清理ChromaDB临时文件和缓存
echo ""
echo "2. 清理ChromaDB临时文件..."

# 清理临时目录中的ChromaDB文件
temp_paths=(
    "/tmp/chroma*"
    "$HOME/.chroma*"
    "./chroma*"
    "./.chroma*"
)

cleaned_files=0
for path in "${temp_paths[@]}"; do
    if ls $path 1> /dev/null 2>&1; then
        echo "清理: $path"
        rm -rf $path 2>/dev/null || echo "⚠️ 无法删除: $path"
        ((cleaned_files++))
    fi
done

if [ $cleaned_files -gt 0 ]; then
    echo "✅ 已清理 $cleaned_files 个ChromaDB临时文件"
else
    echo "✅ 未发现ChromaDB临时文件"
fi

# 3. 清理Python缓存
echo ""
echo "3. 清理Python缓存..."
pycache_paths=(
    "./__pycache__"
    "./tradingagents/__pycache__"
    "./tradingagents/agents/__pycache__"
    "./tradingagents/agents/utils/__pycache__"
)

cleaned_cache=0
for path in "${pycache_paths[@]}"; do
    if [ -d "$path" ]; then
        rm -rf "$path"
        echo "清理: $path"
        ((cleaned_cache++))
    fi
done

if [ $cleaned_cache -gt 0 ]; then
    echo "✅ 已清理 $cleaned_cache 个Python缓存目录"
else
    echo "✅ 未发现Python缓存目录"
fi

# 4. 检查ChromaDB版本兼容性
echo ""
echo "4. 检查ChromaDB版本..."
chroma_version=$(python -c "import chromadb; print(chromadb.__version__)" 2>/dev/null)
if [ ! -z "$chroma_version" ]; then
    echo "ChromaDB版本: $chroma_version"
    
    # 检查是否为推荐版本
    if [[ "$chroma_version" == 1.0.* ]]; then
        echo "✅ ChromaDB版本兼容"
    else
        echo "⚠️ 建议使用ChromaDB 1.0.x版本"
        read -p "是否升级ChromaDB? (y/N): " upgrade
        if [[ "$upgrade" == "y" || "$upgrade" == "Y" ]]; then
            echo "升级ChromaDB..."
            pip install --upgrade "chromadb>=1.0.12"
        fi
    fi
else
    echo "❌ 无法检测ChromaDB版本"
fi

# 5. 检查环境变量冲突
echo ""
echo "5. 检查环境变量..."
chroma_env_vars=(
    "CHROMA_HOST"
    "CHROMA_PORT"
    "CHROMA_DB_IMPL"
    "CHROMA_API_IMPL"
    "CHROMA_TELEMETRY"
)

found_env_vars=()
for var in "${chroma_env_vars[@]}"; do
    value=$(printenv $var)
    if [ ! -z "$value" ]; then
        found_env_vars+=("$var=$value")
    fi
done

if [ ${#found_env_vars[@]} -gt 0 ]; then
    echo "发现ChromaDB环境变量:"
    for var in "${found_env_vars[@]}"; do
        echo "  $var"
    done
    echo "⚠️ 这些环境变量可能导致配置冲突"
else
    echo "✅ 未发现ChromaDB环境变量冲突"
fi

# 6. 测试ChromaDB初始化
echo ""
echo "6. 测试ChromaDB初始化..."
test_script='
import chromadb
from chromadb.config import Settings
import sys

try:
    # 测试基本初始化
    client = chromadb.Client()
    print("✅ 基本初始化成功")
    
    # 测试项目配置
    settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False,
        is_persistent=False
    )
    client2 = chromadb.Client(settings)
    print("✅ 项目配置初始化成功")
    
    # 测试集合创建
    collection = client2.create_collection(name="test_collection")
    print("✅ 集合创建成功")
    
    # 清理测试
    client2.delete_collection(name="test_collection")
    print("✅ ChromaDB测试完成")
    
except Exception as e:
    print(f"❌ ChromaDB测试失败: {e}")
    sys.exit(1)
'

python -c "$test_script" 2>&1

# 7. 提供解决方案建议
echo ""
echo "=== 解决方案建议 ==="
echo "如果问题仍然存在，请尝试以下方案:"
echo ""
echo "方案1: 重启系统"
echo "  - 完全清理内存中的ChromaDB实例"
echo ""
echo "方案2: 使用虚拟环境"
echo "  python -m venv fresh_env"
echo "  source fresh_env/bin/activate"
echo "  pip install -r requirements.txt"
echo ""
echo "方案3: 重新安装ChromaDB"
echo "  pip uninstall chromadb -y"
echo "  pip install chromadb==1.0.12"
echo ""
echo "方案4: 检查Python版本兼容性"
echo "  - 确保使用Python 3.8-3.11"
echo "  - 避免使用Python 3.12+"
echo ""

echo "🔧 修复完成！请重新运行应用程序。"