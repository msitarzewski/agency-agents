## 外汇基础信息（海外）
----

接口：fx_obasic
描述：获取海外外汇基础信息，目前只有FXCM交易商的数据
数量：单次可提取全部数据
积分：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
exchange | str | N | 交易商
classify | str | N | 分类
ts_code | str | N | TS代码

<br>
<br>

classify分类说明

序号|分类代码|分类名称|样例
---- | ----- | ---- | ----
1 | FX | 外汇货币对 | USDCNH（美元人民币对）
2 | INDEX | 指数 | US30（美国道琼斯工业平均指数）
3 | COMMODITY | 大宗商品 | SOYF（大豆）
4 | METAL | 金属 | XAUUSD （黄金）
5 | BUND | 国库债券 | Bund（长期欧元债券）
6 | CRYPTO | 加密数字货币 | BTCUSD (比特币)
7 | FX_BASKET | 外汇篮子 | USDOLLAR （美元指数）


<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 外汇代码
name | str | Y | 名称
classify | str | Y | 分类
exchange | str | Y | 交易商
min_unit | float | Y | 最小交易单位
max_unit | float | Y | 最大交易单位
pip | float | Y | 点
pip_cost | float | Y | 点值
traget_spread | float | Y | 目标差价
min_stop_distance | float | Y | 最小止损距离（点子）
trading_hours | str | Y | 交易时间
break_time | str | Y | 休市时间


**接口示例**

```python

pro = ts.pro_api()

#获取差价合约(CFD)中指数产的基础信息
df = pro.fx_obasic(exchange='FXCM', classify='INDEX', fields='ts_code,name,min_unit,max_unit,pip,pip_cost')

```

<br>
<br>

**数据示例**

			ts_code                  name     min_unit  max_unit  pip  pip_cost
	0    AUS200.FXCM  澳大利亚标准普尔200指数       1.0    2000.0  1.0       0.1
	1     CHN50.FXCM      富时中国A50指数       1.0     100.0  1.0       0.1
	2     ESP35.FXCM    西班牙IBEX35指数       1.0    5000.0  1.0       0.1
	3   EUSTX50.FXCM      欧洲斯托克50指数       1.0    5000.0  1.0       0.1
	4     FRA40.FXCM      法国CAC40指数       1.0    5000.0  1.0       0.1
	5     GER30.FXCM        德国DAX指数       1.0    1000.0  1.0       0.1
	6     HKG33.FXCM         香港恒生指数       1.0     300.0  1.0       1.0
	7    JPN225.FXCM        日经225指数      10.0    1000.0  1.0      10.0
	8    NAS100.FXCM    美国纳斯达克100指数       1.0    5000.0  1.0       0.1
	9    SPX500.FXCM      美国标普500指数       1.0    5000.0  0.1       0.1
	10    UK100.FXCM      英国富时100指数       1.0    4000.0  1.0       0.1
	11     US30.FXCM      道琼斯工业平均指数       1.0    4000.0  1.0       0.1
	12   US2000.FXCM     美国罗素2000指数       1.0    5000.0  0.1       0.1