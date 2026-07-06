#!/usr/bin/env python3
"""
数据库配置管理模块
统一管理MongoDB和Redis的连接配置
"""

import os
from typing import Dict, Any, Optional


class DatabaseConfig:
    """数据库配置管理类"""
    
    @staticmethod
    def get_mongodb_config() -> Dict[str, Any]:
        """
        获取MongoDB配置
        
        Returns:
            Dict[str, Any]: MongoDB配置字典
            
        Raises:
            ValueError: 当必要的配置未设置时
        """
        connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        if not connection_string:
            raise ValueError(
                "MongoDB连接字符串未配置。请设置环境变量 MONGODB_CONNECTION_STRING\n"
                "例如: MONGODB_CONNECTION_STRING=mongodb://localhost:27017/"
            )
        
        return {
            'connection_string': connection_string,
            'database': os.getenv('MONGODB_DATABASE', 'tradingagents'),
            'auth_source': os.getenv('MONGODB_AUTH_SOURCE', 'admin')
        }
    
    @staticmethod
    def get_redis_config() -> Dict[str, Any]:
        """
        获取Redis配置
        
        Returns:
            Dict[str, Any]: Redis配置字典
            
        Raises:
            ValueError: 当必要的配置未设置时
        """
        # 优先使用连接字符串
        connection_string = os.getenv('REDIS_CONNECTION_STRING')
        if connection_string:
            return {
                'connection_string': connection_string,
                'database': int(os.getenv('REDIS_DATABASE', 0))
            }
        
        # 使用分离的配置参数
        host = os.getenv('REDIS_HOST')
        port = os.getenv('REDIS_PORT')
        
        if not host or not port:
            raise ValueError(
                "Redis连接配置未完整设置。请设置以下环境变量之一：\n"
                "1. REDIS_CONNECTION_STRING=redis://localhost:6379/0\n"
                "2. REDIS_HOST + REDIS_PORT (例如: REDIS_HOST=localhost, REDIS_PORT=6379)"
            )
        
        return {
            'host': host,
            'port': int(port),
            'password': os.getenv('REDIS_PASSWORD'),
            'database': int(os.getenv('REDIS_DATABASE', 0))
        }
    
    @staticmethod
    def validate_config() -> Dict[str, bool]:
        """
        验证数据库配置是否完整
        
        Returns:
            Dict[str, bool]: 验证结果
        """
        result = {
            'mongodb_valid': False,
            'redis_valid': False
        }
        
        try:
            DatabaseConfig.get_mongodb_config()
            result['mongodb_valid'] = True
        except ValueError:
            pass
        
        try:
            DatabaseConfig.get_redis_config()
            result['redis_valid'] = True
        except ValueError:
            pass
        
        return result
    
    @staticmethod
    def get_config_status() -> str:
        """
        获取配置状态的友好描述
        
        Returns:
            str: 配置状态描述
        """
        validation = DatabaseConfig.validate_config()
        
        if validation['mongodb_valid'] and validation['redis_valid']:
            return "✅ 所有数据库配置正常"
        elif validation['mongodb_valid']:
            return "⚠️ MongoDB配置正常，Redis配置缺失"
        elif validation['redis_valid']:
            return "⚠️ Redis配置正常，MongoDB配置缺失"
        else:
            return "❌ 数据库配置缺失，请检查环境变量"