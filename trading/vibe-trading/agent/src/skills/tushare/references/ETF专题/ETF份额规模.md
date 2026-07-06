# ETF份额规模


### 接口介绍
接口：etf_share_size
描述：获取沪深ETF每日份额和规模数据，能体现规模份额的变化，掌握ETF资金动向，同时提供每日净值和收盘价；数据指标是分批入库，建议在每日19点后提取；另外，涉及海外的ETF数据更新会晚一些属于正常情况。
限量：单次最大5000条，可根据代码或日期循环提取
积分：需要8000积分可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>

### 输入参数
名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 基金代码 （可从ETF基础信息接口提取）
trade_date | str | N | 交易日期（YYYYMMDD格式，下同）
start_date | str | N | 开始日期
end_date | str | N | 结束日期
exchange | str | N | 交易所（SSE上交所 SZSE深交所）

<br>

### 输出参数
名称 | 类型 | 默认显示 | 描述
---- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | ETF代码
etf_name | str | Y | 基金名称
total_share | float | Y | 总份额（万份）
total_size | float | Y | 总规模（万元）
nav | float | N | 基金份额净值(元)
close | float | N | 收盘价（元）
exchange | str | Y | 交易所（SSE上交所 SZSE深交所 BSE北交所）



### 代码示例
```python

#获取”沪深300ETF华夏”ETF2025年以来每个交易日的份额和规模情况
df = pro.etf_share_size(ts_code='510330.SH', start_date='20250101', end_date='20251224')

#获取2025年12月24日上交所的所有ETF份额和规模情况
df = pro.etf_share_size(trade_date='20251224', exchange='SSE')

```

### 数据结果

        trade_date    ts_code       etf_name  total_share    total_size exchange
    0     20251224  510330.SH  沪深300ETF华夏   4741854.98  2.287898e+07      SSE
    1     20251222  510330.SH  沪深300ETF华夏   4746894.98  2.279127e+07      SSE
    2     20251219  510330.SH  沪深300ETF华夏   4756974.98  2.262512e+07      SSE
    3     20251218  510330.SH  沪深300ETF华夏   4757514.98  2.253778e+07      SSE
    4     20251217  510330.SH  沪深300ETF华夏   4756884.98  2.266418e+07      SSE
    ..         ...        ...         ...          ...           ...      ...
    232   20250108  510330.SH  沪深300ETF华夏   4032384.98  1.599808e+07      SSE
    233   20250107  510330.SH  沪深300ETF华夏   4009164.98  1.592962e+07      SSE
    234   20250106  510330.SH  沪深300ETF华夏   3999084.98  1.577239e+07      SSE
    235   20250103  510330.SH  沪深300ETF华夏   3994674.98  1.578176e+07      SSE
    236   20250102  510330.SH  沪深300ETF华夏   3986754.98  1.593905e+07      SSE