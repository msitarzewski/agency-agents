"""
Mootdx A-Share Data Fetcher — Standard adapter.
Free, no API key, no IP rate limits.

Usage:
    from a_mootdx_fetcher import fetch_daily, fetch_realtime, batch_fetch_daily
"""
from mootdx.quotes import Quotes
import pandas as pd
from typing import Optional, List

FREQ_MAP = {'5min':0,'15min':1,'30min':2,'60min':3,'daily':9,'weekly':5,'monthly':6,'1min':8}

def _get_client():
    return Quotes.factory(market='std')

def _code_to_symbol(code: str) -> tuple:
    code = code.strip().upper()
    if '.' in code:
        parts = code.split('.')
        pure, suffix = parts[0], parts[1].upper()
        market = 1 if suffix in ('SH','1') else 0
    else:
        pure = code
        market = 1 if code[0] in ('6','5','9') else 0
    return market, pure

def fetch_daily(code: str, start_date=None, end_date=None, limit=250) -> pd.DataFrame:
    client = _get_client()
    _, pure = _code_to_symbol(code)
    df = client.bars(symbol=pure, frequency=9, offset=limit)
    if df is None or len(df) == 0:
        return pd.DataFrame()
    if 'datetime' in df.columns:
        df['date'] = pd.to_datetime(df['datetime'])
    df = df.rename(columns={'vol':'volume'})
    cols = [c for c in ['date','open','high','low','close','volume','amount'] if c in df.columns]
    df = df[cols].copy()
    if 'date' in df.columns:
        df = df.set_index('date').sort_index()
        if start_date: df = df[df.index >= pd.Timestamp(start_date)]
        if end_date: df = df[df.index <= pd.Timestamp(end_date)]
    return df

def fetch_realtime(codes: list) -> pd.DataFrame:
    client = _get_client()
    pure_codes = [_code_to_symbol(c)[1] for c in codes]
    df = client.quotes(symbol=pure_codes)
    if df is None or len(df) == 0:
        return pd.DataFrame()
    r = pd.DataFrame()
    r['code'] = df['code']
    r['price'] = df['price']
    r['open'] = df['open']
    r['high'] = df['high']
    r['low'] = df['low']
    r['last_close'] = df['last_close']
    r['change'] = df['price'] - df['last_close']
    r['change_pct'] = ((df['price'] - df['last_close']) / df['last_close'] * 100).round(2)
    r['volume'] = df['vol']
    r['amount'] = df['amount']
    return r

def batch_fetch_daily(codes, limit=250, sleep_sec=0.3):
    import time
    results = {}
    for i, code in enumerate(codes):
        try:
            df = fetch_daily(code, limit=limit)
            if len(df) > 0: results[code] = df
        except: results[code] = pd.DataFrame()
        if i < len(codes) - 1: time.sleep(sleep_sec)
    return results

def get_a_share_list():
    client = _get_client()
    frames = []
    for m in [0, 1]:
        df = client.stocks(market=m)
        if df is not None and len(df) > 0:
            df['market'] = m
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
