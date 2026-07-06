## 主营业务构成
----

接口：fina_mainbz
描述：获得上市公司主营业务构成，分地区和产品两种方式
权限：用户需要至少2000积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  ，单次最大提取100行，总量不限制，可循环获取。
<font color="red">
提示：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用fina_mainbz_vip接口（参数一致），需积攒5000积分。
</font>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 股票代码
period | str | N | 报告期(每个季度最后一天的日期,比如20171231表示年报)
type | str | N | 类型：P按产品 D按地区 I按行业（请输入大写字母P或者D）
start_date | str | N | 报告期开始日期
end_date | str | N | 报告期结束日期


**输出参数**

名称 | 类型 | 描述
--- | ---- | ----
ts_code | str | TS代码
end_date | str | 报告期
bz_item | str | 主营业务来源
bz_sales | float | 主营业务收入(元)
bz_profit | float | 主营业务利润(元)
bz_cost | float | 主营业务成本(元)
curr_type | str | 货币代码
update_flag | str | 是否更新

**代码示例**

```python

pro = ts.pro_api()

df = pro.fina_mainbz(ts_code='000627.SZ', type='P')

```

获取某一季度全部股票数据
```python

df = pro.fina_mainbz_vip(period='20181231', type='P' ,fields='ts_code,end_date,bz_item,bz_sales')

```

**数据样例**

         ts_code  end_date    bz_item       bz_sales       bz_profit bz_cost curr_type
    0  000627.SZ  20171231    其他产品      1.847507e+08      None    None       CNY
    1  000627.SZ  20171231    其他主营业务  1.847507e+08      None    None       CNY
    2  000627.SZ  20171231    聚丙烯        6.629111e+07      None    None       CNY
    3  000627.SZ  20171231    原料药产品    2.685909e+08      None    None       CNY
    4  000627.SZ  20171231    保险业务      5.288595e+10      None    None       CNY