## 港股列表
----

接口：hk_basic
描述：获取港股列表信息
数量：单次可提取全部在交易的港股列表数据
积分：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS代码
list_status | str | N | 上市状态 L上市 D退市 P暂停上市 ，默认L

<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 
name | str | Y | 股票简称
fullname | str | Y | 公司全称
enname | str | Y | 英文名称
cn_spell | str | Y | 拼音
market | str | Y | 市场类别
list_status | str | Y | 上市状态
list_date | str | Y | 上市日期
delist_date | str | Y | 退市日期
trade_unit | float | Y | 交易单位
isin | str | Y | ISIN代码
curr_type | str | Y | 货币代码


<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取全部可交易股票基础信息
df = pro.hk_basic()

#获取全部退市股票基础信息
df = pro.hk_basic(list_status='D')

```

<br>
<br>

**数据示例**

           ts_code             name  ...          isin curr_type
	0     00001.HK               长和  ...  KYG217651051       HKD
	1     00002.HK             中电控股  ...  HK0002007356       HKD
	2     00003.HK           香港中华煤气  ...  HK0003000038       HKD
	3     00004.HK            九龙仓集团  ...  HK0004000045       HKD
	4     00005.HK             汇丰控股  ...  GB0005405286       HKD
	5     00006.HK             电能实业  ...  HK0006000050       HKD
	6     00007.HK           香港金融集团  ...  BMG4613K1099       HKD
	7     00008.HK             电讯盈科  ...  HK0008011667       HKD
	8     00009.HK             九号运通  ...  BMG6547Y1057       HKD
	9     00010.HK             恒隆集团  ...  HK0010000088       HKD
	10    00011.HK             恒生银行  ...  HK0011000095       HKD
	11    00012.HK             恒基地产  ...  HK0012000102       HKD
	12    00014.HK             希慎兴业  ...  HK0014000126       HKD
	13    00015.HK             盈信控股  ...  BMG932121434       HKD
	14    00016.HK            新鸿基地产  ...  HK0016000132       HKD
	15    00017.HK            新世界发展  ...  HK0017000149       HKD
	16    00018.HK           东方报业集团  ...  HK0018000155       HKD
	17    00019.HK          太古股份公司A  ...  HK0019000162       HKD
	18    00020.HK              会德丰  ...  HK0020000177       HKD
	19    00021.HK          大中华地产控股  ...  HK0000132420       HKD
	20    00022.HK             茂盛控股  ...  BMG6051D1175       HKD