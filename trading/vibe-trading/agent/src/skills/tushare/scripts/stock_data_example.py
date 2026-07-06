#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据获取示例脚本
"""

import tushare as ts
import pandas as pd
import os

# 读取环境变量中的token, 或者读取本地记录的token
token = os.getenv('TUSHARE_TOKEN') or ts.get_token()

# 初始化pro接口
pro = ts.pro_api(token)


def get_stock_list():
    """
    获取股票列表
    """
    try:
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        print("股票列表获取成功：")
        print(data.head())
        return data
    except Exception as e:
        print(f"获取股票列表失败：{e}")
        return None


def get_daily_data(ts_code, start_date, end_date):
    """
    获取股票日线数据
    """
    try:
        data = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        print(f"{ts_code}日线数据获取成功：")
        print(data.head())
        return data
    except Exception as e:
        print(f"获取日线数据失败：{e}")
        return None


def get_financial_data(ts_code, year, quarter):
    """
    获取财务指标数据
    """
    try:
        data = pro.fina_indicator(ts_code=ts_code, year=year, quarter=quarter)
        print(f"{ts_code}财务指标数据获取成功：")
        print(data.head())
        return data
    except Exception as e:
        print(f"获取财务指标数据失败：{e}")
        return None


def main():
    """
    主函数
    """
    print("===== tushare 股票数据获取示例 =====")
    
    # 获取股票列表
    stock_list = get_stock_list()
    
    if stock_list is not None:
        # 获取第一只股票的代码
        ts_code = stock_list['ts_code'].iloc[0]
        print(f"\n使用股票代码：{ts_code}")
        
        # 获取日线数据（最近30天）
        import datetime
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
        print(f"\n获取日线数据：{start_date} 至 {end_date}")
        get_daily_data(ts_code, start_date, end_date)
        
        # 获取财务数据（最近一年）
        current_year = datetime.datetime.now().year
        print(f"\n获取财务数据：{current_year-1}年 第4季度")
        get_financial_data(ts_code, current_year-1, 4)


if __name__ == "__main__":
    main()
