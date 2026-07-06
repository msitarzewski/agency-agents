## 通达信板块信息
----

接口：tdx_index
描述：获取通达信板块基础信息，包括概念板块、行业、风格、地域等
限量：单次最大1000条数据，可根据日期参数循环提取
权限：用户积累6000积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 


<br>
<br>


**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 板块代码：xxxxxx.TDX
trade_date | str | N | 交易日期(格式：YYYYMMDD）
idx_type | str | N | 板块类型：概念板块、行业板块、风格板块、地区板块

<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 板块代码
trade_date | str | Y | 交易日期
name | str | Y | 板块名称
idx_type | str | Y | 板块类型
idx_count | int | Y | 成分个数
total_share | float | Y | 总股本(亿)
float_share | float | Y | 流通股(亿)
total_mv | float | Y | 总市值(亿)
float_mv | float | Y | 流通市值(亿)

<br>
<br>

**接口示例**

```python

#获取通达信2025年5月13日的概念板块列表
df = pro.tdx_index(trade_date='20250513', fields='ts_code,name,idx_type,idx_count')


```


<br>
<br>

**数据示例**

        ts_code           name     idx_type  idx_count
	0    880559.TDX   要约收购     风格板块          6
	1    880728.TDX   航运概念     概念板块         64
	2    880355.TDX   日用化工     行业板块         20
	3    880423.TDX   酒店餐饮     行业板块          9
	4    880875.TDX   中小银行     风格板块         28
	..          ...    ...      ...        ...
	477  880528.TDX  军工信息化     概念板块         99
	478  880868.TDX   高贝塔值     风格板块        100
	479  880430.TDX     航空     行业板块         52
	480  880431.TDX     船舶     行业板块         12
	481  880914.TDX   军贸概念     概念板块         25