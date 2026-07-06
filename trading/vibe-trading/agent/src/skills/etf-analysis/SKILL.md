---
name: etf-analysis
description: "ETF分析：产品筛选、费率对比、跟踪误差、流动性评估、策略应用与中国市场ETF量化配置框架。"
category: asset-class
---

# ETF 分析 Skill

## 定位

ETF（交易所交易基金）是被动投资与资产配置的核心工具。本 skill 覆盖 ETF 产品分析、选择方法论、策略应用、中国市场特色以及数据驱动的量化分析方法，为构建基于 ETF 的量化策略与组合提供完整框架。

---

## 1. ETF 产品分类

### 1.1 按标的资产分类

| 类型 | 代表产品 | 特点 |
|------|---------|------|
| **宽基 ETF** | 沪深300ETF (510300)、中证500ETF (510500)、创业板ETF (159915)、科创50ETF (588000) | 流动性最好，交易成本最低，适合核心仓位 |
| **行业 ETF** | 消费ETF (159928)、医疗ETF (512170)、半导体ETF (512480)、银行ETF (512800) | 行业轮动工具，持仓集中度高 |
| **主题 ETF** | 新能源ETF (516160)、碳中和ETF、元宇宙ETF | 主题炒作属性强，生命周期短 |
| **策略ETF / Smart Beta** | 红利ETF (510880)、低波ETF、质量ETF、动量ETF | 因子暴露明确，费率通常略高于宽基 |
| **商品 ETF** | 黄金ETF (518880)、豆粕ETF (159985)、原油ETF (162411) | 实物/期货支撑，注意展期损耗 |
| **债券 ETF** | 国债ETF (511010)、信用债ETF、可转债ETF (511380) | 利率敏感，久期管理关键 |
| **跨境 ETF (QDII)** | 纳指ETF (159632)、标普500ETF (513500)、日经225ETF (513880) | 汇率风险+溢价风险双重叠加 |
| **货币 ETF** | 华宝添益 (511990)、银华日利 (511880) | T+0 申赎，流动性管理工具 |

### 1.2 结构类型

- **普通 ETF**：场内交易，实物申赎（一篮子股票换购），折溢价有套利机制自动收敛
- **LOF（上市开放式基金）**：场内外均可交易，折溢价套利路径相同但效率略低
- **ETF 联接基金**：场外渠道购买的 ETF 替代品，T+1 申赎，无折溢价，适合定投
- **杠杆/反向 ETF**：日内恒定杠杆，长期持有有衰减效应（见第 3.4 节）

---

## 2. ETF 核心指标

### 2.1 跟踪误差（Tracking Error）

衡量 ETF 复制指数能力的最核心指标。

```
日跟踪误差 = std(ETF日收益率 - 指数日收益率)
年化跟踪误差 = 日跟踪误差 × √252
```

**评级标准（A股宽基ETF）**：
- 优秀：年化跟踪误差 < 0.2%
- 合格：0.2% ~ 0.5%
- 较差：> 0.5%

**跟踪误差来源**：
1. 管理费和托管费（持续拖累，每日计提）
2. 分红处理时机（分红再投资延迟）
3. 成分股纳入/剔除时的买卖冲击
4. 现金仓位（申赎带来的暂时性现金拖累）
5. 停牌股处理（用替代品或现金替代）
6. 指数编制方法（全复制 vs 抽样复制）

### 2.2 信息比率（Information Ratio）

```
IR = (ETF年化收益率 - 指数年化收益率) / 年化跟踪误差
```

对 ETF 来说 IR 通常为负（因费率拖累），IR 越接近 0 越好。

### 2.3 折溢价率

```
折溢价率 = (ETF市价 - ETF净值IOPV) / ETF净值IOPV × 100%
```

- **正溢价**：市价 > 净值，套利者卖出 ETF / 申购一篮子股票换购，溢价收敛
- **负折价**：市价 < 净值，套利者买入 ETF / 赎回一篮子股票，折价收敛
- **异常溢价场景**：跨境 QDII ETF（额度限制导致持续溢价）、停牌股比例高的行业 ETF

### 2.4 流动性指标

| 指标 | 含义 | 参考阈值 |
|------|------|--------|
| 日均成交额 | 买卖方便程度 | 宽基 > 1亿，行业 > 2000万 |
| 买卖价差（Spread） | 即时交易成本 | < 0.05% 为优质 |
| 盘口深度 | 单笔大额交易冲击 | 买卖各5档累计 > 500万为佳 |
| 换手率 | 活跃程度 | 过低则流动性风险高 |

