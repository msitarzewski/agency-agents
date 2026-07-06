#!/usr/bin/env python3
"""
计算股票300750的估值指标
"""

import pymongo
from tradingagents.config.database_manager import get_database_manager

def calculate_valuation_ratios(stock_code):
    """计算估值比率"""
    print(f'=== 计算股票{stock_code}的估值指标 ===')
    
    try:
        db_manager = get_database_manager()
        
        if not db_manager.is_mongodb_available():
            print('❌ MongoDB不可用')
            return None
        
        client = db_manager.get_mongodb_client()
        db = client['tradingagents']
        
        # 获取财务数据
        financial_collection = db['stock_financial_data']
        financial_doc = financial_collection.find_one({'code': stock_code})
        
        if not financial_doc:
            print(f'❌ 未找到{stock_code}的财务数据')
            return None
        
        print('✅ 找到财务数据')
        
        # 获取股价数据
        quotes_collection = db['stock_daily_quotes']
        latest_quote = quotes_collection.find_one(
            {'code': stock_code}, 
            sort=[('date', -1)]
        )
        
        if not latest_quote:
            print(f'❌ 未找到{stock_code}的股价数据')
            return None
        
        print('✅ 找到股价数据')
        
        # 提取关键数据
        current_price = latest_quote.get('close', 0)
        total_market_cap = financial_doc.get('money_cap', 0)  # 总市值
        net_profit = financial_doc.get('net_profit', 0)  # 净利润
        total_equity = financial_doc.get('total_hldr_eqy_exc_min_int', 0)  # 股东权益
        revenue = financial_doc.get('revenue', 0)  # 营业收入
        
        print(f'\n📊 基础数据:')
        print(f'  当前股价: {current_price}')
        print(f'  总市值: {total_market_cap:,.0f}')
        print(f'  净利润: {net_profit}')
        print(f'  股东权益: {total_equity}')
        print(f'  营业收入: {revenue}')
        
        # 计算估值指标
        results = {}
        
        # 计算PE比率 (市值/净利润)
        if net_profit and net_profit > 0:
            pe_ratio = total_market_cap / net_profit
            results['PE'] = pe_ratio
            print(f'\n✅ PE比率: {pe_ratio:.2f}')
        else:
            print(f'\n❌ 无法计算PE比率 (净利润: {net_profit})')
        
        # 计算PB比率 (市值/净资产)
        if total_equity and total_equity > 0:
            pb_ratio = total_market_cap / total_equity
            results['PB'] = pb_ratio
            print(f'✅ PB比率: {pb_ratio:.2f}')
        else:
            print(f'❌ 无法计算PB比率 (股东权益: {total_equity})')
        
        # 计算PS比率 (市值/营业收入)
        if revenue and revenue > 0:
            ps_ratio = total_market_cap / revenue
            results['PS'] = ps_ratio
            print(f'✅ PS比率: {ps_ratio:.2f}')
        else:
            print(f'❌ 无法计算PS比率 (营业收入: {revenue})')
        
        # 查看更多财务字段
        print(f'\n🔍 其他可能的估值相关字段:')
        valuation_keywords = ['share', 'equity', 'asset', 'profit', 'income', 'earn']
        
        for key, value in financial_doc.items():
            if any(keyword in key.lower() for keyword in valuation_keywords):
                if isinstance(value, (int, float)) and value != 0:
                    print(f'  {key}: {value}')
        
        return results
        
    except Exception as e:
        print(f'计算估值指标时出错: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    calculate_valuation_ratios('300750')