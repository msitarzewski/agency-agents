## 美股复权行情
----

接口：us_daily_adj，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取美股复权行情，支持美股全市场股票，提供股本、市值、复权因子和成交信息等多个数据指标
限量：单次最大可以提取8000条数据，可循环获取全部，支持分页提取
要求：120积分可以试用查看数据，开通正式权限请参考[权限说明文档](https://tushare.pro/document/1?doc_id=290)

注：美股复权逻辑是：价格 * 复权因子 = 复权价格，比如close * adj_factor = 前复权收盘价。复权因子历史数据可能除权等被刷新，请注意动态更新。

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码（e.g. AAPL）
trade_date | str | N | 交易日期（YYYYMMDD）
start_date | str | N | 开始日期（YYYYMMDD）
end_date | str | N | 结束日期（YYYYMMDD）
exchange | str | N | 交易所（NAS/NYS/OTC)
offset | int | N | 开始行数
limit | int | N | 每页行数行数

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
trade_date | str | Y | 交易日期
close | float | Y | 收盘价
open | float | Y | 开盘价
high | float | Y | 最高价
low | float | Y | 最低价
pre_close | float | Y | 昨收价
change | float | Y | 涨跌额
pct_change | float | Y | 涨跌幅
vol | int | Y | 成交量
amount | float | Y | 成交额
vwap | float | Y | 平均价
adj_factor | float | Y | 复权因子
turnover_ratio | float | Y | 换手率
free_share | int | Y | 流通股本
total_share | int | Y | 总股本
free_mv | float | Y | 流通市值
total_mv | float | Y | 总市值
exchange | str | Y | 交易所代码

<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取单一股票行情
df = pro.us_daily_adj(ts_code='AAPL', start_date='20240101', end_date='20240722')

#获取某一日某个交易所的全部股票
df = pro.us_daily_adj(trade_date='20240722', exhange='NAS')

```

<br>
<br>

**数据示例**

        ts_code trade_date   close pre_close pct_change       vol            amount    vwap adj_factor turnover_ratio
	0      AAPL   20240722  223.96    224.31       0.00  48201836  10846348215.6184  225.02     1.0000           0.31
	1      AAPL   20240719  224.31    224.18       0.00  49151454  11046273687.7475  224.74     1.0000           0.32
	2      AAPL   20240718  224.18    228.88      -0.02  66034563  14869485263.3655  225.18     1.0000           0.43
	3      AAPL   20240717  228.88    234.82      -0.03  57345883  13120715665.5056  228.80     1.0000           0.37
	4      AAPL   20240716  234.82    234.40       0.00  43234278  10128420808.7874  234.27     1.0000           0.28
	..      ...        ...     ...       ...        ...       ...               ...     ...        ...            ...
	134    AAPL   20240108  185.07    180.70       0.02  59144469  10903064025.6147  183.86     0.9974           0.38
	135    AAPL   20240105  180.70    181.43       0.00  62379661  11321622148.8560  181.02     0.9974           0.40
	136    AAPL   20240104  181.43    183.77      -0.01  71983563  13102384071.8889  181.54     0.9974           0.47
	137    AAPL   20240103  183.77    185.15      -0.01  58414461  10767233840.9328  183.84     0.9974           0.38
	138    AAPL   20240102  185.15    192.02      -0.04  82488688  15330365936.2928  185.36     0.9974           0.53
