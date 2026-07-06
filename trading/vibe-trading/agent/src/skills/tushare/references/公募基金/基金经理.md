## 基金经理
----

接口：fund_manager
描述：获取公募基金经理数据，包括基金经理简历等数据
限量：单次最大5000，支持分页提取数据
积分：用户有500积分可获取数据，2000积分以上可以提高访问频次

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ts_code | str | N | 基金代码，支持多只基金，逗号分隔
ann_date | str | N | 公告日期，格式：YYYYMMDD
name | str | N | 基金经理姓名
offset | intint | N | 开始行数
limit | int | N | 每页行数

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 基金代码
ann_date | str | Y | 公告日期
name | str | Y | 基金经理姓名
gender | str | Y | 性别
birth_year | str | Y | 出生年份
edu | str | Y | 学历
nationality | str | Y | 国籍
begin_date | str | Y | 任职日期
end_date | str | Y | 离任日期
resume | str | Y | 简历

<br>
<br>

**代码示例**

```python
#初始接口
pro = ts.pro_api()

#单只基金
df = pro.fund_manager(ts_code='150018.SZ')

#多只基金
df = pro.fund_manager(ts_code='150018.SZ,150008.SZ')

```

<br>
<br>

**数据示例**

		ts_code  ann_date   name  gender birth_year edu nationality begin_date  end_date                                             resume
	0  150018.SZ  20100508   周毅      M       None  硕士          美国   20100507      None  CFA，硕士学位；毕业于北京大学，美国南卡罗莱纳大学，美国约翰霍普金斯大学。曾任美国普华永道...
	1  150018.SZ  20190831   张凯      M       None  硕士          中国   20190829      None  CFA，硕士学位，毕业于清华大学。2009年7月加盟银华基金管理有限公司，从事量化策略研发和...
	2  150018.SZ  20100927  路志刚      M       1969  博士          中国   20100507  20100927  暨南大学金融学博士。曾任广东建设实业集团公司财务主管，广州证券有限公司发行部、营业部经理，金...