## 上市公司基本信息
----

接口：stock_company，可以通过[**数据工具**](https://tushare.pro/webclient/)调试和查看数据。
描述：获取上市公司基础信息，单次提取4500条，可以根据交易所分批提取
积分：用户需要至少120积分才可以调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

**输入参数**

名称 | 类型 | 必须 | 描述
--- | ---- | ---- | ----
ts_code | str | N | 股票代码
exchange | str | N | 交易所代码 ，SSE上交所 SZSE深交所 BSE北交所



**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
ts_code | str | Y | 股票代码
com_name | str | Y | 公司全称
com_id | str | Y | 统一社会信用代码
exchange | str | Y | 交易所代码
chairman | str | Y | 法人代表
manager | str | Y | 总经理
secretary | str | Y | 董秘
reg_capital | float | Y | 注册资本(万元)
setup_date | str | Y | 注册日期
province | str | Y | 所在省份
city | str | Y | 所在城市
introduction | str | N | 公司介绍
website | str | Y | 公司主页
email | str | Y | 电子邮件
office | str | N | 办公室
employees | int | Y | 员工人数
main_business | str | N | 主要业务及产品
business_scope | str | N | 经营范围


**接口示例**

```python
pro = ts.pro_api()

#或者
#pro = ts.pro_api('your token')

df = pro.stock_company(exchange='SZSE', fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')

```

**数据示例**

					ts_code chairman manager secretary   reg_capital setup_date province  \
	0     000001.SZ      谢永林     胡跃飞        周强  1.717041e+06   19871222       广东   
	1     000002.SZ       郁亮     祝九胜        朱旭  1.103915e+06   19840530       广东   
	2     000003.SZ      马钟鸿     马钟鸿        安汪  3.334336e+04   19880208       广东   
	3     000004.SZ      李林琳     李林琳       徐文苏  8.397668e+03   19860505       广东   
	4     000005.SZ       丁芃     郑列列       罗晓春  1.058537e+05   19870730       广东   
	5     000006.SZ      赵宏伟     朱新宏        杜汛  1.349995e+05   19850525       广东   
	6     000007.SZ      智德宇     智德宇       陈伟彬  3.464480e+04   19830311       广东   
	7     000008.SZ      王志全      钟岩       王志刚  2.818330e+05   19891011       北京   
	8     000009.SZ      陈政立     陈政立       郭山清  2.149345e+05   19830706       广东   
	9     000010.SZ       曾嵘     李德友       金小刚  8.198547e+04   19881231       广东   
	10    000011.SZ      刘声向     王航军       范维平  5.959791e+04   19830117       广东   
	11    000012.SZ       陈琳      王健       杨昕宇  2.863277e+05   19840910       广东   
	12    000013.SZ      厉怒江     阮克竖       刘渝敏  3.033550e+04   19920114       广东   
	13    000014.SZ       陈勇      温毅        王凡  2.017052e+04   19870727       广东   
	14    000015.SZ      宿南南      马骧       蒋孝安  1.598761e+05   19880408       广东   
	15    000016.SZ      刘凤喜      周彬       吴勇军  2.407945e+05   19801001       广东  