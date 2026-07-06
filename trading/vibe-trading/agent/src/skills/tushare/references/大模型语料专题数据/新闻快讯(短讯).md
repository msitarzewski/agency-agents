## 新闻快讯
----

接口：news
描述：获取主流新闻网站的快讯新闻数据,提供超过6年以上历史新闻。
限量：单次最大1500条新闻，可根据时间参数循环提取历史
积分：本接口需单独开权限（跟积分没关系），具体请参阅[权限说明](https://tushare.pro/document/1?doc_id=290) 

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
start_date | datetime | Y | 开始日期(格式：2018-11-20 09:00:00）
end_date | datetime | Y | 结束日期
src | str | Y | 新闻来源 见下表

<br>

数据源

| 来源名称 | src标识 | 描述 |
| -------- | -------- | -------- |
| 新浪财经     | sina     | 获取新浪财经实时资讯     |
| 华尔街见闻 | wallstreetcn | 华尔街见闻快讯 |
| 同花顺 | 10jqka | 同花顺财经新闻 |
| 东方财富 | eastmoney | 东方财富财经新闻
| 云财经 | yuncaijing | 云财经新闻
| 凤凰新闻 | fenghuang | 凤凰新闻
| 金融界 | jinrongjie | 金融界新闻
| 财联社 | cls| 财联社快讯
| 第一财经 | yicai | 第一财经快讯


<br>
<br>
日期输入说明： 
<br><br>

* 时间参数格式例子：start_date='2018-11-20 09:00:00', end_date='2018-11-20 22:05:03' 


<br>
<br>


**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
datetime | str | Y | 新闻时间
content | str | Y | 内容
title | str | Y | 标题
channels | str | N | 分类


<br><br>

**接口调用**

```python

pro = ts.pro_api()

df = pro.news(src='sina', start_date='2018-11-21 09:00:00', end_date='2018-11-22 10:10:00')

```

<br><br>

**数据样例**

<img src="https://tushare.pro/files/img/news_sp.png">

<br><br>

更多数据预览，请点击网站头部菜单的[资讯数据](https://tushare.pro/news)。