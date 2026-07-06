## 期货合约信息表
----

接口：fut_basic
描述：获取期货合约列表数据
限量：单次最大10000
积分：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
exchange | str | Y | 交易所代码 CFFEX-中金所 DCE-大商所 CZCE-郑商所 SHFE-上期所 INE-上海国际能源交易中心 GFEX-广州期货交易所
fut_type | str | N | 合约类型 (1 普通合约 2主力与连续合约 默认取全部)
fut_code | str | N | 标准合约代码，如白银AG、AP鲜苹果等
list_date | str | N | 上市开始日期(格式YYYYMMDD，从某日开始以来所有合约）



**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 合约代码
symbol | str | Y | 交易标识
exchange | str | Y | 交易市场
name | str | Y | 中文简称
fut_code | str | Y | 合约产品代码
multiplier | float | Y | 合约乘数(只适用于国债期货、指数期货)
trade_unit | str | Y | 交易计量单位
per_unit | float | Y | 交易单位(每手)
quote_unit | str | Y | 报价单位
quote_unit_desc | str | Y | 最小报价单位说明
d_mode_desc | str | Y | 交割方式说明
list_date | str | Y | 上市日期
delist_date | str | Y | 最后交易日期
d_month | str | Y | 交割月份
last_ddate | str | Y | 最后交割日
trade_time_desc | str | N | 交易时间说明


**接口示例**

```python

pro = ts.pro_api('your token')

df = pro.fut_basic(exchange='DCE', fut_type='1', fields='ts_code,symbol,name,list_date,delist_date')

```

**数据示例**

			ts_code  symbol      name   list_date    delist_date
	0      P0805.DCE   P0805   棕榈油0805  20071029    20080516
	1      P0806.DCE   P0806   棕榈油0806  20071029    20080616
	2      P0807.DCE   P0807   棕榈油0807  20071029    20080714
	3      P0808.DCE   P0808   棕榈油0808  20071029    20080814
	4      P0811.DCE   P0811   棕榈油0811  20071115    20081114
	5      P0812.DCE   P0812   棕榈油0812  20071217    20081212
	6      P0901.DCE   P0901   棕榈油0901  20080116    20090116
	7      P0903.DCE   P0903   棕榈油0903  20080317    20090313
	8      P0906.DCE   P0906   棕榈油0906  20080617    20090612
	9      P0908.DCE   P0908   棕榈油0908  20080815    20090814
	10     P0911.DCE   P0911   棕榈油0911  20081117    20091113
	11     P1001.DCE   P1001   棕榈油1001  20090119    20100115
	12     P1002.DCE   P1002   棕榈油1002  20090216    20100212
	13     P1003.DCE   P1003   棕榈油1003  20090316    20100312
	14     P1004.DCE   P1004   棕榈油1004  20090416    20100415
	15     Y0607.DCE   Y0607    豆油0607  20060109    20060714
	16     Y0611.DCE   Y0611    豆油0611  20060118    20061114
	17     Y0612.DCE   Y0612    豆油0612  20060315    20061214
	18     Y0701.DCE   Y0701    豆油0701  20060315    20070117
	19     Y0708.DCE   Y0708    豆油0708  20060815    20070814
	20     Y0709.DCE   Y0709    豆油0709  20060915    20070914



