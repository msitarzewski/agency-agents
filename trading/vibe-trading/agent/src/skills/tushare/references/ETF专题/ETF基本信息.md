## ETF基础信息
----

接口：etf_basic
描述：获取国内ETF基础信息，包括了QDII。数据来源与沪深交易所公开披露信息。
限量：单次请求最大放回5000条数据（当前ETF总数未超过2000）
权限：用户积8000积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | ETF代码（带.SZ/.SH后缀的6位数字，如：159526.SZ）
index_code | str | N | 跟踪指数代码
list_date | str | N | 上市日期（格式：YYYYMMDD）
list_status | str | N | 上市状态（L上市 D退市 P待上市）
exchange | str | N | 交易所（SH上交所 SZ深交所）
mgr | str | N | 管理人（简称，e.g.华夏基金)


<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 基金交易代码
csname | str | Y | ETF中文简称
extname | str | Y | ETF扩位简称(对应交易所简称)
cname | str | Y | 基金中文全称
index_code | str | Y | ETF基准指数代码
index_name | str | Y | ETF基准指数中文全称
setup_date | str | Y | 设立日期（格式：YYYYMMDD）
list_date | str | Y | 上市日期（格式：YYYYMMDD）
list_status | str | Y | 存续状态（L上市 D退市 P待上市）
exchange | str | Y | 交易所（上交所SH 深交所SZ）
mgr_name | str | Y | 基金管理人简称
custod_name | str | Y | 基金托管人名称
mgt_fee | float | Y | 基金管理人收取的费用
etf_type | str | Y | 基金投资通道类型（境内、QDII）

<br>
<br>

**接口示例**

```python

#获取当前所有上市的ETF列表
df = pro.etf_basic(list_status='L', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')


#获取“嘉实基金”所有上市的ETF列表
df = pro.etf_basic(mgr='嘉实基金'， list_status='L', fields='ts_code,extname,index_code,index_name,exchange,etf_type')


#获取“嘉实基金”在深交所上市的所有ETF列表
df = pro.etf_basic(mgr='嘉实基金'， list_status='L', exchange='SZ', fields='ts_code,extname,index_code,index_name,exchange,etf_type')


#获取以沪深300指数为跟踪指数的所有上市的ETF列表
df = pro.etf_basic(index_code='000300.SH', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')

```


<br>
<br>


**数据示例**

          ts_code       extname    index_code    index_name exchange   mgr_name
	0   159238.SZ      300ETF增强  000300.SH    沪深300指数       SZ   景顺长城基金
	1   159300.SZ        300ETF  000300.SH    沪深300指数       SZ     富国基金
	2   159330.SZ    沪深300ETF基金  000300.SH    沪深300指数       SZ   西藏东财基金
	3   159393.SZ    沪深300指数ETF  000300.SH    沪深300指数       SZ     万家基金
	4   159673.SZ    沪深300ETF鹏华  000300.SH    沪深300指数       SZ     鹏华基金
	5   159919.SZ      沪深300ETF  000300.SH    沪深300指数       SZ     嘉实基金
	6   159925.SZ    沪深300ETF南方  000300.SH    沪深300指数       SZ     南方基金
	7   159927.SZ     鹏华沪深300指数  000300.SH    沪深300指数       SZ     鹏华基金
	8   510300.SH      沪深300ETF  000300.SH    沪深300指数       SH   华泰柏瑞基金
	9   510310.SH   沪深300ETF易方达  000300.SH    沪深300指数       SH    易方达基金
	10  510320.SH    沪深300ETF中金  000300.SH    沪深300指数       SH     中金基金
	11  510330.SH    沪深300ETF华夏  000300.SH    沪深300指数       SH     华夏基金
	12  510350.SH    沪深300ETF工银  000300.SH    沪深300指数       SH   工银瑞信基金
	13  510360.SH    沪深300ETF基金  000300.SH    沪深300指数       SH     广发基金
	14  510370.SH      300指数ETF  000300.SH    沪深300指数       SH     兴业基金
	15  510380.SH      国寿300ETF  000300.SH    沪深300指数       SH   国寿安保基金
	16  510390.SH    沪深300ETF平安  000300.SH    沪深300指数       SH     平安基金
	17  515130.SH    沪深300ETF博时  000300.SH    沪深300指数       SH     博时基金
	18  515310.SH    沪深300指数ETF  000300.SH    沪深300指数       SH    汇添富基金
	19  515330.SH    沪深300ETF天弘  000300.SH    沪深300指数       SH     天弘基金
	20  515350.SH    民生加银300ETF  000300.SH    沪深300指数       SH   民生加银基金
	21  515360.SH    方正沪深300ETF  000300.SH    沪深300指数       SH   方正富邦基金
	22  515380.SH    沪深300ETF泰康  000300.SH    沪深300指数       SH     泰康基金
	23  515390.SH  沪深300ETF指数基金  000300.SH    沪深300指数       SH     华安基金
	24  515660.SH   沪深300ETF国联安  000300.SH    沪深300指数       SH    国联安基金
	25  515930.SH    永赢沪深300ETF  000300.SH    沪深300指数       SH     永赢基金
	26  561000.SH  沪深300ETF增强基金  000300.SH    沪深300指数       SH     华安基金
	27  561300.SH      300增强ETF  000300.SH    沪深300指数       SH     国泰基金
	28  561930.SH    沪深300ETF招商  000300.SH    沪深300指数       SH     招商基金
	29  561990.SH    沪深300增强ETF  000300.SH    沪深300指数       SH     招商基金
	30  563520.SH    沪深300ETF永赢  000300.SH    沪深300指数       SH     永赢基金