### 2.5 费率体系

```
综合费率 = 管理费 + 托管费 + 指数使用费
（不含交易佣金、印花税、申赎费）
```

**长期费率影响公式**：
```
N年费率复利损耗 = (1 - 年费率)^N
例：年费率0.5% vs 0.15%，10年差距 ≈ 3.5%，20年差距 ≈ 6.8%
```

主流宽基 ETF 费率对比（2025年）：
- 华夏/易方达/南方 沪深300ETF：0.15%（管理）+ 0.05%（托管）= 0.20%
- 部分小规模宽基：0.5%+，长期持有劣势明显

### 2.6 规模与流动性评估

- **规模门槛**：
  - < 2亿：清盘风险较高，流动性差
  - 2~10亿：可正常交易，大额资金受限
  - > 10亿：流动性充足，做市商活跃
  - > 100亿：旗舰 ETF，机构首选

- **清盘风险信号**：规模持续下滑、连续90天日均规模 < 5000万

---

## 3. ETF 选择方法论

### 3.1 同类 ETF 比较框架

同一指数往往有多只 ETF，选择步骤：

```
Step 1: 规模筛选 → 剔除 < 5亿的小规模产品
Step 2: 费率比较 → 同等条件下选费率最低
Step 3: 跟踪误差 → 近1年/近3年双维度比较
Step 4: 流动性 → 日均成交额、买卖价差
Step 5: 基金公司 → 指数化投资能力、历史口碑
```

**量化评分模型**：

```python
def etf_score(etf_data: dict) -> float:
    """
    ETF 综合评分（越高越好，满分100）。

    Args:
        etf_data: 包含 scale, fee, tracking_error, avg_volume, spread 的字典

    Returns:
        综合评分 0~100
    """
    score = 0.0
    # 规模得分（30分）
    scale = etf_data['scale_billion']
    score += min(30, scale / 10 * 30)

    # 费率得分（25分）：费率越低越高分
    fee = etf_data['total_fee_pct']  # 年费率百分比
    score += max(0, 25 - fee * 50)

    # 跟踪误差得分（30分）：误差越小越高分
    te = etf_data['tracking_error_annual_pct']
    score += max(0, 30 - te * 60)

    # 流动性得分（15分）
    vol = etf_data['avg_daily_volume_million']
    score += min(15, vol / 10 * 15)

    return round(score, 2)
```

### 3.2 费率影响长期收益的量化分析

```python
import numpy as np

def fee_drag_analysis(annual_return: float, years: int, fee_rates: list[float]) -> dict:
    """
    分析不同费率对长期收益的拖累效果。

    Args:
        annual_return: 指数年化收益率（小数，如0.08）
        years: 投资年限
        fee_rates: 待比较的费率列表（小数，如[0.002, 0.005, 0.015]）

    Returns:
        各费率下的终值倍数和相对拖累字典
    """
    results = {}
    base_value = (1 + annual_return) ** years
    for fee in fee_rates:
        net_return = annual_return - fee
        end_value = (1 + net_return) ** years
        drag = (base_value - end_value) / base_value * 100
        results[f'{fee*100:.2f}%'] = {
            'end_value_multiple': round(end_value, 4),
            'drag_pct': round(drag, 2)
        }
    return results

# 示例：8% 指数收益，20年期
# fee_drag_analysis(0.08, 20, [0.002, 0.005, 0.015])
```

### 3.3 做市商质量评估

优质做市商体现在：
- **价差稳定**：波动期价差扩大幅度小（< 3倍正常水平）
- **深度充足**：盘口各档位金额均匀
- **报价连续性**：不频繁撤单重报
- **大单应对**：大额交易后价差快速恢复

评估方法：
```python
# 通过Level2数据计算有效价差
effective_spread = (ask_price - bid_price) / mid_price * 100  # 单位 %

# 价格冲击成本（Impact Cost）
# 买入N万元所需均价相对于中间价的偏离
impact_cost = (avg_buy_price - mid_price) / mid_price * 100
```

### 3.4 基金公司实力评估

