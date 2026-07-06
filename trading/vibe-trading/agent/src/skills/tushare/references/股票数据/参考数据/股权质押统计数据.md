## 股权质押统计数据
----

接口：pledge_stat
描述：获取股票质押统计数据
限量：单次最大1000
积分：用户需要至少500积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 股票代码
end_date | str | N | 截止日期


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | TS代码
end_date | str | Y | 截止日期
pledge_count | int | Y | 质押次数
unrest_pledge | float | Y | 无限售股质押数量（万）
rest_pledge | float | Y | 限售股份质押数量（万）
total_share | float | Y | 总股本
pledge_ratio | float | Y | 质押比例


**接口使用**
```pyhton
pro = ts.pro_api()
#或者
#pro = ts.pro_api('your token')


df = pro.pledge_stat(ts_code='000014.SZ')

```

或者

```python

df = pro.query('pledge_stat', ts_code='000014.SZ')

```

**数据示例**

				 ts_code  end_date  pledge_count  unrest_pledge  rest_pledge  \
	0    000014.SZ  20180928            23          63.16          0.0   
	1    000014.SZ  20180921            24          63.17          0.0   
	2    000014.SZ  20180914            24          63.17          0.0   
	3    000014.SZ  20180907            28          63.69          0.0   
	4    000014.SZ  20180831            28          63.69          0.0   
	5    000014.SZ  20180824            29          64.74          0.0   
	6    000014.SZ  20180817            29          64.74          0.0   
	7    000014.SZ  20180810            29          64.74          0.0   
	8    000014.SZ  20180803            29          64.74          0.0   
	9    000014.SZ  20180727            29          64.74          0.0   
	10   000014.SZ  20180720            29          64.74          0.0   
	11   000014.SZ  20180713            29          64.74          0.0   
	12   000014.SZ  20180706            30          64.77          0.0   
	13   000014.SZ  20180629            30          64.77          0.0   
	14   000014.SZ  20180622            30          64.77          0.0   
	15   000014.SZ  20180615            28          66.50          0.0 