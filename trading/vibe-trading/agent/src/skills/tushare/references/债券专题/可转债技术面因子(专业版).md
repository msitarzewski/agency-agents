## 可转债技术因子(专业版)
----

接口：cb_factor_pro
描述：获取可转债每日技术面因子数据，用于跟踪可转债当前走势情况，数据由Tushare社区自产，覆盖全历史；输出参数_bfq表示不复权，_qfq表示前复权 _hfq表示后复权，描述中说明了因子的默认传参，如需要特殊参数或者更多因子可以联系管理员评估
限量：单次调取最多返回10000条数据，可以通过日期参数循环
积分：5000积分每分钟可以请求30次，8000积分以上每分钟500次，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 可转债代码
start_date | str | N | 开始日期
end_date | str | N | 结束日期
trade_date | str | N | 交易日期


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 转债代码
trade_date | str | Y | 交易日期
open | float | Y | 开盘价
high | float | Y | 最高价
low | float | Y | 最低价
close | float | Y | 收盘价
pre_close | float | Y | 昨收价
change | float | Y | 涨跌额
pct_change | float | Y | 涨跌幅 （未复权，如果是复权请用 通用行情接口 ）
vol | float | Y | 成交量 （手）
amount | float | Y | 成交金额(万元)
asi_bfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
asit_bfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
atr_bfq | float | Y | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20
bbi_bfq | float | Y | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=20
bias1_bfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias2_bfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias3_bfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
boll_lower_bfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_mid_bfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_upper_bfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
brar_ar_bfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
brar_br_bfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
cci_bfq | float | Y | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14
cr_bfq | float | Y | CR价格动量指标-CLOSE, HIGH, LOW, N=20
dfma_dif_bfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dfma_difma_bfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dmi_adx_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_adxr_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_mdi_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_pdi_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
downdays | float | Y | 连跌天数
updays | float | Y | 连涨天数
dpo_bfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
madpo_bfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
ema_bfq_10 | float | Y | 指数移动平均-N=10
ema_bfq_20 | float | Y | 指数移动平均-N=20
ema_bfq_250 | float | Y | 指数移动平均-N=250
ema_bfq_30 | float | Y | 指数移动平均-N=30
ema_bfq_5 | float | Y | 指数移动平均-N=5
ema_bfq_60 | float | Y | 指数移动平均-N=60
ema_bfq_90 | float | Y | 指数移动平均-N=90
emv_bfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
maemv_bfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
expma_12_bfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
expma_50_bfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
kdj_bfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_d_bfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_k_bfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
ktn_down_bfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_mid_bfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_upper_bfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
lowdays | float | Y | LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值
topdays | float | Y | TOPRANGE(HIGH)表示当前最高价是近多少周期内最高价的最大值
ma_bfq_10 | float | Y | 简单移动平均-N=10
ma_bfq_20 | float | Y | 简单移动平均-N=20
ma_bfq_250 | float | Y | 简单移动平均-N=250
ma_bfq_30 | float | Y | 简单移动平均-N=30
ma_bfq_5 | float | Y | 简单移动平均-N=5
ma_bfq_60 | float | Y | 简单移动平均-N=60
ma_bfq_90 | float | Y | 简单移动平均-N=90
macd_bfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dea_bfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dif_bfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
mass_bfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
ma_mass_bfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
mfi_bfq | float | Y | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14
mtm_bfq | float | Y | 动量指标-CLOSE, N=12, M=6
mtmma_bfq | float | Y | 动量指标-CLOSE, N=12, M=6
obv_bfq | float | Y | 能量潮指标-CLOSE, VOL
psy_bfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
psyma_bfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
roc_bfq | float | Y | 变动率指标-CLOSE, N=12, M=6
maroc_bfq | float | Y | 变动率指标-CLOSE, N=12, M=6
rsi_bfq_12 | float | Y | RSI指标-CLOSE, N=12
rsi_bfq_24 | float | Y | RSI指标-CLOSE, N=24
rsi_bfq_6 | float | Y | RSI指标-CLOSE, N=6
taq_down_bfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_mid_bfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_up_bfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
trix_bfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
trma_bfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
vr_bfq | float | Y | VR容量比率-CLOSE, VOL, M1=26
wr_bfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
wr1_bfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
xsii_td1_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td2_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td3_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td4_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7

**接口用法**

```python

pro = ts.pro_api()

#获取鹤21转债113632.SH所以有历史因子数据
df = pro.cb_factor_pro(ts_code=113632.SH')

#获取交易日期为20250724当天所有可转债的因子数据
df = pro.hk_income(trade_date='20250724')

```

<br>
<br>

**数据样例**

				 ts_code trade_date     open  ...  xsii_td2_bfq  xsii_td3_bfq  xsii_td4_bfq
	0    113632.SH   20250724  129.050  ...     125.93711     133.15621     115.73390
	1    113632.SH   20250723  129.323  ...     125.15884     132.97290     115.57458
	2    113632.SH   20250722  128.783  ...     124.46147     132.83027     115.45061
	3    113632.SH   20250721  126.404  ...     123.75651     132.68214     115.32186
	4    113632.SH   20250718  126.229  ...     123.16743     132.56631     115.22119
	..         ...        ...      ...  ...           ...           ...           ...
	873  113632.SH   20211215  130.950  ...     128.94497     139.66710     121.39290
	874  113632.SH   20211214  131.010  ...           NaN     140.18070     121.83930
	875  113632.SH   20211213  133.890  ...           NaN     141.11160     122.64840
	876  113632.SH   20211210  129.990  ...           NaN     143.65820     124.86180
	877  113632.SH   20211209  127.000  ...           NaN     140.12720     121.79280