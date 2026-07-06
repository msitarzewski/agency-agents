## 涨跌停列表（新）
----

接口：limit_list_d
描述：获取A股每日涨跌停、炸板数据情况，数据从2020年开始（不提供ST股票的统计）
限量：单次最大可以获取2500条数据，可通过日期或者股票循环提取
积分：5000积分每分钟可以请求200次每天总量1万次，8000积分以上每分钟500次每天总量不限制，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期
ts_code | str | N | 股票代码
limit_type | str | N | 涨跌停类型（U涨停D跌停Z炸板）
exchange | str | N | 交易所（SH上交所SZ深交所BJ北交所）
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | 股票代码
industry | str | Y | 所属行业
name | str | Y | 股票名称
close | float | Y | 收盘价
pct_chg | float | Y | 涨跌幅
amount | float | Y | 成交额
limit_amount | float | Y | 板上成交金额(成交价格为该股票跌停价的所有成交额的总和，涨停无此数据)
float_mv | float | Y | 流通市值
total_mv | float | Y | 总市值
turnover_ratio | float | Y | 换手率
fd_amount | float | Y | 封单金额（以涨停价买入挂单的资金总量）
first_time | str | Y | 首次封板时间（跌停无此数据）
last_time | str | Y | 最后封板时间
open_times | int | Y | 炸板次数(跌停为开板次数)
up_stat | str | Y | 涨停统计（N/T T天有N次涨停）
limit_times | int | Y | 连板数（个股连续封板数量）
limit | str | Y | D跌停U涨停Z炸板

<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

df = pro.limit_list_d(trade_date='20220615', limit_type='U', fields='ts_code,trade_date,industry,name,close,pct_chg,open_times,up_stat,limit_times')

```

**数据样例**

		 trade_date ts_code      industry   name  close pct_chg  open_times up_stat  limit_times
	0    20220615  000017.SZ     交运设备   深中华A   3.65    9.94           0     1/1            1
	1    20220615  000025.SZ     汽车服务  特  力Ａ  29.54   10.02           5   12/23            1
	2    20220615  000498.SZ     工程建设   山东路桥  10.41   10.04           3     1/1            1
	3    20220615  000502.SZ     房地产服    绿景退   0.69    9.52           2     3/3            3
	4    20220615  000532.SZ     综合行业   华金资本  12.69    9.97           0     1/1            1
	..        ...        ...      ...    ...    ...     ...         ...     ...          ...
	56   20220615  603633.SH     消费电子   徕木股份  14.58   10.04           3     2/4            1
	57   20220615  603668.SH     农牧饲渔   天马科技  18.22   10.02           0     2/2            2
	58   20220615  603918.SH     互联网服   金桥信息   9.49    9.97           6     1/1            1
	59   20220615  603963.SH       中药   大理药业  14.78    9.97           1     1/1            1
	60   20220615  605068.SH     汽车零部   明新旭腾  29.03   10.00           1     2/2            2

