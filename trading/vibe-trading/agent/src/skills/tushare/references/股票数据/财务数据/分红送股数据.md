## 分红送股
----

接口：dividend
描述：分红送股数据
权限：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS代码
ann_date | str | N | 公告日
record_date | str | N | 股权登记日期 
ex_date | str | N | 除权除息日 
imp_ann_date  | str | N | 实施公告日 

<br>

以上参数至少有一个不能为空

<br>
<br>


**输出参数**


名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
end_date | str | Y | 分红年度
ann_date | str | Y | 预案公告日
div_proc | str | Y | 实施进度
stk_div | float | Y | 每股送转
stk_bo_rate | float | Y | 每股送股比例
stk_co_rate | float | Y | 每股转增比例
cash_div | float | Y | 每股分红（税后）
cash_div_tax | float | Y | 每股分红（税前）
record_date | str | Y | 股权登记日
ex_date | str | Y | 除权除息日
pay_date | str | Y | 派息日
div_listdate | str | Y | 红股上市日
imp_ann_date | str | Y | 实施公告日
base_date | str | N | 基准日
base_share | float | N | 基准股本（万）


**接口示例**

```python

pro = ts.pro_api()

df = pro.dividend(ts_code='600848.SH', fields='ts_code,div_proc,stk_div,record_date,ex_date')

```

**数据样例**

```python

			 ts_code div_proc  stk_div record_date   ex_date
	0  600848.SH       实施     0.10    19950606  19950607
	1  600848.SH       实施     0.10    19970707  19970708
	2  600848.SH       实施     0.15    19960701  19960702
	3  600848.SH       实施     0.10    19980706  19980707
	4  600848.SH       预案     0.00        None      None
	5  600848.SH       实施     0.00    20180522  20180523
	
```