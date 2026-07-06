## 融资融券标的（盘前更新）
----

接口：margin_secs
描述：获取沪深京三大交易所融资融券标的（包括ETF），每天盘前更新
限量：单次最大6000行数据，可根据股票代码、交易日期、交易所代码循环提取
积分：2000积分可调取，5000积分无总量限制，积分越高权限越大，具体参考[权限说明](https://tushare.pro/document/1?doc_id=290)


<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 标的代码
trade_date | str | N | 交易日
exchange | str | N | 交易所（SSE上交所 SZSE深交所 BSE北交所）
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | 标的代码
name | str | Y | 标的名称
exchange | str | Y | 交易所


<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

#获取2024年4月17日上交所融资融券标的
df = pro.margin_secs(trade_date='20240417', exchange='SSE')

```

<br>
<br>


**数据样例**

        trade_date     ts_code      name exchange
	0      20240417  510050 .SH    50ETF       SSE
	1      20240417  510100 .SH  SZ50ETF       SSE
	2      20240417  510150 .SH    消费ETF       SSE
	3      20240417  510180 .SH   180ETF       SSE
	4      20240417  510210 .SH    综指ETF       SSE
	...         ...         ...       ...      ...
	1781   20240417  688799 .SH     华纳药厂       SSE
	1782   20240417  688800 .SH      瑞可达       SSE
	1783   20240417  688819 .SH     天能股份       SSE
	1784   20240417  688981 .SH     中芯国际       SSE
	1785   20240417  689009 .SH     九号公司       SSE
