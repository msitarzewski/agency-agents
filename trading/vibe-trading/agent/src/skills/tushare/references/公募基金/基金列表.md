## 公募基金列表
----

接口：fund_basic，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取公募基金数据列表，包括场内和场外基金
积分：用户需要2000积分才可以调取，单次最大可以提取15000条数据，5000积分以上权限更高，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 基金代码
market | str | N | 交易市场: E场内 O场外（默认E）
status | str | N | 存续状态 D摘牌 I发行 L上市中


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 基金代码
name | str | Y | 简称
management | str | Y | 管理人
custodian | str | Y | 托管人
fund_type | str | Y | 投资类型
found_date | str | Y | 成立日期
due_date | str | Y | 到期日期
list_date | str | Y | 上市时间
issue_date | str | Y | 发行日期
delist_date | str | Y | 退市日期
issue_amount | float | Y | 发行份额(亿)
m_fee | float | Y | 管理费
c_fee | float | Y | 托管费
duration_year | float | Y | 存续期
p_value | float | Y | 面值
min_amount | float | Y | 起点金额(万元)
exp_return | float | Y | 预期收益率
benchmark | str | Y | 业绩比较基准
status | str | Y | 存续状态D摘牌 I发行 L已上市
invest_type | str | Y | 投资风格
type | str | Y | 基金类型
trustee | str | Y | 受托人
purc_startdate | str | Y | 日常申购起始日
redm_startdate | str | Y | 日常赎回起始日
market | str | Y | E场内O场外


**接口用例**

```python

pro = ts.pro_api()

df = pro.fund_basic(market='E')

```

**数据样例**

        ts_code             name         management  custodian      fund_type found_date  \
	1     512850.SH    中信建投北京50ETF     中信建投基金      招商银行       股票型   20180927   
	2     168601.SZ    汇安裕阳三年定期开放       汇安基金    中国光大银行       混合型   20180927 
	3     512860.SH    华安中国A股ETF       华安基金    中国农业银行       股票型   20180927   
	4     159960.SZ    恒生国企     平安大华基金      中国银行       股票型   20180921   
	5     501062.SH    南方瑞合三年       南方基金    中国建设银行       混合型   20180906   
	6     510600.SH    沪50ETF     申万菱信基金    中国工商银行       股票型   20180903   
	7     501061.SH    金选300C       中金基金    中国建设银行       股票型   20180830   
	8     501060.SH    金选300A       中金基金    中国建设银行       股票型   20180830   
	9     166802.SZ     浙商300       浙商基金      华夏银行       股票型   20180820 