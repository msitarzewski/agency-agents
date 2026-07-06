## 指数K线
----

接口：GET /api/v5/market/index-candles
描述：获取指数的K线数据，用于分析基准价格走势。
限频：20次/2s

**输入参数**

| 名称 | 类型 | 必选 | 描述 |
| ---- | ---- | ---- | ---- |
| instId | str | Y | 指数ID，如 `BTC-USD` |
| bar | str | N | K线周期，默认 `1m`。可选：`1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M` |
| after | str | N | 请求此时间戳之前的数据（毫秒） |
| before | str | N | 请求此时间戳之后的数据（毫秒） |
| limit | str | N | 返回条数，默认 100，最大 100 |

**输出参数**

返回二维数组，每条数据：

| 索引 | 描述 |
| ---- | ---- |
| 0 | 开盘时间（毫秒时间戳） |
| 1 | 开盘价 |
| 2 | 最高价 |
| 3 | 最低价 |
| 4 | 收盘价 |
| 5 | K线状态：`0`=未完结，`1`=已完结 |

**接口示例**

```python
import requests
import pandas as pd

BASE_URL = "https://www.okx.com/api/v5"

# 获取 BTC 指数日K
resp = requests.get(f"{BASE_URL}/market/index-candles", params={
    "instId": "BTC-USD",
    "bar": "1D",
    "limit": "30"
})
candles = resp.json()["data"]

columns = ["ts", "open", "high", "low", "close", "confirm"]
df = pd.DataFrame(candles, columns=columns)
df["ts"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
for col in ["open", "high", "low", "close"]:
    df[col] = df[col].astype(float)
print(df[["ts", "open", "high", "low", "close"]].head())
```
