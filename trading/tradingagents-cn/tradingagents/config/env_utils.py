#!/usr/bin/env python3
"""
环境变量解析工具
提供兼容Python 3.13+的强健环境变量解析功能
"""

import os
from typing import Any, Union, Optional


def parse_bool_env(env_var: str, default: bool = False) -> bool:
    """
    解析布尔类型环境变量，兼容多种格式
    
    支持的格式：
    - true/True/TRUE
    - false/False/FALSE  
    - 1/0
    - yes/Yes/YES
    - no/No/NO
    - on/On/ON
    - off/Off/OFF
    
    Args:
        env_var: 环境变量名
        default: 默认值
        
    Returns:
        bool: 解析后的布尔值
    """
    value = os.getenv(env_var)
    
    if value is None:
        return default
    
    # 转换为字符串并去除空白
    value_str = str(value).strip()
    
    if not value_str:
        return default
    
    # 转换为小写进行比较
    value_lower = value_str.lower()
    
    # 真值列表
    true_values = {
        'true', '1', 'yes', 'on', 'enable', 'enabled', 
        't', 'y', 'ok', 'okay'
    }
    
    # 假值列表
    false_values = {
        'false', '0', 'no', 'off', 'disable', 'disabled',
        'f', 'n', 'none', 'null', 'nil'
    }
    
    if value_lower in true_values:
        return True
    elif value_lower in false_values:
        return False
    else:
        # 如果无法识别，记录警告并返回默认值
        print(f"⚠️ 无法解析环境变量 {env_var}='{value}'，使用默认值 {default}")
        return default


def parse_int_env(env_var: str, default: int = 0) -> int:
    """
    解析整数类型环境变量
    
    Args:
        env_var: 环境变量名
        default: 默认值
        
    Returns:
        int: 解析后的整数值
    """
    value = os.getenv(env_var)
    
    if value is None:
        return default
    
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        print(f"⚠️ 无法解析环境变量 {env_var}='{value}' 为整数，使用默认值 {default}")
        return default


def parse_float_env(env_var: str, default: float = 0.0) -> float:
    """
    解析浮点数类型环境变量
    
    Args:
        env_var: 环境变量名
        default: 默认值
        
    Returns:
        float: 解析后的浮点数值
    """
    value = os.getenv(env_var)
    
    if value is None:
        return default
    
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        print(f"⚠️ 无法解析环境变量 {env_var}='{value}' 为浮点数，使用默认值 {default}")
        return default


def parse_str_env(env_var: str, default: str = "") -> str:
    """
    解析字符串类型环境变量
    
    Args:
        env_var: 环境变量名
        default: 默认值
        
    Returns:
        str: 解析后的字符串值
    """
    value = os.getenv(env_var)
    
    if value is None:
        return default
    
    return str(value).strip()


def parse_list_env(env_var: str, separator: str = ",", default: Optional[list] = None) -> list:
    """
    解析列表类型环境变量
    
    Args:
        env_var: 环境变量名
        separator: 分隔符
        default: 默认值
        
    Returns:
        list: 解析后的列表
    """
    if default is None:
        default = []
    
    value = os.getenv(env_var)
    
    if value is None:
        return default
    
    try:
        # 分割并去除空白
        items = [item.strip() for item in value.split(separator)]
        # 过滤空字符串
        return [item for item in items if item]
    except AttributeError:
        print(f"⚠️ 无法解析环境变量 {env_var}='{value}' 为列表，使用默认值 {default}")
        return default


def get_env_info(env_var: str) -> dict:
    """
    获取环境变量的详细信息
    
    Args:
        env_var: 环境变量名
        
    Returns:
        dict: 环境变量信息
    """
    value = os.getenv(env_var)
    
    return {
        'name': env_var,
        'value': value,
        'exists': value is not None,
        'empty': value is None or str(value).strip() == '',
        'type': type(value).__name__ if value is not None else 'None',
        'length': len(str(value)) if value is not None else 0
    }


def validate_required_env_vars(required_vars: list) -> dict:
    """
    验证必需的环境变量是否已设置
    
    Args:
        required_vars: 必需的环境变量列表
        
    Returns:
        dict: 验证结果
    """
    results = {
        'all_set': True,
        'missing': [],
        'empty': [],
        'valid': []
    }
    
    for var in required_vars:
        info = get_env_info(var)
        
        if not info['exists']:
            results['missing'].append(var)
            results['all_set'] = False
        elif info['empty']:
            results['empty'].append(var)
            results['all_set'] = False
        else:
            results['valid'].append(var)
    
    return results


# 兼容性函数：保持向后兼容
def get_bool_env(env_var: str, default: bool = False) -> bool:
    """向后兼容的布尔值解析函数"""
    return parse_bool_env(env_var, default)


def get_int_env(env_var: str, default: int = 0) -> int:
    """向后兼容的整数解析函数"""
    return parse_int_env(env_var, default)


def get_str_env(env_var: str, default: str = "") -> str:
    """向后兼容的字符串解析函数"""
    return parse_str_env(env_var, default)


# 导出主要函数
__all__ = [
    'parse_bool_env',
    'parse_int_env', 
    'parse_float_env',
    'parse_str_env',
    'parse_list_env',
    'get_env_info',
    'validate_required_env_vars',
    'get_bool_env',  # 向后兼容
    'get_int_env',   # 向后兼容
    'get_str_env'    # 向后兼容
]