| 维度 | 评估要点 |
|------|---------|
| ETF 管理规模 | 全市场排名，指数化投资专业度 |
| 跟踪误差历史 | 长期维度（3年+）稳定性 |
| 产品线完整性 | 宽基、行业、跨境覆盖广度 |
| 申赎效率 | T+0 实物申赎处理能力 |
| 做市商合作质量 | 与头部券商做市商的合作稳定性 |

国内 ETF 管理头部公司（规模口径）：华夏、易方达、华泰柏瑞、南方、嘉实、博时

---

## 4. ETF 策略应用

### 4.1 核心-卫星策略（Core-Satellite）

```
总组合 = 核心仓位（70~80%）+ 卫星仓位（20~30%）

核心仓位：宽基ETF（沪深300/中证500/全A）
  → 获取市场beta，低费率，长期持有，减少交易摩擦

卫星仓位：行业ETF/主题ETF/Smart Beta ETF
  → 增强收益，主动暴露特定因子，允许更高换手
```

**再平衡触发条件**：
- 时间触发：每季度/每半年
- 偏离触发：单一资产偏离目标权重 > 5%

### 4.2 行业轮动 ETF 策略

**动量轮动**：
```python
def sector_momentum_rotation(etf_returns: pd.DataFrame, lookback: int = 20, top_n: int = 3) -> list[str]:
    """
    基于动量的行业ETF轮动选择。

    Args:
        etf_returns: 各行业ETF日收益率 DataFrame，列为ETF代码
        lookback: 回看窗口（交易日数）
        top_n: 持有ETF数量

    Returns:
        本期持有的ETF代码列表
    """
    momentum = etf_returns.tail(lookback).sum()
    selected = momentum.nlargest(top_n).index.tolist()
    return selected
```

**宏观周期轮动**：
| 经济周期 | 推荐行业 ETF |
|---------|------------|
| 复苏期（低增长→高增长，低通胀） | 消费、科技、中小盘 |
| 过热期（高增长，高通胀） | 能源、材料、工业 |
| 滞胀期（低增长，高通胀） | 能源、公用事业、消费 |
| 衰退期（高增长→低增长） | 医疗、公用事业、债券ETF |

### 4.3 Smart Beta ETF 因子暴露分析

主要因子及对应ETF：

| 因子 | 代表ETF | 历史有效性（A股） |
|------|--------|--------------|
| 价值（低估值） | 沪深300价值ETF | 中等，受风格切换影响 |
| 红利（高股息） | 红利ETF (510880) | 较强，尤其熊市防御 |
| 低波动 | 中证低波ETF | 较强，夏普比优于宽基 |
| 质量（高ROE） | 中证质量ETF | 较强，长期复合效果好 |
| 动量 | 目前A股产品少 | 中短期有效，长期均值回归 |
| 小盘 | 中证1000ETF (512100) | 强，但流动性风险高 |

**因子暴露分析代码**：
```python
import pandas as pd
import numpy as np
from scipy import stats

def factor_exposure_analysis(etf_returns: pd.Series, factor_returns: dict[str, pd.Series]) -> pd.DataFrame:
    """
    分析ETF对各因子的暴露程度（单因子回归）。

    Args:
        etf_returns: ETF日收益率序列
        factor_returns: 各因子收益率字典 {因子名: 收益率序列}

    Returns:
        包含 beta, t_stat, r_squared 的 DataFrame
    """
    results = []
    for factor_name, factor_ret in factor_returns.items():
        aligned = pd.concat([etf_returns, factor_ret], axis=1).dropna()
        x = aligned.iloc[:, 1].values
        y = aligned.iloc[:, 0].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        results.append({
            'factor': factor_name,
            'beta': round(slope, 4),
            't_stat': round(slope / std_err, 2),
            'r_squared': round(r_value ** 2, 4),
            'p_value': round(p_value, 4)
        })
    return pd.DataFrame(results).set_index('factor')
```

### 4.4 杠杆/反向 ETF 的衰减效应

**Beta 衰减（Volatility Decay）原理**：

```
每日恒定杠杆 N 倍 → 复合效应导致长期收益 ≠ N × 指数收益

衰减量（近似）= N²(N-1)/2 × σ² × T
其中 σ 为指数日波动率，T 为持有天数
```

**数值示例**：
- 指数年化波动率 20%，日波动率 ≈ 1.26%
- 2倍杠杆ETF，持有1年：衰减损耗 ≈ 2² × (2-1)/2 × (0.2)² × 1 ≈ 4%

