## K线数据（OHLCV）
----

接口：GET /api/v5/market/candles
描述：获取K线数据，支持从1分钟到1月多种周期。最多返回1440条历史数据。可通过 after/before 参数翻页获取更早数据。
限频：40次/2s

**输入参数**

| 名称 | 类型 | 必选 | 描述 |
| ---- | ---- | ---- | ---- |
| instId | str | Y | 交易产品ID，如 `BTC-USDT` |
| bar | str | N | K线周期，默认 `1m`。可选：`1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M` |
| after | str | N | 请求此时间戳之前的数据（毫秒），用于翻页 |
| before | str | N | 请求此时间戳之后的数据（毫秒） |
| limit | str | N | 返回条数，默认 100，最大 300 |

**输出参数**

返回二维数组，每条数据按以下顺序排列：

| 索引 | 描述 |
| ---- | ---- |
| 0 | 开盘时间（毫秒时间戳） |
| 1 | 开盘价（Open） |
| 2 | 最高价（High） |
| 3 | 最低价（Low） |
| 4 | 收盘价（Close） |
| 5 | 成交量（币） |
| 6 | 成交额（计价货币） |
| 7 | 成交额（报价货币） |
| 8 | K线状态：`0`=未完结，`1`=已完结 |

**接口示例**

```python
import requests
import pandas as pd

BASE_URL = "https://www.okx.com/api/v5"

# 获取 BTC-USDT 日线，最近30根
resp = requests.get(f"{BASE_URL}/market/candles", params={
    "instId": "BTC-USDT",
    "bar": "1D",
    "limit": "30"
})
candles = resp.json()["data"]

# 转为 DataFrame
columns = ["ts", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm"]
df = pd.DataFrame(candles, columns=columns)
df["ts"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
for col in ["open", "high", "low", "close", "vol"]:
    df[col] = df[col].astype(float)
print(df[["ts", "open", "high", "low", "close", "vol"]].head())

# 获取 ETH-USDT 4小时K线
resp = requests.get(f"{BASE_URL}/market/candles", params={
    "instId": "ETH-USDT",
    "bar": "4H",
    "limit": "50"
})
```

**数据样例**

```json
{
  "code": "0",
  "data": [
    ["1773763200000", "73915.5", "74800", "71966", "72144.3", "5129.27", "377618988.24", "377618988.24", "0"],
    ["1773676800000", "73269.1", "76011.8", "73158", "73917.4", "8631.72", "642101158.54", "642101158.54", "1"],
    ["1773590400000", "71478.1", "74500", "71300", "73269.1", "8461.09", "620450708.74", "620450708.74", "1"]
  ]
}
```
