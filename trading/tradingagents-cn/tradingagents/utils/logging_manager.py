#!/usr/bin/env python3
"""
统一日志管理器
提供项目级别的日志配置和管理功能
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
import toml

# 注意：这里不能导入自己，会造成循环导入
# 在日志系统初始化前，使用标准库自举日志器，避免未定义引用
_bootstrap_logger = logging.getLogger("tradingagents.logging_manager")


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（JSON格式）"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'analysis_type'):
            log_entry['analysis_type'] = record.analysis_type
        if hasattr(record, 'stock_symbol'):
            log_entry['stock_symbol'] = record.stock_symbol
        if hasattr(record, 'cost'):
            log_entry['cost'] = record.cost
        if hasattr(record, 'tokens'):
            log_entry['tokens'] = record.tokens
            
        return json.dumps(log_entry, ensure_ascii=False)


class TradingAgentsLogger:
    """TradingAgents统一日志管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认日志配置"""
        # 尝试从配置文件加载
        config = self._load_config_file()
        if config:
            return config

        # 从环境变量获取配置
        log_level = os.getenv('TRADINGAGENTS_LOG_LEVEL', 'INFO').upper()
        log_dir = os.getenv('TRADINGAGENTS_LOG_DIR', './logs')

        return {
            'level': log_level,
            'format': {
                'console': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
                'file': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
                'structured': 'json'
            },
            'handlers': {
                'console': {
                    'enabled': True,
                    'colored': True,
                    'level': log_level
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'max_size': '10MB',
                    'backup_count': 5,
                    'directory': log_dir
                },
                'error': {
                    'enabled': True,
                    'level': 'WARNING',  # 只记录WARNING及以上级别
                    'max_size': '10MB',
                    'backup_count': 5,
                    'directory': log_dir,
                    'filename': 'error.log'
                },
                'structured': {
                    'enabled': False,  # 默认关闭，可通过环境变量启用
                    'level': 'INFO',
                    'directory': log_dir
                }
            },
            'loggers': {
                'tradingagents': {'level': log_level},
                'web': {'level': log_level},
                'streamlit': {'level': 'WARNING'},  # Streamlit日志较多，设为WARNING
                'urllib3': {'level': 'WARNING'},    # HTTP请求日志较多
                'requests': {'level': 'WARNING'},
                'matplotlib': {'level': 'WARNING'}
            },
            'docker': {
                'enabled': os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true',
                'stdout_only': True  # Docker环境只输出到stdout
            }
        }

    def _load_config_file(self) -> Optional[Dict[str, Any]]:
        """从配置文件加载日志配置"""
        # 确定配置文件路径
        config_paths = [
            'config/logging_docker.toml' if os.getenv('DOCKER_CONTAINER') == 'true' else None,
            'config/logging.toml',
            './logging.toml'
        ]

        for config_path in config_paths:
            if config_path and Path(config_path).exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = toml.load(f)

                    # 转换配置格式
                    return self._convert_toml_config(config_data)
                except Exception as e:
                    _bootstrap_logger.warning(f"警告: 无法加载配置文件 {config_path}: {e}")
                    continue

        return None

    def _convert_toml_config(self, toml_config: Dict[str, Any]) -> Dict[str, Any]:
        """将TOML配置转换为内部配置格式"""
        logging_config = toml_config.get('logging', {})

        # 检查Docker环境
        is_docker = (
            os.getenv('DOCKER_CONTAINER') == 'true' or
            logging_config.get('docker', {}).get('enabled', False)
        )

        return {
            'level': logging_config.get('level', 'INFO'),
            'format': logging_config.get('format', {}),
            'handlers': logging_config.get('handlers', {}),
            'loggers': logging_config.get('loggers', {}),
            'docker': {
                'enabled': is_docker,
                'stdout_only': logging_config.get('docker', {}).get('stdout_only', True)
            },
            'performance': logging_config.get('performance', {}),
            'security': logging_config.get('security', {}),
            'business': logging_config.get('business', {})
        }
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        if self.config['handlers']['file']['enabled']:
            log_dir = Path(self.config['handlers']['file']['directory'])
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['level']))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 添加处理器
        self._add_console_handler(root_logger)

        if not self.config['docker']['enabled'] or not self.config['docker']['stdout_only']:
            self._add_file_handler(root_logger)
            self._add_error_handler(root_logger)  # 🔧 添加错误日志处理器
            if self.config['handlers']['structured']['enabled']:
                self._add_structured_handler(root_logger)
        
        # 配置特定日志器
        self._configure_specific_loggers()
    
    def _add_console_handler(self, logger: logging.Logger):
        """添加控制台处理器"""
        if not self.config['handlers']['console']['enabled']:
            return
            
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = getattr(logging, self.config['handlers']['console']['level'])
        console_handler.setLevel(console_level)
        
        # 选择格式化器
        if self.config['handlers']['console']['colored'] and sys.stdout.isatty():
            formatter = ColoredFormatter(self.config['format']['console'])
        else:
            formatter = logging.Formatter(self.config['format']['console'])
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger):
        """添加文件处理器"""
        if not self.config['handlers']['file']['enabled']:
            return

        log_dir = Path(self.config['handlers']['file']['directory'])
        log_file = log_dir / 'tradingagents.log'

        # 使用RotatingFileHandler进行日志轮转
        max_size = self._parse_size(self.config['handlers']['file']['max_size'])
        backup_count = self.config['handlers']['file']['backup_count']

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        file_level = getattr(logging, self.config['handlers']['file']['level'])
        file_handler.setLevel(file_level)

        formatter = logging.Formatter(self.config['format']['file'])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def _add_error_handler(self, logger: logging.Logger):
        """添加错误日志处理器（只记录WARNING及以上级别）"""
        # 检查错误处理器是否启用
        error_config = self.config['handlers'].get('error', {})
        if not error_config.get('enabled', True):
            return

        log_dir = Path(error_config.get('directory', self.config['handlers']['file']['directory']))
        error_log_file = log_dir / error_config.get('filename', 'error.log')

        # 使用RotatingFileHandler进行日志轮转
        max_size = self._parse_size(error_config.get('max_size', '10MB'))
        backup_count = error_config.get('backup_count', 5)

        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        # 🔧 只记录WARNING及以上级别（WARNING, ERROR, CRITICAL）
        error_level = getattr(logging, error_config.get('level', 'WARNING'))
        error_handler.setLevel(error_level)

        formatter = logging.Formatter(self.config['format']['file'])
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    def _add_structured_handler(self, logger: logging.Logger):
        """添加结构化日志处理器"""
        log_dir = Path(self.config['handlers']['structured']['directory'])
        log_file = log_dir / 'tradingagents_structured.log'
        
        structured_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self._parse_size('10MB'),
            backupCount=3,
            encoding='utf-8'
        )
        
        structured_level = getattr(logging, self.config['handlers']['structured']['level'])
        structured_handler.setLevel(structured_level)
        
        formatter = StructuredFormatter()
        structured_handler.setFormatter(formatter)
        logger.addHandler(structured_handler)
    
    def _configure_specific_loggers(self):
        """配置特定的日志器"""
        for logger_name, logger_config in self.config['loggers'].items():
            logger = logging.getLogger(logger_name)
            level = getattr(logging, logger_config['level'])
            logger.setLevel(level)
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串（如'10MB'）为字节数"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def log_analysis_start(self, logger: logging.Logger, stock_symbol: str, analysis_type: str, session_id: str):
        """记录分析开始"""
        logger.info(
            f"🚀 开始分析 - 股票: {stock_symbol}, 类型: {analysis_type}",
            extra={
                'stock_symbol': stock_symbol,
                'analysis_type': analysis_type,
                'session_id': session_id,
                'event_type': 'analysis_start',
                'timestamp': datetime.now().isoformat()
            }
        )

    def log_analysis_complete(self, logger: logging.Logger, stock_symbol: str, analysis_type: str,
                            session_id: str, duration: float, cost: float = 0):
        """记录分析完成"""
        logger.info(
            f"✅ 分析完成 - 股票: {stock_symbol}, 耗时: {duration:.2f}s, 成本: ¥{cost:.4f}",
            extra={
                'stock_symbol': stock_symbol,
                'analysis_type': analysis_type,
                'session_id': session_id,
                'duration': duration,
                'cost': cost,
                'event_type': 'analysis_complete',
                'timestamp': datetime.now().isoformat()
            }
        )

    def log_module_start(self, logger: logging.Logger, module_name: str, stock_symbol: str,
                        session_id: str, **extra_data):
        """记录模块开始分析"""
        logger.info(
            f"📊 [模块开始] {module_name} - 股票: {stock_symbol}",
            extra={
                'module_name': module_name,
                'stock_symbol': stock_symbol,
                'session_id': session_id,
                'event_type': 'module_start',
                'timestamp': datetime.now().isoformat(),
                **extra_data
            }
        )

    def log_module_complete(self, logger: logging.Logger, module_name: str, stock_symbol: str,
                           session_id: str, duration: float, success: bool = True,
                           result_length: int = 0, **extra_data):
        """记录模块完成分析"""
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(
            f"📊 [模块完成] {module_name} - {status} - 股票: {stock_symbol}, 耗时: {duration:.2f}s",
            extra={
                'module_name': module_name,
                'stock_symbol': stock_symbol,
                'session_id': session_id,
                'duration': duration,
                'success': success,
                'result_length': result_length,
                'event_type': 'module_complete',
                'timestamp': datetime.now().isoformat(),
                **extra_data
            }
        )

    def log_module_error(self, logger: logging.Logger, module_name: str, stock_symbol: str,
                        session_id: str, duration: float, error: str, **extra_data):
        """记录模块分析错误"""
        logger.error(
            f"❌ [模块错误] {module_name} - 股票: {stock_symbol}, 耗时: {duration:.2f}s, 错误: {error}",
            extra={
                'module_name': module_name,
                'stock_symbol': stock_symbol,
                'session_id': session_id,
                'duration': duration,
                'error': error,
                'event_type': 'module_error',
                'timestamp': datetime.now().isoformat(),
                **extra_data
            },
            exc_info=True
        )
    
    def log_token_usage(self, logger: logging.Logger, provider: str, model: str, 
                       input_tokens: int, output_tokens: int, cost: float, session_id: str):
        """记录Token使用"""
        logger.info(
            f"📊 Token使用 - {provider}/{model}: 输入={input_tokens}, 输出={output_tokens}, 成本=¥{cost:.6f}",
            extra={
                'provider': provider,
                'model': model,
                'tokens': {'input': input_tokens, 'output': output_tokens},
                'cost': cost,
                'session_id': session_id,
                'event_type': 'token_usage'
            }
        )


# 全局日志管理器实例
_logger_manager: Optional[TradingAgentsLogger] = None


def get_logger_manager() -> TradingAgentsLogger:
    """获取全局日志管理器实例"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = TradingAgentsLogger()
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器（便捷函数）"""
    return get_logger_manager().get_logger(name)


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """设置项目日志系统（便捷函数）"""
    global _logger_manager
    _logger_manager = TradingAgentsLogger(config)
    return _logger_manager
