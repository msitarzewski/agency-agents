## 国债实际长期利率平均值
----

接口：us_trltr
描述：国债实际长期利率平均值
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
ltr_avg | float | Y | 实际平均利率LT Real Average (10&gt; Yrs)

<br>
<br>

**接口调用**

```python

pro = ts.pro_api()

df = pro.us_trltr(start_date='20180101', end_date='20200327')


#获取指定字段
df = pro.us_trltr(start_date='20180101', end_date='20200327', fields='ltr_avg')

```

<br>

**数据样例**

          date ltr_avg
	0     20200327   -0.02
	1     20200326   -0.05
	2     20200325    0.01
	3     20200324   -0.04
	4     20200323    0.04
	...        ...     ...
	1995  20120404    0.57
	1996  20120403    0.58
	1997  20120402    0.53
	1998  20120330    0.57
	1999  20120329    0.51

