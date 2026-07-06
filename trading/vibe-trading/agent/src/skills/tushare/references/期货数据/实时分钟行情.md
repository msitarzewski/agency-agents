## 期货实时分钟行情
----

接口：rt_fut_min
描述：获取全市场期货合约实时分钟数据，支持1min/5min/15min/30min/60min行情，提供Python SDK、 http Restful API和websocket三种方式，如果需要主力合约分钟，请先通过主力[mapping](https://tushare.pro/document/2?doc_id=189)接口获取对应的合约代码后提取分钟。
限量：每分钟可以请求500次，支持多个合约同时提取
权限：需单独开权限，正式权限请参阅 <u>[权限说明](https://tushare.pro/document/1?doc_id=290) </u> 。

<br>
<br>

**rt_fut_min输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码，e.g.CU2310.SHF，支持多个合约（逗号分隔）
freq | str | Y | 分钟频度（1MIN/5MIN/15MIN/30MIN/60MIN）

<br>
<br>

<font color="red">同时提供当日开市以来所有历史分钟（即：分钟快照回放），接口名：rt_fut_min_daily，只支持一个个合约提取。</font>

**rt_fut_min_daily输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码，e.g.CU2310.SHF，仅支持一次一个合约的回放
freq | str | Y | 分钟频度（1MIN/5MIN/15MIN/30MIN/60MIN）
date_str | str | N | 回放日期（格式：YYYY-MM-DD，默认为交易当日，支持回溯一天）

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
code | str | Y | 股票代码
freq | str | Y | 频度
time | str | Y |  交易时间
open | float | Y |  开盘价
close | float | Y |  收盘价
high | float | Y |  最高价
low | float | Y |  最低价
vol | int | Y |  成交量
amount | float | Y |  成交金额
oi | float | Y | 持仓量

<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

#单个合约
df = pro.df = pro.rt_fut_min(ts_code='CU2501.SHF', freq='1MIN')

#多个合约
df = pro.df = pro.rt_fut_min(ts_code='CU2501.SHF,CU2502.SHF', freq='1MIN')

```

<br>


