## 备用行情
----

接口：bak_daily
描述：获取备用行情，包括特定的行情指标(数据从2017年中左右开始，早期有几天数据缺失，近期正常)
限量：单次最大7000行数据，可以根据日期参数循环获取，正式权限需要5000积分。

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
trade_date | str | N | 交易日期
start_date | str | N | 开始日期
end_date | str | N | 结束日期
offset | str | N | 开始行数
limit | str | N | 最大行数


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
trade_date | str | Y | 交易日期
name | str | Y | 股票名称
pct_change | float | Y | 涨跌幅
close | float | Y | 收盘价
change | float | Y | 涨跌额
open | float | Y | 开盘价
high | float | Y | 最高价
low | float | Y | 最低价
pre_close | float | Y | 昨收价
vol_ratio | float | Y | 量比
turn_over | float | Y | 换手率
swing | float | Y | 振幅
vol | float | Y | 成交量
amount | float | Y | 成交额
selling | float | Y | 内盘（主动卖，手）
buying | float | Y | 外盘（主动买， 手）
total_share | float | Y | 总股本(亿)
float_share | float | Y | 流通股本(亿)
pe | float | Y | 市盈(动)
industry | str | Y | 所属行业
area | str | Y | 所属地域
float_mv | float | Y | 流通市值
total_mv | float | Y | 总市值
avg_price | float | Y | 平均价
strength | float | Y | 强弱度(%)
activity | float | Y | 活跃度(%)
avg_turnover | float | Y | 笔换手
attack | float | Y | 攻击波(%)
interval_3 | float | Y | 近3月涨幅
interval_6 | float | Y | 近6月涨幅


**接口示例**

```python

pro = ts.pro_api()

df = pro.bak_daily(trade_date='20211012', fields='trade_date,ts_code,name,close,open')

```

**数据样例**

        ts_code     trade_date      name  close   open
	0     300605.SZ   20211012  恒锋信息  14.86  12.65
	1     301017.SZ   20211012  漱玉平民  25.21  20.82
	2     300755.SZ   20211012  华致酒行  40.45  37.01
	3     300255.SZ   20211012  常山药业   8.39   7.26
	4     688378.SH   20211012   奥来德  68.62  67.00
	...         ...        ...   ...    ...    ...
	4529  688257.SH   20211012  新锐股份   0.00   0.00
	4530  688255.SH   20211012   凯尔达   0.00   0.00
	4531  688211.SH   20211012  中科微至   0.00   0.00
	4532  605567.SH   20211012  春雪食品   0.00   0.00
	4533  605566.SH   20211012  福莱蒽特   0.00   0.00