**适用场景**：
- 杠杆ETF：强趋势行情中的短期工具（持有 < 1个月）
- 反向ETF：市场对冲、短期下跌押注（不适合长期持有）
- **严禁**：用杠杆/反向ETF做长期配置仓位

### 4.5 ETF 套利策略

**折溢价套利**（需要有实物申赎资格，通常门槛100万份）：

```
溢价套利：
  ETF市价 > IOPV + 交易成本
  → 买入一篮子成分股 → 申购ETF份额 → 卖出ETF
  → 套利利润 ≈ 溢价率 - 冲击成本 - 佣金

折价套利：
  ETF市价 < IOPV - 交易成本
  → 买入ETF份额 → 赎回一篮子成分股 → 卖出成分股
  → 套利利润 ≈ 折价率 - 冲击成本 - 佣金
```

**跨市场套利（ETF vs 期货）**：
```
IF（沪深300股指期货）基差 = 期货价格 - 沪深300指数
当基差 > 合理基差（无风险利率×剩余期限）时：
  → 卖期货 + 买ETF（正向套利）
当基差 < 合理基差时：
  → 买期货 + 卖ETF（反向套利，需融券）
```

**统计套利（配对交易）**：
```python
# 同类ETF（如不同公司发行的沪深300ETF）之间的价差均值回归
# 价差 = 价格差 或 价格比
# 当价差偏离历史均值2个标准差时建仓，回归时平仓
spread = etf_a_price / etf_b_price
z_score = (spread - spread.rolling(60).mean()) / spread.rolling(60).std()
signal = pd.Series(0, index=z_score.index)
signal[z_score > 2] = -1   # ETF_A 相对贵，卖A买B
signal[z_score < -2] = 1   # ETF_A 相对便宜，买A卖B
```

---

## 5. 中国 ETF 市场特色

### 5.1 场内 ETF vs 场外联接基金

| 维度 | 场内 ETF | 场外联接基金 |
|------|---------|-----------|
| 购买渠道 | 证券账户，实时交易 | 银行/基金直销，T+1申赎 |
| 申赎方式 | 实物申赎（机构）或二级市场（个人） | 现金申赎 |
| 折溢价 | 存在（有套利机制） | 不存在 |
| 最小交易单位 | 100份（约10~100元） | 1元起投 |
| 费率 | 较低（管理费+交易佣金） | 略高（申购费+管理费） |
| 适合场景 | 波段操作、大额配置 | 定投、小额长期持有 |

### 5.2 跨境 ETF（QDII）特殊考量

**溢价形成原因**：
- QDII 额度限制：基金公司 QDII 额度用完后暂停申购，套利机制失效
- 汇率影响：人民币贬值时，持有境外资产的 ETF 净值上升，引发追涨
- 时差影响：A 股收盘时海外市场尚未开盘，IOPV 参考价滞后

**溢价率警戒线**：
- < 2%：正常范围，可正常配置
- 2%~5%：溢价明显，入场需谨慎，等待回落
- > 5%：高溢价，存在显著买入风险（净值回落但溢价收窄双杀）

**汇率对冲**：
- 部分 QDII ETF 提供对冲版本（如标普500对冲ETF）
- 对冲成本 ≈ 中美利差（2025年约1.5~2.5%/年），显著降低收益

### 5.3 LOF 与分级基金历史经验

**LOF（上市开放式基金）**：
- 场内外均可交易，折价套利路径：场内折价买入 → 转托管 → 场外赎回
- 转托管时间 T+2~T+3，存在净值变动风险

**分级基金（已全面转型，2020年前历史参考）**：
- A 份额：约定收益型，类似债券
- B 份额：杠杆型，与A约定收益挂钩
- 重要教训：下折机制导致B份额大幅亏损；高溢价套利被轧空
- 现状：监管要求全部转型为普通ETF，不再有新发

### 5.4 中国主要 ETF 指数体系

**宽基指数**：

| 指数 | 成分股 | 特点 |
|------|-------|------|
| 沪深300 | 沪深两市市值最大300只 | 大盘蓝筹，衍生品丰富（IF期货/300期权） |
| 中证500 | 300~800名中盘股 | 中盘成长，与300互补 |
| 中证1000 | 800~1800名小盘股 | 小盘因子，波动较大 |
| 上证50 | 沪市最大50只 | 超大盘，金融地产权重高 |
| 创业板指 | 创业板前100名 | 科技成长，波动大 |
| 科创50 | 科创板前50名 | 硬科技，上市时间短 |
| 北证50 | 北交所前50名 | 新兴市场，流动性弱 |
| 中证全指 / 万得全A | 全市场 | 最宽泛的基准 |

