#!/usr/bin/env python3
"""
内部消息爬虫示例程序
演示如何爬取内部消息数据并入库到消息数据系统
"""
import asyncio
import logging
import sys
import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import time
import random
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import init_db
from app.services.internal_message_service import get_internal_message_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InternalMessageCrawler:
    """内部消息爬虫基类"""
    
    def __init__(self, source_type: str):
        self.source_type = source_type
        self.session = None
        self.headers = {
            'User-Agent': 'Internal-System-Crawler/1.0',
            'Authorization': 'Bearer internal_token_here'  # 内部系统认证
        }
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{source_type}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def clean_content(self, text: str) -> str:
        """清洗文本内容"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        financial_keywords = [
            '业绩', '财报', '营收', '利润', 'ROE', 'ROA', '毛利率',
            '资产负债率', '现金流', '分红', '重组', '并购', 'IPO',
            '估值', 'PE', 'PB', 'PEG', '市盈率', '市净率',
            '增长', '下滑', '亏损', '扭亏', '预期', '预测',
            '风险', '机会', '挑战', '优势', '劣势', '竞争',
            '行业', '市场', '政策', '监管', '合规'
        ]
        
        keywords = []
        text_lower = text.lower()
        for keyword in financial_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords[:10]  # 最多10个关键词
    
    def analyze_sentiment(self, text: str) -> tuple:
        """分析情绪倾向"""
        positive_words = ['利好', '增长', '上涨', '盈利', '超预期', '看好', '推荐', '买入', '强烈推荐']
        negative_words = ['利空', '下滑', '下跌', '亏损', '低于预期', '看空', '卖出', '风险', '警告']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = max(-0.9, -0.5 - (negative_count - positive_count) * 0.1)
        else:
            sentiment = 'neutral'
            score = 0.0
        
        return sentiment, score
    
    def extract_risk_factors(self, text: str) -> List[str]:
        """提取风险因素"""
        risk_patterns = [
            r'风险[：:]([^。；\n]+)',
            r'存在.*?风险',
            r'可能.*?影响',
            r'不确定性.*?因素'
        ]
        
        risks = []
        for pattern in risk_patterns:
            matches = re.findall(pattern, text)
            risks.extend(matches)
        
        return list(set(risks))[:5]  # 最多5个风险因素
    
    def extract_opportunities(self, text: str) -> List[str]:
        """提取机会因素"""
        opportunity_patterns = [
            r'机会[：:]([^。；\n]+)',
            r'有望.*?增长',
            r'预期.*?改善',
            r'潜在.*?价值'
        ]
        
        opportunities = []
        for pattern in opportunity_patterns:
            matches = re.findall(pattern, text)
            opportunities.extend(matches)
        
        return list(set(opportunities))[:5]  # 最多5个机会因素


class ResearchReportCrawler(InternalMessageCrawler):
    """研究报告爬虫"""
    
    def __init__(self):
        super().__init__('research_report')
        self.base_url = "http://internal-research-system/api"
    
    async def crawl_research_reports(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """爬取研究报告"""
        self.logger.info(f"📊 开始爬取研究报告: {symbol}")
        
        try:
            # 模拟内部研究系统API调用
            reports = await self._simulate_research_api(symbol, limit)
            
            # 数据标准化
            standardized_reports = []
            for report in reports:
                standardized_report = await self._standardize_research_report(report, symbol)
                if standardized_report:
                    standardized_reports.append(standardized_report)
            
            self.logger.info(f"✅ 研究报告爬取完成: {len(standardized_reports)} 份")
            return standardized_reports
            
        except Exception as e:
            self.logger.error(f"❌ 研究报告爬取失败: {e}")
            return []
    
    async def _simulate_research_api(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """模拟研究系统API响应"""
        mock_reports = []
        
        report_types = ['quarterly_analysis', 'annual_review', 'industry_analysis', 'valuation_report']
        departments = ['研究部', '投资部', '风控部', '策略部']
        analysts = ['张研究员', '李分析师', '王策略师', '赵投资经理']
        
        for i in range(min(limit, 8)):
            report_type = random.choice(report_types)
            department = random.choice(departments)
            analyst = random.choice(analysts)
            
            mock_report = {
                "report_id": f"RPT_{symbol}_{datetime.now().strftime('%Y%m%d')}_{i:03d}",
                "title": self._generate_report_title(symbol, report_type),
                "content": self._generate_report_content(symbol, report_type),
                "summary": self._generate_report_summary(symbol, report_type),
                "report_type": report_type,
                "department": department,
                "analyst": analyst,
                "analyst_id": f"analyst_{hash(analyst) % 1000:03d}",
                "created_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "rating": random.choice(['strong_buy', 'buy', 'hold', 'sell']),
                "target_price": round(random.uniform(10, 50), 2),
                "confidence_level": round(random.uniform(0.6, 0.95), 2),
                "access_level": random.choice(['internal', 'restricted']),
                "tags": self._generate_report_tags(report_type)
            }
            mock_reports.append(mock_report)
            
            await asyncio.sleep(0.1)
        
        return mock_reports
    
    def _generate_report_title(self, symbol: str, report_type: str) -> str:
        """生成报告标题"""
        titles = {
            'quarterly_analysis': f"{symbol} Q{random.randint(1,4)}季度业绩分析报告",
            'annual_review': f"{symbol} {datetime.now().year}年度投资价值分析",
            'industry_analysis': f"{symbol} 所属行业深度研究报告",
            'valuation_report': f"{symbol} 估值分析与投资建议"
        }
        return titles.get(report_type, f"{symbol} 投资研究报告")
    
    def _generate_report_content(self, symbol: str, report_type: str) -> str:
        """生成报告内容"""
        base_content = f"""
        一、公司概况
        {symbol} 是行业内的重要企业，主营业务稳定，市场地位较为稳固。
        
        二、财务分析
        根据最新财务数据，公司营收增长稳定，盈利能力有所提升。
        主要财务指标表现良好，资产负债结构合理。
        
        三、投资建议
        综合考虑公司基本面、行业前景和市场环境，给出相应投资建议。
        建议关注公司后续业绩表现和行业政策变化。
        
        四、风险提示
        需要关注市场波动风险、政策变化风险和行业竞争加剧风险。
        """
        
        return base_content.strip()
    
    def _generate_report_summary(self, symbol: str, report_type: str) -> str:
        """生成报告摘要"""
        summaries = {
            'quarterly_analysis': f"{symbol} 季度业绩符合预期，维持买入评级",
            'annual_review': f"{symbol} 年度表现良好，长期投资价值显著",
            'industry_analysis': f"{symbol} 行业前景向好，公司竞争优势明显",
            'valuation_report': f"{symbol} 当前估值合理，具备投资价值"
        }
        return summaries.get(report_type, f"{symbol} 投资价值分析")
    
    def _generate_report_tags(self, report_type: str) -> List[str]:
        """生成报告标签"""
        tag_map = {
            'quarterly_analysis': ['季度分析', '业绩评估', '财务分析'],
            'annual_review': ['年度回顾', '价值分析', '长期投资'],
            'industry_analysis': ['行业研究', '竞争分析', '市场前景'],
            'valuation_report': ['估值分析', '投资建议', '目标价格']
        }
        return tag_map.get(report_type, ['投资研究'])
    
    async def _standardize_research_report(self, raw_report: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """标准化研究报告数据"""
        try:
            content = self.clean_content(raw_report.get('content', ''))
            if not content:
                return None
            
            # 情绪分析
            sentiment, sentiment_score = self.analyze_sentiment(content)
            
            # 提取关键词、风险和机会
            keywords = self.extract_keywords(content)
            risk_factors = self.extract_risk_factors(content)
            opportunities = self.extract_opportunities(content)
            
            # 解析时间
            created_time = datetime.fromisoformat(raw_report.get('created_date', '').replace('Z', '+00:00'))
            
            return {
                "message_id": raw_report.get('report_id'),
                "message_type": "research_report",
                "title": raw_report.get('title'),
                "content": content,
                "summary": raw_report.get('summary'),
                "source": {
                    "type": "internal_research",
                    "department": raw_report.get('department'),
                    "author": raw_report.get('analyst'),
                    "author_id": raw_report.get('analyst_id'),
                    "reliability": "high"
                },
                "category": "fundamental_analysis",
                "subcategory": raw_report.get('report_type'),
                "tags": raw_report.get('tags', []),
                "importance": "high",
                "impact_scope": "stock_specific",
                "time_sensitivity": "medium_term",
                "confidence_level": raw_report.get('confidence_level', 0.8),
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "keywords": keywords,
                "risk_factors": risk_factors,
                "opportunities": opportunities,
                "related_data": {
                    "financial_metrics": ["revenue", "profit", "roe", "roa"],
                    "price_targets": [raw_report.get('target_price')],
                    "rating": raw_report.get('rating')
                },
                "access_level": raw_report.get('access_level', 'internal'),
                "permissions": ["research_team", "investment_team"],
                "created_time": created_time,
                "effective_time": created_time,
                "expiry_time": created_time + timedelta(days=90),
                "data_source": "internal_research_system",
                "symbol": symbol
            }
            
        except Exception as e:
            self.logger.error(f"❌ 研究报告标准化失败: {e}")
            return None


class AnalystNoteCrawler(InternalMessageCrawler):
    """分析师笔记爬虫"""
    
    def __init__(self):
        super().__init__('analyst_note')
        self.base_url = "http://internal-analyst-system/api"
    
    async def crawl_analyst_notes(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """爬取分析师笔记"""
        self.logger.info(f"📝 开始爬取分析师笔记: {symbol}")
        
        try:
            # 模拟分析师系统API调用
            notes = await self._simulate_analyst_api(symbol, limit)
            
            # 数据标准化
            standardized_notes = []
            for note in notes:
                standardized_note = await self._standardize_analyst_note(note, symbol)
                if standardized_note:
                    standardized_notes.append(standardized_note)
            
            self.logger.info(f"✅ 分析师笔记爬取完成: {len(standardized_notes)} 条")
            return standardized_notes
            
        except Exception as e:
            self.logger.error(f"❌ 分析师笔记爬取失败: {e}")
            return []
    
    async def _simulate_analyst_api(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """模拟分析师系统API响应"""
        mock_notes = []
        
        note_types = ['market_observation', 'technical_analysis', 'news_comment', 'strategy_update']
        analysts = ['资深分析师A', '技术分析师B', '策略分析师C', '行业分析师D']
        
        for i in range(min(limit, 15)):
            note_type = random.choice(note_types)
            analyst = random.choice(analysts)
            
            mock_note = {
                "note_id": f"NOTE_{symbol}_{int(time.time())}_{i}",
                "title": self._generate_note_title(symbol, note_type),
                "content": self._generate_note_content(symbol, note_type),
                "note_type": note_type,
                "analyst": analyst,
                "analyst_id": f"analyst_{hash(analyst) % 1000:03d}",
                "department": "投资部",
                "created_time": (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                "priority": random.choice(['high', 'medium', 'low']),
                "confidence": round(random.uniform(0.5, 0.9), 2),
                "tags": self._generate_note_tags(note_type)
            }
            mock_notes.append(mock_note)
            
            await asyncio.sleep(0.05)
        
        return mock_notes
    
    def _generate_note_title(self, symbol: str, note_type: str) -> str:
        """生成笔记标题"""
        titles = {
            'market_observation': f"{symbol} 市场表现观察",
            'technical_analysis': f"{symbol} 技术面分析笔记",
            'news_comment': f"{symbol} 最新消息点评",
            'strategy_update': f"{symbol} 投资策略更新"
        }
        return titles.get(note_type, f"{symbol} 分析笔记")
    
    def _generate_note_content(self, symbol: str, note_type: str) -> str:
        """生成笔记内容"""
        contents = {
            'market_observation': f"{symbol} 今日表现相对稳定，成交量较昨日有所放大。主力资金流向需要持续关注。",
            'technical_analysis': f"{symbol} 技术面显示突破20日均线，MACD指标转正，短期趋势向好。建议关注量价配合情况。",
            'news_comment': f"{symbol} 发布重要公告，对公司基本面产生积极影响。建议密切关注后续进展。",
            'strategy_update': f"基于最新市场环境和公司基本面变化，调整{symbol}投资策略，维持谨慎乐观态度。"
        }
        return contents.get(note_type, f"{symbol} 相关分析观点")
    
    def _generate_note_tags(self, note_type: str) -> List[str]:
        """生成笔记标签"""
        tag_map = {
            'market_observation': ['市场观察', '资金流向', '成交量分析'],
            'technical_analysis': ['技术分析', '均线系统', '指标分析'],
            'news_comment': ['消息面', '公告解读', '事件影响'],
            'strategy_update': ['策略调整', '投资建议', '风险控制']
        }
        return tag_map.get(note_type, ['分析笔记'])
    
    async def _standardize_analyst_note(self, raw_note: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """标准化分析师笔记数据"""
        try:
            content = self.clean_content(raw_note.get('content', ''))
            if not content:
                return None
            
            # 情绪分析
            sentiment, sentiment_score = self.analyze_sentiment(content)
            
            # 提取关键词
            keywords = self.extract_keywords(content)
            
            # 解析时间
            created_time = datetime.fromisoformat(raw_note.get('created_time', '').replace('Z', '+00:00'))
            
            # 重要性映射
            priority_map = {'high': 'high', 'medium': 'medium', 'low': 'low'}
            importance = priority_map.get(raw_note.get('priority'), 'medium')
            
            return {
                "message_id": raw_note.get('note_id'),
                "message_type": "analyst_note",
                "title": raw_note.get('title'),
                "content": content,
                "summary": content[:100] + "..." if len(content) > 100 else content,
                "source": {
                    "type": "analyst",
                    "department": raw_note.get('department'),
                    "author": raw_note.get('analyst'),
                    "author_id": raw_note.get('analyst_id'),
                    "reliability": "medium"
                },
                "category": self._map_category(raw_note.get('note_type')),
                "subcategory": raw_note.get('note_type'),
                "tags": raw_note.get('tags', []),
                "importance": importance,
                "impact_scope": "stock_specific",
                "time_sensitivity": "short_term",
                "confidence_level": raw_note.get('confidence', 0.7),
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "keywords": keywords,
                "risk_factors": [],
                "opportunities": [],
                "related_data": {
                    "technical_indicators": ["ma20", "macd", "volume"],
                    "price_targets": [],
                    "rating": "hold"
                },
                "access_level": "internal",
                "permissions": ["investment_team", "research_team"],
                "created_time": created_time,
                "effective_time": created_time,
                "expiry_time": created_time + timedelta(days=7),
                "data_source": "internal_analyst_system",
                "symbol": symbol
            }
            
        except Exception as e:
            self.logger.error(f"❌ 分析师笔记标准化失败: {e}")
            return None
    
    def _map_category(self, note_type: str) -> str:
        """映射笔记类型到分析类别"""
        category_map = {
            'market_observation': 'market_sentiment',
            'technical_analysis': 'technical_analysis',
            'news_comment': 'fundamental_analysis',
            'strategy_update': 'risk_assessment'
        }
        return category_map.get(note_type, 'fundamental_analysis')


async def crawl_and_save_internal_messages(symbols: List[str], message_types: List[str] = None):
    """爬取并保存内部消息"""
    if message_types is None:
        message_types = ['research_report', 'analyst_note']
    
    logger.info(f"🚀 开始爬取内部消息: {symbols}, 类型: {message_types}")
    
    try:
        # 初始化数据库
        await init_db()
        
        # 获取服务
        service = await get_internal_message_service()
        
        total_saved = 0
        
        for symbol in symbols:
            logger.info(f"📊 处理股票: {symbol}")
            
            for msg_type in message_types:
                try:
                    # 创建对应类型的爬虫
                    if msg_type == 'research_report':
                        async with ResearchReportCrawler() as crawler:
                            messages = await crawler.crawl_research_reports(symbol, limit=10)
                    elif msg_type == 'analyst_note':
                        async with AnalystNoteCrawler() as crawler:
                            messages = await crawler.crawl_analyst_notes(symbol, limit=20)
                    else:
                        logger.warning(f"⚠️ 不支持的消息类型: {msg_type}")
                        continue
                    
                    if messages:
                        # 保存到数据库
                        result = await service.save_internal_messages(messages)
                        saved_count = result.get('saved', 0)
                        total_saved += saved_count
                        
                        logger.info(f"✅ {msg_type} - {symbol}: 保存 {saved_count} 条消息")
                    else:
                        logger.warning(f"⚠️ {msg_type} - {symbol}: 未获取到消息")
                    
                    # 类型间延迟
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ {msg_type} - {symbol} 处理失败: {e}")
                    continue
            
            # 股票间延迟
            await asyncio.sleep(2)
        
        logger.info(f"🎉 内部消息爬取完成! 总计保存: {total_saved} 条")
        return total_saved
        
    except Exception as e:
        logger.error(f"❌ 内部消息爬取过程异常: {e}")
        return 0


async def main():
    """主函数"""
    # 测试股票列表
    test_symbols = ["000001", "000002", "600000"]
    
    # 测试消息类型
    test_types = ["research_report", "analyst_note"]
    
    logger.info("📊 内部消息爬虫示例程序启动")
    
    # 执行爬取
    saved_count = await crawl_and_save_internal_messages(test_symbols, test_types)
    
    logger.info(f"📊 爬取结果统计:")
    logger.info(f"   - 处理股票: {len(test_symbols)} 只")
    logger.info(f"   - 处理类型: {len(test_types)} 种")
    logger.info(f"   - 保存消息: {saved_count} 条")
    
    if saved_count > 0:
        logger.info("✅ 内部消息爬虫运行成功!")
    else:
        logger.warning("⚠️ 未保存任何消息，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
