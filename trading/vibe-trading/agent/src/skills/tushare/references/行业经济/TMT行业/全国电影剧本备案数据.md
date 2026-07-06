## 全国电影剧本备案数据
----

接口：film_record
描述：获取全国电影剧本备案的公示数据
限量：单次最大500，总量不限制
数据权限：用户需要至少120积分才可以调取，积分越多调取频次越高，具体请参阅[积分获取办法](https://tushare.pro/document/1?doc_id=13)  

<br>
<br>

**输入参数**

名称 | 类型  | 必选 | 描述
---- | ----- | ---- | ----
ann_date | str | N | 公布日期 （至少输入一个参数，格式：YYYYMMDD，日期不连续，定期公布）
start_date | str | N | 开始日期
end_date | str | N | 结束日期

<br>
<br>

**输出参数**

名称 | 类型 | 默认显示 | 描述
--- | ---- | ---- | ----
rec_no | str | Y | 备案号
film_name | str | Y | 影片名称
rec_org | str | Y | 备案单位
script_writer | str | Y | 编剧
rec_result | str | Y | 备案结果
rec_area | str | Y | 备案地（备案时间）
classified | str | Y | 影片分类
date_range | str | Y | 备案日期区间
ann_date | str | Y | 备案结果发布时间


<br>
<br>


**接口使用**

```python
pro = ts.pro_api()
#或者
#pro = ts.pro_api('your token')

df = pro.film_record(start_date='20181014', end_date='20181214')
```

<br>
<br>

**数据示例**


<img src="http://tushare.org/img/film_record.png">