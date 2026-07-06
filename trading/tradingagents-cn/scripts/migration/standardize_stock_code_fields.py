"""
数据库字段标准化迁移脚本
将所有集合的股票代码字段统一为 symbol 和 full_symbol

执行步骤:
1. 备份数据库
2. 添加新字段 (symbol, full_symbol)
3. 创建新索引
4. 验证数据完整性
5. (可选) 删除旧字段

使用方法:
    python scripts/migration/standardize_stock_code_fields.py --dry-run  # 预览
    python scripts/migration/standardize_stock_code_fields.py --execute  # 执行
    python scripts/migration/standardize_stock_code_fields.py --rollback # 回滚
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class StockCodeFieldMigration:
    """股票代码字段标准化迁移"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = None
        self.db = None
        self.backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def connect(self):
        """连接数据库"""
        mongo_host = os.getenv("MONGODB_HOST", "localhost")
        mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongo_username = os.getenv("MONGODB_USERNAME", "admin")
        mongo_password = os.getenv("MONGODB_PASSWORD", "tradingagents123")
        mongo_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
        db_name = os.getenv("MONGODB_DATABASE", "tradingagents")
        
        mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/?authSource={mongo_auth_source}"
        
        print(f"🔌 连接数据库: {mongo_host}:{mongo_port}/{db_name}")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        print("✅ 数据库连接成功")
        
    def disconnect(self):
        """断开数据库连接"""
        if self.client:
            self.client.close()
            print("🔌 数据库连接已关闭")
    
    def backup_collection(self, collection_name: str):
        """备份集合"""
        backup_name = f"{collection_name}_backup_{self.backup_suffix}"
        
        if self.dry_run:
            print(f"  [DRY-RUN] 将备份集合: {collection_name} -> {backup_name}")
            return
        
        print(f"  💾 备份集合: {collection_name} -> {backup_name}")
        
        # 复制集合
        pipeline = [{"$match": {}}, {"$out": backup_name}]
        list(self.db[collection_name].aggregate(pipeline))
        
        count = self.db[backup_name].count_documents({})
        print(f"  ✅ 备份完成: {count} 条记录")
    
    def migrate_stock_basic_info(self):
        """迁移 stock_basic_info 集合"""
        collection_name = "stock_basic_info"
        print(f"\n{'='*60}")
        print(f"📊 迁移集合: {collection_name}")
        print(f"{'='*60}")
        
        collection = self.db[collection_name]
        
        # 1. 备份
        self.backup_collection(collection_name)
        
        # 2. 统计当前状态
        total_count = collection.count_documents({})
        has_code = collection.count_documents({"code": {"$exists": True}})
        has_symbol = collection.count_documents({"symbol": {"$exists": True}})
        
        print(f"\n📈 当前状态:")
        print(f"  总记录数: {total_count}")
        print(f"  有 code 字段: {has_code}")
        print(f"  有 symbol 字段: {has_symbol}")
        
        # 3. 添加 symbol 和 full_symbol 字段
        print(f"\n🔄 添加新字段...")
        
        if self.dry_run:
            print(f"  [DRY-RUN] 将为 {has_code} 条记录添加 symbol 和 full_symbol")
            return
        
        # 更新记录
        update_pipeline = [
            {
                "$set": {
                    # 添加 symbol (从 code 复制)
                    "symbol": "$code",
                    # 添加 full_symbol (code + 市场后缀)
                    "full_symbol": {
                        "$concat": [
                            "$code",
                            ".",
                            {
                                "$switch": {
                                    "branches": [
                                        {
                                            "case": {"$regexMatch": {"input": "$market", "regex": "深圳"}},
                                            "then": "SZ"
                                        },
                                        {
                                            "case": {"$regexMatch": {"input": "$market", "regex": "上海"}},
                                            "then": "SH"
                                        },
                                        {
                                            "case": {"$regexMatch": {"input": "$market", "regex": "北京"}},
                                            "then": "BJ"
                                        }
                                    ],
                                    "default": "SZ"
                                }
                            }
                        ]
                    },
                    # 添加标准化的 market 字段
                    "market_code": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {"$regexMatch": {"input": "$market", "regex": "深圳"}},
                                    "then": "SZ"
                                },
                                {
                                    "case": {"$regexMatch": {"input": "$market", "regex": "上海"}},
                                    "then": "SH"
                                },
                                {
                                    "case": {"$regexMatch": {"input": "$market", "regex": "北京"}},
                                    "then": "BJ"
                                }
                            ],
                            "default": "SZ"
                        }
                    }
                }
            }
        ]
        
        result = collection.update_many(
            {"code": {"$exists": True}},
            update_pipeline
        )
        
        print(f"  ✅ 更新完成: {result.modified_count} 条记录")
        
        # 4. 创建新索引
        print(f"\n🔍 创建索引...")

        # 检查并删除旧索引
        existing_indexes = collection.list_indexes()
        index_names = [idx['name'] for idx in existing_indexes]

        # 如果存在旧的 symbol_1 索引（非唯一），删除它
        if "symbol_1" in index_names:
            print(f"  🗑️  删除旧索引: symbol_1")
            collection.drop_index("symbol_1")

        try:
            collection.create_index([("symbol", ASCENDING)], unique=True, name="symbol_1_unique")
            print(f"  ✅ 创建索引: symbol_1_unique")
        except Exception as e:
            print(f"  ⚠️  索引创建失败: symbol_1_unique - {e}")

        try:
            collection.create_index([("full_symbol", ASCENDING)], unique=True, name="full_symbol_1_unique")
            print(f"  ✅ 创建索引: full_symbol_1_unique")
        except Exception as e:
            print(f"  ⚠️  索引创建失败: full_symbol_1_unique - {e}")

        try:
            collection.create_index([("market_code", ASCENDING), ("symbol", ASCENDING)], name="market_symbol_1")
            print(f"  ✅ 创建索引: market_symbol_1")
        except Exception as e:
            print(f"  ⚠️  索引创建失败: market_symbol_1 - {e}")
        
        # 5. 验证
        self.verify_collection(collection_name)
    
    def migrate_analysis_tasks(self):
        """迁移 analysis_tasks 集合"""
        collection_name = "analysis_tasks"
        print(f"\n{'='*60}")
        print(f"📊 迁移集合: {collection_name}")
        print(f"{'='*60}")
        
        collection = self.db[collection_name]
        
        # 1. 备份
        self.backup_collection(collection_name)
        
        # 2. 统计当前状态
        total_count = collection.count_documents({})
        has_stock_code = collection.count_documents({"stock_code": {"$exists": True}})
        has_symbol = collection.count_documents({"symbol": {"$exists": True}})
        
        print(f"\n📈 当前状态:")
        print(f"  总记录数: {total_count}")
        print(f"  有 stock_code 字段: {has_stock_code}")
        print(f"  有 symbol 字段: {has_symbol}")
        
        # 3. 添加 symbol 字段
        print(f"\n🔄 添加新字段...")
        
        if self.dry_run:
            print(f"  [DRY-RUN] 将为 {has_stock_code} 条记录添加 symbol")
            return
        
        result = collection.update_many(
            {"stock_code": {"$exists": True}},
            [{"$set": {"symbol": "$stock_code"}}]
        )
        
        print(f"  ✅ 更新完成: {result.modified_count} 条记录")
        
        # 4. 创建新索引
        print(f"\n🔍 创建索引...")

        try:
            collection.create_index([("symbol", ASCENDING), ("created_at", DESCENDING)], name="symbol_created_at_1")
            print(f"  ✅ 创建索引: symbol_created_at_1")
        except Exception as e:
            print(f"  ⚠️  索引创建失败: symbol_created_at_1 - {e}")

        try:
            collection.create_index([("user_id", ASCENDING), ("symbol", ASCENDING)], name="user_symbol_1")
            print(f"  ✅ 创建索引: user_symbol_1")
        except Exception as e:
            print(f"  ⚠️  索引创建失败: user_symbol_1 - {e}")
        
        # 5. 验证
        self.verify_collection(collection_name)
    
    def verify_collection(self, collection_name: str):
        """验证集合数据完整性"""
        print(f"\n🔍 验证数据完整性...")
        
        collection = self.db[collection_name]
        
        if collection_name == "stock_basic_info":
            # 验证 symbol 和 full_symbol
            total = collection.count_documents({})
            has_symbol = collection.count_documents({"symbol": {"$exists": True, "$ne": None}})
            has_full_symbol = collection.count_documents({"full_symbol": {"$exists": True, "$ne": None}})
            
            print(f"  总记录数: {total}")
            print(f"  有 symbol: {has_symbol} ({has_symbol/total*100:.1f}%)")
            print(f"  有 full_symbol: {has_full_symbol} ({has_full_symbol/total*100:.1f}%)")
            
            if has_symbol == total and has_full_symbol == total:
                print(f"  ✅ 验证通过")
            else:
                print(f"  ❌ 验证失败: 存在缺失字段")
                
        elif collection_name == "analysis_tasks":
            # 验证 symbol
            total = collection.count_documents({})
            has_symbol = collection.count_documents({"symbol": {"$exists": True, "$ne": None}})
            
            print(f"  总记录数: {total}")
            print(f"  有 symbol: {has_symbol} ({has_symbol/total*100:.1f}%)")
            
            if has_symbol == total:
                print(f"  ✅ 验证通过")
            else:
                print(f"  ❌ 验证失败: 存在缺失字段")
    
    def run(self):
        """执行迁移"""
        try:
            self.connect()
            
            print(f"\n{'='*60}")
            print(f"🚀 开始数据库字段标准化迁移")
            print(f"{'='*60}")
            print(f"模式: {'DRY-RUN (预览)' if self.dry_run else 'EXECUTE (执行)'}")
            print(f"备份后缀: {self.backup_suffix}")
            
            # 迁移各个集合
            self.migrate_stock_basic_info()
            self.migrate_analysis_tasks()
            
            print(f"\n{'='*60}")
            print(f"✅ 迁移完成")
            print(f"{'='*60}")
            
            if self.dry_run:
                print(f"\n💡 这是预览模式，没有实际修改数据")
                print(f"   使用 --execute 参数执行实际迁移")
            else:
                print(f"\n✅ 数据已成功迁移")
                print(f"   备份集合后缀: {self.backup_suffix}")
                print(f"   如需回滚，请使用 --rollback 参数")
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description="数据库字段标准化迁移")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改数据")
    parser.add_argument("--execute", action="store_true", help="执行迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚到备份")
    
    args = parser.parse_args()
    
    if args.rollback:
        print("❌ 回滚功能尚未实现")
        return
    
    # 默认为 dry-run 模式
    dry_run = not args.execute
    
    migration = StockCodeFieldMigration(dry_run=dry_run)
    migration.run()


if __name__ == "__main__":
    main()

