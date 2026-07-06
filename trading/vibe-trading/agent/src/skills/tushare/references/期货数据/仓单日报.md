## 仓单日报
----

接口：fut_wsr
描述：获取仓单日报数据，了解各仓库/厂库的仓单变化
限量：单次最大1000，总量不限制
积分：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期
symbol | str | N | 产品代码
start_date | str | N | 开始日期(YYYYMMDD格式，下同)
end_date | str | N | 结束日期
exchange | str | N | 交易所代码


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
trade_date | str | Y | 交易日期
symbol | str | Y | 产品代码
fut_name | str | Y | 产品名称
warehouse | str | Y | 仓库名称
wh_id | str | N | 仓库编号
pre_vol | int | Y | 昨日仓单量
vol | int | Y | 今日仓单量
vol_chg | int | Y | 增减量
area | str | N | 地区
year | str | N | 年度
grade | str | N | 等级
brand | str | N | 品牌
place | str | N | 产地
pd | int | N | 升贴水
is_ct | str | N | 是否折算仓单
unit | str | Y | 单位
exchange | str | N | 交易所


**接口示例**

```python

pro = ts.pro_api('your token')

df = pro.fut_wsr(trade_date='20181113', symbol='ZN')

```

**数据示例**


		 trade_date symbol fut_name    warehouse  pre_vol   vol  vol_chg unit
	0    20181113     ZN        锌      上海裕强     4960  4960        0    吨
	1    20181113     ZN        锌      上港物流      702   702        0    吨
	2    20181113     ZN        锌    上港物流苏州        0     0        0    吨
	3    20181113     ZN        锌      中储吴淞        0     0        0    吨
	4    20181113     ZN        锌      中储大场        0     0        0    吨
	5    20181113     ZN        锌      中储晟世        0     0        0    吨
	6    20181113     ZN        锌      中金圣源      428   353      -75    吨
	7    20181113     ZN        锌      全胜物流     2882  2882        0    吨
	8    20181113     ZN        锌      南储仓储       25    25        0    吨
	9    20181113     ZN        锌      同盛松江        0     0        0    吨
	10   20181113     ZN        锌    国储837处        0     0        0    吨
	11   20181113     ZN        锌      国储天威        0     0        0    吨
	12   20181113     ZN        锌    国能物流常州      200   200        0    吨
	13   20181113     ZN        锌   外运华东张华浜        0     0        0    吨
	14   20181113     ZN        锌     宁波九龙仓        0     0        0    吨
	15   20181113     ZN        锌  广储830三水西        0     0        0    吨
	16   20181113     ZN        锌      康运萧山        0     0        0    吨
	17   20181113     ZN        锌      无锡国联        0     0        0    吨
	18   20181113     ZN        锌      期晟公司      449   226     -223    吨
	19   20181113     ZN        锌      浙江康运       25    25        0    吨
	20   20181113     ZN        锌     百金汇物流        0     0        0    吨
	21   20181113     ZN        锌      裕强闵行        0     0        0    吨