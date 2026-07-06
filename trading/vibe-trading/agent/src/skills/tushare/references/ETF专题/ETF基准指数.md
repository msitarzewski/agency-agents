## ETF基准指数列表
----

接口：etf_index
描述：获取ETF基准指数列表信息
限量：单次请求最大返回5000行数据（当前未超过2000个）
权限：用户积累8000积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 指数代码
pub_date | str | N | 发布日期（格式：YYYYMMDD）
base_date | str | N | 指数基期（格式：YYYYMMDD）

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 指数代码
indx_name | str | Y | 指数全称
indx_csname | str | Y | 指数简称
pub_party_name | str | Y | 指数发布机构
pub_date | str | Y | 指数发布日期 
base_date | str | Y | 指数基日
bp | float | Y | 指数基点(点)
adj_circle | str | Y | 指数成份证券调整周期

<br>
<br>

**接口示例**

```python

#获取当前ETF跟踪的基准指数列表
df = pro.etf_index(fields='ts_code,indx_name,pub_date,bp')


```
<br>
<br>


**数据示例**

              ts_code        indx_name         pub_date           bp
	0        000068.SH         上证自然资源指数  20100528  1000.000000
	1        000001.SH           上证综合指数  19910715   100.000000
	2        000989.SH       中证全指可选消费指数  20110802  1000.000000
	3       000990.CSI       中证全指主要消费指数  20110802  1000.000000
	4        000043.SH         上证超级大盘指数  20090423  1000.000000
	...            ...              ...       ...          ...
	1458    932368.CSI     中证800自由现金流指数  20241211  1000.000000
	1460     000680.SH        上证科创板综合指数  20250120  1000.000000
	1461     000681.SH      上证科创板综合价格指数  20250120  1000.000000
