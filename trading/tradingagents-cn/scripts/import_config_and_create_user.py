#!/usr/bin/env python3
"""
导入配置数据并创建默认用户

功能：
1. 从导出的 JSON 文件导入配置数据到 MongoDB
2. 创建默认管理员用户（admin/admin123）
3. 支持选择性导入集合
4. 支持覆盖或跳过已存在的数据

使用方法：
    python scripts/import_config_and_create_user.py <export_file.json>
    python scripts/import_config_and_create_user.py <export_file.json> --overwrite
    python scripts/import_config_and_create_user.py <export_file.json> --collections system_configs users
"""

import json
import sys
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from bson import ObjectId


def load_env_config(script_dir: Path) -> dict:
    """从 .env 文件加载配置

    Args:
        script_dir: 脚本所在目录

    Returns:
        配置字典，包含 mongodb_port 等
    """
    # 查找 .env 文件（在项目根目录）
    env_file = script_dir.parent / '.env'

    config = {
        'mongodb_port': 27017,  # 默认端口
        'mongodb_host': 'localhost',
        'mongodb_username': 'admin',
        'mongodb_password': 'tradingagents123',
        'mongodb_database': 'tradingagents',
        'mongodb_auth_source': 'admin',
        'mongodb_connection_string': None,
    }

    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        if key == 'MONGODB_PORT':
                            config['mongodb_port'] = int(value)
                        elif key == 'MONGODB_HOST':
                            config['mongodb_host'] = value
                        elif key == 'MONGODB_USERNAME':
                            config['mongodb_username'] = value
                        elif key == 'MONGODB_PASSWORD':
                            config['mongodb_password'] = value
                        elif key == 'MONGODB_DATABASE_NAME':
                            config['mongodb_database'] = value
                        elif key == 'MONGODB_DATABASE':
                            # 仅在没有更显式的 DATABASE_NAME 时作为回退
                            if not config.get('mongodb_database') or config['mongodb_database'] == 'tradingagents':
                                config['mongodb_database'] = value
                        elif key == 'MONGODB_AUTH_SOURCE':
                            config['mongodb_auth_source'] = value
                        elif key == 'MONGODB_CONNECTION_STRING':
                            config['mongodb_connection_string'] = value
        except Exception as e:
            print(f"⚠️  警告: 读取 .env 文件失败: {e}")
            print(f"   使用默认配置")
    else:
        print(f"⚠️  警告: .env 文件不存在: {env_file}")
        print(f"   使用默认配置")

    return config


# 默认管理员用户
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "email": "admin@tradingagents.cn"
}

# 配置集合列表（按照导出顺序）
CONFIG_COLLECTIONS = [
    # v2.0 核心配置
    "workflow_definitions",
    "workflows",
    "agent_configs",
    "tool_configs",
    "tool_agent_bindings",
    "agent_workflow_bindings",
    "agent_io_definitions",

    # 系统配置
    "system_configs",
    "llm_providers",
    "model_catalog",
    "platform_configs",
    "datasource_groupings",
    "market_categories",
    "smtp_config",
    "sync_status",

    # 用户相关
    "users",
    "user_tags",
    "user_favorites",

    # 交易系统
    "trading_systems",
    "paper_accounts",
    "paper_market_rules",
    "real_accounts",

    # 提示词
    "prompt_templates",
    "user_template_configs",

    # 调度任务
    "scheduled_analysis_configs",
    "scheduler_metadata",

    # 其他配置
    "watchlist_groups",

    # 分析报告
    "unified_analysis_tasks",
    "analysis_tasks",
    "analysis_reports",
    "position_analysis_reports",
    "portfolio_analysis_reports",

    # 历史记录（可选）
    "workflow_history",
    "template_history",
    "scheduled_analysis_history",
    "notifications",
    "email_records",

    # 交易记录（可选）
    "paper_positions",
    "paper_orders",
    "paper_trades",
    "real_positions",
    "capital_transactions",
    "position_changes",
    "trade_reviews",
    "trading_system_evaluations",
]

# 增量模式下各集合的唯一键（用于判断文档是否已存在，避免重复插入）
# 支持单键或键列表（多键组合）
COLLECTION_UNIQUE_KEYS = {
    "agent_configs": ["agent_id"],
    "prompt_templates": ["agent_id", "preference_type"],
    "system_configs": ["key"],
    "workflow_definitions": ["id"],
    "workflows": ["id"],
    "tool_configs": ["tool_id"],  # fallback: name
    "llm_providers": ["provider_id"],
    "model_catalog": ["model_id"],
    "platform_configs": ["platform_id"],
    "datasource_groupings": ["name"],
    "market_categories": ["name"],
    "tool_agent_bindings": ["tool_id", "agent_id"],
    "agent_workflow_bindings": ["agent_id", "workflow_id"],
}


