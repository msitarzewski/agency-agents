## 美股复权因子
----

接口：us_adjfactor
描述：获取美股每日复权因子数据，在每天美股收盘后滚动刷新
限量：单次最大15000行数据，可以根据日期循环
权限：本接口是在开通美股日线权限后自动获取权限，权限请参考[权限说明文档](https://tushare.pro/document/1?doc_id=290)

<br>
<br>


**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
trade_date | str | N | 交易日期（格式：YYYYMMDD，下同）
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
trade_date | str | Y | 交易日期
exchange | str | Y | 交易所
cum_adjfactor | float | Y | 累计复权因子
close_price | float | Y | 收盘价

<br>
<br>


**接口示例**

```python

pro = ts.pro_api()

#获取美股单一股票复权因子
df = pro.us_adjfactor(ts_code='AAPL', start_date='20240101', end_date='20251022')

#获取美股某一日全部股票的复权因子
df = pro.us_adjfactor(trade_date='20251031')

```

<br>
<br>

**数据示例**

          ts_code trade_date exchange cum_adjfactor close_price
	0       TAGOF   20251031      OTC      1.000000        None
	1        BABA   20251031      NYS      1.000000  170.430000
	2         CZR   20251031      NAS      1.000000   20.100000
	3        DEEP   20251031      ARC      1.000000   35.025100
	4        AVAL   20251031      NYS      1.000000    4.220000
	...       ...        ...      ...           ...         ...
	14995   MRETF   20251031      OTC      1.000000    7.150000
	14996     CHI   20251031      NAS      1.000000   11.390000
	14997    TBHC   20251031      NAS      1.000000    1.510000
	14998   MQMIF   20251031      OTC      1.000000    0.127600
	14999     TAC   20251031      NYS      1.000000   17.670000