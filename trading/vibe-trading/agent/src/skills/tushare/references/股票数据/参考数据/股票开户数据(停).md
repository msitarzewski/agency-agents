## 股票账户开户数据
----

接口：stk_account
描述：获取股票账户开户数据，统计周期为一周
积分：600积分可调取，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13) 

注：此数据官方已经停止更新。

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
date | str | N | 日期
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
date | str | Y | 统计周期
weekly_new | float | Y | 本周新增（万）
total | float | Y | 期末总账户数（万）
weekly_hold | float | Y | 本周持仓账户数（万）
weekly_trade | float | Y | 本周参与交易账户数（万）


<br>
<br>

**接口使用**

```pyhton

pro = ts.pro_api()

df = pro.stk_account(start_date='20180101', end_date='20181231')

```

<br>
<br>


**数据示例**

        date      weekly_new     total weekly_hold weekly_trade
	0   20181228       20.81  14650.44        None         None
	1   20181221       21.04  14629.63        None         None
	2   20181214       21.21  14608.59        None         None
	3   20181207       22.28  14587.38        None         None
	4   20181130       23.56  14565.10        None         None
	5   20181123       24.16  14541.54        None         None
	6   20181116       24.57  14517.38        None         None
	7   20181109       24.11  14492.81        None         None
	8   20181102       23.97  14468.70        None         None
	9   20181026       26.00  14444.73        None         None
	10  20181019       24.13  14418.73        None         None
	11  20181012       25.30  14394.60        None         None
	12  20180928       20.09  14369.30        None         None
	13  20180921       23.24  14349.21        None         None
	14  20180914       24.08  14325.97        None         None
	15  20180907       23.58  14301.89        None         None
	16  20180831       24.06  14278.31        None         None
	17  20180824       23.12  14254.25        None         None
	18  20180817       23.04  14231.12        None         None
	19  20180810       23.96  14208.09        None         None
	20  20180803       24.22  14184.12        None         None
	
<br>
<br>

数据说明：从2017年2月10日开始，中国证券登记结算公司停止了发布本周持仓账户数和本周交易账户数；另外，2015年5月8日之前的数据结构也不同，具体请参阅[股票开户旧数据](https://tushare.pro/document/2?doc_id=165)接口。
