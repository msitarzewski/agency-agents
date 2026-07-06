## 个股资金流向（DC）
----

接口：moneyflow_dc
描述：获取东方财富个股资金流向数据，每日盘后更新，数据开始于20230911
限量：单次最大获取6000条数据，可根据日期或股票代码循环提取数据
积分：用户需要至少5000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
trade_date | str | N | 交易日期（YYYYMMDD格式，下同）
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | 股票代码
name | str | Y | 股票名称
pct_change | float | Y | 涨跌幅
close | float | Y | 最新价
net_amount | float | Y | 今日主力净流入额（万元）
net_amount_rate | float | Y | 今日主力净流入净占比（%）
buy_elg_amount | float | Y | 今日超大单净流入额（万元）
buy_elg_amount_rate | float | Y | 今日超大单净流入占比（%）
buy_lg_amount | float | Y | 今日大单净流入额（万元）
buy_lg_amount_rate | float | Y | 今日大单净流入占比（%）
buy_md_amount | float | Y | 今日中单净流入额（万元）
buy_md_amount_rate | float | Y | 今日中单净流入占比（%）
buy_sm_amount | float | Y | 今日小单净流入额（万元）
buy_sm_amount_rate | float | Y | 今日小单净流入占比（%）

<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取单日全部股票数据
df = pro.moneyflow_dc(trade_date='20241011')

#获取单个股票数据
df = pro.moneyflow_dc(ts_code='002149.SZ', start_date='20240901', end_date='20240913')


```

<br>
<br>

		trade_date ts_code  name  pct_change  ...  buy_md_amount  buy_md_amount_rate  buy_sm_amount  buy_sm_amount_rate
	0   20240913  002149.SZ  西部材料       -1.34  ...         -12.65               -0.35         -62.43               -1.72
	1   20240912  002149.SZ  西部材料        1.43  ...          13.71                0.33        -388.43               -9.25
	2   20240911  002149.SZ  西部材料       -0.79  ...         -26.10               -1.68          95.69                6.15
	3   20240910  002149.SZ  西部材料       -0.08  ...        -199.50               -7.26         -69.29               -2.52
	4   20240909  002149.SZ  西部材料        1.12  ...          66.76                2.48        -198.12               -7.37
	5   20240906  002149.SZ  西部材料       -2.49  ...        -104.57               -2.74         769.65               20.19
	6   20240905  002149.SZ  西部材料       -0.70  ...        -307.62               -8.11         346.51                9.14
	7   20240904  002149.SZ  西部材料       -0.92  ...         370.98                9.56         -23.25               -0.60
	8   20240903  002149.SZ  西部材料        0.93  ...        -195.45               -3.87         643.41               12.75
	9   20240902  002149.SZ  西部材料       -3.44  ...         195.50                2.32         988.69               11.71


