## 中央结算系统持股汇总
----

接口：ccass_hold
描述：获取中央结算系统持股汇总数据，覆盖全部历史数据，根据交易所披露时间，当日数据在下一交易日早上9点前完成入库
限量：单次最大5000条数据，可循环或分页提供全部
积分：用户120积分可以试用看数据，5000积分每分钟可以请求300次，8000积分以上可以请求500次每分钟，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

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
shareholding | str | Y | 于中央结算系统的持股量(股)<br>Shareholding in CCASS
hold_nums | str | Y | 参与者数目（个）
hold_ratio | str | Y | 占于上交所上市及交易的A股总数的百分比（%）<br>% of the total number of A shares listed and traded on the SSE

Note:
1.	The total number of A shares listed and traded on the SSE of the relevant SSE-listed company used for calculating the percentage of shareholding may not have taken into account any change in connection with or as a result of any corporate actions of the relevant company and hence, may not be up-to-date. The percentage of shareholding is for reference only.
2.	The total number of A shares listed and traded on the SSE of the relevant SSE-listed company used for calculating the percentage of shareholding may not be equal to the actual total number of issued shares of that company.

<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

df = pro.ccass_hold(ts_code='00960.HK')

```

**数据样例**

        trade_date   ts_code  name       shareholding hold_nums hold_ratio
	0     20220519  00960.HK  龍湖集團   4576163843       182      75.30
	1     20220518  00960.HK  龍湖集團   4576043843       182      75.30
	2     20220517  00960.HK  龍湖集團   4575955343       180      75.30
	3     20220516  00960.HK  龍湖集團   4575905343       179      75.30
	4     20220513  00960.HK  龍湖集團   4575905343       181      75.30