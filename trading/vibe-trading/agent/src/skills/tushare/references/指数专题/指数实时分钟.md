## A股实时分钟
----

接口：rt_idx_min
描述：获取交易所指数实时分钟数据，包括1~60min
限量：单次最大1000行数据，可以通过股票代码提取数据，支持逗号分隔的多个代码同时提取
权限：正式权限请参阅 <u>[权限说明](https://tushare.pro/document/1?doc_id=290) </u>

注：支持股票当日开盘以来的所有历史分钟数据提取，接口名：rt_idx_min_daily（仅支持一个个指数提取，不同同时提取多个），可以[在线开通](https://tushare.pro/weborder/#/permission)权限。

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
freq | str | Y | 1MIN,5MIN,15MIN,30MIN,60MIN （大写）
ts_code | str | Y | 支持单个和多个：000001.SH 或者 000001.SH,399300.SZ


<br>
<br>

**freq参数说明**

freq | 说明 
--- | ---- 
1MIN | 1分钟
5MIN | 5分钟
15MIN | 15分钟
30MIN | 30分钟
60MIN | 60分钟

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
time | None | Y | 交易时间
open | float | Y | 开盘价
close | float | Y | 收盘价
high | float | Y | 最高价
low | float | Y | 最低价
vol | float | Y | 成交量(股）
amount | float | Y | 成交额（元）



**接口用法**

```python

pro = ts.pro_api()

#获取上证综指000001.SH的实时分钟数据
df = pro.rt_idx_min(ts_code='000001.SH', freq='1MIN')

```

<br>
<br>