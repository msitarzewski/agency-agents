"""
新闻相关性过滤器
用于过滤与特定股票/公司不相关的新闻，提高新闻分析质量
"""

import pandas as pd
import re
from typing import List, Dict, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NewsRelevanceFilter:
    """基于规则的新闻相关性过滤器"""
    
    def __init__(self, stock_code: str, company_name: str):
        """
        初始化过滤器
        
        Args:
            stock_code: 股票代码，如 "600036"
            company_name: 公司名称，如 "招商银行"
        """
        self.stock_code = stock_code.upper()
        self.company_name = company_name
        
        # 排除关键词 - 这些词出现时降低相关性
        self.exclude_keywords = [
            'etf', '指数基金', '基金', '指数', 'index', 'fund',
            '权重股', '成分股', '板块', '概念股', '主题基金',
            '跟踪指数', '被动投资', '指数投资', '基金持仓'
        ]
        
        # 包含关键词 - 这些词出现时提高相关性
        self.include_keywords = [
            '业绩', '财报', '公告', '重组', '并购', '分红', '派息',
            '高管', '董事', '股东', '增持', '减持', '回购',
            '年报', '季报', '半年报', '业绩预告', '业绩快报',
            '股东大会', '董事会', '监事会', '重大合同',
            '投资', '收购', '出售', '转让', '合作', '协议'
        ]
        
        # 强相关关键词 - 这些词出现时大幅提高相关性
        self.strong_keywords = [
            '停牌', '复牌', '涨停', '跌停', '限售解禁',
            '股权激励', '员工持股', '定增', '配股', '送股',
            '资产重组', '借壳上市', '退市', '摘帽', 'ST'
        ]
    
    def calculate_relevance_score(self, title: str, content: str) -> float:
        """
        计算新闻相关性评分
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            float: 相关性评分 (0-100)
        """
        score = 0
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 1. 直接提及公司名称
        if self.company_name in title:
            score += 50  # 标题中出现公司名称，高分
            logger.debug(f"[过滤器] 标题包含公司名称 '{self.company_name}': +50分")
        elif self.company_name in content:
            score += 25  # 内容中出现公司名称，中等分
            logger.debug(f"[过滤器] 内容包含公司名称 '{self.company_name}': +25分")
            
        # 2. 直接提及股票代码
        if self.stock_code in title:
            score += 40  # 标题中出现股票代码，高分
            logger.debug(f"[过滤器] 标题包含股票代码 '{self.stock_code}': +40分")
        elif self.stock_code in content:
            score += 20  # 内容中出现股票代码，中等分
            logger.debug(f"[过滤器] 内容包含股票代码 '{self.stock_code}': +20分")
            
        # 3. 强相关关键词检查
        strong_matches = []
        for keyword in self.strong_keywords:
            if keyword in title_lower:
                score += 30
                strong_matches.append(keyword)
            elif keyword in content_lower:
                score += 15
                strong_matches.append(keyword)
        
        if strong_matches:
            logger.debug(f"[过滤器] 强相关关键词匹配: {strong_matches}")
            
        # 4. 包含关键词检查
        include_matches = []
        for keyword in self.include_keywords:
            if keyword in title_lower:
                score += 15
                include_matches.append(keyword)
            elif keyword in content_lower:
                score += 8
                include_matches.append(keyword)
        
        if include_matches:
            logger.debug(f"[过滤器] 相关关键词匹配: {include_matches[:3]}...")  # 只显示前3个
            
        # 5. 排除关键词检查（减分）
        exclude_matches = []
        for keyword in self.exclude_keywords:
            if keyword in title_lower:
                score -= 40  # 标题中出现排除词，大幅减分
                exclude_matches.append(keyword)
            elif keyword in content_lower:
                score -= 20  # 内容中出现排除词，中等减分
                exclude_matches.append(keyword)
        
        if exclude_matches:
            logger.debug(f"[过滤器] 排除关键词匹配: {exclude_matches[:3]}...")
            
        # 6. 特殊规则：如果标题完全不包含公司信息但包含排除词，严重减分
        if (self.company_name not in title and self.stock_code not in title and 
            any(keyword in title_lower for keyword in self.exclude_keywords)):
            score -= 30
            logger.debug(f"[过滤器] 标题无公司信息但含排除词: -30分")
        
        # 确保评分在0-100范围内
        final_score = max(0, min(100, score))
        
        logger.debug(f"[过滤器] 最终评分: {final_score}分 - 标题: {title[:30]}...")
        
        return final_score
    
    def filter_news(self, news_df: pd.DataFrame, min_score: float = 30) -> pd.DataFrame:
        """
        过滤新闻DataFrame
        
        Args:
            news_df: 原始新闻DataFrame
            min_score: 最低相关性评分阈值
            
        Returns:
            pd.DataFrame: 过滤后的新闻DataFrame，按相关性评分排序
        """
        if news_df.empty:
            logger.warning("[过滤器] 输入新闻DataFrame为空")
            return news_df
        
        logger.info(f"[过滤器] 开始过滤新闻，原始数量: {len(news_df)}条，最低评分阈值: {min_score}")
        
        filtered_news = []
        
        for idx, row in news_df.iterrows():
            title = row.get('新闻标题', row.get('标题', ''))
            content = row.get('新闻内容', row.get('内容', ''))
            
            # 计算相关性评分
            score = self.calculate_relevance_score(title, content)
            
            if score >= min_score:
                row_dict = row.to_dict()
                row_dict['relevance_score'] = score
                filtered_news.append(row_dict)
                
                logger.debug(f"[过滤器] 保留新闻 (评分: {score:.1f}): {title[:50]}...")
            else:
                logger.debug(f"[过滤器] 过滤新闻 (评分: {score:.1f}): {title[:50]}...")
        
        # 创建过滤后的DataFrame
        if filtered_news:
            filtered_df = pd.DataFrame(filtered_news)
            # 按相关性评分排序
            filtered_df = filtered_df.sort_values('relevance_score', ascending=False)
            logger.info(f"[过滤器] 过滤完成，保留 {len(filtered_df)}条 新闻")
        else:
            filtered_df = pd.DataFrame()
            logger.warning(f"[过滤器] 所有新闻都被过滤，无符合条件的新闻")
            
        return filtered_df
    
    def get_filter_statistics(self, original_df: pd.DataFrame, filtered_df: pd.DataFrame) -> Dict:
        """
        获取过滤统计信息
        
        Args:
            original_df: 原始新闻DataFrame
            filtered_df: 过滤后新闻DataFrame
            
        Returns:
            Dict: 统计信息
        """
        stats = {
            'original_count': len(original_df),
            'filtered_count': len(filtered_df),
            'filter_rate': (len(original_df) - len(filtered_df)) / len(original_df) * 100 if len(original_df) > 0 else 0,
            'avg_score': filtered_df['relevance_score'].mean() if not filtered_df.empty else 0,
            'max_score': filtered_df['relevance_score'].max() if not filtered_df.empty else 0,
            'min_score': filtered_df['relevance_score'].min() if not filtered_df.empty else 0
        }
        
        return stats


