"""
增强新闻过滤器 - 集成本地小模型和规则过滤
支持多种过滤策略：规则过滤、语义相似度、本地分类模型
"""

import pandas as pd
import re
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np

# 导入基础过滤器
from .news_filter import NewsRelevanceFilter, create_news_filter, get_company_name

logger = logging.getLogger(__name__)

class EnhancedNewsFilter(NewsRelevanceFilter):
    """增强新闻过滤器，集成本地模型和多种过滤策略"""
    
    def __init__(self, stock_code: str, company_name: str, use_semantic: bool = True, use_local_model: bool = False):
        """
        初始化增强过滤器
        
        Args:
            stock_code: 股票代码
            company_name: 公司名称
            use_semantic: 是否使用语义相似度过滤
            use_local_model: 是否使用本地分类模型
        """
        super().__init__(stock_code, company_name)
        self.use_semantic = use_semantic
        self.use_local_model = use_local_model
        
        # 语义模型相关
        self.sentence_model = None
        self.company_embedding = None
        
        # 本地分类模型相关
        self.classification_model = None
        self.tokenizer = None
        
        # 初始化模型
        if use_semantic:
            self._init_semantic_model()
        if use_local_model:
            self._init_classification_model()
    
    def _init_semantic_model(self):
        """初始化语义相似度模型"""
        try:
            logger.info("[增强过滤器] 正在加载语义相似度模型...")
            
            # 尝试使用sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer
                
                # 使用轻量级中文模型
                model_name = "paraphrase-multilingual-MiniLM-L12-v2"  # 支持中文的轻量级模型
                self.sentence_model = SentenceTransformer(model_name)
                
                # 预计算公司相关的embedding
                company_texts = [
                    self.company_name,
                    f"{self.company_name}股票",
                    f"{self.company_name}公司",
                    f"{self.stock_code}",
                    f"{self.company_name}业绩",
                    f"{self.company_name}财报"
                ]
                
                self.company_embedding = self.sentence_model.encode(company_texts)
                logger.info(f"[增强过滤器] ✅ 语义模型加载成功: {model_name}")
                
            except ImportError:
                logger.warning("[增强过滤器] sentence-transformers未安装，跳过语义过滤")
                self.use_semantic = False
                
        except Exception as e:
            logger.error(f"[增强过滤器] 语义模型初始化失败: {e}")
            self.use_semantic = False
    
    def _init_classification_model(self):
        """初始化本地分类模型"""
        try:
            logger.info("[增强过滤器] 正在加载本地分类模型...")
            
            # 尝试使用transformers库的中文分类模型
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
                
                # 使用轻量级中文文本分类模型
                model_name = "uer/roberta-base-finetuned-chinanews-chinese"
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.classification_model = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                logger.info(f"[增强过滤器] ✅ 分类模型加载成功: {model_name}")
                
            except ImportError:
                logger.warning("[增强过滤器] transformers未安装，跳过本地模型分类")
                self.use_local_model = False
                
        except Exception as e:
            logger.error(f"[增强过滤器] 本地分类模型初始化失败: {e}")
            self.use_local_model = False
    
    def calculate_semantic_similarity(self, title: str, content: str) -> float:
        """
        计算语义相似度评分
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            float: 语义相似度评分 (0-100)
        """
        if not self.use_semantic or self.sentence_model is None:
            return 0
        
        try:
            # 组合标题和内容的前200字符
            text = f"{title} {content[:200]}"
            
            # 计算文本embedding
            text_embedding = self.sentence_model.encode([text])
            
            # 计算与公司相关文本的相似度
            similarities = []
            for company_emb in self.company_embedding:
                similarity = np.dot(text_embedding[0], company_emb) / (
                    np.linalg.norm(text_embedding[0]) * np.linalg.norm(company_emb)
                )
                similarities.append(similarity)
            
            # 取最高相似度
            max_similarity = max(similarities)
            
            # 转换为0-100评分
            semantic_score = max(0, min(100, max_similarity * 100))
            
            logger.debug(f"[增强过滤器] 语义相似度评分: {semantic_score:.1f}")
            return semantic_score
            
        except Exception as e:
            logger.error(f"[增强过滤器] 语义相似度计算失败: {e}")
            return 0
    
    def classify_news_relevance(self, title: str, content: str) -> float:
        """
        使用本地模型分类新闻相关性
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            float: 分类相关性评分 (0-100)
        """
        if not self.use_local_model or self.classification_model is None:
            return 0
        
        try:
            import torch
            
            # 构建分类文本
            text = f"{title} {content[:300]}"
            
            # 添加公司信息作为上下文
            context_text = f"关于{self.company_name}({self.stock_code})的新闻: {text}"
            
            # 分词和编码
            inputs = self.tokenizer(
                context_text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            # 模型推理
            with torch.no_grad():
                outputs = self.classification_model(**inputs)
                logits = outputs.logits
                
                # 使用softmax获取概率分布
                probabilities = torch.softmax(logits, dim=-1)
                
                # 假设第一个类别是"相关"，第二个是"不相关"
                # 这里需要根据具体模型调整
                relevance_prob = probabilities[0][0].item()  # 相关性概率
                
                # 转换为0-100评分
                classification_score = relevance_prob * 100
                
                logger.debug(f"[增强过滤器] 分类模型评分: {classification_score:.1f}")
                return classification_score
                
        except Exception as e:
            logger.error(f"[增强过滤器] 本地模型分类失败: {e}")
            return 0
    
    def calculate_enhanced_relevance_score(self, title: str, content: str) -> Dict[str, float]:
        """
        计算增强相关性评分（综合多种方法）
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            Dict: 包含各种评分的字典
        """
        scores = {}
        
        # 1. 基础规则评分
        rule_score = super().calculate_relevance_score(title, content)
        scores['rule_score'] = rule_score
        
        # 2. 语义相似度评分
        if self.use_semantic:
            semantic_score = self.calculate_semantic_similarity(title, content)
            scores['semantic_score'] = semantic_score
        else:
            scores['semantic_score'] = 0
        
        # 3. 本地模型分类评分
        if self.use_local_model:
            classification_score = self.classify_news_relevance(title, content)
            scores['classification_score'] = classification_score
        else:
            scores['classification_score'] = 0
        
        # 4. 综合评分（加权平均）
        weights = {
            'rule': 0.4,      # 规则过滤权重40%
            'semantic': 0.35,  # 语义相似度权重35%
            'classification': 0.25  # 分类模型权重25%
        }
        
        final_score = (
            weights['rule'] * rule_score +
            weights['semantic'] * scores['semantic_score'] +
            weights['classification'] * scores['classification_score']
        )
        
        scores['final_score'] = final_score
        
        logger.debug(f"[增强过滤器] 综合评分 - 规则:{rule_score:.1f}, 语义:{scores['semantic_score']:.1f}, "
                    f"分类:{scores['classification_score']:.1f}, 最终:{final_score:.1f}")
        
        return scores
    
    def filter_news_enhanced(self, news_df: pd.DataFrame, min_score: float = 40) -> pd.DataFrame:
        """
        增强新闻过滤
        
        Args:
            news_df: 原始新闻DataFrame
            min_score: 最低综合评分阈值
            
        Returns:
            pd.DataFrame: 过滤后的新闻DataFrame，包含详细评分信息
        """
        if news_df.empty:
            logger.warning("[增强过滤器] 输入新闻DataFrame为空")
            return news_df
        
        logger.info(f"[增强过滤器] 开始增强过滤，原始数量: {len(news_df)}条，最低评分阈值: {min_score}")
        
        filtered_news = []
        
        for idx, row in news_df.iterrows():
            title = row.get('新闻标题', row.get('标题', ''))
            content = row.get('新闻内容', row.get('内容', ''))
            
            # 计算增强评分
            scores = self.calculate_enhanced_relevance_score(title, content)
            
            if scores['final_score'] >= min_score:
                row_dict = row.to_dict()
                row_dict.update(scores)  # 添加所有评分信息
                filtered_news.append(row_dict)
                
                logger.debug(f"[增强过滤器] 保留新闻 (综合评分: {scores['final_score']:.1f}): {title[:50]}...")
            else:
                logger.debug(f"[增强过滤器] 过滤新闻 (综合评分: {scores['final_score']:.1f}): {title[:50]}...")
        
        # 创建过滤后的DataFrame
        if filtered_news:
            filtered_df = pd.DataFrame(filtered_news)
            # 按综合评分排序
            filtered_df = filtered_df.sort_values('final_score', ascending=False)
            logger.info(f"[增强过滤器] 增强过滤完成，保留 {len(filtered_df)}条 新闻")
        else:
            filtered_df = pd.DataFrame()
            logger.warning(f"[增强过滤器] 所有新闻都被过滤，无符合条件的新闻")
            
        return filtered_df


def create_enhanced_news_filter(ticker: str, use_semantic: bool = True, use_local_model: bool = False) -> EnhancedNewsFilter:
    """
    创建增强新闻过滤器的便捷函数
    
    Args:
        ticker: 股票代码
        use_semantic: 是否使用语义相似度过滤
        use_local_model: 是否使用本地分类模型
        
    Returns:
        EnhancedNewsFilter: 配置好的增强过滤器实例
    """
    company_name = get_company_name(ticker)
    return EnhancedNewsFilter(ticker, company_name, use_semantic, use_local_model)


# 使用示例
if __name__ == "__main__":
    # 测试增强过滤器
    import pandas as pd
    
    # 模拟新闻数据
    test_news = pd.DataFrame([
        {
            '新闻标题': '招商银行发布2024年第三季度业绩报告',
            '新闻内容': '招商银行今日发布第三季度财报，净利润同比增长8%，资产质量持续改善...'
        },
        {
            '新闻标题': '上证180ETF指数基金（530280）自带杠铃策略',
            '新闻内容': '数据显示，上证180指数前十大权重股分别为贵州茅台、招商银行600036...'
        },
        {
            '新闻标题': '银行ETF指数(512730)多只成分股上涨',
            '新闻内容': '银行板块今日表现强势，招商银行、工商银行等多只成分股上涨...'
        },
        {
            '新闻标题': '招商银行与某科技公司签署战略合作协议',
            '新闻内容': '招商银行宣布与知名科技公司达成战略合作，将在数字化转型方面深度合作...'
        }
    ])
    
    print("=== 测试增强新闻过滤器 ===")
    
    # 创建增强过滤器（仅使用规则过滤，避免模型依赖）
    enhanced_filter = create_enhanced_news_filter('600036', use_semantic=False, use_local_model=False)
    
    # 过滤新闻
    filtered_news = enhanced_filter.filter_news_enhanced(test_news, min_score=30)
    
    print(f"原始新闻: {len(test_news)}条")
    print(f"过滤后新闻: {len(filtered_news)}条")
    
    if not filtered_news.empty:
        print("\n过滤后的新闻:")
        for _, row in filtered_news.iterrows():
            print(f"- {row['新闻标题']} (综合评分: {row['final_score']:.1f})")
            print(f"  规则评分: {row['rule_score']:.1f}, 语义评分: {row['semantic_score']:.1f}, 分类评分: {row['classification_score']:.1f}")