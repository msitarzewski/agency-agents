## 股权质押明细
----

接口：pledge_detail
描述：获取股票质押明细数据
限量：单次最大1000
积分：用户需要至少500积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS股票代码
ann_date | str | Y | 公告日期
holder_name | str | Y | 股东名称
pledge_amount | float | Y | 质押数量（万股）
start_date | str | Y | 质押开始日期
end_date | str | Y | 质押结束日期
is_release | str | Y | 是否已解押
release_date | str | Y | 解押日期
pledgor | str | Y | 质押方
holding_amount | float | Y | 持股总数（万股）
pledged_amount | float | Y | 质押总数（万股）
p_total_ratio | float | Y | 本次质押占总股本比例
h_total_ratio | float | Y | 持股总数占总股本比例
is_buyback | str | Y | 是否回购（0否 1是）


**接口使用**
```pyhton
pro = ts.pro_api()
#或者
#pro = ts.pro_api('your token')


df = pro.pledge_detail(ts_code='000014.SZ')

```

或者

```python

df = pro.query('pledge_detail', ts_code='000014.SZ')

```

**数据示例**

				 ts_code  ann_date         holder_name          pledge_amount start_date  \
	0  000014.SZ  20180106  中科汇通(深圳)股权投资基金有限公司       500.0000   20171114   
	1  000014.SZ  20180106  中科汇通(深圳)股权投资基金有限公司       922.0055   20171114   
	2  000014.SZ  20171221  中科汇通(深圳)股权投资基金有限公司       600.0000   20171114   
	3  000014.SZ  20171216  中科汇通(深圳)股权投资基金有限公司       300.0000   20171114   
	4  000014.SZ  20171111  中科汇通(深圳)股权投资基金有限公司       2321.9955   20151127   
	5  000014.SZ  20170616  中科汇通(深圳)股权投资基金有限公司       0.0100   20151127   
	6  000014.SZ  20060927  深圳市沙河实业(集团)有限公司             1936.3698   20050119  