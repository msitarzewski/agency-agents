#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finnhub示例数据下载脚本

这个脚本用于创建示例的Finnhub数据文件，以便测试新闻数据功能。
在没有真实API密钥或数据的情况下，可以使用此脚本创建测试数据。
"""

import os
import json
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.config import get_config, set_config

def create_sample_news_data(ticker, data_dir, days=7):
    """
    创建示例新闻数据
    
    Args:
        ticker (str): 股票代码
        data_dir (str): 数据目录
        days (int): 生成多少天的数据
    """
    # 创建目录结构
    news_dir = os.path.join(data_dir, "finnhub_data", "news_data")
    os.makedirs(news_dir, exist_ok=True)
    
    # 生成示例新闻数据
    sample_news = {
        "AAPL": [
            "苹果公司发布新款iPhone，销量预期强劲",
            "苹果在人工智能领域取得重大突破",
            "苹果股价创历史新高，投资者信心增强",
            "苹果宣布新的环保计划，致力于碳中和",
            "苹果服务业务收入持续增长"
        ],
        "TSLA": [
            "特斯拉交付量超预期，股价大涨",
            "特斯拉自动驾驶技术获得新突破",
            "特斯拉在中国市场表现强劲",
            "特斯拉能源业务快速增长",
            "马斯克宣布特斯拉新工厂计划"
        ],
        "MSFT": [
            "微软云业务Azure收入大幅增长",
            "微软AI助手Copilot用户数量激增",
            "微软与OpenAI合作深化",
            "微软Office 365订阅用户创新高",
            "微软游戏业务表现亮眼"
        ],
        "GOOGL": [
            "谷歌搜索广告收入稳定增长",
            "谷歌云计算业务竞争力提升",
            "谷歌AI模型Gemini性能优异",
            "YouTube广告收入超预期",
            "谷歌在量子计算领域取得进展"
        ],
        "AMZN": [
            "亚马逊AWS云服务市场份额扩大",
            "亚马逊Prime会员数量持续增长",
            "亚马逊物流网络进一步优化",
            "亚马逊广告业务快速发展",
            "亚马逊在AI领域投资加大"
        ]
    }
    
    # 为指定股票生成数据
    if ticker not in sample_news:
        # 如果不在预定义列表中，使用通用模板
        headlines = [
            f"{ticker}公司业绩超预期，股价上涨",
            f"{ticker}宣布重大战略调整",
            f"{ticker}在行业中地位稳固",
            f"{ticker}管理层对未来前景乐观",
            f"{ticker}获得分析师买入评级"
        ]
    else:
        headlines = sample_news[ticker]
    
    # 生成日期数据
    data = {}
    current_date = datetime.now()
    
    for i in range(days):
        date = current_date - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # 每天生成1-3条新闻
        num_news = random.randint(1, 3)
        daily_news = []
        
        for j in range(num_news):
            headline_idx = (i + j) % len(headlines)
            headline = headlines[headline_idx]
            
            news_item = {
                "headline": headline,
                "summary": f"根据最新报道，{headline}。这一消息对投资者来说具有重要意义，可能会影响股票的短期和长期表现。分析师认为这一发展符合公司的战略方向。",
                "source": "财经新闻",
                "url": f"https://example.com/news/{ticker.lower()}-{date_str}-{j+1}",
                "datetime": int(date.timestamp())
            }
            daily_news.append(news_item)
        
        data[date_str] = daily_news
    
    # 保存数据文件
    file_path = os.path.join(news_dir, f"{ticker}_data_formatted.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 创建示例新闻数据: {file_path}")
    logger.info(f"   包含 {len(data)} 天的数据，共 {sum(len(news) for news in data.values())} 条新闻")
    
    return file_path

def create_sample_insider_data(ticker, data_dir, data_type):
    """
    创建示例内部人数据
    
    Args:
        ticker (str): 股票代码
        data_dir (str): 数据目录
        data_type (str): 数据类型 (insider_senti 或 insider_trans)
    """
    # 创建目录结构
    insider_dir = os.path.join(data_dir, "finnhub_data", data_type)
    os.makedirs(insider_dir, exist_ok=True)
    
    data = {}
    current_date = datetime.now()
    
    if data_type == "insider_senti":
        # 内部人情绪数据
        for i in range(3):  # 生成3个月的数据
            date = current_date - timedelta(days=30*i)
            date_str = date.strftime("%Y-%m-%d")
            
            sentiment_data = [{
                "year": date.year,
                "month": date.month,
                "change": round(random.uniform(-1000000, 1000000), 2),
                "mspr": round(random.uniform(0, 1), 4)
            }]
            
            data[date_str] = sentiment_data
    
    elif data_type == "insider_trans":
        # 内部人交易数据
        executives = ["CEO John Smith", "CFO Jane Doe", "CTO Mike Johnson"]
        
        for i in range(7):  # 生成7天的数据
            date = current_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            if random.random() > 0.7:  # 30%概率有交易
                transaction_data = [{
                    "filingDate": date_str,
                    "name": random.choice(executives),
                    "change": random.randint(-10000, 10000),
                    "share": random.randint(1000, 50000),
                    "transactionPrice": round(random.uniform(100, 300), 2),
                    "transactionCode": random.choice(["S", "P", "A"]),
                    "transactionDate": date_str
                }]
                data[date_str] = transaction_data
    
    # 保存数据文件
    file_path = os.path.join(insider_dir, f"{ticker}_data_formatted.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 创建示例{data_type}数据: {file_path}")
    return file_path

def main():
    """
    主函数
    """
    logger.info(f"Finnhub示例数据下载脚本")
    logger.info(f"=")
    
    # 获取配置
    config = get_config()
    data_dir = config.get('data_dir')
    
    if not data_dir:
        logger.error(f"❌ 数据目录未配置")
        return
    
    logger.info(f"数据目录: {data_dir}")
    
    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    # 常用股票代码
    tickers = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]
    
    logger.info(f"\n创建示例数据...")
    
    # 为每个股票创建新闻数据
    for ticker in tickers:
        create_sample_news_data(ticker, data_dir, days=7)
        create_sample_insider_data(ticker, data_dir, "insider_senti")
        create_sample_insider_data(ticker, data_dir, "insider_trans")
    
    logger.info(f"\n=== 数据创建完成 ===")
    logger.info(f"数据位置: {data_dir}")
    logger.info(f"包含以下股票的示例数据:")
    for ticker in tickers:
        logger.info(f"  - {ticker}: 新闻、内部人情绪、内部人交易")
    
    logger.info(f"\n现在您可以测试Finnhub新闻功能了！")
    
    # 测试数据获取
    logger.info(f"\n=== 测试数据获取 ===")
    try:
        from tradingagents.dataflows.interface import get_finnhub_news

        
        result = get_finnhub_news(
            ticker="AAPL",
            curr_date=datetime.now().strftime("%Y-%m-%d"),
            look_back_days=3
        )
        
        if result and "无法获取" not in result:
            logger.info(f"✅ 新闻数据获取成功！")
            logger.info(f"示例内容: {result[:200]}...")
        else:
            logger.error(f"⚠️ 新闻数据获取失败，请检查配置")
            logger.info(f"返回结果: {result}")
    
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    main()