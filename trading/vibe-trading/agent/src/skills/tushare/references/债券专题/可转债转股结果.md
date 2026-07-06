## 可转债转股结果
----

接口：cb_share
描述：获取可转债转股结果
限量：单次最大2000，总量不限制
权限：用户需要至少2000积分才可以调取，但有流量控制，5000积分以上频次相对较高，积分越多权限越大，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | Y | 转债代码，支持多值输入
ann_date | str | Y | 公告日期（YYYYMMDD格式，下同）
start_date | str | N | 公告开始日期
end_date | str | N | 公告结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 债券代码
bond_short_name | str | Y | 债券简称
publish_date | str | Y | 公告日期
end_date | str | Y | 统计截止日期
issue_size | float | Y | 可转债发行总额
convert_price_initial | float | Y | 初始转换价格
convert_price | float | Y | 本次转换价格
convert_val | float | Y | 本次转股金额
convert_vol | float | Y | 本次转股数量
convert_ratio | float | Y | 本次转股比例
acc_convert_val | float | Y | 累计转股金额
acc_convert_vol | float | Y | 累计转股数量
acc_convert_ratio | float | Y | 累计转股比例
remain_size | float | Y | 可转债剩余金额
total_shares | float | Y | 转股后总股本

<br>
<br>


**接口示例**

```python

pro = ts.pro_api(your token)
#获取可转债转股结果
df = pro.cb_share(ts_code="113001.SH,110027.SH",fields="ts_code,end_date,convert_price,convert_val,convert_ratio,acc_convert_ratio")

```

<br>
<br>

**数据示例**

			ts_code    end_date convert_price   convert_val convert_ratio acc_convert_ratio
	0    110027.SH  2015-02-16       12.0000  117572928.00      2.939323           99.9126
	1    110027.SH  2015-02-13       12.0000  521211288.00     13.030282           96.9733
	2    110027.SH  2015-02-12       12.0000  486077580.00     12.151940           83.9430
	3    110027.SH  2015-02-11       12.0000  304362204.00      7.609055           71.7910
	4    110027.SH  2015-02-10       12.0000  334752476.00      8.368812           64.1820
	..         ...         ...           ...           ...           ...               ...
	244  113001.SH  2010-12-10        3.7800       5998.86      0.000015            0.0002
	245  113001.SH  2010-12-09        3.7800       5998.86      0.000015            0.0002
	246  113001.SH  2010-12-06        3.7800      18994.50      0.000047            0.0002
	247  113001.SH  2010-12-03        3.7800      12991.86      0.000032            0.0001
	248  113001.SH  2010-12-02        3.7800      33982.20      0.000085            0.0001
