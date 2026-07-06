#!/usr/bin/env python3
"""
使用记录数据模型
用于 Token 使用统计和成本跟踪
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UsageRecord:
    """使用记录"""
    timestamp: str  # 时间戳
    provider: str  # 供应商
    model_name: str  # 模型名称
    input_tokens: int  # 输入token数
    output_tokens: int  # 输出token数
    cost: float  # 成本
    currency: str = "CNY"  # 货币单位
    session_id: str = ""  # 会话ID
    analysis_type: str = "stock_analysis"  # 分析类型


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str  # 供应商：dashscope, openai, google, etc.
    model_name: str  # 模型名称
    api_key: str  # API密钥
    base_url: Optional[str] = None  # 自定义API地址
    max_tokens: int = 4000  # 最大token数
    temperature: float = 0.7  # 温度参数
    enabled: bool = True  # 是否启用


@dataclass
class PricingConfig:
    """定价配置"""
    provider: str  # 供应商
    model_name: str  # 模型名称
    input_price_per_1k: float  # 输入token价格（每1000个token）
    output_price_per_1k: float  # 输出token价格（每1000个token）
    currency: str = "CNY"  # 货币单位

