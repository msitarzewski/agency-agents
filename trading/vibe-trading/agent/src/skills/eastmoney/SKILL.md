---
name: eastmoney
category: data-source
description: 东方财富（Eastmoney）免费免鉴权数据接口，覆盖资金流向、龙虎榜、融资融券、大宗交易、股东户数、限售解禁、行业概念板块、券商研报、财经新闻、美股/港股三大报表+主要指标、全市场选股与代码搜索。所有请求经共享 IP 限速层节流（东财按源 IP 限流并临时封禁突发请求），通过 Vibe-Trading 工具直接调用，无需 token。
---
# Eastmoney（东方财富）

## 概述

东方财富对外开放了一批免费、免鉴权的行情与披露接口（push2 / push2his / datacenter-web / reportapi / search-api）。这些接口由 Vibe-Trading 内置工具封装，统一返回 `{"ok": true/false, ...}` JSON 信封，覆盖 A 股 / 港股 / 美股的资金面、披露面、舆情面与基本面数据。本技能是上述接口的**索引页**：每个接口的端点 URL、入参、返回字段写在 `references/` 下；调用范例写在 `scripts/` 下。

> **限速红线**：东方财富按**源 IP** 限流，并会临时封禁突发请求。所有工具内部已经过共享 per-host 节流层（`backtest.loaders._http`），切勿绕过工具直接对端点发起裸 HTTP 突发请求。可用环境变量 `VIBE_TRADING_EASTMONEY_MIN_INTERVAL` 调整最小请求间隔（默认 1.0 秒）。

## 快速上手

这些接口已注册为 Vibe-Trading 工具，直接以工具名调用即可，无需安装 SDK、无需 token：

```python
from src.tools.fund_flow_tool import FundFlowTool

# 主力 / 超大单 / 大单 / 中单 / 小单 净流入（近 30 日）
print(FundFlowTool().execute(codes=["600519.SH", "00700.HK"], period="daily", days=30))
```

底层共享客户端 `backtest.loaders.eastmoney_client` 负责 `secid` 解析与限速 GET：

```python
from backtest.loaders.eastmoney_client import resolve_secid, get_json

resolve_secid("600519.SH")   # -> "1.600519"
resolve_secid("00700.HK")    # -> "116.00700"
resolve_secid("AAPL.US")     # -> "105.AAPL"（经 suggest 端点解析并进程内缓存）
```

## 参数格式说明

- **代码（symbol）**：`<code>.<exchange>` 形式，交易所后缀大写。A 股 `600519.SH` / `000001.SZ` / `830799.BJ`，港股 `00700.HK`（零填充至 5 位），美股 `AAPL.US`。
- **secid**：东财内部寻址 `<market>.<code>`。SH=1，SZ/BJ=0，HK=116，美股 NASDAQ=105 / NYSE=106 / AMEX=107（美股 market 前缀由 suggest 端点解析）。
- **日期**：datacenter `filter` 用 `YYYY-MM-DD`；kline `beg`/`end` 用 `YYYYMMDD`。
- **返回**：统一 JSON 字符串信封，成功 `{"ok": true, "market", "source": "eastmoney", "data": {...}}`，失败 `{"ok": false, "error": ...}`。单个失败 symbol 以 per-symbol error 上报，不中断批次。

> 链接约定：本文档内所有指向 `references/` 的链接均以**技能名前缀** `eastmoney/references/...` 书写。`read_file` 工具以 `skills/` 为根解析路径，省略前缀会读取失败。

## python 脚本示例

- [资金流向 + 板块联动研究](eastmoney/scripts/fund_flow_example.py)
- [龙虎榜 + 大宗交易 + 融资融券披露面研究](eastmoney/scripts/disclosure_example.py)
- [研报舆情 + 美股/港股财报基本面研究](eastmoney/scripts/fundamentals_example.py)
- [代码搜索 + 全市场选股](eastmoney/scripts/screen_search_example.py)

## 接口列表

### 资金面

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `get_fund_flow` | [资金流向](eastmoney/references/资金面/资金流向.md) | A股/港股/美股 | 主力/超大单/大单/中单/小单净流入，日线历史或当日分钟线 |

### 龙虎榜

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `get_dragon_tiger` | [龙虎榜](eastmoney/references/龙虎榜/龙虎榜.md) | A股 | 某交易日全市场上榜个股 + 指定个股的买卖席位排名 |

### 参考数据（披露面）

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `get_margin_trading` | [融资融券](eastmoney/references/参考数据/融资融券.md) | A股 | 个股每日融资余额/融资买入/融券余额/RZRQ 合计 |
| `get_block_trades` | [大宗交易](eastmoney/references/参考数据/大宗交易.md) | A股 | 逐笔成交价/量/额、相对收盘折溢价、买卖营业部 |
| `get_shareholder_count` | [股东户数](eastmoney/references/参考数据/股东户数.md) | A股 | 各报告期股东户数、环比变动、户均持股 |
| `get_lockup_expiry` | [限售解禁](eastmoney/references/参考数据/限售解禁.md) | A股 | 个股全历史解禁表，或全市场未来 N 日解禁日历 |

### 板块

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `get_sector_info` | [行业概念板块](eastmoney/references/板块/行业概念板块.md) | A股 | 个股所属行业/概念板块（membership）或行业板块按涨幅排名（ranking） |

### 研报舆情

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `get_research_reports` | [券商研报](eastmoney/references/研报舆情/券商研报.md) | A股 | 券商研报列表（标题/机构/分析师/评级/EPS·PE 预测）+ 同花顺一致预期 EPS |
| `get_stock_news` | [财经新闻](eastmoney/references/研报舆情/财经新闻.md) | A股/港股/美股 | 个股新闻或全市场财经快讯（A 股走东财，美/港走 Yahoo） |

### 财务报表（美股 / 港股）

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `get_financial_statements` | [三大报表与主要指标](eastmoney/references/财务报表/三大报表与主要指标.md) | 美股/港股(东财)·A股(新浪) | 资产负债表/利润表/现金流量表/主要指标（GMAININDICATOR） |

### 选股检索

| 工具 | 标题(详细文档) | 市场 | 描述 |
| ---- | -------------- | ---- | ---- |
| `screen_market` | [全市场选股](eastmoney/references/选股检索/全市场选股.md) | A股/美股/港股 | 全市场按涨跌幅/成交量/成交额/换手率排名取 top N |
| `search_symbol` | [代码搜索](eastmoney/references/选股检索/代码搜索.md) | 多市场 | 名称/代码片段解析为候选 symbol + 市场（东财 suggest + Yahoo + SEC CIK） |
