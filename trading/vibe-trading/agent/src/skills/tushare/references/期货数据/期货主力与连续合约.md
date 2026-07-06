## 期货主力与连续合约
----

接口：fut_mapping
描述：获取期货主力（或连续）合约与月合约映射数据
限量：单次最大2000条，总量不限制
积分：用户需要至少2000积分才可以调取，未来可能调整积分，请尽可能多积累积分。具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 合约代码
trade_date | str | N | 交易日期(YYYYMMDD格式，下同)
start_date | str | N | 开始日期
end_date | str | N | 结束日期


<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 连续合约代码
trade_date | str | Y | 起始日期
mapping_ts_code | str | Y | 期货合约代码

<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取主力合约TF.CFX每日对应的月合约
df = pro.fut_mapping(ts_code='TF.CFX')

```


<br>
<br>

**数据示例**

		 ts_code trade_date mapping_ts_code
	0     TF.CFX   20190823      TF1912.CFX
	1     TF.CFX   20190822      TF1912.CFX
	2     TF.CFX   20190821      TF1912.CFX
	3     TF.CFX   20190820      TF1912.CFX
	4     TF.CFX   20190819      TF1912.CFX
	5     TF.CFX   20190816      TF1912.CFX
	6     TF.CFX   20190815      TF1912.CFX
	7     TF.CFX   20190814      TF1912.CFX
	8     TF.CFX   20190813      TF1912.CFX
	9     TF.CFX   20190812      TF1909.CFX
	10    TF.CFX   20190809      TF1909.CFX
	11    TF.CFX   20190808      TF1909.CFX
	12    TF.CFX   20190807      TF1909.CFX
	13    TF.CFX   20190806      TF1909.CFX
	14    TF.CFX   20190805      TF1909.CFX
	15    TF.CFX   20190802      TF1909.CFX
	16    TF.CFX   20190801      TF1909.CFX
	17    TF.CFX   20190731      TF1909.CFX
	18    TF.CFX   20190730      TF1909.CFX
	19    TF.CFX   20190729      TF1909.CFX
	20    TF.CFX   20190726      TF1909.CFX
