## 美股财务指标数据
----

接口：us_fina_indicator，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取美股上市公司财务指标数据，目前只覆盖主要美股和中概股。为避免服务器压力，现阶段每次请求最多返回200条记录，可通过设置日期多次请求获取更多数据。
权限：需单独开权限或有15000积分，具体权限信息请参考[权限列表](https://tushare.pro/document/1?doc_id=290)
提示：当前接口按单只股票获取其历史数据，单次请求最大返回10000行数据，可循环提取

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码
period | str | N | 报告期（格式：YYYYMMDD，每个季度最后一天的日期，如20241231)
report_type | str | N | 报告期类型(Q1一季报Q2半年报Q3三季报Q4年报)
start_date | str | N | 报告期开始时间（格式：YYYYMMDD）
end_date | str | N | 报告结束始时间（格式：YYYYMMDD）

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
end_date | str | Y | 报告期
ind_type | str | Y | 报告类型,Q1一季报,Q2中报,Q3三季报,Q4年报
security_name_abbr | str | Y | 股票名称
accounting_standards | str | Y | 会计准则
notice_date | str | Y | 公告日期
start_date | str | Y | 报告期开始时间
std_report_date | str | Y | 标准报告期
financial_date | str | Y | 年结日
currency | str | Y | 币种
date_type | str | Y | 报告期类型
report_type | str | Y | 报告类型
operate_income | float | Y | 收入
operate_income_yoy | float | Y | 收入增长
gross_profit | float | Y | 毛利
gross_profit_yoy | float | Y | 毛利增长
parent_holder_netprofit | float | Y | 归母净利润
parent_holder_netprofit_yoy | float | Y | 归母净利润增长
basic_eps | float | Y | 基本每股收益
diluted_eps | float | Y | 稀释每股收益
gross_profit_ratio | float | Y | 销售毛利率
net_profit_ratio | float | Y | 销售净利率
accounts_rece_tr | float | Y | 应收账款周转率(次)
inventory_tr | float | Y | 存货周转率(次)
total_assets_tr | float | Y | 总资产周转率(次)
accounts_rece_tdays | float | Y | 应收账款周转天数
inventory_tdays | float | Y | 存货周转天数
total_assets_tdays | float | Y | 总资产周转天数
roe_avg | float | Y | 净资产收益率
roa | float | Y | 总资产净利率
current_ratio | float | Y | 流动比率(倍)
speed_ratio | float | Y | 速动比率(倍)
ocf_liqdebt | float | Y | 经营业务现金净额/流动负债
debt_asset_ratio | float | Y | 资产负债率
equity_ratio | float | Y | 产权比率
basic_eps_yoy | float | Y | 基本每股收益同比增长
gross_profit_ratio_yoy | float | Y | 毛利率同比增长(%)
net_profit_ratio_yoy | float | Y | 净利率同比增长(%)
roe_avg_yoy | float | Y | 平均净资产收益率同比增长(%)
roa_yoy | float | Y | 净资产收益率同比增长(%)
debt_asset_ratio_yoy | float | Y | 资产负债率同比增长(%)
current_ratio_yoy | float | Y | 流动比率同比增长(%)
speed_ratio_yoy | float | Y | 速动比率同比增长(%)
currency_abbr | str | Y | 币种
total_income | float | Y | 收入总额
total_income_yoy | float | Y | 收入总额同比增长
premium_income | float | Y | 保费收入
premium_income_yoy | float | Y | 保费收入同比
basic_eps_cs | float | Y | 基本每股收益
basic_eps_cs_yoy | float | Y | 基本每股收益同比增长
diluted_eps_cs | float | Y | 稀释每股收益
payout_ratio | float | Y | 保费收入/赔付支出
capitial_ratio | float | Y | 总资产周转率
roe | float | Y | 净资产收益率
roe_yoy | float | Y | 净资产收益率同比增长
debt_ratio | float | Y | 资产负债率
debt_ratio_yoy | float | Y | 资产负债率同比增长
net_interest_income | float | Y | 净利息收入
net_interest_income_yoy | float | Y | 净利息收入增长
diluted_eps_cs_yoy | float | Y | 稀释每股收益增长
loan_loss_provision | float | Y | 贷款损失准备
loan_loss_provision_yoy | float | Y | 贷款损失准备增长
loan_deposit | float | Y | 贷款/存款
loan_equity | float | Y | 贷款/股东权益(倍)
loan_assets | float | Y | 贷款/总资产
deposit_equity | float | Y | 存款/股东权益(倍)
deposit_assets | float | Y | 存款/总资产
rol | float | Y | 贷款回报率
rod | float | Y | 存款回报率

