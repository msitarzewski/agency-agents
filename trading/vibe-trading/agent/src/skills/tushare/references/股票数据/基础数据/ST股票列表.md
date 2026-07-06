## ST股票列表
----

接口：stock_st，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取ST股票列表，可根据交易日期获取历史上每天的ST列表
权限：3000积分起
提示：每天上午9:20更新，单次请求最大返回1000行数据，可循环提取,本接口数据从20160101开始,太早历史无法补齐


<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
trade_date | str | N | 交易日期（格式：YYYYMMDD下同）
start_date | str | N | 开始时间
end_date | str | N | 结束时间

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
name | str | Y | 股票名称
trade_date | str | Y | 交易日期
type | str | Y | 类型
type_name | str | Y | 类型名称

<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

#获取20250813日所有的ST股票
df = pro.stock_st(trade_date='20250813')


```

<br>
<br>

**数据样例**

				 ts_code   name trade_date type type_name
	0    300313.SZ  *ST天山   20250813   ST     风险警示板
	1    605081.SH  *ST太和   20250813   ST     风险警示板
	2    300391.SZ  *ST长药   20250813   ST     风险警示板
	3    300343.SZ   ST联创   20250813   ST     风险警示板
	4    300044.SZ   ST赛为   20250813   ST     风险警示板
	..         ...    ...        ...  ...       ...
	170  300175.SZ   ST朗源   20250813   ST     风险警示板
	171  603721.SH  *ST天择   20250813   ST     风险警示板
	172  600289.SH   ST信通   20250813   ST     风险警示板
	173  000929.SZ  *ST兰黄   20250813   ST     风险警示板
	174  000638.SZ  *ST万方   20250813   ST     风险警示板