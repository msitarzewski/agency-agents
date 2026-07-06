## 每日停复牌信息
----

接口：suspend_d
更新时间：不定期
描述：按日期方式获取股票每日停复牌信息

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码(可输入多值)
trade_date| str | N | 交易日日期
start_date | str | N | 停复牌查询开始日期
end_date | str | N | 停复牌查询结束日期
suspend_type | str | N | 停复牌类型：S-停牌,R-复牌


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
trade_date | str | Y | 停复牌日期
suspend_timing | str | Y | 日内停牌时间段
suspend_type | str | Y | 停复牌类型：S-停牌，R-复牌



**接口用法**

```python

pro = ts.pro_api()

#提取2020-03-12的停牌股票
df = pro.suspend_d(suspend_type='S', trade_date='20200312')

```

**数据样例**

			ts_code suspend_type trade_date suspend_timing
	0   000029.SZ            S     20200312           None
	1   000502.SZ            S     20200312           None
	2   000939.SZ            S     20200312           None
	3   000977.SZ            S     20200312           None
	4   000995.SZ            S     20200312           None
	5   002260.SZ            S     20200312           None
	6   002450.SZ            S     20200312           None
	7   002604.SZ            S     20200312           None
	8   300028.SZ            S     20200312           None
	9   300104.SZ            S     20200312           None
	10  300216.SZ            S     20200312           None
	11  300592.SZ            S     20200312           None
	12  300819.SZ            S     20200312    09:30-10:00
	13  300821.SZ            S     20200312    09:30-10:00
	14  600074.SH            S     20200312           None
	15  600145.SH            S     20200312           None
	16  600228.SH            S     20200312           None
	17  600310.SH            S     20200312           None
	18  600610.SH            S     20200312           None
	19  600745.SH            S     20200312           None
	20  600766.SH            S     20200312           None
	21  600891.SH            S     20200312           None
	22  601127.SH            S     20200312           None
	23  601162.SH            S     20200312           None
	24  603002.SH            S     20200312           None
	25  603399.SH            S     20200312           None
	
