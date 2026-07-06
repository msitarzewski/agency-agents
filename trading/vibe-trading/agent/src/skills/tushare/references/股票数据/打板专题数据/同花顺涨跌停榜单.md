## 涨跌停榜单（同花顺）
----

接口：limit_list_ths
描述：获取同花顺每日涨跌停榜单数据，历史数据从20231101开始提供，增量每天16点左右更新
限量：单次最大4000条，可根据日期或股票代码循环提取
积分：8000积分以上每分钟500次，每天总量不限制，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 
<br><br>
注意：本接口只限个人学习和研究使用，如需商业用途，请自行联系同花顺解决数据采购问题。
<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期
ts_code | str | N | 股票代码
limit_type | str | N | 涨停池、连扳池、冲刺涨停、炸板池、跌停池，默认：涨停池
market | str | N | HS-沪深主板 GEM-创业板 STAR-科创板
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
ts_code | str | Y | 股票代码
name | str | Y | 股票名称
price | float | Y | 收盘价(元)
pct_chg | float | Y | 涨跌幅%
open_num | int | Y | 打开次数
lu_desc | str | Y | 涨停原因
limit_type | str | Y | 板单类别
tag | str | Y | 涨停标签
status | str | Y | 涨停状态（N连板、一字板）
first_lu_time | str | N | 首次涨停时间
last_lu_time | str | N | 最后涨停时间
first_ld_time | str | N | 首次跌停时间
last_ld_time | str | N | 最后跌停时间
limit_order | float | Y | 封单量(元|个)
limit_amount | float | Y | 封单额(元|个)
turnover_rate | float | Y | 换手率%
free_float | float | Y | 实际流通(元|个)
lu_limit_order | float | Y | 最大封单(元|个)
limit_up_suc_rate | float | Y | 近一年涨停封板率
turnover | float | Y | 成交额
rise_rate | float | N | 涨速
sum_float | float | N |  总市值（亿元）
market_type | str | Y | 股票类型：HS沪深主板、GEM创业板、STAR科创板

<br>
<br>

**接口用法**

```python

pro = ts.pro_api()

df = pro.limit_list_ths(trade_date='20241125', limit_type='涨停池', fields='ts_code,trade_date,tag,status,lu_desc')

```

**数据样例**

         trade_date   ts_code              lu_desc         tag          status
	0     20241125  603518.SH              服装家纺+电商    首板    换手板
	1     20241125  003036.SZ  高端纺织机械设备+近年来收购了2家公司  4天4板    T字板
	2     20241125  301268.SZ    精密结构件+华为+光伏+一体化压铸    首板    换手板
	3     20241125  603655.SH     橡胶+汽车零部件+间接供货特斯拉  2天2板    换手板
	4     20241125  600119.SH    上海国资+产业投资+物流+跨境电商  4天2板    换手板
	..         ...        ...                  ...   ...    ...
	149   20241125  002348.SZ        固态电池+玩具+互联网教育  4天2板    一字板
	150   20241125  002175.SZ   “东方系”+芯片+智能制造+物业管理  4天4板    一字板
	151   20241125  002155.SZ       湖南万古金矿田探矿获重大突破  3天3板    一字板
	152   20241125  002117.SZ   智能机器人+拟向子公司增资+AI应用  2天2板    一字板
	153   20241125  002103.SZ       IP产品+广告营销+跨境电商  7天5板    一字板