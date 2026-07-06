## 期货周/月线行情(每日更新)
----

接口：fut_weekly_monthly
描述：期货周/月线行情(每日更新)
限量：单次最大6000

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS代码
trade_date | str | N | 交易日期
start_date | str | N | 开始交易日期
end_date | str | N | 结束交易日期
freq | str | Y | 频率week周，month月
exchange | str | N | 交易所


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 期货代码
trade_date | str | Y | 交易日期（每周五或者月末日期）
end_date | str | Y | 计算截至日期
freq | str | Y | 频率(周week,月month)
open | float | Y | (周/月)开盘价
high | float | Y | (周/月)最高价
low | float | Y | (周/月)最低价
close | float | Y | (周/月)收盘价
pre_close | float | Y | 前一(周/月)收盘价
settle | float | Y | (周/月)结算价
pre_settle | float | Y | 前一(周/月)结算价
vol | float | Y | (周/月)成交量(手)
amount | float | Y | (周/月)成交金额(万元)
oi | float | Y | (周/月)持仓量(手)
oi_chg | float | Y | (周/月)持仓量变化
exchange | str | Y | 交易所
change1 | float | Y | (周/月)涨跌1 收盘价-昨结算价
change2 | float | Y | (周/月)涨跌2 结算价-昨结算价

