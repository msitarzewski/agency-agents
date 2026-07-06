## 公募基金公司
----

接口：fund_company
描述：获取公募基金管理人列表
积分：用户需要1500积分才可以调取，一次可以提取全部数据。具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

无，可提取全部


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
name | str | Y | 基金公司名称
shortname | str | Y | 简称
short_enname | str | N | 英文缩写
province | str | Y | 省份
city | str | Y | 城市
address | str | Y | 注册地址
phone | str | Y | 电话
office | str | Y | 办公地址
website | str | Y | 公司网址
chairman | str | Y | 法人代表
manager | str | Y | 总经理
reg_capital | float | Y | 注册资本
setup_date | str | Y | 成立日期
end_date | str | Y | 公司终止日期
employees | float | Y | 员工总数
main_business | str | Y | 主要产品及业务
org_code | str | Y | 组织机构代码
credit_code | str | Y | 统一社会信用代码

**接口示例**

```python

pro = ts.pro_api()

df = pro.fund_company()

```

**数据示例**

                      name                   shortname          province   city  \
	0           北京广能投资基金管理有限公司        广能基金       北京    北京市   
	1               平安银行股份有限公司        平安银行       广东    深圳市   
	2               宏源证券股份有限公司        宏源证券       新疆  乌鲁木齐市   
	3            陕西省国际信托股份有限公司         陕国投       陕西    西安市   
	4               东北证券股份有限公司        东北证券       吉林    长春市   
	5               国元证券股份有限公司        国元证券       安徽    合肥市   
	6               国海证券股份有限公司        国海证券       广西    桂林市   
	7               广发证券股份有限公司        广发证券       广东    广州市   
	8               长江证券股份有限公司        长江证券       湖北    武汉市   
	9           上海浦东发展银行股份有限公司        浦发银行       上海    上海市   
	10              东方金钰股份有限公司        东方金钰       湖北    鄂州市   
	11              国金证券股份有限公司        国金证券       四川    成都市   
