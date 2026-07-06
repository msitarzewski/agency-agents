## 可转债发行
----

接口：cb_issue
描述：获取可转债发行数据
限量：单次最大2000，可多次提取，总量不限制
积分：用户需要至少2000积分才可以调取，5000积分以上频次相对较高，积分越多权限越大，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS代码
ann_date | str | N | 发行公告日
start_date | str | N | 公告开始日期
end_date | str | N | 公告结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 转债代码
ann_date | str | Y | 发行公告日
res_ann_date | str | Y | 发行结果公告日
plan_issue_size | float | Y | 计划发行总额（元）
issue_size | float | Y | 发行总额（元）
issue_price | float | Y | 发行价格
issue_type | str | Y | 发行方式
issue_cost | float | N | 发行费用（元）
onl_code | str | Y | 网上申购代码
onl_name | str | Y | 网上申购简称
onl_date | str | Y | 网上发行日期
onl_size | float | Y | 网上发行总额（张）
onl_pch_vol | float | Y | 网上发行有效申购数量（张）
onl_pch_num | int | Y | 网上发行有效申购户数
onl_pch_excess | float | Y | 网上发行超额认购倍数
onl_winning_rate | float | N | 网上发行中签率（%）
shd_ration_code | str | Y | 老股东配售代码
shd_ration_name | str | Y | 老股东配售简称
shd_ration_date | str | Y | 老股东配售日
shd_ration_record_date | str | Y | 老股东配售股权登记日
shd_ration_pay_date | str | Y | 老股东配售缴款日
shd_ration_price | float | Y | 老股东配售价格
shd_ration_ratio | float | Y | 老股东配售比例
shd_ration_size | float | Y | 老股东配售数量（张）
shd_ration_vol | float | N | 老股东配售有效申购数量（张）
shd_ration_num | int | N | 老股东配售有效申购户数
shd_ration_excess | float | N | 老股东配售超额认购倍数
offl_size | float | Y | 网下发行总额（张）
offl_deposit | float | N | 网下发行定金比例（%）
offl_pch_vol | float | N | 网下发行有效申购数量（张）
offl_pch_num | int | N | 网下发行有效申购户数
offl_pch_excess | float | N | 网下发行超额认购倍数
offl_winning_rate | float | N | 网下发行中签率
lead_underwriter | str | N | 主承销商
lead_underwriter_vol | float | N | 主承销商包销数量（张）


<br>
<br>

**接口示例**

```python

pro = ts.pro_api()


#获取可转债发行数据
df = pro.cb_issue(ann_date='20190612')


#获取可转债发行数据，自定义字段
df = pro.cb_issue(fields='ts_code,ann_date,issue_size')

```

<br>
<br>

**数据示例**

		ts_code  ann_date issue_size
	0    110072.SH  20200814    33.7000
	1    113600.SH  20200811     5.9500
	2    113598.SH  20200729     3.3000
	3    113038.SH  20200729    50.0000
	4    128125.SZ  20200728     4.5000
	..         ...       ...        ...
	489  100009.SH  20000223    13.5000
	490  125302.SZ  19990727    15.0000
	491  125301.SZ  19980826     2.0000
	492  100001.SH  19980730     1.5000
	493  125009.SZ      None     5.0000