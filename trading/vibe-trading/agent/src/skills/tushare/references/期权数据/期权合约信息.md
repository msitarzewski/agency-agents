## 期权合约信息
----

接口：opt_basic
描述：获取期权合约信息
积分：用户需要至少5000积分可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS期权代码
exchange | str | N | 交易所代码 （包括上交所SSE等[交易所](https://tushare.pro/document/2?doc_id=157)）
list_date | str | N | 上市交易日
opt_code | str | N | 标准合约代码，OP+期货合约TS_CODE，如棕榈油2207合约，输入OPP2207.DCE
call_put | str | N | 期权类型

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
exchange | str | Y | 交易市场
name | str | Y | 合约名称
per_unit | str | Y | 合约单位
opt_code | str | Y | 标的合约代码
opt_type | str | Y | 合约类型
call_put | str | Y | 期权类型
exercise_type | str | Y | 行权方式
exercise_price | float | Y | 行权价格
s_month | str | Y | 结算月
maturity_date | str | Y | 到期日
list_price | float | Y | 挂牌基准价
list_date | str | Y | 开始交易日期
delist_date | str | Y | 最后交易日期
last_edate | str | Y | 最后行权日期
last_ddate | str | Y | 最后交割日期
quote_unit | str | Y | 报价单位
min_price_chg | str | Y | 最小价格波幅

<br>
<br>

**接口示例**

```python

pro = ts.pro_api('your token')

df = pro.opt_basic(exchange='DCE', fields='ts_code,name,exercise_type,list_date,delist_date')

```

<br>
<br>

**数据示例**

              ts_code            name             exercise_type list_date delist_date
	0    M1707-C-2400.DCE  豆粕期权1707认购2400            美式  20170605    20170607
	1    M1707-P-2400.DCE  豆粕期权1707认沽2400            美式  20170605    20170607
	2    M1803-P-2550.DCE  豆粕期权1803认沽2550            美式  20170407    20180207
	3    M1707-C-2500.DCE  豆粕期权1707认购2500            美式  20170410    20170607
	4    M1707-P-2500.DCE  豆粕期权1707认沽2500            美式  20170410    20170607
	5    M1803-C-2550.DCE  豆粕期权1803认购2550            美式  20170407    20180207
	6    M1808-C-3550.DCE  豆粕期权1808认购3550            美式  20180409    20180706
	7    M1808-P-3550.DCE  豆粕期权1808认沽3550            美式  20180409    20180706
	8    M1809-C-3550.DCE  豆粕期权1809认购3550            美式  20180409    20180807
	9    M1809-P-3550.DCE  豆粕期权1809认沽3550            美式  20180409    20180807
	10   M1811-C-3550.DCE  豆粕期权1811认购3550            美式  20180409    20181012
	11   M1811-P-3550.DCE  豆粕期权1811认沽3550            美式  20180409    20181012
	12   M1812-C-3500.DCE  豆粕期权1812认购3500            美式  20180409    20181107
	13   M1812-C-3550.DCE  豆粕期权1812认购3550            美式  20180409    20181107
	14   M1711-P-2450.DCE  豆粕期权1711认沽2450            美式  20170601    20171013
	15   M1712-C-2450.DCE  豆粕期权1712认购2450            美式  20170601    20171107
	16   M1712-P-2450.DCE  豆粕期权1712认沽2450            美式  20170601    20171107
	17   M1801-C-2450.DCE  豆粕期权1801认购2450            美式  20170601    20171207
	18   M1801-P-2450.DCE  豆粕期权1801认沽2450            美式  20170601    20171207
	19   M1803-C-2450.DCE  豆粕期权1803认购2450            美式  20170601    20180207
	20   M1803-P-2450.DCE  豆粕期权1803认沽2450            美式  20170601    20180207