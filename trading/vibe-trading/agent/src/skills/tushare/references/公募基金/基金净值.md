## 公募基金净值
----

接口：fund_nav，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取公募基金净值数据
积分：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS基金代码 （二选一）
nav_date | str | N | 净值日期 （二选一）
market | str | N | E场内 O场外
start_date | str | N | 净值开始日期 
end_date | str | N | 净值结束日期 


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
ann_date | str | Y | 公告日期
nav_date | str | Y | 净值日期
unit_nav | float | Y | 单位净值
accum_nav | float | Y | 累计净值
accum_div | float | Y | 累计分红
net_asset | float | Y | 资产净值
total_netasset | float | Y | 合计资产净值
adj_nav | float | Y | 复权单位净值


**代码示例**

```python

pro = ts.pro_api()

df = pro.fund_nav(ts_code='165509.SZ')

```

**数据示例**

            ts_code  ann_date  nav_date  unit_nav  accum_nav accum_div  \
	0     165509.SZ  20181019  20181018     1.104      1.587      None   
	1     165509.SZ  20181018  20181017     1.110      1.587      None   
	2     165509.SZ  20181017  20181016     1.110      1.587      None   
	3     165509.SZ  20181016  20181015     1.110      1.587      None   
	4     165509.SZ  20181013  20181012     1.110      1.587      None   
	5     165509.SZ  20181012  20181011     1.110      1.587      None   
	6     165509.SZ  20181011  20181010     1.110      1.587      None   
	7     165509.SZ  20181010  20181009     1.110      1.587      None   
	8     165509.SZ  20181009  20181008     1.109      1.586      None   
	9     165509.SZ  20180929  20180928     1.109      1.586      None   
	10    165509.SZ  20180928  20180927     1.109      1.586      None  

