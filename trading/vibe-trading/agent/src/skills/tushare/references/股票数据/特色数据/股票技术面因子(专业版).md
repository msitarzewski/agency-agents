## 股票技术面因子(专业版)
----

接口：stk_factor_pro
描述：获取股票每日技术面因子数据，用于跟踪股票当前走势情况，数据由Tushare社区自产，覆盖全历史；输出参数_bfq表示不复权，_qfq表示前复权 _hfq表示后复权，描述中说明了因子的默认传参，如需要特殊参数或者更多因子可以联系管理员评估
限量：单次调取最多返回10000条数据，可以通过日期参数循环
积分：5000积分每分钟可以请求30次，8000积分以上每分钟500次，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
trade_date | str | N | 交易日期(格式：yyyymmdd，下同)
start_date | str | N | 开始日期
end_date | str | N | 结束日期


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
trade_date | str | Y | 交易日期
open | float | Y | 开盘价
open_hfq | float | Y | 开盘价（后复权）
open_qfq | float | Y | 开盘价（前复权）
high | float | Y | 最高价
high_hfq | float | Y | 最高价（后复权）
high_qfq | float | Y | 最高价（前复权）
low | float | Y | 最低价
low_hfq | float | Y | 最低价（后复权）
low_qfq | float | Y | 最低价（前复权）
close | float | Y | 收盘价
close_hfq | float | Y | 收盘价（后复权）
close_qfq | float | Y | 收盘价（前复权）
pre_close | float | Y | 昨收价(前复权)--为daily接口的pre_close,以当时复权因子计算值跟前一日close_qfq对不上，可不用
change | float | Y | 涨跌额
pct_chg | float | Y | 涨跌幅 （除权后的涨跌幅）
vol | float | Y | 成交量 （手）
amount | float | Y | 成交额 （千元）
turnover_rate | float | Y | 换手率（%）
turnover_rate_f | float | Y | 换手率（自由流通股）
volume_ratio | float | Y | 量比
pe | float | Y | 市盈率（总市值/净利润， 亏损的PE为空）
pe_ttm | float | Y | 市盈率（TTM，亏损的PE为空）
pb | float | Y | 市净率（总市值/净资产）
ps | float | Y | 市销率
ps_ttm | float | Y | 市销率（TTM）
dv_ratio | float | Y | 股息率 （%）
dv_ttm | float | Y | 股息率（TTM）（%）
total_share | float | Y | 总股本 （万股）
float_share | float | Y | 流通股本 （万股）
free_share | float | Y | 自由流通股本 （万）
total_mv | float | Y | 总市值 （万元）
circ_mv | float | Y | 流通市值（万元）
adj_factor | float | Y | 复权因子
asi_bfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
asi_hfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
asi_qfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
asit_bfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
asit_hfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
asit_qfq | float | Y | 振动升降指标-OPEN, CLOSE, HIGH, LOW, M1=26, M2=10
atr_bfq | float | Y | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20
atr_hfq | float | Y | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20
atr_qfq | float | Y | 真实波动N日平均值-CLOSE, HIGH, LOW, N=20
bbi_bfq | float | Y | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=20
bbi_hfq | float | Y | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=21
bbi_qfq | float | Y | BBI多空指标-CLOSE, M1=3, M2=6, M3=12, M4=22
bias1_bfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias1_hfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias1_qfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias2_bfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias2_hfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias2_qfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias3_bfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias3_hfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
bias3_qfq | float | Y | BIAS乖离率-CLOSE, L1=6, L2=12, L3=24
boll_lower_bfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_lower_hfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_lower_qfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_mid_bfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_mid_hfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_mid_qfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_upper_bfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_upper_hfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
boll_upper_qfq | float | Y | BOLL指标，布林带-CLOSE, N=20, P=2
brar_ar_bfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
brar_ar_hfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
brar_ar_qfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
brar_br_bfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
brar_br_hfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
brar_br_qfq | float | Y |  BRAR情绪指标-OPEN, CLOSE, HIGH, LOW, M1=26
cci_bfq | float | Y | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14
cci_hfq | float | Y | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14
cci_qfq | float | Y | 顺势指标又叫CCI指标-CLOSE, HIGH, LOW, N=14
cr_bfq | float | Y | CR价格动量指标-CLOSE, HIGH, LOW, N=20
cr_hfq | float | Y | CR价格动量指标-CLOSE, HIGH, LOW, N=20
cr_qfq | float | Y | CR价格动量指标-CLOSE, HIGH, LOW, N=20
dfma_dif_bfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dfma_dif_hfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dfma_dif_qfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dfma_difma_bfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dfma_difma_hfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dfma_difma_qfq | float | Y | 平行线差指标-CLOSE, N1=10, N2=50, M=10
dmi_adx_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_adx_hfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_adx_qfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_adxr_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_adxr_hfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_adxr_qfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_mdi_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_mdi_hfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_mdi_qfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_pdi_bfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_pdi_hfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
dmi_pdi_qfq | float | Y |  动向指标-CLOSE, HIGH, LOW, M1=14, M2=6
downdays | float | Y | 连跌天数
updays | float | Y | 连涨天数
dpo_bfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
dpo_hfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
dpo_qfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
madpo_bfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
madpo_hfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
madpo_qfq | float | Y | 区间震荡线-CLOSE, M1=20, M2=10, M3=6
ema_bfq_10 | float | Y | 指数移动平均-N=10
ema_bfq_20 | float | Y | 指数移动平均-N=20
ema_bfq_250 | float | Y | 指数移动平均-N=250
ema_bfq_30 | float | Y | 指数移动平均-N=30
ema_bfq_5 | float | Y | 指数移动平均-N=5
ema_bfq_60 | float | Y | 指数移动平均-N=60
ema_bfq_90 | float | Y | 指数移动平均-N=90
ema_hfq_10 | float | Y | 指数移动平均-N=10
ema_hfq_20 | float | Y | 指数移动平均-N=20
ema_hfq_250 | float | Y | 指数移动平均-N=250
ema_hfq_30 | float | Y | 指数移动平均-N=30
ema_hfq_5 | float | Y | 指数移动平均-N=5
ema_hfq_60 | float | Y | 指数移动平均-N=60
ema_hfq_90 | float | Y | 指数移动平均-N=90
ema_qfq_10 | float | Y | 指数移动平均-N=10
ema_qfq_20 | float | Y | 指数移动平均-N=20
ema_qfq_250 | float | Y | 指数移动平均-N=250
ema_qfq_30 | float | Y | 指数移动平均-N=30
ema_qfq_5 | float | Y | 指数移动平均-N=5
ema_qfq_60 | float | Y | 指数移动平均-N=60
ema_qfq_90 | float | Y | 指数移动平均-N=90
emv_bfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
emv_hfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
emv_qfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
maemv_bfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
maemv_hfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
maemv_qfq | float | Y | 简易波动指标-HIGH, LOW, VOL, N=14, M=9
expma_12_bfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
expma_12_hfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
expma_12_qfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
expma_50_bfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
expma_50_hfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
expma_50_qfq | float | Y | EMA指数平均数指标-CLOSE, N1=12, N2=50
kdj_bfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_hfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_qfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_d_bfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_d_hfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_d_qfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_k_bfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_k_hfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
kdj_k_qfq | float | Y | KDJ指标-CLOSE, HIGH, LOW, N=9, M1=3, M2=3
ktn_down_bfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_down_hfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_down_qfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_mid_bfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_mid_hfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_mid_qfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_upper_bfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_upper_hfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
ktn_upper_qfq | float | Y | 肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10
lowdays | float | Y | LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值
topdays | float | Y | TOPRANGE(HIGH)表示当前最高价是近多少周期内最高价的最大值
ma_bfq_10 | float | Y | 简单移动平均-N=10
ma_bfq_20 | float | Y | 简单移动平均-N=20
ma_bfq_250 | float | Y | 简单移动平均-N=250
ma_bfq_30 | float | Y | 简单移动平均-N=30
ma_bfq_5 | float | Y | 简单移动平均-N=5
ma_bfq_60 | float | Y | 简单移动平均-N=60
ma_bfq_90 | float | Y | 简单移动平均-N=90
ma_hfq_10 | float | Y | 简单移动平均-N=10
ma_hfq_20 | float | Y | 简单移动平均-N=20
ma_hfq_250 | float | Y | 简单移动平均-N=250
ma_hfq_30 | float | Y | 简单移动平均-N=30
ma_hfq_5 | float | Y | 简单移动平均-N=5
ma_hfq_60 | float | Y | 简单移动平均-N=60
ma_hfq_90 | float | Y | 简单移动平均-N=90
ma_qfq_10 | float | Y | 简单移动平均-N=10
ma_qfq_20 | float | Y | 简单移动平均-N=20
ma_qfq_250 | float | Y | 简单移动平均-N=250
ma_qfq_30 | float | Y | 简单移动平均-N=30
ma_qfq_5 | float | Y | 简单移动平均-N=5
ma_qfq_60 | float | Y | 简单移动平均-N=60
ma_qfq_90 | float | Y | 简单移动平均-N=90
macd_bfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_hfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_qfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dea_bfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dea_hfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dea_qfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dif_bfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dif_hfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
macd_dif_qfq | float | Y | MACD指标-CLOSE, SHORT=12, LONG=26, M=9
mass_bfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
mass_hfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
mass_qfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
ma_mass_bfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
ma_mass_hfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
ma_mass_qfq | float | Y | 梅斯线-HIGH, LOW, N1=9, N2=25, M=6
mfi_bfq | float | Y | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14
mfi_hfq | float | Y | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14
mfi_qfq | float | Y | MFI指标是成交量的RSI指标-CLOSE, HIGH, LOW, VOL, N=14
mtm_bfq | float | Y | 动量指标-CLOSE, N=12, M=6
mtm_hfq | float | Y | 动量指标-CLOSE, N=12, M=6
mtm_qfq | float | Y | 动量指标-CLOSE, N=12, M=6
mtmma_bfq | float | Y | 动量指标-CLOSE, N=12, M=6
mtmma_hfq | float | Y | 动量指标-CLOSE, N=12, M=6
mtmma_qfq | float | Y | 动量指标-CLOSE, N=12, M=6
obv_bfq | float | Y | 能量潮指标-CLOSE, VOL
obv_hfq | float | Y | 能量潮指标-CLOSE, VOL
obv_qfq | float | Y | 能量潮指标-CLOSE, VOL
psy_bfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
psy_hfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
psy_qfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
psyma_bfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
psyma_hfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
psyma_qfq | float | Y | 投资者对股市涨跌产生心理波动的情绪指标-CLOSE, N=12, M=6
roc_bfq | float | Y | 变动率指标-CLOSE, N=12, M=6
roc_hfq | float | Y | 变动率指标-CLOSE, N=12, M=6
roc_qfq | float | Y | 变动率指标-CLOSE, N=12, M=6
maroc_bfq | float | Y | 变动率指标-CLOSE, N=12, M=6
maroc_hfq | float | Y | 变动率指标-CLOSE, N=12, M=6
maroc_qfq | float | Y | 变动率指标-CLOSE, N=12, M=6
rsi_bfq_12 | float | Y | RSI指标-CLOSE, N=12
rsi_bfq_24 | float | Y | RSI指标-CLOSE, N=24
rsi_bfq_6 | float | Y | RSI指标-CLOSE, N=6
rsi_hfq_12 | float | Y | RSI指标-CLOSE, N=12
rsi_hfq_24 | float | Y | RSI指标-CLOSE, N=24
rsi_hfq_6 | float | Y | RSI指标-CLOSE, N=6
rsi_qfq_12 | float | Y | RSI指标-CLOSE, N=12
rsi_qfq_24 | float | Y | RSI指标-CLOSE, N=24
rsi_qfq_6 | float | Y | RSI指标-CLOSE, N=6
taq_down_bfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_down_hfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_down_qfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_mid_bfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_mid_hfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_mid_qfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_up_bfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_up_hfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
taq_up_qfq | float | Y | 唐安奇通道(海龟)交易指标-HIGH, LOW, 20
trix_bfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
trix_hfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
trix_qfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
trma_bfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
trma_hfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
trma_qfq | float | Y | 三重指数平滑平均线-CLOSE, M1=12, M2=20
vr_bfq | float | Y | VR容量比率-CLOSE, VOL, M1=26
vr_hfq | float | Y | VR容量比率-CLOSE, VOL, M1=26
vr_qfq | float | Y | VR容量比率-CLOSE, VOL, M1=26
wr_bfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
wr_hfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
wr_qfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
wr1_bfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
wr1_hfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
wr1_qfq | float | Y | W&R 威廉指标-CLOSE, HIGH, LOW, N=10, N1=6
xsii_td1_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td1_hfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td1_qfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td2_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td2_hfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td2_qfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td3_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td3_hfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td3_qfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td4_bfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td4_hfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7
xsii_td4_qfq | float | Y | 薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7

