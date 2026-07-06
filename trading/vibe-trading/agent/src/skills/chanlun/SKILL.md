---
name: chanlun
description: 基于缠论（缠中说禅）的形态识别引擎，使用czsc库自动检测K线分型、笔、中枢，并生成一买/一卖/二买/二卖/三买/三卖等买卖点信号。支持多周期分析和形态分类（3/5/7/9/11笔形态）。
category: strategy
---
# 缠论形态识别

## 用途

基于**缠中说禅**理论的价格形态识别。缠论是一套完全基于价格结构的技术分析方法，核心链路：

```
原始K线 → 去包含处理 → 分型识别 → 笔检测 → 中枢构建 → 买卖点判定
```

适用于任何有 OHLCV 数据的市场（A股、加密货币、期货等）。

## 核心概念

| 概念 | 说明 | 详细文档 |
| --- | --- | --- |
| 分型（FX） | 顶分型：中间K线最高；底分型：中间K线最低 | [分型](references/核心概念/分型.md) |
| 笔（BI） | 相邻顶底分型之间的一段走势，最小单元 | [笔](references/核心概念/笔.md) |
| 中枢（ZS） | 至少3笔构成的价格重叠区域，趋势的核心 | [中枢](references/核心概念/中枢.md) |

## 买卖点体系

| 买卖点 | 含义 | 详细文档 |
| --- | --- | --- |
| 一买/一卖 | 趋势结束后的第一个反转信号（背驰点） | [一买一卖](references/买卖点/一买一卖.md) |
| 二买/二卖 | 一买/一卖后回调不破底/顶的确认信号 | [二买二卖](references/买卖点/二买二卖.md) |
| 三买/三卖 | 中枢上移/下移后回调不进入前中枢的信号 | [三买三卖](references/买卖点/三买三卖.md) |

## 依赖安装

```bash
pip install czsc requests pandas
```

## 快速上手

```python
from czsc import CZSC, RawBar, Freq
from datetime import datetime

# 准备 RawBar 列表（需按时间正序排列）
bars = [
    RawBar(symbol="BTC-USDT", id=0, dt=datetime(2026,1,1),
           freq=Freq.D, open=70000, close=71000,
           high=72000, low=69000, vol=1000, amount=71000000),
    # ... 更多K线
]

# 创建分析器，自动检测分型/笔/中枢
c = CZSC(bars)

# 访问结果
print(c.bi_list)    # 已完成的笔
print(c.bars_ubi)   # 未完成笔中的K线
```

## 可用信号函数（czsc.signals.cxt）

czsc 内置 43 个缠论信号函数，核心如下：

| 函数 | 说明 | 类型 |
| --- | --- | --- |
| `cxt_first_buy_V221126` | 一买信号 | 买卖点 |
| `cxt_first_sell_V221126` | 一卖信号 | 买卖点 |
| `cxt_second_bs_V230320` | 均线辅助二买二卖 | 买卖点 |
| `cxt_third_bs_V230318` | 均线辅助三买三卖 | 买卖点 |
| `cxt_third_buy_V230228` | 笔三买辅助 | 买卖点 |
| `cxt_double_zs_V230311` | 两中枢组合判断BS1 | 中枢 |
| `cxt_three_bi_V230618` | 三笔形态分类 | 形态 |
| `cxt_five_bi_V230619` | 五笔形态分类 | 形态 |
| `cxt_seven_bi_V230620` | 七笔形态分类 | 形态 |
| `cxt_nine_bi_V230621` | 九笔形态分类 | 形态 |
| `cxt_eleven_bi_V230622` | 十一笔形态分类 | 形态 |
| `cxt_bi_base_V230228` | BI基础信号（方向/转折） | 基础 |
| `cxt_bi_end_V230312` | MACD辅助笔结束 | 辅助 |
| `cxt_range_oscillation_V230620` | 区间震荡判断 | 辅助 |
| `cxt_zhong_shu_gong_zhen_V221221` | 大小级别中枢共振 | 中枢 |

## 信号约定

- 信号引擎输出：`1`=做多，`-1`=做空，`0`=观望
- 做多条件：一买信号 或 三笔向上盘背 或 五笔类一买
- 做空条件：一卖信号 或 三笔向下盘背 或 五笔类一卖
- 中枢辅助：价格在中枢下沿附近做多优势，上沿附近做空优势

## 数据格式

czsc 接受 `List[RawBar]`，每个 RawBar 包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| symbol | str | 标的代码 |
| id | int | 序号（从0开始） |
| dt | datetime | 时间 |
| freq | Freq | 频率：`Freq.F1/F5/F15/F30/F60/D/W/M` |
| open | float | 开盘价 |
| close | float | 收盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| vol | float | 成交量 |
| amount | float | 成交额 |

## 实现方式

使用 [czsc](https://github.com/waditu/czsc) 库（v0.9.68+），基于纯 Python 实现（可选 Rust 加速后端）。支持增量更新，适合实时分析。
