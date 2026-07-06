#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金数据获取示例脚本
"""

import tushare as ts
import pandas as pd
import os

# 读取环境变量中的token, 或者读取本地记录的token
token = os.getenv('TUSHARE_TOKEN') or ts.get_token()

# 初始化pro接口
pro = ts.pro_api(token)


def get_fund_list():
    """
    获取基金列表
    """
    try:
        data = pro.fund_basic(market='E', status='L', fields='ts_code,fund_name,fund_type,found_date,issue_date,delist_date')
        print("基金列表获取成功：")
        print(data.head())
        return data
    except Exception as e:
        print(f"获取基金列表失败：{e}")
        return None


def get_fund_nav(ts_code, start_date, end_date):
    """
    获取基金净值数据
    """
    try:
        data = pro.fund_nav(ts_code=ts_code, start_date=start_date, end_date=end_date)
        print(f"{ts_code}基金净值数据获取成功：")
        print(data.head())
        return data
    except Exception as e:
        print(f"获取基金净值数据失败：{e}")
        return None


def get_fund_manager():
    """
    获取基金经理数据
    """
    try:
        data = pro.fund_manager(limit=10, fields='ts_code,fund_name,manager_name,begin_date,end_date')
        print("基金经理数据获取成功：")
        print(data.head())
        return data
    except Exception as e:
        print(f"获取基金经理数据失败：{e}")
        return None


def main():
    """
    主函数
    """
    print("===== tushare 基金数据获取示例 =====")
    
    # 获取基金列表
    fund_list = get_fund_list()
    
    if fund_list is not None:
        # 获取第一只基金的代码
        ts_code = fund_list['ts_code'].iloc[0]
        print(f"\n使用基金代码：{ts_code}")
        
        # 获取基金净值数据（最近30天）
        import datetime
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
        print(f"\n获取基金净值数据：{start_date} 至 {end_date}")
        get_fund_nav(ts_code, start_date, end_date)
    
    # 获取基金经理数据
    print("\n获取基金经理数据：")
    get_fund_manager()


if __name__ == "__main__":
    main()
