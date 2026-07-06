#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据模型定义
定义标准化的股票数据结构，用于MongoDB存储和数据交换
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class MarketType(str, Enum):
    """市场类型枚举"""
    CN = "CN"  # 中国A股
    HK = "HK"  # 港股
    US = "US"  # 美股


class StockStatus(str, Enum):
    """股票状态枚举"""
    LISTED = "L"      # 上市
    DELISTED = "D"    # 退市
    SUSPENDED = "P"   # 暂停上市


class ReportType(str, Enum):
    """报告类型枚举"""
    ANNUAL = "annual"      # 年报
    QUARTERLY = "quarterly" # 季报


class NewsCategory(str, Enum):
    """新闻类别枚举"""
    COMPANY_ANNOUNCEMENT = "company_announcement"  # 公司公告
    INDUSTRY_NEWS = "industry_news"               # 行业新闻
    MARKET_NEWS = "market_news"                   # 市场新闻
    RESEARCH_REPORT = "research_report"           # 研究报告


class SentimentType(str, Enum):
    """情绪类型枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class BaseStockModel(BaseModel):
    """股票数据基础模型"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    data_source: str = Field(..., description="数据来源")
    version: int = Field(default=1, description="数据版本")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class StockBasicInfo(BaseStockModel):
    """股票基础信息模型"""
    symbol: str = Field(..., description="标准化股票代码", regex=r"^\d{6}$")
    exchange_symbol: str = Field(..., description="交易所完整代码")
    name: str = Field(..., description="股票名称")
    name_en: Optional[str] = Field(None, description="英文名称")
    market: str = Field(..., description="交易所")
    board: str = Field(..., description="板块")
    industry: str = Field(..., description="行业")
    industry_code: Optional[str] = Field(None, description="行业代码")
    sector: str = Field(..., description="所属板块")
    list_date: date = Field(..., description="上市日期")
    delist_date: Optional[date] = Field(None, description="退市日期")
    area: str = Field(..., description="所在地区")
    market_cap: Optional[float] = Field(None, description="总市值")
    float_cap: Optional[float] = Field(None, description="流通市值")
    total_shares: Optional[float] = Field(None, description="总股本")
    float_shares: Optional[float] = Field(None, description="流通股本")
    currency: str = Field(default="CNY", description="交易货币")
    status: StockStatus = Field(default=StockStatus.LISTED, description="上市状态")
    is_hs: bool = Field(default=False, description="是否沪深港通标的")

    @validator('symbol')
    def validate_symbol(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('股票代码必须是6位数字')
        return v


class StockDailyQuote(BaseStockModel):
    """股票日线行情模型"""
    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    pre_close: float = Field(..., description="前收盘价")
    change: float = Field(..., description="涨跌额")
    pct_chg: float = Field(..., description="涨跌幅(%)")
    volume: float = Field(..., description="成交量(股)")
    amount: float = Field(..., description="成交额(元)")
    turnover_rate: Optional[float] = Field(None, description="换手率(%)")
    volume_ratio: Optional[float] = Field(None, description="量比")
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    ps: Optional[float] = Field(None, description="市销率")
    dv_ratio: Optional[float] = Field(None, description="股息率")
    dv_ttm: Optional[float] = Field(None, description="滚动股息率")
    total_mv: Optional[float] = Field(None, description="总市值")
    circ_mv: Optional[float] = Field(None, description="流通市值")
    adj_factor: float = Field(default=1.0, description="复权因子")


class StockRealtimeQuote(BaseStockModel):
    """股票实时行情模型"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    pre_close: float = Field(..., description="前收盘价")
    open: float = Field(..., description="今开")
    high: float = Field(..., description="今高")
    low: float = Field(..., description="今低")
    change: float = Field(..., description="涨跌额")
    pct_chg: float = Field(..., description="涨跌幅")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    bid_prices: List[float] = Field(default_factory=list, description="买1-5价")
    bid_volumes: List[float] = Field(default_factory=list, description="买1-5量")
    ask_prices: List[float] = Field(default_factory=list, description="卖1-5价")
    ask_volumes: List[float] = Field(default_factory=list, description="卖1-5量")
    timestamp: datetime = Field(..., description="行情时间")


class BalanceSheetData(BaseModel):
    """资产负债表数据"""
    total_assets: Optional[float] = Field(None, description="资产总计")
    total_liab: Optional[float] = Field(None, description="负债合计")
    total_hldr_eqy_exc_min_int: Optional[float] = Field(None, description="股东权益合计")
    total_cur_assets: Optional[float] = Field(None, description="流动资产合计")
    total_nca: Optional[float] = Field(None, description="非流动资产合计")
    total_cur_liab: Optional[float] = Field(None, description="流动负债合计")
    total_ncl: Optional[float] = Field(None, description="非流动负债合计")
    cash_and_equivalents: Optional[float] = Field(None, description="货币资金")


class IncomeStatementData(BaseModel):
    """利润表数据"""
    total_revenue: Optional[float] = Field(None, description="营业总收入")
    revenue: Optional[float] = Field(None, description="营业收入")
    oper_cost: Optional[float] = Field(None, description="营业总成本")
    gross_profit: Optional[float] = Field(None, description="毛利润")
    oper_profit: Optional[float] = Field(None, description="营业利润")
    total_profit: Optional[float] = Field(None, description="利润总额")
    n_income: Optional[float] = Field(None, description="净利润")
    n_income_attr_p: Optional[float] = Field(None, description="归母净利润")
    basic_eps: Optional[float] = Field(None, description="基本每股收益")
    diluted_eps: Optional[float] = Field(None, description="稀释每股收益")


class CashflowStatementData(BaseModel):
    """现金流量表数据"""
    n_cashflow_act: Optional[float] = Field(None, description="经营活动现金流量净额")
    n_cashflow_inv_act: Optional[float] = Field(None, description="投资活动现金流量净额")
    n_cashflow_fin_act: Optional[float] = Field(None, description="筹资活动现金流量净额")
    c_cash_equ_end_period: Optional[float] = Field(None, description="期末现金及现金等价物余额")
    c_cash_equ_beg_period: Optional[float] = Field(None, description="期初现金及现金等价物余额")


class FinancialIndicators(BaseModel):
    """财务指标数据"""
    roe: Optional[float] = Field(None, description="净资产收益率")
    roa: Optional[float] = Field(None, description="总资产收益率")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    net_margin: Optional[float] = Field(None, description="净利率")
    debt_to_assets: Optional[float] = Field(None, description="资产负债率")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    quick_ratio: Optional[float] = Field(None, description="速动比率")
    eps: Optional[float] = Field(None, description="每股收益")
    bvps: Optional[float] = Field(None, description="每股净资产")
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    dividend_yield: Optional[float] = Field(None, description="股息率")


class StockFinancialData(BaseStockModel):
    """股票财务数据模型"""
    symbol: str = Field(..., description="股票代码")
    report_period: str = Field(..., description="报告期", regex=r"^\d{8}$")
    report_type: ReportType = Field(..., description="报告类型")
    ann_date: date = Field(..., description="公告日期")
    f_ann_date: Optional[date] = Field(None, description="实际公告日期")
    balance_sheet: Optional[BalanceSheetData] = Field(None, description="资产负债表数据")
    income_statement: Optional[IncomeStatementData] = Field(None, description="利润表数据")
    cashflow_statement: Optional[CashflowStatementData] = Field(None, description="现金流量表数据")
    financial_indicators: Optional[FinancialIndicators] = Field(None, description="财务指标")


class StockNews(BaseStockModel):
    """股票新闻模型"""
    symbol: Optional[str] = Field(None, description="相关股票代码")
    symbols: List[str] = Field(default_factory=list, description="相关股票列表")
    title: str = Field(..., description="新闻标题")
    content: Optional[str] = Field(None, description="新闻内容")
    summary: Optional[str] = Field(None, description="新闻摘要")
    url: str = Field(..., description="新闻链接")
    source: str = Field(..., description="新闻来源")
    author: Optional[str] = Field(None, description="作者")
    publish_time: datetime = Field(..., description="发布时间")
    category: NewsCategory = Field(..., description="新闻类别")
    sentiment: Optional[SentimentType] = Field(None, description="情绪分析")
    sentiment_score: Optional[float] = Field(None, description="情绪得分", ge=-1, le=1)
    keywords: List[str] = Field(default_factory=list, description="关键词")
    importance: str = Field(default="medium", description="重要性")
    language: str = Field(default="zh-CN", description="语言")


class MovingAverages(BaseModel):
    """移动平均线数据"""
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")


class TechnicalIndicatorsData(BaseModel):
    """技术指标数据"""
    rsi: Optional[float] = Field(None, description="RSI相对强弱指标")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_hist: Optional[float] = Field(None, description="MACD柱状图")
    kdj_k: Optional[float] = Field(None, description="KDJ-K值")
    kdj_d: Optional[float] = Field(None, description="KDJ-D值")
    kdj_j: Optional[float] = Field(None, description="KDJ-J值")
    boll_upper: Optional[float] = Field(None, description="布林带上轨")
    boll_mid: Optional[float] = Field(None, description="布林带中轨")
    boll_lower: Optional[float] = Field(None, description="布林带下轨")
    cci: Optional[float] = Field(None, description="CCI顺势指标")
    williams_r: Optional[float] = Field(None, description="威廉指标")
    bias: Optional[float] = Field(None, description="乖离率")
    roc: Optional[float] = Field(None, description="变动率指标")
    emt: Optional[float] = Field(None, description="简易波动指标")


class StockTechnicalIndicators(BaseStockModel):
    """股票技术指标模型"""
    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    period: str = Field(default="daily", description="周期")
    ma: Optional[MovingAverages] = Field(None, description="移动平均线")
    indicators: Optional[TechnicalIndicatorsData] = Field(None, description="技术指标")


class DataSourceConfig(BaseStockModel):
    """数据源配置模型"""
    source_name: str = Field(..., description="数据源名称")
    source_type: str = Field(..., description="数据源类型")
    priority: int = Field(..., description="优先级")
    status: str = Field(default="active", description="状态")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置信息")
    supported_data_types: List[str] = Field(default_factory=list, description="支持的数据类型")
    supported_markets: List[MarketType] = Field(default_factory=list, description="支持的市场")
    last_sync_time: Optional[datetime] = Field(None, description="最后同步时间")


class DataSyncLog(BaseStockModel):
    """数据同步日志模型"""
    task_id: str = Field(..., description="任务ID")
    data_type: str = Field(..., description="数据类型")
    data_source: str = Field(..., description="数据源")
    symbols: List[str] = Field(default_factory=list, description="同步的股票列表")
    sync_date: date = Field(..., description="同步日期")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: str = Field(default="pending", description="状态")
    total_records: int = Field(default=0, description="总记录数")
    success_records: int = Field(default=0, description="成功记录数")
    failed_records: int = Field(default=0, description="失败记录数")
    error_message: Optional[str] = Field(None, description="错误信息")
    performance: Dict[str, Any] = Field(default_factory=dict, description="性能指标")


# 导出所有模型
__all__ = [
    'MarketType', 'StockStatus', 'ReportType', 'NewsCategory', 'SentimentType',
    'BaseStockModel', 'StockBasicInfo', 'StockDailyQuote', 'StockRealtimeQuote',
    'StockFinancialData', 'StockNews', 'StockTechnicalIndicators',
    'DataSourceConfig', 'DataSyncLog',
    'BalanceSheetData', 'IncomeStatementData', 'CashflowStatementData',
    'FinancialIndicators', 'MovingAverages', 'TechnicalIndicatorsData'
]
