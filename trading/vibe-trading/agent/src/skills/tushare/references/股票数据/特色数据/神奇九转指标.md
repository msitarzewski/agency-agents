## 神奇九转指标
----

接口：stk_nineturn（由于涉及分钟数据每天21点更新）
描述：神奇九转（又称“九转序列”）是一种基于技术分析的股票趋势反转指标，其思想来源于技术分析大师汤姆·迪马克（Tom DeMark）的TD序列。该指标的核心功能是通过识别股价在上涨或下跌过程中连续9天的特定走势，来判断股价的潜在反转点，从而帮助投资者提高抄底和逃顶的成功率，日线级别配合60min的九转效果更好，数据从20230101开始。
限量：单次提取最大返回10000行数据，可通过股票代码和日期循环获取全部数据
权限：达到6000积分可以调用

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
trade_date | str | N | 交易日期 （格式：YYYY-MM-DD HH:MM:SS)
freq | str | N | 频率(日daily)
start_date | str | N | 开始时间
end_date | str | N | 结束时间

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
trade_date | datetime | Y | 交易日期
freq | str | Y | 频率(日daily)
open | float | Y | 开盘价
high | float | Y | 最高价
low | float | Y | 最低价
close | float | Y | 收盘价
vol | float | Y | 成交量
amount | float | Y | 成交额
up_count | float | Y | 上九转计数
down_count | float | Y | 下九转计数
nine_up_turn | str | Y | 是否上九转)+9表示上九转
nine_down_turn | str | Y | 是否下九转-9表示下九转

<br>
<br>


**接口用法**

```python

pro = ts.pro_api()

df=pro.stk_nineturn(ts_code='000001.SZ',freq='daily',fields='ts_code,trade_date,freq,up_count,down_count,nine_up_turn,nine_down_turn')

```

<br>
<br>

**数据样例**

        ts_code           trade_date     freq  up_count  down_count nine_up_turn nine_down_turn
	0    000001.SZ  2025-01-17 00:00:00  daily       3.0         0.0         None           None
	1    000001.SZ  2025-01-16 00:00:00  daily       2.0         0.0         None           None
	2    000001.SZ  2025-01-15 00:00:00  daily       1.0         0.0         None           None
	3    000001.SZ  2025-01-14 00:00:00  daily       0.0         3.0         None           None
	4    000001.SZ  2025-01-13 00:00:00  daily       0.0         2.0         None           None
	..         ...                  ...    ...       ...         ...          ...            ...
	491  000001.SZ  2023-01-09 00:00:00  daily       1.0         0.0         None           None
	492  000001.SZ  2023-01-06 00:00:00  daily       0.0         0.0         None           None
	493  000001.SZ  2023-01-05 00:00:00  daily       0.0         0.0         None           None
	494  000001.SZ  2023-01-04 00:00:00  daily       0.0         0.0         None           None
	495  000001.SZ  2023-01-03 00:00:00  daily       0.0         0.0         None           None