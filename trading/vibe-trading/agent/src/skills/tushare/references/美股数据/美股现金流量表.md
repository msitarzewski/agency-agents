## 美股现金流量表
----


接口：us_cashflow，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取美股上市公司现金流量表数据（目前只覆盖主要美股和中概股）
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


#获取美股英伟达NVDA股票的2024年度现金流量表数据
df = pro.us_cashflow(ts_code='NVDA', period='20241231')

#获取美股英伟达NVDA股票现金流量表历年新增借款数据
df = pro.us_cashflow(ts_code='NVDA', ind_name='新增借款')

```

<br>
<br>


**数据样例**

			 ts_code  end_date ind_type name         ind_name     ind_value report_type
	0       NVDA  20250427       Q1  英伟达     现金及现金等价物期末余额  1.523400e+10         单季报
	1       NVDA  20250427       Q1  英伟达     现金及现金等价物期初余额  8.589000e+09         单季报
	2       NVDA  20250427       Q1  英伟达  现金及现金等价物增加(减少)额  6.645000e+09         单季报
	3       NVDA  20250427       Q1  英伟达    筹资活动产生的现金流量净额 -1.555300e+10         单季报
	4       NVDA  20250427       Q1  英伟达         筹资业务其他项目 -1.584000e+09         单季报
	...      ...       ...      ...  ...              ...           ...         ...
	2001    NVDA  20050501       Q1  英伟达       经营业务调整其他项目  0.000000e+00         单季报
	2002    NVDA  20050501       Q1  英伟达            减值及拨备 -3.410000e+05         单季报
	2003    NVDA  20050501       Q1  英伟达         基于股票的补偿费  2.850000e+05         单季报
	2004    NVDA  20050501       Q1  英伟达            折旧及摊销  2.489700e+07         单季报
	2005    NVDA  20050501       Q1  英伟达              净利润  6.444400e+07         单季报