**指数调整规律**：
- 沪深300/中证500：每年6月和12月调整一次
- 调整前后：纳入股票涨、剔除股票跌（短期），提供事件驱动机会

---

## 6. ETF 组合构建

### 6.1 基于 ETF 的资产配置实现

**经典配置框架（可用ETF实现）**：

```
股债 60/40 中国版：
  沪深300ETF 30% + 中证500ETF 20% + 中债ETF 40% + 黄金ETF 10%

全天候组合（中国版）：
  股票ETF（沪深300）25%
  长期国债ETF        40%
  中期国债ETF        15%
  黄金ETF            7.5%
  商品ETF            12.5%

哑铃策略：
  宽基ETF（低风险核心）50%
  行业/主题ETF（高弹性进攻）50%
```

### 6.2 全球化配置的 ETF 工具选择

```
A股：沪深300ETF 510300 / 中证500ETF 510500
美股：纳指ETF 159632 / 标普500ETF 513500
港股：恒生ETF 159920 / 恒生科技ETF 513130
欧洲：德国DAX ETF / 欧洲50ETF（规模较小）
日本：日经225ETF 513880 / 东证ETF
新兴：越南ETF / 印度ETF（部分有QDII溢价）

固定收益：
  国内：国债ETF 511010 / 政金债ETF
  美国：美债ETF（QDII）

商品：
  黄金ETF 518880
  原油ETF 162411
  CRB商品指数ETF（国内较少）
```

### 6.3 再平衡频率与交易成本权衡

**再平衡成本**：
```
单次再平衡成本 ≈ 交易金额 × (佣金率 + 价差/2 + 冲击成本)
≈ 交易金额 × 0.05%~0.15%（宽基ETF）

年化再平衡成本 = 单次成本 × 年均调仓次数
```

**最优再平衡频率建议**：
- 纯被动配置（波动低）：每年2次（6月/12月）
- 行业轮动（波动高）：每月或每季度
- 阈值触发法：偏离目标权重 > 5% 时触发，通常优于固定频率

**免佣金再平衡技巧**：
- 利用新增资金定向补仓偏低仓位，减少卖出操作
- 分红收益优先配置到低配资产

### 6.4 税务效率考量

中国 ETF 税务规则：
- **个人投资者**：
  - 股票型ETF资本利得免税（持有期间）
  - ETF分红：现金分红免税，红利再投资不计税
  - 货币ETF利息收入：暂免个人所得税
- **机构投资者**：
  - 资本利得需计入企业所得税（25%）
  - 持股期间分红：持股 > 12个月免税

**税务效率策略**：
- 高换手的行业轮动策略尽量放在个人账户（利用资本利得免税）
- 定期定额长期持有，减少短期资本利得实现频率

---

## 7. 数据分析方法

### 7.1 用 Tushare 获取 ETF 数据

```python
import tushare as ts
import pandas as pd

def get_etf_list(pro: ts.pro_api) -> pd.DataFrame:
    """
    获取全市场ETF列表。

    Args:
        pro: tushare pro_api 实例

    Returns:
        ETF基本信息 DataFrame
    """
    df = pro.fund_basic(market='E', status='L')  # E=ETF, L=上市中
    return df[['ts_code', 'name', 'management', 'found_date', 'issue_date']]


def get_etf_nav(pro: ts.pro_api, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取ETF净值数据（IOPV）。

    Args:
        pro: tushare pro_api 实例
        ts_code: ETF代码，如 '510300.SH'
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'

    Returns:
        包含 trade_date, nav, accum_nav 的 DataFrame
    """
    df = pro.fund_nav(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('end_date').reset_index(drop=True)


def get_etf_daily(pro: ts.pro_api, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取ETF场内日行情（市价）。

    Args:
        pro: tushare pro_api 实例
        ts_code: ETF代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含 trade_date, open, high, low, close, vol, amount 的 DataFrame
    """
    df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df.sort_values('trade_date').reset_index(drop=True)


def get_index_daily(pro: ts.pro_api, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取基准指数日行情（用于计算跟踪误差）。

    Args:
        pro: tushare pro_api 实例
        index_code: 指数代码，如 '000300.SH'（沪深300）
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含 trade_date, close 的 DataFrame
    """
    df = pro.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
    return df[['trade_date', 'close', 'pct_chg']].sort_values('trade_date').reset_index(drop=True)
```