注：输出指标太多可在接口fields参数设定你需要的指标，例如：fields='ts_coe,bps,basic_eps'
<br>
<br>


**接口用法**

```python

pro = ts.pro_api()

#获取美股英伟达NVDA股票2024年度的财务指标数据
df = pro.us_fina_indicator(ts_code='NVDA', period='20241231')

#获取美股英伟达NVDA股票历年年报财务指标数据
df = pro.us_fina_indicator(ts_code='NVDA', report_type='Q4')

```

<br>
<br>

**数据样例**

		 ts_code  end_date ind_type security_name_abbr accounting_standards notice_date start_date std_report_date financial_date currency date_type report_type  operate_income  operate_income_yoy  \
	0     NVDA  20250427       Q1                英伟达               美国会计准则    20250528   20250127        20250331            2-1       美元       单季报     2025/Q1    4.406200e+10             69.1829   
	1     NVDA  20250126       Q4                英伟达               美国会计准则    20250226   20240129        20241231           1-26       美元        年报     2024/FY    1.304970e+11            114.2034   
	2     NVDA  20241027       Q3                英伟达               美国会计准则    20241120   20240129        20240930           1-26       美元      累计季报     2024/Q9    9.116600e+10            134.8489   
	3     NVDA  20240728       Q2                英伟达               美国会计准则    20240828   20240129        20240630           1-26       美元      累计季报     2024/Q6    5.608400e+10            170.9503   
	4     NVDA  20240428       Q1                英伟达               美国会计准则    20250528   20240129        20240331           1-26       美元       单季报     2024/Q1    2.604400e+10            262.1246   
	5     NVDA  20240128       Q4                英伟达               美国会计准则    20250226   20230130        20231231           1-28       美元        年报     2023/FY    6.092200e+10            125.8545   
	6     NVDA  20231029       Q3                英伟达               美国会计准则    20241120   20230130        20230930           1-28       美元      累计季报     2023/Q9    3.881900e+10             85.5327   
	7     NVDA  20230730       Q2                英伟达               美国会计准则    20240828   20230131        20230630           1-28       美元      累计季报     2023/Q6    2.069900e+10             38.0670   
	8     NVDA  20230430       Q1                英伟达               美国会计准则    20240529   20230130        20230331           1-28       美元       单季报     2023/Q1    7.192000e+09            -13.2239   
	9     NVDA  20230129       Q4                英伟达               美国会计准则    20250226   20220131        20221231           1-29       美元        年报     2022/FY    2.697400e+10              0.2229   
	10    NVDA  20221030       Q3                英伟达               美国会计准则    20231121   20220131        20220930           1-29       美元      累计季报     2022/Q9    2.092300e+10              8.5725   
	11    NVDA  20220731       Q2                英伟达               美国会计准则    20230828   20220201        20220630           1-29       美元      累计季报     2022/Q6    1.499200e+10             23.2084   
	12    NVDA  20220501       Q1                英伟达               美国会计准则    20230526   20220131        20220331           1-29       美元       单季报     2022/Q1    8.288000e+09             46.4052   
	13    NVDA  20220130       Q4                英伟达               美国会计准则    20240221   20210201        20211231           1-30       美元        年报     2021/FY    2.691400e+10             61.4033   
	14    NVDA  20211031       Q3                英伟达               美国会计准则    20221118   20210201        20210930           1-30       美元      累计季报     2021/Q9    1.927100e+10             65.1045   