## 柜台流通式债券报价
----

接口：bc_otcqt
描述：柜台流通式债券报价
限量：单次最大2000条，可多次提取，总量不限制
积分：用户需要至少500积分可以试用调取，2000积分以上频次相对较高，积分越多权限越大，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期(YYYYMMDD格式，下同)
start_date | str | N | 开始日期
end_date | str | N | 结束日期
ts_code | str | N | TS代码
bank | str | N | 报价机构


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | N | 报价日期
qt_time | str | N | 报价时间
bank | str | N | 报价机构
ts_code | str | N | 债券编码
name | str | N | 债券简称
maturity | str | N | 期限
remain_maturity | str | N | 剩余期限
bond_type | str | N | 债券类型
coupon_rate | float | N | 票面利率（%）
buy_price | float | N | 投资者买入全价
sell_price | float | N | 投资者卖出全价
buy_yield | float | N | 投资者买入到期收益率（%）
sell_yield | float | N | 投资者卖出到期收益率（%）

<br>
<br>

**接口示例**

```python
pro = ts.pro_api(your token)
#柜台流通式债券报价
df = pro.bc_otcqt(start_date='20240325',end_date='20240329',ts_code='200013.BC',fields='trade_date,qt_time,bank,ts_code,name,remain_maturity,buy_yield,sell_yield')

```

<br>
<br>

**数据示例**

			trade_date   qt_time  bank    ts_code      name remain_maturity buy_yield sell_yield
	0   20240329  08:11:02  浦发银行  200013.BC  20附息国债13          1年207天    1.9263     1.7977
	1   20240329  09:05:28  招商银行  200013.BC  20附息国债13          1年207天    1.8950     1.8350
	2   20240329  09:10:24  工商银行  200013.BC  20附息国债13          1年207天    1.8850     1.8528
	3   20240329  09:14:48  建设银行  200013.BC  20附息国债13          1年207天    1.8837     1.8451
	4   20240329  09:18:18  中国银行  200013.BC  20附息国债13          1年207天    1.9040     1.8200
	5   20240329  10:40:09  北京银行  200013.BC  20附息国债13          1年207天    1.9043     1.8271
	6   20240329  15:46:38  农业银行  200013.BC  20附息国债13          1年207天    1.8697     1.8054
	7   20240329  18:36:29  交通银行  200013.BC  20附息国债13          1年207天    1.8464     1.8142