### 7.2 跟踪误差计算代码模板

```python
import numpy as np
import pandas as pd


def calc_tracking_error(
    etf_prices: pd.Series,
    index_prices: pd.Series,
    annualize: bool = True
) -> dict:
    """
    计算ETF对标的指数的跟踪误差。

    Args:
        etf_prices: ETF净值序列（以date为索引）
        index_prices: 指数价格序列（以date为索引）
        annualize: 是否年化，默认True

    Returns:
        包含 tracking_error, avg_daily_diff, max_daily_diff 的字典
    """
    # 对齐数据
    aligned = pd.concat([etf_prices, index_prices], axis=1).dropna()
    aligned.columns = ['etf', 'index']

    # 计算日收益率差值
    etf_ret = aligned['etf'].pct_change().dropna()
    idx_ret = aligned['index'].pct_change().dropna()
    daily_diff = etf_ret - idx_ret

    # 跟踪误差 = 差值的标准差
    te_daily = daily_diff.std()
    te = te_daily * np.sqrt(252) if annualize else te_daily

    return {
        'tracking_error': round(te * 100, 4),       # 百分比
        'avg_daily_diff': round(daily_diff.mean() * 100, 4),  # 平均日偏差 %
        'max_daily_diff': round(daily_diff.abs().max() * 100, 4),  # 最大单日偏差 %
        'annualized': annualize
    }


def compare_etfs_same_index(
    etf_codes: list[str],
    index_code: str,
    pro,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    比较追踪同一指数的多只ETF的跟踪表现。

    Args:
        etf_codes: ETF代码列表
        index_code: 基准指数代码
        pro: tushare pro_api 实例
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        各ETF的跟踪误差比较 DataFrame
    """
    index_df = get_index_daily(pro, index_code, start_date, end_date)
    index_prices = index_df.set_index('trade_date')['close']

    results = []
    for code in etf_codes:
        nav_df = get_etf_nav(pro, code, start_date, end_date)
        etf_prices = nav_df.set_index('end_date')['nav']
        te_result = calc_tracking_error(etf_prices, index_prices)
        te_result['ts_code'] = code
        results.append(te_result)

    return pd.DataFrame(results).set_index('ts_code').sort_values('tracking_error')
```

### 7.3 折溢价率监控

```python
def calc_premium_discount(
    market_price: float,
    iopv: float
) -> dict:
    """
    计算ETF折溢价率及套利信号。

    Args:
        market_price: ETF场内市价
        iopv: 实时净值（IOPV）

    Returns:
        包含 premium_pct, signal, arbitrage_feasible 的字典
    """
    premium_pct = (market_price - iopv) / iopv * 100

    if premium_pct > 0.3:
        signal = 'PREMIUM_HIGH'   # 溢价：卖出ETF或申购套利
        feasible = premium_pct > 0.5  # 扣除成本后是否可套利
    elif premium_pct < -0.3:
        signal = 'DISCOUNT_HIGH'  # 折价：买入ETF或赎回套利
        feasible = premium_pct < -0.5
    else:
        signal = 'NORMAL'
        feasible = False

    return {
        'premium_pct': round(premium_pct, 4),
        'signal': signal,
        'arbitrage_feasible': feasible
    }


def monitor_qdii_premium(pro, qdii_codes: list[str], date: str) -> pd.DataFrame:
    """
    监控QDII ETF溢价率（溢价过高时发出预警）。

    Args:
        pro: tushare pro_api 实例
        qdii_codes: QDII ETF代码列表
        date: 查询日期 'YYYYMMDD'

    Returns:
        各QDII ETF的溢价率和风险等级 DataFrame
    """
    results = []
    for code in qdii_codes:
        # 获取市价
        price_df = pro.fund_daily(ts_code=code, trade_date=date)
        # 获取净值
        nav_df = pro.fund_nav(ts_code=code, end_date=date)

        if not price_df.empty and not nav_df.empty:
            market_price = price_df.iloc[0]['close']
            nav = nav_df.iloc[0]['nav']
            premium_pct = (market_price - nav) / nav * 100
            risk_level = (
                'HIGH' if premium_pct > 5
                else 'MEDIUM' if premium_pct > 2
                else 'LOW'
            )
            results.append({
                'ts_code': code,
                'market_price': market_price,
                'nav': nav,
                'premium_pct': round(premium_pct, 2),
                'risk_level': risk_level
            })

    return pd.DataFrame(results).sort_values('premium_pct', ascending=False)
```

