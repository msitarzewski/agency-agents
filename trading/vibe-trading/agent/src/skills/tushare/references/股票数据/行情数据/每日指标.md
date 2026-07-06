## 每日指标
----

接口：daily_basic，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
更新时间：交易日每日15点～17点之间
描述：获取全部股票每日重要的基本面指标，可用于选股分析、报表展示等。单次请求最大返回6000条数据，可按日线循环提取全部历史。
积分：至少2000积分才可以调取，5000积分无总量限制，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码（二选一）
trade_date | str | N | 交易日期 （二选一）
start_date | str | N | 开始日期(YYYYMMDD)
end_date | str | N | 结束日期(YYYYMMDD)

**注：日期都填YYYYMMDD格式，比如20181010**

**输出参数**

名称 | 类型 | 描述
--- | ---- | ----
ts_code | str | TS股票代码
trade_date | str | 交易日期
close | float | 当日收盘价
turnover_rate | float | 换手率（%）
turnover_rate_f | float | 换手率（自由流通股）
volume_ratio | float | 量比
pe | float | 市盈率（总市值/净利润， 亏损的PE为空）
pe_ttm | float | 市盈率（TTM，亏损的PE为空）
pb | float | 市净率（总市值/净资产）
ps | float | 市销率
ps_ttm | float | 市销率（TTM）
dv_ratio | float | 股息率 （%）
dv_ttm | float | 股息率（TTM）（%）
total_share | float | 总股本 （万股）
float_share | float | 流通股本 （万股）
free_share | float | 自由流通股本 （万）
total_mv | float | 总市值 （万元）
circ_mv | float | 流通市值（万元）


**接口用法**
```python

pro = ts.pro_api()

df = pro.daily_basic(ts_code='', trade_date='20180726', fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')

```

或者

```python

df = pro.query('daily_basic', ts_code='', trade_date='20180726',fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')

```

**数据样例**

		ts_code     trade_date  turnover_rate  volume_ratio        pe       pb
	0     600230.SH   20180726         2.4584          0.72    8.6928   3.7203
	1     600237.SH   20180726         1.4737          0.88  166.4001   1.8868
	2     002465.SZ   20180726         0.7489          0.72   71.8943   2.6391
	3     300732.SZ   20180726         6.7083          0.77   21.8101   3.2513
	4     600007.SH   20180726         0.0381          0.61   23.7696   2.3774
	5     300068.SZ   20180726         1.4583          0.52   27.8166   1.7549
	6     300552.SZ   20180726         2.0728          0.95   56.8004   2.9279
	7     601369.SH   20180726         0.2088          0.95   44.1163   1.8001
	8     002518.SZ   20180726         0.5814          0.76   15.1004   2.5626
	9     002913.SZ   20180726        12.1096          1.03   33.1279   2.9217
	10    601818.SH   20180726         0.1893          0.86    6.3064   0.7209
	11    600926.SH   20180726         0.6065          0.46    9.1772   0.9808
	12    002166.SZ   20180726         0.7582          0.82   16.9868   3.3452
	13    600841.SH   20180726         0.3754          1.02   66.2647   2.2302
	14    300634.SZ   20180726        23.1127          1.26  120.3053  14.3168
	15    300126.SZ   20180726         1.2304          1.11  348.4306   1.5171
	16    300718.SZ   20180726        17.6612          0.92   32.0239   3.8661
	17    000708.SZ   20180726         0.5575          0.70   10.3674   1.0276
	18    002626.SZ   20180726         0.6187          0.83   22.7580   4.2446
	19    600816.SH   20180726         0.6745          0.65   11.0778   3.2214