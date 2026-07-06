## 业绩快报
----

接口：express
描述：获取上市公司业绩快报
权限：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  
<font color="red">
提示：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用express_vip接口（参数一致），需积攒5000积分。
</font>


**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码 
ann_date | str | N | 公告日期 
start_date | str | N | 公告开始日期
end_date | str | N | 公告结束日期
period | str | N | 报告期(每个季度最后一天的日期,比如20171231表示年报，20170630半年报，20170930三季报)


**输出参数**

名称 | 类型 | 描述
--- | ---- | ----
ts_code | str | TS股票代码
ann_date | str | 公告日期
end_date | str | 报告期
revenue | float | 营业收入(元)
operate_profit | float | 营业利润(元)
total_profit | float | 利润总额(元)
n_income | float | 净利润(元)
total_assets | float | 总资产(元)
total_hldr_eqy_exc_min_int | float | 股东权益合计(不含少数股东权益)(元)
diluted_eps | float | 每股收益(摊薄)(元)
diluted_roe | float | 净资产收益率(摊薄)(%)
yoy_net_profit | float | 去年同期修正后净利润
bps | float | 每股净资产
yoy_sales | float | 同比增长率:营业收入
yoy_op | float | 同比增长率:营业利润
yoy_tp | float | 同比增长率:利润总额
yoy_dedu_np | float | 同比增长率:归属母公司股东的净利润
yoy_eps | float | 同比增长率:基本每股收益
yoy_roe | float | 同比增减:加权平均净资产收益率
growth_assets | float | 比年初增长率:总资产
yoy_equity | float | 比年初增长率:归属母公司的股东权益
growth_bps | float | 比年初增长率:归属于母公司股东的每股净资产
or_last_year | float | 去年同期营业收入
op_last_year | float | 去年同期营业利润
tp_last_year | float | 去年同期利润总额
np_last_year | float | 去年同期净利润
eps_last_year | float | 去年同期每股收益
open_net_assets | float | 期初净资产
open_bps | float | 期初每股净资产
perf_summary | str | 业绩简要说明
is_audit | int | 是否审计： 1是 0否
remark | str | 备注


**接口用法**

```python

pro = ts.pro_api()

pro.express(ts_code='600000.SH', start_date='20180101', end_date='20180701', fields='ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets')

```

获取某一季度全部股票数据
```python

df = pro.express_vip(period='20181231',fields='ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets')

```

**数据样例**

         ts_code  ann_date  end_date       revenue  operate_profit  total_profit      n_income  total_assets  \
    0  603535.SH  20180411  20180331  2.064659e+08    3.345047e+07  3.340047e+07  2.672643e+07  1.682111e+09   
    1  603535.SH  20180208  20171231  1.034262e+09    1.323373e+08  1.440493e+08  1.188325e+08  1.710466e+09   
    2  603535.SH  20171016  20170930  7.064117e+08    9.509520e+07  9.931530e+07  8.202480e+07  1.672986e+09