### 7.4 资金流入流出分析

```python
def etf_fund_flow_analysis(
    pro,
    ts_code: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    分析ETF规模变化与资金净流入/流出。

    Args:
        pro: tushare pro_api 实例
        ts_code: ETF代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含规模变化和资金流向估算的 DataFrame
    """
    nav_df = get_etf_nav(pro, ts_code, start_date, end_date)
    nav_df['end_date'] = pd.to_datetime(nav_df['end_date'])
    nav_df = nav_df.sort_values('end_date')

    # 规模（单位亿元）
    nav_df['scale'] = nav_df['unit_nav'] * nav_df['fund_share'] / 1e8

    # 净值变动引起的规模变化（被动）
    nav_df['nav_return'] = nav_df['unit_nav'].pct_change()
    nav_df['passive_change'] = nav_df['scale'].shift(1) * nav_df['nav_return']

    # 资金净流入 ≈ 规模变化 - 净值带来的被动变化
    nav_df['net_flow'] = nav_df['scale'].diff() - nav_df['passive_change']

    # 统计区间
    summary = {
        'total_net_flow': nav_df['net_flow'].sum(),       # 区间总净流入（亿元）
        'avg_daily_flow': nav_df['net_flow'].mean(),      # 日均净流入
        'inflow_days': (nav_df['net_flow'] > 0).sum(),    # 净流入天数
        'outflow_days': (nav_df['net_flow'] < 0).sum(),   # 净流出天数
        'current_scale': nav_df['scale'].iloc[-1]          # 最新规模
    }

    return nav_df[['end_date', 'unit_nav', 'scale', 'net_flow']], summary


def cross_etf_flow_comparison(
    pro,
    etf_codes: list[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    比较同类ETF的资金流向，判断资金偏好。

    Args:
        pro: tushare pro_api 实例
        etf_codes: 同类ETF代码列表
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        各ETF资金流向汇总对比 DataFrame
    """
    rows = []
    for code in etf_codes:
        _, summary = etf_fund_flow_analysis(pro, code, start_date, end_date)
        summary['ts_code'] = code
        rows.append(summary)
    return pd.DataFrame(rows).set_index('ts_code').sort_values('total_net_flow', ascending=False)
```

---

## 8. 常见分析场景与提示词模板

### 场景 1：筛选同类最优 ETF

```
分析追踪 [沪深300/中证500/xxx] 指数的所有ETF，
维度：规模、费率、近1年跟踪误差、日均成交额、买卖价差。
给出综合评分排名，并推荐最适合[长期持有/波段操作/大额配置]的产品。
```

### 场景 2：行业 ETF 轮动信号

```
基于过去 [20/60] 日动量，在以下行业ETF中选出前3名：
[消费、医疗、科技、能源、金融、工业、材料、公用事业]
同时排除近30日跌幅超过15%的ETF。
```

### 场景 3：ETF 组合回测

```
构建以下ETF组合并回测 [2020-01-01 至 2025-12-31]：
- 沪深300ETF 40%
- 中证500ETF 20%
- 国债ETF 30%
- 黄金ETF 10%
每季度再平衡，计算年化收益、夏普比率、最大回撤、与沪深300的相关性。
```

### 场景 4：QDII 溢价风险监控

```
监控以下QDII ETF的实时折溢价率：[纳指ETF 159632、标普500 513500、日经225 513880]
溢价 > 3% 时发出预警，建议等待回落后再入场。
```

---

## 9. 关键注意事项

1. **停牌替代**：行业ETF中若有大量停牌股，IOPV 失真，折溢价参考意义下降
2. **QDII 额度**：额度耗尽时申购暂停，溢价可能持续数月，不适合套利
3. **成分股调整**：每年6月/12月指数调整前后1~2周会有一定规律性机会
4. **杠杆ETF禁止长持**：衰减效应在震荡市中极其明显，严格限制持有周期
5. **货币ETF**：本质是货币市场基金，与普通ETF逻辑不同，流动性管理工具而非投资工具
6. **流动性差的ETF**：大额交易应拆分多日，避免自我冲击
7. **税务处理**：ETF 基金分红中若含股息收益，征税规则与资本利得不同，注意区分
