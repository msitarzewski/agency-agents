## 国债长期利率
----

接口：us_tltr
描述：国债长期利率
限量：单次最大可获取2000行数据，可循环获取
权限：用户积累120积分可以使用，积分越高频次越高。具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
date | str | N | 日期
start_date | str | N | 开始日期
end_date | str | N | 结束日期
fields | str | N | 指定字段

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
date | str | Y | 日期
ltc | float | Y | 收益率 LT COMPOSITE (&gt;10 Yrs)
cmt | float | Y | 20年期CMT利率(TREASURY 20-Yr CMT)
e_factor | float | Y | 外推因子EXTRAPOLATION FACTOR

<br>
<br>

**接口调用**

```python

pro = ts.pro_api()

df = pro.us_tltr(start_date='20180101', end_date='20200327')


#获取5年期和20年期数据
df = pro.us_tltr(start_date='20180101', end_date='20200327', fields='ltc,cmt')

```

<br>

**数据样例**

              date   ltc   cmt e_factor
	0     20200327  1.19  1.09     None
	1     20200326  1.32  1.20     None
	2     20200325  1.35  1.23     None
	3     20200324  1.30  1.19     None
	4     20200323  1.25  1.12     None
	...        ...   ...   ...      ...
	1995  20120404  2.98  3.02     None
	1996  20120403  3.02  3.07     None
	1997  20120402  2.96  3.00     None
	1998  20120330  2.96  3.00     None
	1999  20120329  2.89  2.93     None
