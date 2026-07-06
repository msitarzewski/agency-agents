## 公募基金分红
----

接口：fund_div
描述：获取公募基金分红数据
积分：用户需要至少400积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ann_date | str | N | 公告日（以下参数四选一）
ex_date | str | N | 除息日
pay_date | str | N | 派息日
ts_code | str | N | 基金代码


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
ann_date | str | Y | 公告日期
imp_anndate | str | Y | 分红实施公告日
base_date | str | Y | 分配收益基准日
div_proc | str | Y | 方案进度
record_date | str | Y | 权益登记日
ex_date | str | Y | 除息日
pay_date | str | Y | 派息日
earpay_date | str | Y | 收益支付日
net_ex_date | str | Y | 净值除权日
div_cash | float | Y | 每股派息(元)
base_unit | float | Y | 基准基金份额(万份)
ear_distr | float | Y | 可分配收益(元)
ear_amount | float | Y | 收益分配金额(元)
account_date | str | Y | 红利再投资到账日
base_year | str | Y | 份额基准年度


**接口示例**

```python

pro = ts.pro_api()

df = pro.fund_div(ann_date='20181018')

```

**数据示例**

		ts_code  ann_date imp_anndate base_date div_proc record_date   ex_date  \
	0  161618.OF  20181018    20181018  20180928       实施    20181022  20181022   
	1  161619.OF  20181018    20181018  20180928       实施    20181022  20181022   
	2  005485.OF  20181018    20181018  20181015       实施    20181022  20181022   
	3  519330.OF  20181018    20181018  20181012       实施    20181022  20181022   
	4  519331.OF  20181018    20181018  20181012       实施    20181022  20181022   
	5  164702.SZ  20181018    20181018  20180930       实施    20181022  20181023   
	6  005068.OF  20181018    20181018  20181016       实施    20181022  20181022   
	7  519953.OF  20181018    20181018  20181016       实施    20181022  20181022   
	
	   pay_date earpay_date net_ex_date  div_cash    base_unit    ear_distr  \
	0  20181024        None        None    0.0170   14982.2740   5018943.83   
	1  20181024        None        None    0.0150    2894.7015    823800.02   
	2  20181024        None        None    0.0180  101004.4450  18689411.19   
	3  20181024        None        None    0.0060  219742.3332  65922699.95   
	4  20181024        None        None    0.0050       4.8656      1216.42   
	5  20181024        None        None    0.0150   41287.3653   8058271.35   
	6  20181024        None        None    0.0237    4953.9392   1174773.90   
	7  20181024        None        None    0.0191   23038.2415   4408682.75