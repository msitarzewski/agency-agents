#!/usr/bin/env python3
"""
增强分析历史功能演示脚本
展示如何使用新的历史分析功能
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def demo_load_analysis_results():
    """演示加载分析结果"""
    print("🔍 演示：加载分析结果")
    print("-" * 30)
    
    try:
        from web.components.analysis_results import load_analysis_results
        
        # 加载最近的分析结果
        results = load_analysis_results(limit=5)
        
        print(f"📊 找到 {len(results)} 个分析结果")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 股票: {result.get('stock_symbol', 'unknown')}")
            print(f"   时间: {datetime.fromtimestamp(result.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M')}")
            print(f"   状态: {'✅ 完成' if result.get('status') == 'completed' else '❌ 失败'}")
            print(f"   分析师: {', '.join(result.get('analysts', []))}")
            
            # 显示摘要（如果有）
            summary = result.get('summary', '')
            if summary:
                preview = summary[:100] + "..." if len(summary) > 100 else summary
                print(f"   摘要: {preview}")
        
        return results
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return []


def demo_text_similarity():
    """演示文本相似度计算"""
    print("\n🔍 演示：文本相似度计算")
    print("-" * 30)
    
    try:
        from web.components.analysis_results import calculate_text_similarity
        
        # 测试文本
        texts = [
            "招商银行基本面良好，建议买入",
            "招商银行财务状况优秀，推荐购买",
            "平安银行技术指标显示下跌趋势",
            "中国平安保险业务增长强劲"
        ]
        
        print("📝 测试文本:")
        for i, text in enumerate(texts, 1):
            print(f"   {i}. {text}")
        
        print("\n📊 相似度矩阵:")
        print("     ", end="")
        for i in range(len(texts)):
            print(f"  {i+1:>6}", end="")
        print()
        
        for i, text1 in enumerate(texts):
            print(f"  {i+1}. ", end="")
            for j, text2 in enumerate(texts):
                similarity = calculate_text_similarity(text1, text2)
                print(f"  {similarity:>6.2f}", end="")
            print()
        
        print("\n💡 解读:")
        print("   - 1.00 表示完全相同")
        print("   - 0.50+ 表示较高相似度")
        print("   - 0.30- 表示较低相似度")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")


def demo_report_content_extraction():
    """演示报告内容提取"""
    print("\n🔍 演示：报告内容提取")
    print("-" * 30)
    
    try:
        from web.components.analysis_results import get_report_content
        
        # 模拟不同来源的分析结果
        test_cases = [
            {
                'name': '文件系统数据',
                'result': {
                    'source': 'file_system',
                    'reports': {
                        'final_trade_decision': '# 最终交易决策\n\n建议买入，目标价位 50 元',
                        'fundamentals_report': '# 基本面分析\n\n公司财务状况良好'
                    }
                }
            },
            {
                'name': '数据库数据',
                'result': {
                    'full_data': {
                        'final_trade_decision': '建议持有，等待更好时机',
                        'market_report': '技术指标显示震荡趋势'
                    }
                }
            },
            {
                'name': '直接数据',
                'result': {
                    'final_trade_decision': '建议卖出，风险较高',
                    'news_report': '近期负面新闻较多'
                }
            }
        ]
        
        for case in test_cases:
            print(f"\n📋 {case['name']}:")
            result = case['result']
            
            # 尝试提取不同类型的报告
            report_types = ['final_trade_decision', 'fundamentals_report', 'market_report', 'news_report']
            
            for report_type in report_types:
                content = get_report_content(result, report_type)
                if content:
                    preview = content[:50] + "..." if len(content) > 50 else content
                    print(f"   ✅ {report_type}: {preview}")
                else:
                    print(f"   ❌ {report_type}: 无内容")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")


def demo_stock_grouping():
    """演示股票分组功能"""
    print("\n🔍 演示：股票分组分析")
    print("-" * 30)
    
    try:
        from web.components.analysis_results import load_analysis_results
        
        # 加载分析结果
        results = load_analysis_results(limit=50)
        
        if not results:
            print("❌ 没有找到分析结果")
            return
        
        # 按股票代码分组
        stock_groups = {}
        for result in results:
            stock_symbol = result.get('stock_symbol', 'unknown')
            if stock_symbol not in stock_groups:
                stock_groups[stock_symbol] = []
            stock_groups[stock_symbol].append(result)
        
        print(f"📊 共找到 {len(stock_groups)} 只股票的分析记录")
        
        # 显示每只股票的分析次数
        stock_counts = [(stock, len(analyses)) for stock, analyses in stock_groups.items()]
        stock_counts.sort(key=lambda x: x[1], reverse=True)
        
        print("\n📈 股票分析频率排行:")
        for i, (stock, count) in enumerate(stock_counts[:10], 1):
            print(f"   {i:>2}. {stock}: {count} 次分析")
        
        # 找出有多次分析的股票
        multi_analysis_stocks = {k: v for k, v in stock_groups.items() if len(v) >= 2}
        
        if multi_analysis_stocks:
            print(f"\n🔄 有多次分析记录的股票 ({len(multi_analysis_stocks)} 只):")
            for stock, analyses in multi_analysis_stocks.items():
                print(f"   📊 {stock}: {len(analyses)} 次分析")
                
                # 显示时间范围
                timestamps = [a.get('timestamp', 0) for a in analyses]
                if timestamps:
                    earliest = datetime.fromtimestamp(min(timestamps))
                    latest = datetime.fromtimestamp(max(timestamps))
                    print(f"      ⏰ 时间范围: {earliest.strftime('%m-%d')} 到 {latest.strftime('%m-%d')}")
        else:
            print("\n💡 提示: 没有找到有多次分析记录的股票")
            print("   建议对同一股票进行多次分析以体验趋势对比功能")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")


def create_demo_data():
    """创建演示数据"""
    print("\n🔍 演示：创建演示数据")
    print("-" * 30)
    
    try:
        # 创建演示数据目录
        demo_stocks = ['DEMO001', 'DEMO002']
        base_dir = project_root / "data" / "analysis_results" / "detailed"
        
        for stock in demo_stocks:
            for days_ago in [0, 1, 3, 7]:
                date_str = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                reports_dir = base_dir / stock / date_str / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)
                
                # 创建不同的报告内容
                reports = {
                    'final_trade_decision.md': f'# {stock} 交易决策 ({date_str})\n\n{"买入" if days_ago % 2 == 0 else "持有"}建议',
                    'fundamentals_report.md': f'# {stock} 基本面分析\n\n基本面评分: {85 - days_ago * 2}/100',
                    'market_report.md': f'# {stock} 技术分析\n\n技术指标显示{"上涨" if days_ago < 3 else "震荡"}趋势'
                }
                
                for filename, content in reports.items():
                    report_file = reports_dir / filename
                    with open(report_file, 'w', encoding='utf-8') as f:
                        f.write(content)
        
        print(f"✅ 已为 {len(demo_stocks)} 只演示股票创建历史数据")
        print("   现在可以在Web界面中体验同股票历史对比功能")
        
    except Exception as e:
        print(f"❌ 创建演示数据失败: {e}")


def main():
    """主演示函数"""
    print("🚀 增强分析历史功能演示")
    print("=" * 50)
    
    demos = [
        ("加载分析结果", demo_load_analysis_results),
        ("文本相似度计算", demo_text_similarity),
        ("报告内容提取", demo_report_content_extraction),
        ("股票分组分析", demo_stock_grouping),
        ("创建演示数据", create_demo_data)
    ]
    
    for demo_name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ {demo_name} 演示失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("\n💡 下一步:")
    print("   1. 启动Web应用: python start_web.py")
    print("   2. 访问 '📈 分析结果' 页面")
    print("   3. 体验新的对比和统计功能")


if __name__ == "__main__":
    main()
