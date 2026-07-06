## 期权日线行情
----

接口：opt_daily
描述：获取期权日线行情
限量：单次最大15000条数据，可跟进日线或者代码循环，总量不限制
积分：用户需要至少2000积分才可以调取，但有流量控制，请自行提高积分，积分越多权限越大，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS合约代码（输入代码或时间至少任意一个参数）
trade_date | str | N | 交易日期
start_date | str | N | 开始日期
end_date | str | N | 结束日期
exchange | str | N | 交易所(SSE/SZSE/CFFEX/DCE/SHFE/CZCE）

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
trade_date | str | Y | 交易日期
exchange | str | Y | 交易市场
pre_settle | float | Y | 昨结算价
pre_close | float | Y | 前收盘价
open | float | Y | 开盘价
high | float | Y | 最高价
low | float | Y | 最低价
close | float | Y | 收盘价
settle | float | Y | 结算价
vol | float | Y | 成交量(手)
amount | float | Y | 成交金额(万元)
oi | float | Y | 持仓量(手)

<br>
<br>

**接口示例**

```python

pro = ts.pro_api('your token')

df = pro.opt_daily(trade_date='20181212')

```

<br>
<br>

**数据示例**


			ts_code trade_date exchange  ...      vol       amount       oi
	0         10001313.SH   20181212      SSE  ...  38354.0  1261.435472  98882.0
	1         10001314.SH   20181212      SSE  ...  14472.0   234.933288  79980.0
	2         10001315.SH   20181212      SSE  ...  10092.0    69.311776  72370.0
	3         10001316.SH   20181212      SSE  ...   5434.0    16.107224  55117.0
	4         10001317.SH   20181212      SSE  ...   4240.0     5.798919  61746.0
	..                ...        ...      ...  ...      ...          ...      ...
	753  M1911-P-2900.DCE   20181212      DCE  ...      0.0     0.000000     20.0
	754  M1911-P-2950.DCE   20181212      DCE  ...      0.0     0.000000     20.0
	755  M1911-P-3000.DCE   20181212      DCE  ...      0.0     0.000000     20.0
	756  M1911-P-3050.DCE   20181212      DCE  ...      0.0     0.000000     20.0
	757  M1911-P-3100.DCE   20181212      DCE  ...      0.0     0.000000      0.0