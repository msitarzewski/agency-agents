## 美股列表
----

接口：us_basic
描述：获取美股列表信息
限量：单次最大6000，可分页提取
积分：120积分可以试用，5000积分有正式权限

<br>
<br>


**输入参数**

名称 | 类型  | 必选 | 描述|示例
---- | ----- | ---- | ---- | ----
ts_code | str | N | 股票代码 | AAPL（苹果）
classify | str | N | 股票分类 | ADR/GDR/EQ
offset | str | N | 开始行数 | 1：第一行
limit | str | N | 每页最大行数 | 500：每页500行

<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 美股代码
name | str | Y | 中文名称
enname | str | N | 英文名称
classify | str | Y | 分类ADR/GDR/EQ
list_date | str | Y | 上市日期
delist_date | str | Y | 退市日期

<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取默认美国股票基础信息，单次6000行
df = pro.us_basic()


```

<br>
<br>

**数据示例**

		 ts_code  name classify list_date delist_date
	0       ONCY  None      EQT  20011005        None
	1       SCCO  None      EQT  19950124        None
	2      KAOCF  None      EQT  19740319        None
	3      BOIRF  None      EQT  19880628        None
	4      SDXOF  None      EQT  19830304        None
	...      ...   ...      ...       ...         ...
	5995   ESESQ  None      EQT  20031014        None
	5996    TRKX  None      EQT  20000718        None
	5997   ELAMF  None      EQT  19960320        None
	5998    CZNB  None      EQT  20120724        None
	5999   CRRSQ  None      EQT  20010619        None
