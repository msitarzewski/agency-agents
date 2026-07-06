## 通达信板块行情
----

接口：tdx_daily
描述：获取通达信各板块行情，包括成交和估值等数据
限量：单次提取最大3000条数据，可根据板块代码和日期参数循环提取
权限：用户积累6000积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

<br>
<br>


**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 板块代码：xxxxxx.TDX
trade_date | str | N | 交易日期，格式YYYYMMDD,下同
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 板块代码
trade_date | str | Y | 交易日期
close | float | Y | 收盘点位
open | float | Y | 开盘点位
high | float | Y | 最高点位
low | float | Y | 最低点位
pre_close | float | Y | 昨日收盘点
change | float | Y | 涨跌点位
pct_change | float | Y | 涨跌幅%
vol | float | Y | 成交量（手）
amount | float | Y | 成交额（万元）, 对于期货指数，该字段存储持仓量
rise | str | Y | 收盘涨速%
vol_ratio | float | Y | 量比
turnover_rate | float | Y | 换手%
swing | float | Y | 振幅%
up_num | int | Y | 上涨家数
down_num | int | Y | 下跌家数
limit_up_num | int | Y | 涨停家数
limit_down_num | int | Y | 跌停家数
lu_days | int | Y | 连涨天数
3day | float | Y | 3日涨幅%
5day | float | Y | 5日涨幅%
10day | float | Y | 10日涨幅%
20day | float | Y | 20日涨幅%
60day | float | Y | 60日涨幅%
mtd | float | Y | 月初至今%
ytd | float | Y | 年初至今%
1year | float | Y | 一年涨幅%
pe | str | Y | 市盈率
pb | str | Y | 市净率
float_mv | float | Y | 流通市值(亿)
ab_total_mv | float | Y | AB股总市值（亿）
float_share | float | Y | 流通股(亿)
total_share | float | Y | 总股本(亿)
bm_buy_net | float | Y | 主买净额(元)
bm_buy_ratio | float | Y | 主买占比%
bm_net | float | Y | 主力净额
bm_ratio | float | Y | 主力占比%

<br>
<br>

**接口示例**

```python

#获取通达信2025年5月13日概念板块行情
df = pro.tdx_daily(trade_date='20250513')


```


<br>
<br>

**数据示例**

        ts_code trade_date    close     open     high  ...  total_share  bm_buy_net  bm_buy_ratio     bm_net  bm_ratio
	0    880559.TDX   20250513  4344.82  4243.64  4377.61  ...        63.92    -3711.74         -5.99    3460.16      5.58
	1    880728.TDX   20250513  1426.69  1417.49  1429.39  ...      2060.22    -6268.93         -0.29   28491.26      1.32
	2    880355.TDX   20250513  1432.23  1403.51  1445.14  ...        70.76     -923.37         -0.17   58055.81     10.40
	3    880423.TDX   20250513   919.10   907.35   921.78  ...        56.45    12268.21          8.46     420.44      0.29
	4    880875.TDX   20250513  1385.67  1365.73  1387.00  ...      1986.86   207359.44         16.90    3214.69      0.26
	..          ...        ...      ...      ...      ...  ...          ...         ...           ...        ...       ...
	482  880528.TDX   20250513  1298.93  1334.78  1335.18  ...       579.52  -566197.66        -12.66 -285997.36     -6.40
	483  880868.TDX   20250513  1359.55  1412.46  1418.79  ...       108.15   -11975.73         -0.80     -89.57     -0.01
	484  880430.TDX   20250513  1865.61  1914.31  1914.31  ...       398.07  -333388.49        -10.96 -200437.09     -6.59
	485  880431.TDX   20250513   796.66   825.16   825.16  ...       367.64  -246591.46        -23.97 -131926.99    -12.82
	486  880914.TDX   20250513  1009.77  1047.47  1047.55  ...       310.96  -337334.58        -10.57 -423231.69    -13.26