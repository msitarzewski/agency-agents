#!/usr/bin/env python3
# mongo_migration.py
import subprocess
import sys
import time
from datetime import datetime

class MongoMigrator:
    def __init__(self, source_host, target_host, source_container, target_container):
        self.source_host = source_host
        self.target_host = target_host  # 如果是本机可以用 'localhost'
        self.source_container = source_container
        self.target_container = target_container
        self.mongo_config = {
            'username': 'admin',
            'password': 'tradingagents123',
            'auth_db': 'admin',
            'database': 'tradingagents_hub'
        }
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def run_command(self, command, description):
        self.log(f"执行: {description}")
        self.log(f"命令: {command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✅ {description} 成功")
                if result.stdout:
                    self.log(f"输出: {result.stdout.strip()}")
                return True
            else:
                self.log(f"❌ {description} 失败")
                self.log(f"返回码: {result.returncode}")
                if result.stderr:
                    self.log(f"错误: {result.stderr.strip()}")
                if result.stdout:
                    self.log(f"输出: {result.stdout.strip()}")
                return False
        except Exception as e:
            self.log(f"❌ {description} 异常: {str(e)}")
            return False
    
    def check_source_connection(self):
        """检查源数据库连接"""
        # 使用本地MongoDB容器连接远程MongoDB
        cmd = f'docker exec {self.target_container} mongo -u {self.mongo_config["username"]} -p "{self.mongo_config["password"]}" --host {self.source_host} --port 27017 --authenticationDatabase {self.mongo_config["auth_db"]} --eval "db.runCommand({{ping: 1}})"'
        return self.run_command(cmd, "检查源数据库连接")
    
    def check_target_connection(self):
        """检查目标数据库连接"""
        cmd = f'docker exec {self.target_container} mongo -u {self.mongo_config["username"]} -p "{self.mongo_config["password"]}" --authenticationDatabase {self.mongo_config["auth_db"]} --eval "db.runCommand({{ping: 1}})"'
        return self.run_command(cmd, "检查目标数据库连接")
    
    def get_source_stats(self):
        """获取源数据库统计信息"""
        cmd = f"docker exec {self.target_container} mongo -u {self.mongo_config['username']} -p '{self.mongo_config['password']}' --host {self.source_host} --port 27017 --authenticationDatabase {self.mongo_config['auth_db']} --eval 'db.getSiblingDB(\"{self.mongo_config['database']}\").stats()'"
        self.run_command(cmd, "获取源数据库统计")
    
    def migrate_data(self):
        """执行数据迁移"""
        # 使用Docker容器执行迁移
        source_uri = f"mongodb://{self.mongo_config['username']}:{self.mongo_config['password']}@{self.source_host}:27017/{self.mongo_config['database']}?authSource={self.mongo_config['auth_db']}"
        target_uri = f"mongodb://{self.mongo_config['username']}:{self.mongo_config['password']}@localhost:27017/?authSource={self.mongo_config['auth_db']}"
        
        cmd = f"docker exec {self.target_container} bash -c \"mongodump --uri='{source_uri}' --archive --gzip | mongorestore --uri='{target_uri}' --drop --archive --gzip\""
        
        return self.run_command(cmd, "数据迁移")
    
    def verify_migration(self):
        """验证迁移结果"""
        cmd = f"docker exec {self.target_container} mongo -u {self.mongo_config['username']} -p '{self.mongo_config['password']}' --authenticationDatabase {self.mongo_config['auth_db']} --eval 'db.getSiblingDB(\"{self.mongo_config['database']}\").stats()'"
        return self.run_command(cmd, "验证迁移结果")
    
    def run_migration(self):
        """执行完整迁移流程"""
        self.log("🚀 开始MongoDB数据迁移")
        
        # 检查连接
        if not self.check_source_connection():
            self.log("❌ 源数据库连接失败，终止迁移")
            return False
            
        if not self.check_target_connection():
            self.log("❌ 目标数据库连接失败，终止迁移")
            return False
        
        # 获取源数据统计
        self.get_source_stats()
        
        # 执行迁移
        if not self.migrate_data():
            self.log("❌ 数据迁移失败")
            return False
        
        # 验证结果
        if not self.verify_migration():
            self.log("❌ 迁移验证失败")
            return False
        
        self.log("🎉 数据迁移完成！")
        return True

if __name__ == "__main__":
    # 配置参数
    SOURCE_HOST = "192.168.0.223"  # 源服务器IP
    TARGET_HOST = "localhost"       # 目标服务器（本机）
    SOURCE_CONTAINER = "tradingagents-mongodb"  # 源容器名
    TARGET_CONTAINER = "tradingagents-mongodb"  # 目标容器名
    
    # 创建迁移器并执行
    migrator = MongoMigrator(SOURCE_HOST, TARGET_HOST, SOURCE_CONTAINER, TARGET_CONTAINER)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)