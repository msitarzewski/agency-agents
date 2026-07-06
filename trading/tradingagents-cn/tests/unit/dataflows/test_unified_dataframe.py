import pandas as pd
from unittest import mock

from tradingagents.dataflows.unified_dataframe import get_china_daily_df_unified


def test_unified_dataframe_prefers_tushare_then_akshare_then_baostock():
    # 模拟三个来源：tushare成功，后两个不应被调用
    with mock.patch('tradingagents.dataflows.unified_dataframe.get_tushare_adapter') as m_ts, \
         mock.patch('tradingagents.dataflows.unified_dataframe.get_akshare_provider') as m_ak, \
         mock.patch('tradingagents.dataflows.unified_dataframe.get_baostock_provider') as m_bs, \
         mock.patch('tradingagents.dataflows.unified_dataframe.get_data_source_manager') as m_dsm:

        df_ts = pd.DataFrame({
            'Open':[1,2], 'High':[2,3], 'Low':[0.5,1.5], 'Close':[1.5,2.5], 'Volume':[100,200], 'Amount':[150,500], 'trade_date':['2024-01-01','2024-01-02']
        })
        m_ts.return_value.get_stock_data.return_value = df_ts
        m_ak.return_value.get_stock_data.return_value = pd.DataFrame()
        m_bs.return_value.get_stock_data.return_value = pd.DataFrame()

        # 当前源为 tushare
        m_dsm.return_value.current_source.value = 'tushare'
        m_dsm.return_value.available_sources = []

        df = get_china_daily_df_unified('000001', '2024-01-01', '2024-01-31')
        assert not df.empty
        assert 'close' in df.columns  # 已标准化
        assert df.shape[0] == 2


def test_unified_dataframe_fallback_to_baostock_when_others_fail():
    with mock.patch('tradingagents.dataflows.unified_dataframe.get_tushare_adapter') as m_ts, \
         mock.patch('tradingagents.dataflows.unified_dataframe.get_akshare_provider') as m_ak, \
         mock.patch('tradingagents.dataflows.unified_dataframe.get_baostock_provider') as m_bs, \
         mock.patch('tradingagents.dataflows.unified_dataframe.get_data_source_manager') as m_dsm:

        m_ts.return_value.get_stock_data.return_value = pd.DataFrame()
        m_ak.return_value.get_stock_data.return_value = pd.DataFrame()
        df_bs = pd.DataFrame({
            'date':['2024-01-01','2024-01-02'], 'code':['sz.000001','sz.000001'],
            'open':[1,2], 'high':[2,3], 'low':[0.5,1.5], 'close':[1.5,2.5], 'volume':[100,200], 'amount':[150,500]
        })
        m_bs.return_value.get_stock_data.return_value = df_bs

        m_dsm.return_value.current_source.value = 'tushare'
        m_dsm.return_value.available_sources = ['akshare','baostock']

        df = get_china_daily_df_unified('000001', '2024-01-01', '2024-01-31')
        assert not df.empty
        assert 'close' in df.columns
        assert df.iloc[0]['close'] == 1.5

