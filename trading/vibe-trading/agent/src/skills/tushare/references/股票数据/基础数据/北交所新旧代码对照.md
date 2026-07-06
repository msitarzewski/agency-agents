## 北交所新旧代码对照表
----

接口：bse_mapping
描述：获取北交所股票代码变更后新旧代码映射表数据
限量：单次最大1000条（本接口总数据量300以内）
积分：120积分即可调取

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
o_code | str | N | 旧代码
n_code | str | N | 新代码

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
name | str | Y | 股票名称
o_code | str | Y | 原代码
n_code | str | Y | 新代码
list_date | str | Y | 上市日期

<br>
<br>

**接口示例**

```python

#获取方大新材新旧代码对照数据
df = pro.bse_mapping(o_code='838163.BJ')


#获取全部变更的股票代码对照表
df = pro.bse_mapping()


```


<br>
<br>

**数据示例**

		  name     o_code   n_code    list_date
	0  方大新材  838163.BJ  920163.BJ  20200727