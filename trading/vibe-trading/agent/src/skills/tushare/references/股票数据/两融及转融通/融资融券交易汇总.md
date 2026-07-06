## 融资融券交易汇总
----

接口：margin
描述：获取融资融券每日交易汇总数据
限量：单次请求最大返回4000行数据，可根据日期循环
权限：2000积分可获得本接口权限，积分越高权限越大，具体参考[权限说明](https://tushare.pro/document/1?doc_id=290)

<br>
<br>


**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
trade_date | str | N | 交易日期（格式：YYYYMMDD，下同）
start_date | str | N | 开始日期
end_date | str | N | 结束日期
exchange_id | str | N | 交易所代码（SSE上交所SZSE深交所BSE北交所）

**输出参数**

<br>
<br>

名称 | 类型 | 描述
--- | ---- | ----
trade_date | str | 交易日期
exchange_id | str | 交易所代码（SSE上交所SZSE深交所BSE北交所）
rzye | float | 融资余额(元)
rzmre | float | 融资买入额(元)
rzche | float | 融资偿还额(元)
rqye | float | 融券余额(元)
rqmcl | float | 融券卖出量(股,份,手)
rzrqye | float | 融资融券余额(元)
rqyl | float | 融券余量(股,份,手)

<br>
<br>

**接口使用**

```python

pro = ts.pro_api()

df = pro.margin(trade_date='20180802')

```

或者

```python

df = pro.query('margin', trade_date='20180802', exchange_id='SSE')

```

**数据样例**

      trade_date exchange_id          rzye         rzmre         rzche  \
    0   20180802        SZSE  3.495054e+11  1.347549e+10  1.463921e+10   
    1   20180802         SSE  5.311746e+11  1.484584e+10  1.573947e+10   
    
               rqye       rqmcl        rzrqye  
    0  1.083380e+09  24418046.0  3.505888e+11  
    1  6.029618e+09  83721012.0  5.372042e+11  



**说明**
融资融券数据从证券交易所网站直接获取，提供了有记录以来的全部汇总和明细数据。
根据交所网站提示：数据根据券商申报的数据汇总，由券商保证数据的真实、完整、准确。

其中：
本日融资余额(元)=前日融资余额＋本日融资买入-本日融资偿还额
本日融券余量(股)=前日融券余量＋本日融券卖出量-本日融券买入量-本日现券偿还量
本日融券余额(元)=本日融券余量×本日收盘价
本日融资融券余额(元)=本日融资余额＋本日融券余额

2014年9月22日起，“融资融券交易总量”数据包含调出标的证券名单的证券的融资融券余额