#!/bin/bash
# TradingAgents 目录初始化脚本
# 创建Docker容器需要的本地目录结构

echo "🚀 TradingAgents 目录初始化"
echo "=========================="

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 项目根目录: $PROJECT_ROOT"

# 创建必要的目录
DIRECTORIES=(
    "logs"
    "data"
    "data/cache"
    "data/exports"
    "data/temp"
    "config"
    "config/runtime"
)

echo ""
echo "📂 创建目录结构..."

for dir in "${DIRECTORIES[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "✅ 创建目录: $dir"
    else
        echo "📁 目录已存在: $dir"
    fi
done

# 设置目录权限
echo ""
echo "🔧 设置目录权限..."

# 确保日志目录可写
chmod 755 logs
echo "✅ 设置 logs 目录权限: 755"

# 确保数据目录可写
chmod 755 data
chmod 755 data/cache
chmod 755 data/exports
chmod 755 data/temp
echo "✅ 设置 data 目录权限: 755"

# 确保配置目录可写
chmod 755 config
chmod 755 config/runtime
echo "✅ 设置 config 目录权限: 755"

# 创建 .gitkeep 文件保持目录结构
echo ""
echo "📝 创建 .gitkeep 文件..."

GITKEEP_DIRS=(
    "logs"
    "data/cache"
    "data/exports"
    "data/temp"
    "config/runtime"
)

for dir in "${GITKEEP_DIRS[@]}"; do
    if [ ! -f "$dir/.gitkeep" ]; then
        touch "$dir/.gitkeep"
        echo "✅ 创建: $dir/.gitkeep"
    fi
done

# 创建日志配置文件
echo ""
echo "📋 创建日志配置文件..."

LOG_CONFIG_FILE="config/logging.toml"
if [ ! -f "$LOG_CONFIG_FILE" ]; then
    cat > "$LOG_CONFIG_FILE" << 'EOF'
# TradingAgents 日志配置文件
[logging]
version = 1
disable_existing_loggers = false

[logging.formatters.standard]
format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"

[logging.formatters.detailed]
format = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"

[logging.handlers.console]
class = "logging.StreamHandler"
level = "INFO"
formatter = "standard"
stream = "ext://sys.stdout"

[logging.handlers.file]
class = "logging.handlers.RotatingFileHandler"
level = "DEBUG"
formatter = "detailed"
filename = "/app/logs/tradingagents.log"
maxBytes = 104857600  # 100MB
backupCount = 5
encoding = "utf8"

[logging.handlers.error_file]
class = "logging.handlers.RotatingFileHandler"
level = "ERROR"
formatter = "detailed"
filename = "/app/logs/tradingagents_error.log"
maxBytes = 52428800  # 50MB
backupCount = 3
encoding = "utf8"

[logging.loggers.tradingagents]
level = "DEBUG"
handlers = ["console", "file", "error_file"]
propagate = false

[logging.loggers.streamlit]
level = "INFO"
handlers = ["console", "file"]
propagate = false

[logging.loggers.akshare]
level = "WARNING"
handlers = ["file"]
propagate = false

[logging.loggers.tushare]
level = "WARNING"
handlers = ["file"]
propagate = false

[logging.root]
level = "INFO"
handlers = ["console", "file"]
EOF
    echo "✅ 创建日志配置: $LOG_CONFIG_FILE"
else
    echo "📁 日志配置已存在: $LOG_CONFIG_FILE"
fi

# 创建 .gitignore 文件
echo ""
echo "📝 更新 .gitignore 文件..."

GITIGNORE_ENTRIES=(
    "# 日志文件"
    "logs/*.log"
    "logs/*.log.*"
    ""
    "# 数据缓存"
    "data/cache/*"
    "data/temp/*"
    "!data/cache/.gitkeep"
    "!data/temp/.gitkeep"
    ""
    "# 运行时配置"
    "config/runtime/*"
    "!config/runtime/.gitkeep"
    ""
    "# 导出文件"
    "data/exports/*.pdf"
    "data/exports/*.docx"
    "data/exports/*.xlsx"
    "!data/exports/.gitkeep"
)

# 检查 .gitignore 是否存在
if [ ! -f ".gitignore" ]; then
    touch ".gitignore"
fi

# 添加条目到 .gitignore（如果不存在）
for entry in "${GITIGNORE_ENTRIES[@]}"; do
    if [ -n "$entry" ] && ! grep -Fxq "$entry" .gitignore; then
        echo "$entry" >> .gitignore
    fi
done

echo "✅ 更新 .gitignore 文件"

# 创建 README 文件
echo ""
echo "📚 创建目录说明文件..."

README_FILE="logs/README.md"
if [ ! -f "$README_FILE" ]; then
    cat > "$README_FILE" << 'EOF'
# TradingAgents 日志目录

此目录用于存储 TradingAgents 应用的日志文件。

## 日志文件说明

- `tradingagents.log` - 主应用日志文件
- `tradingagents_error.log` - 错误日志文件
- `tradingagents.log.1`, `tradingagents.log.2` 等 - 轮转的历史日志文件

## 日志级别

- **DEBUG** - 详细的调试信息
- **INFO** - 一般信息
- **WARNING** - 警告信息
- **ERROR** - 错误信息
- **CRITICAL** - 严重错误

## 日志轮转

- 主日志文件最大 100MB，保留 5 个历史文件
- 错误日志文件最大 50MB，保留 3 个历史文件

## 获取日志

如果遇到问题需要发送日志给开发者，请发送：
1. `tradingagents.log` - 主日志文件
2. `tradingagents_error.log` - 错误日志文件（如果存在）

## Docker 环境

在 Docker 环境中，此目录映射到容器内的 `/app/logs` 目录。
EOF
    echo "✅ 创建日志说明: $README_FILE"
fi

# 显示目录结构
echo ""
echo "📋 目录结构预览:"
echo "=================="

if command -v tree >/dev/null 2>&1; then
    tree -a -I '.git' --dirsfirst -L 3
else
    find . -type d -not -path './.git*' | head -20 | sort
fi

echo ""
echo "🎉 目录初始化完成！"
echo ""
echo "💡 接下来的步骤:"
echo "1. 运行 Docker Compose: docker-compose up -d"
echo "2. 检查日志文件: ls -la logs/"
echo "3. 实时查看日志: tail -f logs/tradingagents.log"
echo ""
echo "📁 重要目录说明:"
echo "   logs/     - 应用日志文件"
echo "   data/     - 数据缓存和导出文件"
echo "   config/   - 运行时配置文件"
echo ""
echo "🔧 如果遇到权限问题，请运行:"
echo "   sudo chown -R \$USER:\$USER logs data config"
