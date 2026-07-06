## 卖方盈利预测数据
----

接口：report_rc
描述：获取券商（卖方）每天研报的盈利预测数据，数据从2010年开始，每晚19~22点更新当日数据
限量：单次最大3000条，可分页和循环提取所有数据
权限：本接口120积分可以试用，每天10次请求，正式权限需8000积分，每天可请求100000次，10000积分以上无总量限制。

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
report_date | str | N | 报告日期
start_date | str | N | 报告开始日期
end_date | str | N | 报告结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
name | str | Y | 股票名称
report_date | str | Y | 研报日期
report_title | str | Y | 报告标题
report_type | str | Y | 报告类型
classify | str | Y | 报告分类
org_name | str | Y | 机构名称
author_name | str | Y | 作者
quarter | str | Y | 预测报告期
op_rt | float | Y | 预测营业收入（万元）
op_pr | float | Y | 预测营业利润（万元）
tp | float | Y | 预测利润总额（万元）
np | float | Y | 预测净利润（万元）
eps | float | Y | 预测每股收益（元）
pe | float | Y | 预测市盈率
rd | float | Y | 预测股息率
roe | float | Y | 预测净资产收益率
ev_ebitda | float | Y | 预测EV/EBITDA
rating | str | Y | 卖方评级
max_price | float | Y | 预测最高目标价
min_price | float | Y | 预测最低目标价
imp_dg | str | N | 机构关注度
create_time | datetime | N | TS数据更新时间

<br>
<br>

**接口用法**
```python

pro = ts.pro_api()

df = pro.report_rc(ts_code='', report_date='20220429')

```

<br>
<br>

**数据样例**

        ts_code        name      report_date   classify   org_name quarter     eps       pe
	0     000733.SZ  振华科技    20220429     一般报告     安信证券  2024Q4  6.7800  14.2000
	1     000858.SZ   五粮液    20220429     一般报告     华西证券  2022Q4  6.9800  23.7700
	2     000858.SZ   五粮液    20220429     一般报告     华西证券  2023Q4  8.2200  20.1800
	3     000858.SZ   五粮液    20220429     一般报告     华西证券  2024Q4  9.5800  17.3100
	4     000858.SZ   五粮液    20220429     一般报告     信达证券  2022Q4  7.1100  23.3100
	...         ...   ...         ...      ...      ...     ...     ...      ...
	2552  688385.SH  复旦微电    20220429     一般报告     方正证券  2022Q4  0.9100  62.7000
	2553  688385.SH  复旦微电    20220429     一般报告     方正证券  2023Q4  1.1600  49.1900
	2554  688385.SH  复旦微电    20220429     一般报告     方正证券  2024Q4  1.5800  36.3200
	2555  000733.SZ  振华科技    20220429     一般报告     安信证券  2022Q4  4.3000  22.4000
	2556  000733.SZ  振华科技    20220429     一般报告     安信证券  2023Q4  5.4100  17.8000
