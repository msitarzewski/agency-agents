## 港股复权行情
----

接口：hk_daily_adj，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取港股复权行情，提供股票股本、市值和成交及换手多个数据指标
限量：单次最大可以提取6000条数据，可循环获取全部，支持分页提取
要求：120积分可以试用查看数据，开通正式权限请参考[权限说明文档](https://tushare.pro/document/1?doc_id=290)

注：港股复权逻辑是：价格 * 复权因子 = 复权价格，比如close * adj_factor = 前复权收盘价。复权因子历史数据可能除权等被刷新，请注意动态更新。

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码（e.g. 00001.HK）
trade_date | str | N | 交易日期（YYYYMMDD）
start_date | str | N | 开始日期（YYYYMMDD）
end_date | str | N | 结束日期（YYYYMMDD）

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
vol | None | Y | 成交量
amount | float | Y | 成交额
vwap | float | Y | 平均价
adj_factor | float | Y | 复权因子
turnover_ratio | float | Y | 换手率(基于总股本)
free_share | None | Y | 流通股本
total_share | None | Y | 总股本
free_mv | float | Y | 流通市值
total_mv | float | Y | 总市值


<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取单一股票行情
df = pro.hk_daily_adj(ts_code='00001.HK', start_date='20240101', end_date='20240722')

#获取某一日某个交易所的全部股票
df = pro.hk_daily_adj(trade_date='20240722')

```

<br>
<br>

**数据示例**

          ts_code trade_date  close pre_close      vol adj_factor turnover_ratio
	0    00001.HK   20240722  40.95     40.90  2799284     1.0000           0.07
	1    00001.HK   20240719  40.90     40.85  6472801     1.0000           0.17
	2    00001.HK   20240718  40.85     40.50  5498406     1.0000           0.14
	3    00001.HK   20240717  40.50     39.95  4151953     1.0000           0.11
	4    00001.HK   20240716  39.95     40.15  3978223     1.0000           0.10
	..        ...        ...    ...       ...      ...        ...            ...
	131  00001.HK   20240108  38.91     39.05  3271763     0.9572           0.09
	132  00001.HK   20240105  39.05     39.24  2731319     0.9572           0.07
	133  00001.HK   20240104  39.24     39.58  2800255     0.9572           0.07
	134  00001.HK   20240103  39.58     39.48  3498817     0.9572           0.09
	135  00001.HK   20240102  39.48     40.06  2782895     0.9572           0.07

	[136 rows x 7 columns]