def _build_unique_query(doc: Dict[str, Any], collection_name: str) -> Optional[Dict[str, Any]]:
    """根据集合的唯一键构建查询条件"""
    if "_id" in doc:
        return {"_id": doc["_id"]}
    keys = COLLECTION_UNIQUE_KEYS.get(collection_name)
    if keys:
        query = {}
        for k in keys:
            if k in doc and doc[k] is not None:
                query[k] = doc[k]
        if query:
            return query
        # 单键集合若主键缺失，尝试备用键
        if collection_name == "tool_configs" and "name" in doc:
            return {"name": doc["name"]}
    # 通用回退
    if "username" in doc:
        return {"username": doc["username"]}
    if "name" in doc:
        return {"name": doc["name"]}
    if "key" in doc:
        return {"key": doc["key"]}
    return None


def hash_password(password: str) -> str:
    """使用 SHA256 哈希密码（与系统一致）"""
    return hashlib.sha256(password.encode()).hexdigest()


def convert_to_bson(data: Any) -> Any:
    """将 JSON 数据转换为 BSON 兼容格式"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 处理 ObjectId
            if key == "_id" or key.endswith("_id"):
                if isinstance(value, str) and len(value) == 24:
                    try:
                        result[key] = ObjectId(value)
                        continue
                    except:
                        pass
            
            # 处理日期时间
            if key.endswith("_at") or key in ["created_at", "updated_at", "last_login", "added_at"]:
                if isinstance(value, str):
                    try:
                        result[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        continue
                    except:
                        pass
            
            result[key] = convert_to_bson(value)
        return result
    
    elif isinstance(data, list):
        return [convert_to_bson(item) for item in data]
    
    else:
        return data


def load_export_file(file_path: str) -> Dict[str, Any]:
    """加载导出的 JSON 文件"""
    print(f"\n📂 加载导出文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "export_info" not in data or "data" not in data:
            print("❌ 错误: 文件格式不正确，缺少 export_info 或 data 字段")
            sys.exit(1)
        
        export_info = data["export_info"]
        print(f"✅ 文件加载成功")
        print(f"   导出时间: {export_info.get('created_at', 'Unknown')}")
        print(f"   导出格式: {export_info.get('format', 'Unknown')}")
        print(f"   集合数量: {len(export_info.get('collections', []))}")
        
        return data
    
    except FileNotFoundError:
        print(f"❌ 错误: 文件不存在: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 错误: JSON 解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: 加载文件失败: {e}")
        sys.exit(1)


def connect_mongodb(use_docker: bool = True, config: dict = None) -> MongoClient:
    """连接到 MongoDB

    Args:
        use_docker: True=在 Docker 容器内运行（使用 mongodb 服务名）
                   False=在宿主机运行（使用 localhost）
        config: 配置字典，包含端口等信息
    """
    if config is None:
        config = {
            'mongodb_port': 27017,
            'mongodb_host': 'localhost',
            'mongodb_username': 'admin',
            'mongodb_password': 'tradingagents123',
            'mongodb_database': 'tradingagents',
            'mongodb_auth_source': 'admin',
            'mongodb_connection_string': None,
        }

    database = config['mongodb_database']
    auth_source = config.get('mongodb_auth_source') or 'admin'
    mongo_uri = config.get('mongodb_connection_string')
    env_name = "Docker 容器内" if use_docker else "宿主机"

    if not mongo_uri:
        # 构建 MongoDB URI
        host = 'mongodb' if use_docker else config['mongodb_host']
        port = config['mongodb_port']
        username = config['mongodb_username']
        password = config['mongodb_password']
        mongo_uri = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource={auth_source}"
        masked_uri = f"mongodb://{username}:***@{host}:{port}/{database}?authSource={auth_source}"
    else:
        # 如果是 Docker 模式，并且 .env 写的是 localhost，则替换成容器内服务名
        if use_docker:
            mongo_uri = mongo_uri.replace("@localhost:", "@mongodb:")
            mongo_uri = mongo_uri.replace("//localhost:", "//mongodb:")
        masked_uri = re.sub(r"://([^:/]+):([^@]+)@", r"://\1:***@", mongo_uri)

    print(f"\n🔌 连接到 MongoDB ({env_name})...")
    print(f"   URI: {masked_uri}")
    print(f"   数据库: {database}")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # 测试连接
        client.admin.command('ping')
        print(f"✅ MongoDB 连接成功")
        return client

    except Exception as e:
        print(f"❌ 错误: MongoDB 连接失败: {e}")
        if use_docker:
            print(f"   请确保在 Docker 容器内运行，或使用 --host 参数在宿主机运行")
            print(f"   检查容器: docker ps | grep mongodb")
        else:
            print(f"   请确保 MongoDB 正在运行并监听端口 {port}")
            print(f"   检查端口: netstat -an | findstr {port}")
        sys.exit(1)


def import_collection(
    db: Any,
    collection_name: str,
    documents: List[Dict[str, Any]],
    overwrite: bool = False
) -> Dict[str, int]:
    """导入单个集合"""
    collection = db[collection_name]
    
    # 转换文档格式
    converted_docs = [convert_to_bson(doc) for doc in documents]
    
    if overwrite:
        # 覆盖模式：删除现有数据
        result = collection.delete_many({})
        deleted_count = result.deleted_count
        
        if converted_docs:
            result = collection.insert_many(converted_docs)
            inserted_count = len(result.inserted_ids)
        else:
            inserted_count = 0
        
        return {
            "deleted": deleted_count,
            "inserted": inserted_count,
            "skipped": 0
        }
    else:
        # 增量模式：跳过已存在的文档（使用集合专属唯一键）
        inserted_count = 0
        skipped_count = 0

        for doc in converted_docs:
            query = _build_unique_query(doc, collection_name)
            if query is None:
                # 没有唯一标识，直接插入（可能产生重复，但部分集合无稳定唯一键）
                collection.insert_one(doc)
                inserted_count += 1
                continue

            existing = collection.find_one(query)
            if existing:
                skipped_count += 1
            else:
                collection.insert_one(doc)
                inserted_count += 1

        return {
            "deleted": 0,
            "inserted": inserted_count,
            "skipped": skipped_count
        }


def create_default_admin(db: Any, overwrite: bool = False) -> bool:
    """创建默认管理员用户"""
    print(f"\n👤 创建默认管理员用户...")
    
    users_collection = db.users
    
    # 检查用户是否已存在
    existing_user = users_collection.find_one({"username": DEFAULT_ADMIN["username"]})
    
    if existing_user:
        if not overwrite:
            print(f"⚠️  用户 '{DEFAULT_ADMIN['username']}' 已存在，跳过创建")
            return False
        else:
            print(f"⚠️  用户 '{DEFAULT_ADMIN['username']}' 已存在，将覆盖")
            users_collection.delete_one({"username": DEFAULT_ADMIN["username"]})
    
    # 创建用户文档
    user_doc = {
        "username": DEFAULT_ADMIN["username"],
        "email": DEFAULT_ADMIN["email"],
        "hashed_password": hash_password(DEFAULT_ADMIN["password"]),
        "is_active": True,
        "is_verified": True,
        "is_admin": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None,
        "preferences": {
            "default_market": "A股",
            "default_depth": "深度",
            "ui_theme": "light",
            "language": "zh-CN",
            "notifications_enabled": True,
            "email_notifications": False
        },
        "daily_quota": 10000,
        "concurrent_limit": 10,
        "total_analyses": 0,
        "successful_analyses": 0,
        "failed_analyses": 0,
        "favorite_stocks": []
    }
    
    users_collection.insert_one(user_doc)
    
    print(f"✅ 默认管理员用户创建成功")
    print(f"   用户名: {DEFAULT_ADMIN['username']}")
    print(f"   密码: {DEFAULT_ADMIN['password']}")
    print(f"   邮箱: {DEFAULT_ADMIN['email']}")
    print(f"   角色: 管理员")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="导入配置数据并创建默认用户",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 在 Docker 容器内运行（默认）
  python scripts/import_config_and_create_user.py

  # 在宿主机运行（连接到 localhost:27017）
  python scripts/import_config_and_create_user.py --host

  # 从指定文件导入（默认覆盖模式）
  python scripts/import_config_and_create_user.py export.json

  # 增量模式：跳过已存在的数据
  python scripts/import_config_and_create_user.py --incremental

  # 只导入指定的集合
  python scripts/import_config_and_create_user.py --collections system_configs users

  # 只创建默认用户，不导入数据
  python scripts/import_config_and_create_user.py --create-user-only
        """
    )

    parser.add_argument(
        "export_file",
        nargs="?",
        help="导出的 JSON 文件路径（默认：install/database_export_config_*.json）"
    )
    parser.add_argument(
        "--host",
        action="store_true",
        help="在宿主机运行（连接 localhost:27017），默认在 Docker 容器内运行（连接 mongodb:27017）"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=True,
        help="覆盖已存在的数据（默认：覆盖）"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="增量模式：跳过已存在的数据"
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        help="指定要导入的集合（默认：所有配置集合）"
    )
    parser.add_argument(
        "--create-user-only",
        action="store_true",
        help="只创建默认用户，不导入数据"
    )
    parser.add_argument(
        "--skip-user",
        action="store_true",
        help="跳过创建默认用户"
    )
    parser.add_argument(
        "--mongodb-port",
        type=int,
        help="MongoDB 端口（覆盖 .env 配置）"
    )
    parser.add_argument(
        "--mongodb-host",
        type=str,
        help="MongoDB 主机（覆盖 .env 配置）"
    )

    args = parser.parse_args()

    # 处理 incremental 参数（如果指定了 --incremental，则 overwrite 为 False）
    if args.incremental:
        args.overwrite = False

    # 如果没有指定文件，尝试从 install 目录查找
    if not args.create_user_only and not args.export_file:
        install_dir = project_root / "install"
        if install_dir.exists():
            # 查找 database_export_config_*.json 文件
            config_files = list(install_dir.glob("database_export_config_*.json"))
            if config_files:
                # 使用最新的文件
                args.export_file = str(sorted(config_files)[-1])
                print(f"💡 未指定文件，使用默认配置: {args.export_file}")
            else:
                parser.error("install 目录中未找到配置文件 (database_export_config_*.json)")
        else:
            parser.error("必须提供导出文件路径，或使用 --create-user-only")
    
    print("=" * 80)
    print("📦 导入配置数据并创建默认用户")
    print("=" * 80)

    # 加载 .env 配置
    script_dir = Path(__file__).parent
    env_config = load_env_config(script_dir)

    # 命令行参数覆盖 .env 配置
    if args.mongodb_port:
        env_config['mongodb_port'] = args.mongodb_port
        print(f"💡 使用命令行指定的 MongoDB 端口: {args.mongodb_port}")
    if args.mongodb_host:
        env_config['mongodb_host'] = args.mongodb_host
        print(f"💡 使用命令行指定的 MongoDB 主机: {args.mongodb_host}")
        # 主机被显式覆盖时，不再复用 .env 里的完整连接串
        env_config['mongodb_connection_string'] = None

    # 连接数据库
    use_docker = not args.host  # 默认在 Docker 内运行，除非指定 --host
    client = connect_mongodb(use_docker=use_docker, config=env_config)
    db_name = env_config['mongodb_database']
    db = client[db_name]
    print(f"🎯 当前导入目标数据库: {db_name}")
    
    # 导入数据
    if not args.create_user_only:
        # 加载导出文件
        export_data = load_export_file(args.export_file)
        data = export_data["data"]
        
        # 确定要导入的集合
        if args.collections:
            collections_to_import = args.collections
        else:
            collections_to_import = [c for c in CONFIG_COLLECTIONS if c in data]
        
        print(f"\n📋 准备导入 {len(collections_to_import)} 个集合:")
        for col in collections_to_import:
            doc_count = len(data.get(col, []))
            print(f"   - {col}: {doc_count} 个文档")
        
        # 导入集合
        print(f"\n🚀 开始导入...")
        print(f"   模式: {'覆盖' if args.overwrite else '增量'}")
        
        total_stats = {
            "deleted": 0,
            "inserted": 0,
            "skipped": 0
        }
        
        for collection_name in collections_to_import:
            if collection_name not in data:
                print(f"⚠️  跳过 {collection_name}: 导出文件中不存在")
                continue
            
            documents = data[collection_name]
            print(f"\n   导入 {collection_name}...")
            
            try:
                stats = import_collection(db, collection_name, documents, args.overwrite)
                total_stats["deleted"] += stats["deleted"]
                total_stats["inserted"] += stats["inserted"]
                total_stats["skipped"] += stats["skipped"]
                
                if args.overwrite:
                    print(f"      ✅ 删除 {stats['deleted']} 个，插入 {stats['inserted']} 个")
                else:
                    print(f"      ✅ 插入 {stats['inserted']} 个，跳过 {stats['skipped']} 个")
            
            except Exception as e:
                print(f"      ❌ 失败: {e}")
        
        print(f"\n📊 导入统计:")
        if args.overwrite:
            print(f"   删除: {total_stats['deleted']} 个文档")
        print(f"   插入: {total_stats['inserted']} 个文档")
        if not args.overwrite:
            print(f"   跳过: {total_stats['skipped']} 个文档")
    
    # 创建默认用户
    if not args.skip_user:
        create_default_admin(db, args.overwrite)
    
    # 关闭连接
    client.close()
    
    print("\n" + "=" * 80)
    print("✅ 操作完成！")
    print("=" * 80)
    
    if not args.skip_user:
        print(f"\n🔐 登录信息:")
        print(f"   用户名: {DEFAULT_ADMIN['username']}")
        print(f"   密码: {DEFAULT_ADMIN['password']}")
    
    print(f"\n📝 后续步骤:")
    print(f"   1. 重启后端服务: docker restart tradingagents-backend")
    print(f"   2. 访问前端并使用默认账号登录")
    print(f"   3. 检查系统配置是否正确加载")


if __name__ == "__main__":
    main()

