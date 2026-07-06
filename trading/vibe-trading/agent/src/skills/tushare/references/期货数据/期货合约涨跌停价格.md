## 期货合约涨跌停价格（盘前）
----

接口：ft_limit
描述：获取所有期货合约每天的涨跌停价格及最低保证金率，数据开始于2005年。
限量：单次最大获取4000行数据，可以通过日期、合约代码等参数循环获取所有历史
积分：用户积5000积分可调取，积分获取方法具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 合约代码
trade_date | str | N | 交易日期（格式：YYYYMMDD）
start_date | str | N | 开始日期
end_date | str | N | 结束日期
cont | str | N | 合约代码（例如：cont='CU')
exchange | str | N | 交易所代码 （例如：exchange='DCE')

<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | TS股票代码
name | str | Y | 合约名称
up_limit | float | Y | 涨停价
down_limit | float | Y | 跌停价
m_ratio | float | Y | 最低交易保证金率（%）
cont | str | Y | 合约代码
exchange | str | Y | 交易所代码

<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取单日全部期货合约涨跌停价格
df = pro.ft_limit(trade_date='20250213')

#获取单个品种所有合约涨跌停价格
df = pro.ft_limit(cont='CU')


```

<br>
<br>


**数据样例**

        trade_date     ts_code     name      up_limit down_limit m_ratio cont exchange
	0     20250213   A2503.DCE  连豆一2503   4229.000   3751.000   7.000    A      DCE
	1     20250213   A2505.DCE  连豆一2505   4249.000   3769.000   7.000    A      DCE
	2     20250213   A2507.DCE  连豆一2507   4258.000   3776.000   7.000    A      DCE
	3     20250213   A2509.DCE  连豆一2509   4268.000   3786.000   7.000    A      DCE
	4     20250213   A2511.DCE  连豆一2511   4234.000   3756.000   7.000    A      DCE
	..         ...         ...      ...        ...        ...     ...  ...      ...
	783   20250213  ZN2509.SHF   沪锌2509  24890.000  21635.000   9.000   ZN     SHFE
	784   20250213  ZN2510.SHF   沪锌2510  24885.000  21630.000   9.000   ZN     SHFE
	785   20250213  ZN2511.SHF   沪锌2511  24780.000  21535.000   9.000   ZN     SHFE
	786   20250213  ZN2512.SHF   沪锌2512  24700.000  21465.000   9.000   ZN     SHFE
	787   20250213  ZN2601.SHF   沪锌2601  24710.000  21475.000   9.000   ZN     SHFE