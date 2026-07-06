## 财务指标数据
----

接口：fina_indicator，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取上市公司财务指标数据，为避免服务器压力，现阶段每次请求最多返回100条记录，可通过设置日期多次请求获取更多数据。
权限：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  
<font color="red">
提示：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用fina_indicator_vip接口（参数一致），需积攒5000积分。
</font>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | TS股票代码,e.g. 600001.SH/000001.SZ
ann_date | str | N | 公告日期
start_date | str | N | 报告期开始日期
end_date | str | N | 报告期结束日期
period | str | N | 报告期(每个季度最后一天的日期,比如20171231表示年报)


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
ann_date | str | Y | 公告日期
end_date | str | Y | 报告期
eps | float | Y | 基本每股收益
dt_eps | float | Y | 稀释每股收益
total_revenue_ps | float | Y | 每股营业总收入
revenue_ps | float | Y | 每股营业收入
capital_rese_ps | float | Y | 每股资本公积
surplus_rese_ps | float | Y | 每股盈余公积
undist_profit_ps | float | Y | 每股未分配利润
extra_item | float | Y | 非经常性损益
profit_dedt | float | Y | 扣除非经常性损益后的净利润（扣非净利润）
gross_margin | float | Y | 毛利
current_ratio | float | Y | 流动比率
quick_ratio | float | Y | 速动比率
cash_ratio | float | Y | 保守速动比率
invturn_days | float | N | 存货周转天数
arturn_days | float | N | 应收账款周转天数
inv_turn | float | N | 存货周转率
ar_turn | float | Y | 应收账款周转率
ca_turn | float | Y | 流动资产周转率
fa_turn | float | Y | 固定资产周转率
assets_turn | float | Y | 总资产周转率
op_income | float | Y | 经营活动净收益
valuechange_income | float | N | 价值变动净收益
interst_income | float | N | 利息费用
daa | float | N | 折旧与摊销
ebit | float | Y | 息税前利润
ebitda | float | Y | 息税折旧摊销前利润
fcff | float | Y | 企业自由现金流量
fcfe | float | Y | 股权自由现金流量
current_exint | float | Y | 无息流动负债
noncurrent_exint | float | Y | 无息非流动负债
interestdebt | float | Y | 带息债务
netdebt | float | Y | 净债务
tangible_asset | float | Y | 有形资产
working_capital | float | Y | 营运资金
networking_capital | float | Y | 营运流动资本
invest_capital | float | Y | 全部投入资本
retained_earnings | float | Y | 留存收益
diluted2_eps | float | Y | 期末摊薄每股收益
bps | float | Y | 每股净资产
ocfps | float | Y | 每股经营活动产生的现金流量净额
retainedps | float | Y | 每股留存收益
cfps | float | Y | 每股现金流量净额
ebit_ps | float | Y | 每股息税前利润
fcff_ps | float | Y | 每股企业自由现金流量
fcfe_ps | float | Y | 每股股东自由现金流量
netprofit_margin | float | Y | 销售净利率
grossprofit_margin | float | Y | 销售毛利率
cogs_of_sales | float | Y | 销售成本率
expense_of_sales | float | Y | 销售期间费用率
profit_to_gr | float | Y | 净利润/营业总收入
saleexp_to_gr | float | Y | 销售费用/营业总收入
adminexp_of_gr | float | Y | 管理费用/营业总收入
finaexp_of_gr | float | Y | 财务费用/营业总收入
impai_ttm | float | Y | 资产减值损失/营业总收入
gc_of_gr | float | Y | 营业总成本/营业总收入
op_of_gr | float | Y | 营业利润/营业总收入
ebit_of_gr | float | Y | 息税前利润/营业总收入
roe | float | Y | 净资产收益率
roe_waa | float | Y | 加权平均净资产收益率
roe_dt | float | Y | 净资产收益率(扣除非经常损益)
roa | float | Y | 总资产报酬率
npta | float | Y | 总资产净利润
roic | float | Y | 投入资本回报率
roe_yearly | float | Y | 年化净资产收益率
roa2_yearly | float | Y | 年化总资产报酬率
roe_avg | float | N | 平均净资产收益率(增发条件)
opincome_of_ebt | float | N | 经营活动净收益/利润总额
investincome_of_ebt | float | N | 价值变动净收益/利润总额
n_op_profit_of_ebt | float | N | 营业外收支净额/利润总额
tax_to_ebt | float | N | 所得税/利润总额
dtprofit_to_profit | float | N | 扣除非经常损益后的净利润/净利润
salescash_to_or | float | N | 销售商品提供劳务收到的现金/营业收入
ocf_to_or | float | N | 经营活动产生的现金流量净额/营业收入
ocf_to_opincome | float | N | 经营活动产生的现金流量净额/经营活动净收益
capitalized_to_da | float | N | 资本支出/折旧和摊销
debt_to_assets | float | Y | 资产负债率
assets_to_eqt | float | Y | 权益乘数
dp_assets_to_eqt | float | Y | 权益乘数(杜邦分析)
ca_to_assets | float | Y | 流动资产/总资产
nca_to_assets | float | Y | 非流动资产/总资产
tbassets_to_totalassets | float | Y | 有形资产/总资产
int_to_talcap | float | Y | 带息债务/全部投入资本
eqt_to_talcapital | float | Y | 归属于母公司的股东权益/全部投入资本
currentdebt_to_debt | float | Y | 流动负债/负债合计
longdeb_to_debt | float | Y | 非流动负债/负债合计
ocf_to_shortdebt | float | Y | 经营活动产生的现金流量净额/流动负债
debt_to_eqt | float | Y | 产权比率
eqt_to_debt | float | Y | 归属于母公司的股东权益/负债合计
eqt_to_interestdebt | float | Y | 归属于母公司的股东权益/带息债务
tangibleasset_to_debt | float | Y | 有形资产/负债合计
tangasset_to_intdebt | float | Y | 有形资产/带息债务
tangibleasset_to_netdebt | float | Y | 有形资产/净债务
ocf_to_debt | float | Y | 经营活动产生的现金流量净额/负债合计
ocf_to_interestdebt | float | N | 经营活动产生的现金流量净额/带息债务
ocf_to_netdebt | float | N | 经营活动产生的现金流量净额/净债务
ebit_to_interest | float | N | 已获利息倍数(EBIT/利息费用)
longdebt_to_workingcapital | float | N | 长期债务与营运资金比率
ebitda_to_debt | float | N | 息税折旧摊销前利润/负债合计
turn_days | float | Y | 营业周期
roa_yearly | float | Y | 年化总资产净利率
roa_dp | float | Y | 总资产净利率(杜邦分析)
fixed_assets | float | Y | 固定资产合计
profit_prefin_exp | float | N | 扣除财务费用前营业利润
non_op_profit | float | N | 非营业利润
op_to_ebt | float | N | 营业利润／利润总额
nop_to_ebt | float | N | 非营业利润／利润总额
ocf_to_profit | float | N | 经营活动产生的现金流量净额／营业利润
cash_to_liqdebt | float | N | 货币资金／流动负债
cash_to_liqdebt_withinterest | float | N | 货币资金／带息流动负债
op_to_liqdebt | float | N | 营业利润／流动负债
op_to_debt | float | N | 营业利润／负债合计
roic_yearly | float | N | 年化投入资本回报率
total_fa_trun | float | N | 固定资产合计周转率
profit_to_op | float | Y | 利润总额／营业收入
q_opincome | float | N | 经营活动单季度净收益
q_investincome | float | N | 价值变动单季度净收益
q_dtprofit | float | N | 扣除非经常损益后的单季度净利润
q_eps | float | N | 每股收益(单季度)
q_netprofit_margin | float | N | 销售净利率(单季度)
q_gsprofit_margin | float | N | 销售毛利率(单季度)
q_exp_to_sales | float | N | 销售期间费用率(单季度)
q_profit_to_gr | float | N | 净利润／营业总收入(单季度)
q_saleexp_to_gr | float | Y | 销售费用／营业总收入 (单季度)
q_adminexp_to_gr | float | N | 管理费用／营业总收入 (单季度)
q_finaexp_to_gr | float | N | 财务费用／营业总收入 (单季度)
q_impair_to_gr_ttm | float | N | 资产减值损失／营业总收入(单季度)
q_gc_to_gr | float | Y | 营业总成本／营业总收入 (单季度)
q_op_to_gr | float | N | 营业利润／营业总收入(单季度)
q_roe | float | Y | 净资产收益率(单季度)
q_dt_roe | float | Y | 净资产单季度收益率(扣除非经常损益)
q_npta | float | Y | 总资产净利润(单季度)
q_opincome_to_ebt | float | N | 经营活动净收益／利润总额(单季度)
q_investincome_to_ebt | float | N | 价值变动净收益／利润总额(单季度)
q_dtprofit_to_profit | float | N | 扣除非经常损益后的净利润／净利润(单季度)
q_salescash_to_or | float | N | 销售商品提供劳务收到的现金／营业收入(单季度)
q_ocf_to_sales | float | Y | 经营活动产生的现金流量净额／营业收入(单季度)
q_ocf_to_or | float | N | 经营活动产生的现金流量净额／经营活动净收益(单季度)
basic_eps_yoy | float | Y | 基本每股收益同比增长率(%)
dt_eps_yoy | float | Y | 稀释每股收益同比增长率(%)
cfps_yoy | float | Y | 每股经营活动产生的现金流量净额同比增长率(%)
op_yoy | float | Y | 营业利润同比增长率(%)
ebt_yoy | float | Y | 利润总额同比增长率(%)
netprofit_yoy | float | Y | 归属母公司股东的净利润同比增长率(%)
dt_netprofit_yoy | float | Y | 归属母公司股东的净利润-扣除非经常损益同比增长率(%)
ocf_yoy | float | Y | 经营活动产生的现金流量净额同比增长率(%)
roe_yoy | float | Y | 净资产收益率(摊薄)同比增长率(%)
bps_yoy | float | Y | 每股净资产相对年初增长率(%)
assets_yoy | float | Y | 资产总计相对年初增长率(%)
eqt_yoy | float | Y | 归属母公司的股东权益相对年初增长率(%)
tr_yoy | float | Y | 营业总收入同比增长率(%)
or_yoy | float | Y | 营业收入同比增长率(%)
q_gr_yoy | float | N | 营业总收入同比增长率(%)(单季度)
q_gr_qoq | float | N | 营业总收入环比增长率(%)(单季度)
q_sales_yoy | float | Y | 营业收入同比增长率(%)(单季度)
q_sales_qoq | float | N | 营业收入环比增长率(%)(单季度)
q_op_yoy | float | N | 营业利润同比增长率(%)(单季度)
q_op_qoq | float | Y | 营业利润环比增长率(%)(单季度)
q_profit_yoy | float | N | 净利润同比增长率(%)(单季度)
q_profit_qoq | float | N | 净利润环比增长率(%)(单季度)
q_netprofit_yoy | float | N | 归属母公司股东的净利润同比增长率(%)(单季度)
q_netprofit_qoq | float | N | 归属母公司股东的净利润环比增长率(%)(单季度)
equity_yoy | float | Y | 净资产同比增长率
rd_exp | float | N | 研发费用
update_flag | str | N | 更新标识

**接口用法**

```python

pro = ts.pro_api()

df = pro.fina_indicator(ts_code='600000.SH')

```

或者

```python

df = pro.query('fina_indicator', ts_code='600000.SH', start_date='20170101', end_date='20180801')

```


**数据样例**

    ts_code  ann_date  end_date   eps  dt_eps  total_revenue_ps  revenue_ps  \
	0  600000.SH  20180830  20180630  0.95    0.95            2.8024      2.8024   
	1  600000.SH  20180428  20180331  0.46    0.46            1.3501      1.3501   
	2  600000.SH  20180428  20171231  1.84    1.84            5.7447      5.7447   
	3  600000.SH  20180428  20171231  1.84    1.84            5.7447      5.7447   
	4  600000.SH  20171028  20170930  1.45    1.45            4.2507      4.2507   
	5  600000.SH  20171028  20170930  1.45    1.45            4.2507      4.2507   
	6  600000.SH  20170830  20170630  0.97    0.97            2.9659      2.9659   
	7  600000.SH  20170427  20170331  0.63    0.63            1.9595      1.9595   
	8  600000.SH  20170427  20170331  0.63    0.63            1.9595      1.9595  