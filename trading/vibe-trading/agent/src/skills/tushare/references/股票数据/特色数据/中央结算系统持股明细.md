## 中央结算系统持股明细
----

接口：ccass_hold_detail
描述：获取中央结算系统机构席位持股明细，数据覆盖**全历史**，根据交易所披露时间，当日数据在下一交易日早上9点前完成
限量：单次最大返回6000条数据，可以循环或分页提取
积分：用户积8000积分可调取，每分钟可以请求300次

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码 (e.g. 605009.SH)
hk_code | str | N | 港交所代码 （e.g. 95009）
trade_date | str | N | 交易日期(YYYYMMDD格式，下同)
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | 股票代号
name | str | Y | 股票名称
col_participant_id | str | Y | 参与者编号
col_participant_name | str | Y | 机构名称
col_shareholding | str | Y | 持股量(股)
col_shareholding_percent | str | Y | 占已发行股份/权证/单位百分比(%)

<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

df = pro.ccass_hold_detail(ts_code='00960.HK', trade_date='20211101', fields='trade_date,ts_code,col_participant_id,col_participant_name,col_shareholding')

```

**数据样例**

        trade_date   ts_code col_participant_id       col_participant_name         col_shareholding
	0     20211101  00960.HK             B01777         大和资本市场香港有限公司             3000
	1     20211101  00960.HK             B01977             中财证券有限公司             3000
	2     20211101  00960.HK             B02068             勤丰证券有限公司             3000
	3     20211101  00960.HK             B01413       京华山一国际(香港)有限公司             2500
	4     20211101  00960.HK             B02120           利弗莫尔证券有限公司             2500
	..         ...       ...                ...                  ...              ...
	164   20211101  00960.HK             B01459         奕丰证券(香港)有限公司             3000
	165   20211101  00960.HK             B01508       西证(香港)证券经纪有限公司             3000
	166   20211101  00960.HK             B01511             达利证券有限公司             3000
	167   20211101  00960.HK             B01657         日盛嘉富证券国际有限公司             3000
	168   20211101  00960.HK             B01712             华生证券有限公司             3000