## 游资每日明细
----

接口：hm_detail
描述：获取每日游资交易明细，数据开始于2022年8。游资分类名录，请点击<a href="https://tushare.pro/document/2?doc_id=311">游资名录</a>
限量：单次最多提取2000条记录，可循环调取，总量不限制
积分：用户积10000积分可调取使用，积分获取办法请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 


<img src="https://tushare.pro/files/wx/yzpt.png">

注：数据为当日部分数据，此处只未作为示例效果。

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期(YYYYMMDD)
ts_code | str | N | 股票代码
hm_name | str | N | 游资名称
start_date | str | N | 开始日期(YYYYMMDD)
end_date | str | N | 结束日期(YYYYMMDD)

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | 股票代码
ts_name | str | Y | 股票名称
buy_amount | float | Y | 买入金额（元）
sell_amount | float | Y | 卖出金额（元）
net_amount | float | Y | 净买卖（元）
hm_name | str | Y | 游资名称
hm_orgs | str | Y | 关联机构（一般为营业部或机构专用）
tag | str | N | 标签

<br>
<br>

**接口示例**

```python

pro = ts.pro_api()

#获取单日全部明细
df = pro.hm_detail(trade_date='20230815')

```


<br>
<br>