# 股票代码到公司名称的映射
STOCK_COMPANY_MAPPING = {
    # A股主要银行
    '600036': '招商银行',
    '000001': '平安银行', 
    '600000': '浦发银行',
    '601166': '兴业银行',
    '002142': '宁波银行',
    '601328': '交通银行',
    '601398': '工商银行',
    '601939': '建设银行',
    '601288': '农业银行',
    '601818': '光大银行',
    '600015': '华夏银行',
    '600016': '民生银行',
    
    # A股主要白酒股
    '000858': '五粮液',
    '600519': '贵州茅台',
    '000568': '泸州老窖',
    '002304': '洋河股份',
    '000596': '古井贡酒',
    '603369': '今世缘',
    '000799': '酒鬼酒',
    
    # A股主要科技股
    '000002': '万科A',
    '000858': '五粮液',
    '002415': '海康威视',
    '000725': '京东方A',
    '002230': '科大讯飞',
    '300059': '东方财富',
    
    # 更多股票可以继续添加...
}

def get_company_name(ticker: str) -> str:
    """
    获取股票代码对应的公司名称
    
    Args:
        ticker: 股票代码
        
    Returns:
        str: 公司名称
    """
    # 清理股票代码（移除后缀）
    clean_ticker = ticker.split('.')[0]
    
    company_name = STOCK_COMPANY_MAPPING.get(clean_ticker)
    
    if company_name:
        logger.debug(f"[公司映射] {ticker} -> {company_name}")
        return company_name
    else:
        # 如果没有映射，返回默认名称
        default_name = f"股票{clean_ticker}"
        logger.warning(f"[公司映射] 未找到 {ticker} 的公司名称映射，使用默认: {default_name}")
        return default_name


def create_news_filter(ticker: str) -> NewsRelevanceFilter:
    """
    创建新闻过滤器的便捷函数
    
    Args:
        ticker: 股票代码
        
    Returns:
        NewsRelevanceFilter: 配置好的过滤器实例
    """
    company_name = get_company_name(ticker)
    return NewsRelevanceFilter(ticker, company_name)


# 使用示例
if __name__ == "__main__":
    # 测试过滤器
    import pandas as pd
    
    # 模拟新闻数据
    test_news = pd.DataFrame([
        {
            '新闻标题': '招商银行发布2024年第三季度业绩报告',
            '新闻内容': '招商银行今日发布第三季度财报，净利润同比增长8%...'
        },
        {
            '新闻标题': '上证180ETF指数基金（530280）自带杠铃策略',
            '新闻内容': '数据显示，上证180指数前十大权重股分别为贵州茅台、招商银行600036...'
        },
        {
            '新闻标题': '银行ETF指数(512730多只成分股上涨',
            '新闻内容': '银行板块今日表现强势，招商银行、工商银行等多只成分股上涨...'
        }
    ])
    
    # 创建过滤器
    filter = create_news_filter('600036')
    
    # 过滤新闻
    filtered_news = filter.filter_news(test_news, min_score=30)
    
    print(f"原始新闻: {len(test_news)}条")
    print(f"过滤后新闻: {len(filtered_news)}条")
    
    if not filtered_news.empty:
        print("\n过滤后的新闻:")
        for _, row in filtered_news.iterrows():
            print(f"- {row['新闻标题']} (评分: {row['relevance_score']:.1f})")