# 配置导入脚本使用说明

## 功能概述

`import_config_and_create_user.py` 脚本用于：
1. 从导出的 JSON 文件导入配置数据到 MongoDB
2. 创建默认管理员用户（admin/admin123）
3. 支持在 Docker 容器内或宿主机上运行

## 运行环境

### 1. 在 Docker 容器内运行（默认）

适用场景：在测试服务器上，通过 Docker 容器运行脚本

```bash
# 进入后端容器
docker exec -it tradingagents-backend bash

# 运行脚本（使用默认配置文件）
python scripts/import_config_and_create_user.py

# 或指定配置文件
python scripts/import_config_and_create_user.py /path/to/export.json
```

**连接信息：**
- MongoDB 地址：`mongodb:27017`（Docker 内部服务名）
- 数据库：`tradingagents`
- 认证：`admin/tradingagents123`

### 2. 在宿主机上运行

适用场景：在开发机上，直接运行脚本（不进入容器）

```bash
# 使用 --host 参数
python scripts/import_config_and_create_user.py --host

# 或指定配置文件
python scripts/import_config_and_create_user.py --host /path/to/export.json
```

**连接信息：**
- MongoDB 地址：`localhost:27017`（宿主机端口映射）
- 数据库：`tradingagents`
- 认证：`admin/tradingagents123`

**前提条件：**
- MongoDB 容器已启动
- 端口 27017 已映射到宿主机

## 常用命令

### 基本导入

```bash
# Docker 容器内运行（默认）
python scripts/import_config_and_create_user.py

# 宿主机运行
python scripts/import_config_and_create_user.py --host
```

### 覆盖已存在的数据

```bash
# 删除现有数据并重新导入
python scripts/import_config_and_create_user.py --overwrite

# 宿主机运行 + 覆盖
python scripts/import_config_and_create_user.py --host --overwrite
```

### 只导入指定集合

```bash
# 只导入 system_configs 和 users
python scripts/import_config_and_create_user.py --collections system_configs users

# 宿主机运行 + 指定集合
python scripts/import_config_and_create_user.py --host --collections llm_providers model_catalog
```

### 只创建用户

```bash
# 不导入数据，只创建默认管理员用户
python scripts/import_config_and_create_user.py --create-user-only

# 宿主机运行 + 只创建用户
python scripts/import_config_and_create_user.py --host --create-user-only
```

### 跳过创建用户

```bash
# 只导入数据，不创建用户
python scripts/import_config_and_create_user.py --skip-user
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `export_file` | 导出的 JSON 文件路径 | `install/database_export_config_*.json`（最新文件） |
| `--host` | 在宿主机运行（连接 localhost:27017） | 否（默认在 Docker 内运行） |
| `--overwrite` | 覆盖已存在的数据 | 否（默认跳过已存在的数据） |
| `--collections` | 指定要导入的集合 | 所有配置集合 |
| `--create-user-only` | 只创建默认用户，不导入数据 | 否 |
| `--skip-user` | 跳过创建默认用户 | 否 |

## 导入的集合

脚本会导入以下集合（如果存在于导出文件中）：

- `system_configs` - 系统配置
- `users` - 用户信息
- `llm_providers` - LLM 厂家配置
- `market_categories` - 市场分类
- `user_tags` - 用户标签
- `datasource_groupings` - 数据源分组
- `platform_configs` - 平台配置
- `user_configs` - 用户配置
- `model_catalog` - 模型目录

## 默认管理员用户

脚本会创建以下默认管理员用户：

- **用户名：** `admin`
- **密码：** `admin123`
- **邮箱：** `admin@tradingagents.cn`
- **角色：** 管理员
- **状态：** 已激活、已验证

## 故障排查

### 1. 连接失败（Docker 容器内）

**错误信息：**
```
❌ 错误: MongoDB 连接失败: ...
```

**解决方案：**
```bash
# 检查 MongoDB 容器是否运行
docker ps | grep mongodb

# 检查容器网络
docker network inspect tradingagents-network

# 确保后端容器和 MongoDB 容器在同一网络
```

### 2. 连接失败（宿主机）

**错误信息：**
```
❌ 错误: MongoDB 连接失败: ...
```

**解决方案：**
```bash
# 检查端口映射
docker ps | grep 27017

# 确保 MongoDB 容器映射了 27017 端口
# docker-compose.yml 中应该有：
# ports:
#   - "27017:27017"
```

### 3. 文件不存在

**错误信息：**
```
❌ 错误: 文件不存在: ...
```

**解决方案：**
```bash
# 检查 install 目录
ls -la install/database_export_config_*.json

# 或指定完整路径
python scripts/import_config_and_create_user.py /full/path/to/export.json
```

## 完整示例

### 场景 1：测试服务器首次部署

```bash
# 1. 进入后端容器
docker exec -it tradingagents-backend bash

# 2. 导入配置并创建用户
python scripts/import_config_and_create_user.py

# 3. 退出容器
exit

# 4. 重启后端服务
docker restart tradingagents-backend

# 5. 访问前端并登录
# 用户名: admin
# 密码: admin123
```

### 场景 2：开发机测试

```bash
# 1. 确保 MongoDB 容器运行
docker ps | grep mongodb

# 2. 在宿主机运行脚本
python scripts/import_config_and_create_user.py --host

# 3. 重启后端服务
docker restart tradingagents-backend
```

### 场景 3：更新配置（覆盖模式）

```bash
# 1. 备份现有数据（可选）
docker exec tradingagents-backend python scripts/export_config.py

# 2. 导入新配置（覆盖）
docker exec tradingagents-backend python scripts/import_config_and_create_user.py --overwrite

# 3. 重启后端服务
docker restart tradingagents-backend
```

## 注意事项

1. **数据备份：** 使用 `--overwrite` 前建议先备份现有数据
2. **用户密码：** 首次登录后请立即修改默认密码
3. **API Key：** 导入的配置中 API Key 已脱敏，需要在前端重新配置
4. **环境变量：** 确保 `.env` 文件中的 MongoDB 连接信息正确
5. **网络连接：** Docker 容器内运行时，确保容器在同一网络中

## 相关脚本

- `scripts/export_config.py` - 导出配置数据
- `scripts/backup_database.py` - 备份数据库
- `scripts/restore_database.py` - 恢复数据库

