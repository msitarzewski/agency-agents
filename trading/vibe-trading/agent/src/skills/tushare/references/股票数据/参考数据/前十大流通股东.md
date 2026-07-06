## 前十大流通股东
----

接口：top10_floatholders
描述：获取上市公司前十大流通股东数据
积分：需2000积分以上才可以调取本接口，5000积分以上频次会更高

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | TS代码
period | str | N | 报告期（YYYYMMDD格式，一般为每个季度最后一天）
ann_date | str | N | 公告日期
start_date | str | N | 报告期开始日期
end_date | str | N | 报告期结束日期


**输出参数**

名称 | 类型 | 描述
--- | ---- | ----
ts_code | str | TS股票代码
ann_date | str | 公告日期
end_date | str | 报告期
holder_name | str | 股东名称
hold_amount | float | 持有数量（股）
hold_ratio | float | 占总股本比例(%)
hold_float_ratio | float  | 占流通股本比例(%)
hold_change | float  | 持股变动
holder_type | str | 股东类型


**接口用法**

```python

pro = ts.pro_api()

df = pro.top10_floatholders(ts_code='600000.SH', start_date='20170101', end_date='20171231')

```

或者

```python

df = pro.query('top10_floatholders', ts_code='600000.SH', start_date='20170101', end_date='20171231')

```

**数据样例**

         ts_code  ann_date  end_date                        holder_name   hold_amount
    0  600000.SH  20180428  20171231  富德生命人寿保险股份有限公司-资本金  1.763232e+09
    1  600000.SH  20180428  20171231          上海国际集团有限公司  5.489319e+09
    2  600000.SH  20180428  20171231   富德生命人寿保险股份有限公司-传统  2.779437e+09
    3  600000.SH  20180428  20171231        中国证券金融股份有限公司  1.216979e+09
    4  600000.SH  20180428  20171231       梧桐树投资平台有限责任公司  8.861313e+08
    5  600000.SH  20180428  20171231       上海上国投资产管理有限公司  1.395571e+09
    6  600000.SH  20180428  20171231  富德生命人寿保险股份有限公司-万能H  1.270429e+09
    7  600000.SH  20180428  20171231        上海国鑫投资发展有限公司  5.392559e+08
    8  600000.SH  20180428  20171231      中央汇金资产管理有限责任公司  3.985214e+08
    9  600000.SH  20180428  20171231      中国移动通信集团广东有限公司  5.334893e+09