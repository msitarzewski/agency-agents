## 股东增减持
----

接口：stk_holdertrade
描述：获取上市公司增减持数据，了解重要股东近期及历史上的股份增减变化
限量：单次最大提取3000行记录，总量不限制
积分：用户需要至少2000积分才可以调取。基础积分有流量控制，积分越多权限越大，5000积分以上无明显限制，请自行提高积分，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | TS股票代码
ann_date | str | N | 公告日期
start_date | str | N | 公告开始日期
end_date | str | N | 公告结束日期
trade_type | str | N | 交易类型IN增持DE减持
holder_type | str | N | 股东类型C公司P个人G高管

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
ann_date | str | Y | 公告日期
holder_name | str | Y | 股东名称
holder_type | str | Y | 股东类型G高管P个人C公司
in_de | str | Y | 类型IN增持DE减持
change_vol | float | Y | 变动数量
change_ratio | float | Y | 占流通比例（%）
after_share | float | Y | 变动后持股
after_ratio | float | Y | 变动后占流通比例（%）
avg_price | float | Y | 平均价格
total_share | float | Y | 持股总数
begin_date | str | N | 增减持开始日期
close_date | str | N | 增减持结束日期

<br>
<br>

**接口示例**

```python

#获取单日全部增减持数据
df = pro.stk_holdertrade(ann_date='20190426')

#获取单个股票数据
df = pro.stk_holdertrade(ts_code='002149.SZ')

#获取当日增持数据
df = pro.stk_holdertrade(ann_date='20190426', trade_type='IN')

```


<br>
<br>

**数据示例**

        ts_code    ann_date          holder_name     holder_type in_de  \
	0   300216.SZ  20190426          郑国胜           P    DE   
	1   300216.SZ  20190426          黄盛秋           P    DE   
	2   300216.SZ  20190426          刘燕             G    DE   
	3   300216.SZ  20190426          邓铁山           G    DE   
	4   002806.SZ  20190426          广东省科技创业投资有限公司           C    DE   
	5   603801.SH  20190426          尚志有限公司           C    DE   
	6   600728.SH  20190426          重庆中新融鑫投资中心(有限合伙)           C    DE   
	7   300115.SZ  20190426          新疆长盈粤富股权投资有限公司           C    DE   
	8   300115.SZ  20190426           新疆长盈粤富股权投资有限公司           C    DE   
	9   601288.SH  20190426          上海锦江国际旅游股份有限公司           C    DE   
	10  603906.SH  20190426          建投嘉驰(上海)投资有限公司           C    DE   

    change_vol  change_ratio  after_share  after_ratio  avg_price  total_share  
	0     387871.0        0.1356    3385659.0       1.1834     3.8100    3385659.0  
	1      49056.0        0.0171    1194457.0       0.4175     3.7800    1194457.0  
	2     498062.0        0.1741          0.0          NaN     3.6700    8892000.0  
	3    2358900.0        0.8245         25.0       0.0000     3.2100    7076800.0  
	4    1086100.0        1.8826   10836700.0      18.7838    21.5100   25499200.0  
	5    3200000.0        3.8450    6808299.0       8.1806    31.5500    6808299.0  
	6   14710000.0        0.9170   76942195.0       4.7965     9.9400   76942195.0  
	7    9470000.0        1.0457  378846759.0      41.8343    13.6400  378846759.0  
	8    8690000.0        0.9596  370156759.0      40.8748    13.6800  370156759.0  
	9   14868500.0        0.0051          0.0          NaN        NaN          0.0  
	10   2540640.0        2.7223   22144800.0      23.7286    13.0241   22144800.0  
