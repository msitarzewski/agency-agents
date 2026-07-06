## 指数成分和权重
----

接口：index_weight
描述：获取各类指数成分和权重，**月度数据** ，建议输入参数里开始日期和结束日分别输入当月第一天和最后一天的日期。
来源：指数公司网站公开数据
积分：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
index_code | str | Y | 指数代码，来源<a href="https://tushare.pro/document/2?doc_id=94">指数基础信息接口</a>
trade_date | str | N | 交易日期（格式YYYYMMDD，下同）
start_date | str | N | 开始日期
end_date | None | N | 结束日期

**输出参数**

名称 | 类型 | 描述
--- | ---- | ----
index_code | str | 指数代码
con_code | str | 成分代码
trade_date | str | 交易日期
weight | float | 权重

**接口调用**

```python

pro = ts.pro_api()

#提取沪深300指数2018年9月成分和权重
df = pro.index_weight(index_code='399300.SZ', start_date='20180901', end_date='20180930')

```


**数据样例**

        index_code   con_code trade_date  weight
    0    399300.SZ  000001.SZ   20180903  0.8656
    1    399300.SZ  000002.SZ   20180903  1.1330
    2    399300.SZ  000060.SZ   20180903  0.1125
    3    399300.SZ  000063.SZ   20180903  0.4273
    4    399300.SZ  000069.SZ   20180903  0.2010
    5    399300.SZ  000157.SZ   20180903  0.1699
    6    399300.SZ  000402.SZ   20180903  0.0816
    7    399300.SZ  000413.SZ   20180903  0.2023
    8    399300.SZ  000415.SZ   20180903  0.0648
    9    399300.SZ  000423.SZ   20180903  0.2100
    10   399300.SZ  000425.SZ   20180903  0.1884