## 大盘指数每日指标
----

接口：index_dailybasic，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：目前只提供上证综指，深证成指，上证50，中证500，中小板指，创业板指的每日指标数据
数据来源：Tushare社区统计计算
数据历史：从2004年1月开始提供
数据权限：用户需要至少400积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期 （格式：YYYYMMDD，比如20181018，下同）
ts_code | str | N | TS代码
start_date | str | N | 开始日期
end_date | str | N | 结束日期

注：trade_date，ts_code 至少要输入一个参数，单次限量3000条（即，单一指数单次可提取超过12年历史），总量不限制。



**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
trade_date | str | Y | 交易日期
total_mv | float | Y | 当日总市值（元）
float_mv | float | Y | 当日流通市值（元）
total_share | float | Y | 当日总股本（股）
float_share | float | Y | 当日流通股本（股）
free_share | float | Y | 当日自由流通股本（股）
turnover_rate | float | Y | 换手率
turnover_rate_f | float | Y | 换手率(基于自由流通股本)
pe | float | Y | 市盈率
pe_ttm | float | Y | 市盈率TTM
pb | float | Y | 市净率


**接口示例**

```python

pro = ts.pro_api()

df = pro.index_dailybasic(trade_date='20181018', fields='ts_code,trade_date,turnover_rate,pe')

```

**数据示例**


		ts_code  trade_date  turnover_rate     pe
	0  000001.SH   20181018           0.38  11.92
	1  000300.SH   20181018           0.27  11.17
	2  000905.SH   20181018           0.82  18.03
	3  399001.SZ   20181018           0.88  17.48
	4  399005.SZ   20181018           0.85  21.43
	5  399006.SZ   20181018           1.50  29.56
	6  399016.SZ   20181018           1.06  18.86
	7  399300.SZ   20181018           0.27  11.17