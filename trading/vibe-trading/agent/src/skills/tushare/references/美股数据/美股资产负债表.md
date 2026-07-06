## 美股资产负债表
----

接口：us_balancesheet，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取美股上市公司资产负债表（目前只覆盖主要美股和中概股）
权限：需单独开权限或有15000积分，具体权限信息请参考[权限列表](https://tushare.pro/document/1?doc_id=290)
提示：当前接口按单只股票获取其历史数据，单次请求最大返回10000行数据，可循环提取

<br>
<br>


**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码
period | str | N | 报告期（格式：YYYYMMDD，每个季度最后一天的日期，如20241231)
ind_name | str | N | 指标名(如：新增借款）
report_type | str | N | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)
start_date | str | N | 报告期开始时间（格式：YYYYMMDD）
end_date | str | N | 报告结束始时间（格式：YYYYMMDD）

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
end_date | str | Y | 报告期
ind_type | str | Y | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)
name | str | Y | 股票名称
ind_name | str | Y | 财务科目名称
ind_value | float | Y | 财务科目值
report_type | str | Y | 报告类型

<br>
<br>


**接口用法**

```python

pro = ts.pro_api()

#获取美股英伟达NVDA股票Q4的资产负债表数据
df = pro.us_balancesheet(ts_code='NVDA', report_type='Q4')

#获取美股英伟达NVDA股票历年应收帐款指标数据
df = pro.us_balancesheet(ts_code='NVDA', ind_name='应收帐款')

```

<br>
<br>


**数据样例**

			 ts_code  end_date ind_type name     ind_name     ind_value report_type
	0       NVDA  20250427       Q1  英伟达    负债及股东权益合计  1.252540e+11         一季报
	1       NVDA  20250427       Q1  英伟达       股东权益合计  8.384300e+10         一季报
	2       NVDA  20250427       Q1  英伟达   归属于母公司股东权益  8.384300e+10         一季报
	3       NVDA  20250427       Q1  英伟达       其他综合收益  1.860000e+08         一季报
	4       NVDA  20250427       Q1  英伟达         股本溢价  1.147500e+10         一季报
	...      ...       ...      ...  ...          ...           ...         ...
	2459    NVDA  20060129       Q4  英伟达     预付款项(流动)  2.438700e+07          年报
	2460    NVDA  20060129       Q4  英伟达  递延所得税资产(流动)  2.682000e+06          年报
	2461    NVDA  20060129       Q4  英伟达           存货  2.548700e+08          年报
	2462    NVDA  20060129       Q4  英伟达         应收账款  3.181860e+08          年报
	2463    NVDA  20060129       Q4  英伟达     现金及现金等价物  5.517560e+08          年报
