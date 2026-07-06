## 港股财务指标数据
----
接口：hk_fina_indicator，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取港股上市公司财务指标数据，为避免服务器压力，现阶段每次请求最多返回200条记录，可通过设置日期多次请求获取更多数据。
权限：需单独开权限或有15000积分，具体权限信息请参考[权限列表](https://tushare.pro/document/1?doc_id=290)
提示：当前接口按单只股票获取其历史数据，单次请求最大返回10000行数据，可循环提取

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码
period | str | N | 报告期(格式：YYYYMMDD）
report_type | str | N | 报告期类型（Q1一季报Q2半年报Q3三季报Q4年报）
start_date | str | N | 报告期开始日期(格式：YYYYMMDD）
end_date | str | N | 报告结束日期(格式：YYYYMMDD）

<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
name | str | Y | 股票名称
end_date | str | Y | 报告期
ind_type | str | Y | 报告类型,Q-按报告期(季度),Y-按年度
report_type | str | Y | 报告期类型
std_report_date | str | Y | 标准报告期
per_netcash_operate | float | Y | 每股经营现金流(元)
per_oi | float | Y | 每股营业收入(元)
bps | float | Y | 每股净资产(元)
basic_eps | float | Y | 基本每股收益(元)
diluted_eps | float | Y | 稀释每股收益(元)
operate_income | float | Y | 营业总收入(元)
operate_income_yoy | float | Y | 营业总收入同比增长(%)
gross_profit | float | Y | 毛利润(元)
gross_profit_yoy | float | Y | 毛利润同比增长(%)
holder_profit | float | Y | 归母净利润(元)
holder_profit_yoy | float | Y | 归母净利润同比增长(%)
gross_profit_ratio | float | Y | 毛利率(%)
eps_ttm | float | Y | ttm每股收益(元)
operate_income_qoq | float | Y | 营业总收入滚动环比增长(%)
net_profit_ratio | float | Y | 净利率(%)
roe_avg | float | Y | 平均净资产收益率(%)
gross_profit_qoq | float | Y | 毛利润滚动环比增长(%)
roa | float | Y | 总资产净利率(%)
holder_profit_qoq | float | Y | 归母净利润滚动环比增长(%)
roe_yearly | float | Y | 年化净资产收益率(%)
roic_yearly | float | Y | 年化投资回报率(%)
total_assets | float | Y | 资产总额
total_liabilities | float | Y | 负债总额
tax_ebt | float | Y | 所得税/利润总额(%)
ocf_sales | float | Y | 经营现金流/营业收入(%)
total_parent_equity | float | Y | 本公司权益持有人应占权益
debt_asset_ratio | float | Y | 资产负债率(%)
operate_profit | float | Y | 经营盈利
pretax_profit | float | Y | 除税前盈利
netcash_operate | float | Y | 经营活动所得现金流量净额
netcash_invest | float | Y | 投资活动耗用现金流量净额
netcash_finance | float | Y | 融资活动耗用现金流量净额
end_cash | float | Y | 期末的现金及现金等价物
divi_ratio | float | Y | 分红比例
dividend_rate | float | Y | 股息率
current_ratio | float | Y | 流动比率(倍)
common_acs | float | Y | 普通股应计股息
currentdebt_debt | float | Y | 流动负债/总负债(%)
issued_common_shares | float | Y | 已发行普通股
hk_common_shares | float | Y | 港股本(**不建议使用数据源有误**)
per_shares | float | Y | 每手股数
total_market_cap | float | Y | 总市值
hksk_market_cap | float | Y | 港股市值
pe_ttm | float | Y | 滚动市盈率
pb_ttm | float | Y | 滚动市净率
report_date_sq | str | Y | 季报日期
report_type_sq | str | Y | 报告类型
operate_income_sq | float | Y | 营业收入
dps_hkd | float | Y | 每股股息（港元）
operate_income_qoq_sq | float | Y | 营业收入环比
net_profit_ratio_sq | float | Y | 净利润率
holder_profit_sq | float | Y | 归属于股东净利润
holder_profit_qoq_sq | float | Y | 归母净利润环比
roe_avg_sq | float | Y | 平均净资产收益率
pe_ttm_sq | float | Y | 季报滚动市盈率
pb_ttm_sq | float | Y | 季报滚动市净率
roa_sq | float | Y | 总资产收益率
start_date | float | Y | 会计年度起始日
fiscal_year | float | Y | 会计年度截止日
currency | str | Y | 币种 港元（hkd）
is_cny_code | float | Y | 是否人民币代码
dps_hkd_ly | float | Y | 上一年每股股息
org_type | str | Y | 企业类型
premium_income | float | Y | 保费收入
premium_income_yoy | float | Y | 保费收入同比
net_interest_income | float | Y | 净利息收入
net_interest_income_yoy | float | Y | 净利息收入同比
fee_commission_income | float | Y | 手续费及佣金收入
fee_commission_income_yoy | float | Y | 手续费及佣金收入同比
accounts_rece_tdays | float | Y | 应收账款周转率(次)
inventory_tdays | float | Y | 存货周转率(次)
current_assets_tdays | float | Y | 流动资产周转率(次)
total_assets_tdays | float | Y | 总资产周转率(次)
premium_expense | float | Y | 保险赔付支出
loan_deposit | float | Y | 贷款/存款
loan_equity | float | Y | 贷款/股东权益
loan_assets | float | Y | 贷款/总资产
deposit_equity | float | Y | 存款/股东权益
deposit_assets | float | Y | 存款/总资产
equity_multiplier | float | Y | 权益乘数
equity_ratio | float | Y | 产权比率

注：输出指标太多可在接口fields参数设定你需要的指标，例如：fields='ts_coe,bps,basic_eps'
<br>
<br>



**接口用法**

```python

pro = ts.pro_api()

#获取港股腾讯控股00700.HK股票2014年度的财务指标数据
df = pro.hk_fina_indicator(ts_code='00700.HK', period='20241231')

#获取港股腾讯控股00700.HK股票历年年报财务指标数据
df = pro.hk_fina_indicator(ts_code='00700.HK', report_type='Q4')

```

<br>
<br>

**数据样例**

			 ts_code  name  end_date  ... deposit_assets equity_multiplier equity_ratio
	0   00700.HK  腾讯控股  20250331  ...           None            1.7083       0.7644
	1   00700.HK  腾讯控股  20241231  ...           None            1.6899       0.7469
	2   00700.HK  腾讯控股  20240930  ...           None            1.7576       0.8140
	3   00700.HK  腾讯控股  20240630  ...           None            1.7841       0.8451
	4   00700.HK  腾讯控股  20240331  ...           None            1.7962       0.8601
	..       ...   ...       ...  ...            ...               ...          ...
	86  00700.HK  腾讯控股  20030930  ...           None               NaN          NaN
	87  00700.HK  腾讯控股  20030630  ...           None               NaN          NaN
	88  00700.HK  腾讯控股  20030331  ...           None               NaN          NaN
	89  00700.HK  腾讯控股  20021231  ...           None            1.0794       0.0794
	90  00700.HK  腾讯控股  20011231  ...           None            1.3563       0.3563