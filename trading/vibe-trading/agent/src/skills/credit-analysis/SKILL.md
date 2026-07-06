---
name: credit-analysis
description: "固收与信用分析：信用债评级、利差分析、违约风险评估、城投债研究、可转债定价与策略。"
category: analysis
---

# Credit Analysis Skill — 固收与信用分析

## 适用场景

当用户提出以下类型问题时，优先调用本 skill：
- 债券定价、YTM 计算、久期/凸性分析
- 企业信用评级、违约概率估算
- 信用利差分析与交易策略
- 城投债、ABS/MBS 信用评估
- 利率风险管理（DV01、关键利率久期）
- 中国固收市场结构分析

---

## 一、信用分析框架

### 1.1 信用评级体系

#### 主体评级 vs 债项评级

| 类型 | 定义 | 评级对象 |
|------|------|----------|
| **主体评级（Issuer Rating）** | 发行人整体偿债能力 | 企业、政府、金融机构 |
| **债项评级（Issue Rating）** | 特定债券的信用质量 | 具体债券，考虑抵押品、优先级、契约条款 |

债项评级可高于或低于主体评级（取决于担保结构）。

#### 标准普尔 / 穆迪 / 中国评级对照

| S&P | Moody's | 中国评级 | 含义 |
|-----|---------|----------|------|
| AAA | Aaa | AAA | 最高信用质量，极低违约风险 |
| AA+/AA/AA- | Aa1/Aa2/Aa3 | AA+/AA/AA- | 高质量，极低违约风险 |
| A+/A/A- | A1/A2/A3 | A+/A/A- | 较高信用质量 |
| BBB+/BBB/BBB- | Baa1/Baa2/Baa3 | BBB+/BBB/BBB- | 投资级下限（IG/HY分水岭） |
| BB+及以下 | Ba1及以下 | BB+及以下 | 高收益/投机级 |
| D | D | D | 违约 |

> **中国特点**：国内评级虚高，AA级在国内约等同于国际BBB-，需结合评级展望（正面/稳定/负面）综合判断。

---

### 1.2 Altman Z-Score 模型

用于预测企业财务困境，原始模型适用于上市制造业：

```
Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5
```

| 变量 | 计算公式 | 含义 |
|------|----------|------|
| X1 | 营运资本 / 总资产 | 流动性 |
| X2 | 留存收益 / 总资产 | 盈利积累 |
| X3 | EBIT / 总资产 | 盈利能力 |
| X4 | 股权市值 / 总负债账面值 | 财务杠杆 |
| X5 | 销售收入 / 总资产 | 资产效率 |

**判断区间**：
- Z > 2.99：安全区（低违约风险）
- 1.81 < Z < 2.99：灰色区（需深入分析）
- Z < 1.81：危险区（高违约风险）

**改进版本**：
- Z'（私有企业）：X4改用股权账面值，临界值2.90/1.23
- Z''（非制造业/新兴市场）：去掉X5，临界值2.60/1.10

**局限性**：
- 基于历史数据，滞后性强
- 不适用金融类企业（杠杆定义不同）
- 中国市场需重新标定参数

---

### 1.3 Merton 结构化模型

将公司股权视为对公司资产的看涨期权（执行价格=债务面值）：

**核心假设**：
- 公司资产价值 V 遵循几何布朗运动：`dV = μV dt + σ_V V dW`
- 债务为零息债，面值 D，到期日 T
- 违约仅在 T 时刻发生（欧式违约设定）

**股权定价（BS公式）**：
```
E = V·N(d1) - D·e^(-rT)·N(d2)

d1 = [ln(V/D) + (r + σ_V²/2)T] / (σ_V·√T)
d2 = d1 - σ_V·√T
```

**违约概率（风险中性）**：
```
PD = N(-d2)
```

**距违约距离（DD, Distance to Default）**：
```
DD = [ln(V/D) + (μ - σ_V²/2)T] / (σ_V·√T)
```

**信用利差估算**：
```
信用利差 ≈ -ln[N(d2) + (V/D·e^(rT))·N(-d1)] / T
```

**参数估算方法**（联立方程组）：
1. E = V·N(d1) - D·e^(-rT)·N(d2)
2. σ_E·E = N(d1)·σ_V·V

---

### 1.4 KMV 模型（预期违约频率 EDF）

KMV 是 Merton 模型的商业化实现，由穆迪收购：

**步骤**：
1. 用股价和股权波动率反推资产价值 V 和资产波动率 σ_V
2. 计算违约触发点（Default Point）：`DP = 短期债务 + 0.5×长期债务`
3. 计算距违约距离：`DD = (V - DP) / (V × σ_V)`
4. 通过历史违约数据库将 DD 映射为 EDF（非正态映射）

**与 Merton 的区别**：
- 违约触发点不是全部债务，而是短期+半长期
- DD→EDF 映射基于实证数据库，非正态分布假设
- EDF 是真实世界概率，而非风险中性概率

**EDF 参考区间**（约）：
- EDF < 0.1%：投资级
- 0.1%–1%：BBB-BB 级
- 1%–5%：B 级
- EDF > 5%：CCC 及以下

---

### 1.5 信用评分卡方法论

适用于零售信贷/ABS 底层资产分析：

**建模流程**：
1. **数据准备**：收集历史贷款数据，定义违约标签（如逾期90天+）
2. **特征工程**：WOE（Weight of Evidence）编码
3. **特征选择**：IV值（Information Value）筛选，IV>0.02保留
4. **模型训练**：Logistic Regression（主流）、XGBoost
5. **评分转换**：`Score = A - B×ln(odds)`，通常基准分600，PDO=20

**WOE 和 IV 计算**：
```python
WOE_i = ln(好样本比例_i / 坏样本比例_i)
IV_i = (好样本比例_i - 坏样本比例_i) × WOE_i
总IV = Σ IV_i
```

**IV 参考标准**：
- IV < 0.02：无预测力
- 0.02–0.1：弱预测力
- 0.1–0.3：中等预测力
- IV > 0.3：强预测力

---

## 二、固收产品分析

### 2.1 国债与政府债

#### 收益率曲线分析

**即期利率曲线（Zero Curve）**：各期限无风险零息债收益率，通过 Bootstrap 方法从附息债提取。

**远期利率曲线（Forward Curve）**：
```
f(T1, T2) = [(1+r2)^T2 / (1+r1)^T1]^(1/(T2-T1)) - 1
```

**期限利差**：
- 10Y-2Y：经济周期预判指标，负值通常预示衰退
- 10Y-1Y：流动性偏好衡量指标
- 30Y-10Y：超长端供需判断

**收益率曲线形态**：
| 形态 | 特征 | 经济含义 |
|------|------|----------|
| 正斜率（Normal） | 长端>短端 | 经济扩张预期 |
| 平坦（Flat） | 各期限相近 | 经济转折点 |
| 倒挂（Inverted） | 短端>长端 | 衰退信号 |
| 驼峰（Humped） | 中端最高 | 流动性分层 |

#### 中国国债收益率曲线特点
- 基准曲线：中国国债（CGBs）+ 国开债（Policy Bank Bonds）
- 关键点位：1Y/3Y/5Y/7Y/10Y/30Y
- 10Y国债为核心基准利率

---

### 2.2 企业债分析

#### 核心指标

**票面利率（Coupon Rate）**：发行时约定，按面值计息。

**到期收益率 YTM（Yield to Maturity）**：
使 债券现值 = 市场价格的内部收益率：
```
P = Σ [C/(1+y)^t] + F/(1+y)^n
```
其中 C=票息，F=面值，y=YTM，n=期数。

**当期收益率（Current Yield）**：`CY = 年票息 / 市场价格`（忽略本金损益）

**修正久期（Modified Duration）**：
```
MD = -dP/P ÷ dy = Macaulay Duration / (1+y/m)
```
含义：利率每变化1%，债券价格变化约MD%（反向）。

**凸性（Convexity）**：
```
CX = [Σ t(t+1)·CF_t/(1+y)^(t+2)] / P
价格变化修正：ΔP/P ≈ -MD·Δy + 0.5·CX·(Δy)²
```

#### 债券价格公式（完整）
```python
def bond_price(face, coupon_rate, ytm, n_periods, freq=1):
    """附息债券定价（贴现现金流法）。

    Args:
        face: 面值
        coupon_rate: 票面利率（年化）
        ytm: 到期收益率（年化）
        n_periods: 剩余付息期数
        freq: 每年付息次数（1=年付，2=半年付）

    Returns:
        债券现值（脏价）
    """
    c = face * coupon_rate / freq
    y = ytm / freq
    pv_coupons = c * (1 - (1+y)**(-n_periods)) / y
    pv_face = face / (1+y)**n_periods
    return pv_coupons + pv_face
```

---

### 2.3 可转债（纯债部分）

> 可转债的转股期权部分详见 `convertible-bond` skill，本节聚焦纯债价值。

**纯债价值（Bond Floor）**：
```
纯债价值 = Σ [票息/(1+r_straight)^t] + 面值/(1+r_straight)^n
```
其中 r_straight 为同评级同期限直债收益率。

**转股溢价率与纯债溢价率**：
- 转股溢价率 = (可转债价格 - 转股价值) / 转股价值
- 纯债溢价率 = (可转债价格 - 纯债价值) / 纯债价值

**下修条款信用含义**：
下修转股价可能导致摊薄，需评估公司意愿（强赎冲动 vs 回售压力）。

---

### 2.4 ABS/MBS 分析

#### 底层资产分析框架

**资产质量指标**：
- 加权平均票息（WAC）
- 加权平均剩余期限（WAM）
- 加权平均贷款价值比（LTV）
- 历史逾期率（DPD 30/60/90+）
- 累计违约率（CDR，Cumulative Default Rate）

**早偿率模型**：
- CPR（Conditional Prepayment Rate）：年化早偿率
- SMM（Single Monthly Mortality）：月早偿率
  ```
  CPR = 1 - (1 - SMM)^12
  SMM = 1 - (1 - CPR)^(1/12)
  ```
- PSA 模型：标准早偿假设（PSA100 = 前30个月线性增至6%/年，之后6%/年恒定）

**分层结构（Tranche）分析**：
- 优先级（Senior）：最先受偿，评级最高
- 夹层（Mezzanine）：次级受偿
- 劣后级（Equity/Junior）：首先吸收损失，超额利差归属

**关键风险指标**：
```
增信倍数 = (底层资产池规模 - 优先级规模) / 优先级规模
超额利差 = 底层资产池利率 - 优先级融资成本 - 服务费
```

---

### 2.5 城投债信用分析

城投债（LGFV，地方政府融资平台债）是中国固收市场特有品种。

#### 分析框架

**四维评估模型**：

| 维度 | 核心指标 | 权重 |
|------|----------|------|
| 区域财政实力 | 一般公共预算收入、GDP规模、财政自给率 | 40% |
| 平台层级 | 省级>市级>区县级，级别越高隐性支持越强 | 25% |
| 平台地位 | 是否唯一城投、资产注入力度、业务多元化 | 20% |
| 债务结构 | 有息负债规模、短期债务占比、再融资压力 | 15% |

**隐性债务风险信号**：
- 城投货币资金/短期债务 < 0.5（流动性紧张）
- EBITDA利息覆盖率 < 1（依赖外部融资付息）
- 非标融资占比>30%（再融资风险高）
- 区县级城投、弱区域（负债率>100%）

**城投估值溢价结构**（参考）：
```
城投利率 ≈ 同期国债 + 流动性溢价(30-50bp) + 区域溢价(0-200bp) + 平台溢价(0-100bp)
```

**政策风险**：2023年城投化债政策后分化加剧，关注：
- 一揽子化债进度
- 平台转型（城投转企业）
- 区域名单管理政策

---

## 三、利率风险管理

### 3.1 久期体系

#### Macaulay Duration（麦考利久期）

时间加权现金流现值之和，单位为"年"：
```
D_mac = Σ [t × CF_t/(1+y)^t] / P
```

#### Modified Duration（修正久期）

利率敏感性度量：
```
D_mod = D_mac / (1 + y/m)
ΔP ≈ -D_mod × P × Δy
```

#### Effective Duration（有效久期）

适用于含权债券（可赎回债、MBS等）：
```
D_eff = (P_down - P_up) / (2 × P_0 × Δy)
```
其中 P_down/P_up 为利率下移/上移Δy后的价格。

#### Dollar Duration（久期金额）

```
Dollar Duration = D_mod × P × 面值
```

---

### 3.2 凸性（Convexity）

衡量久期对利率的敏感性（二阶效应）：

```
C = Σ [t(t+1) × CF_t/(1+y)^(t+2)] / P

价格精确估算：
ΔP/P ≈ -D_mod·Δy + 0.5·C·(Δy)²
```

**凸性的价值**：正凸性使债券在利率下行时涨幅大于预期（利率上行时跌幅小于预期），因此正凸性债券比负凸性债券（如可赎回债、MBS）更受青睐。

---

### 3.3 DV01（基点价值）

利率变动1基点（0.01%）导致的价格变化：
```
DV01 = D_mod × P × 0.0001
```

组合层面：`Portfolio DV01 = Σ (DV01_i × 持仓量_i)`

**用途**：利率对冲比率计算
```
对冲比率 = DV01_被对冲头寸 / DV01_对冲工具
```

---

### 3.4 关键利率久期（Key Rate Duration, KRD）

衡量收益率曲线各关键期限平行移动1bp对价格的影响：
- 常用关键点：1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y
- `KRD_i = -ΔP/(P × Δy_i)`（仅第i个关键利率变动1bp）
- `Σ KRD_i ≈ D_mod`（各关键利率久期之和约等于修正久期）

**应用**：
- 识别组合对特定期限利率的暴露
- 精确对冲非平行移动风险（扭曲/蝶式）

---

### 3.5 免疫策略

**久期匹配（Duration Matching）**：
使资产组合久期 = 负债久期，对利率平行移动免疫。
条件：`Σ (w_i × D_i) = D_liability`

**现金流匹配（Cash Flow Matching）**：
直接匹配每期现金流，彻底消除再投资风险，但灵活性差、成本高。

**条件免疫（Contingent Immunization）**：
当组合价值超过安全底线时主动管理，跌至底线时切换为被动免疫。

**再平衡频率**：
- 久期随时间漂移，需定期（季度/月度）再平衡
- 利率大幅变动（>50bp）后立即再平衡

---

## 四、信用利差分析

### 4.1 信用利差的构成

```
信用利差（Credit Spread）= 违约风险溢价 + 流动性溢价 + 税收溢价（部分市场）
```

| 组成部分 | 影响因素 | 量化方式 |
|----------|----------|----------|
| 违约风险溢价 | 评级、行业、财务状况、宏观周期 | CDS报价、模型测算 |
| 流动性溢价 | 发行规模、剩余期限、市场深度 | 买卖价差、换手率 |
| 税收溢价 | 国债免税优惠（部分国家/投资者） | 利率差异分析 |

**利差衡量基准**：
- 国际市场：G-Spread（vs 国债）、I-Spread（vs 掉期）、Z-Spread（零息利差）、OAS（期权调整利差）
- 中国市场：信用利差通常对比国债或AAA城投

**OAS（Option-Adjusted Spread）**：
剥离嵌入期权价值后的信用利差，适用于含权债比较：
```
P = Σ CF_t / (1 + r_t + OAS)^t
```

---

### 4.2 信用利差曲线形态

**正斜率**（常见）：长期利差 > 短期利差，反映期限不确定性叠加。

**平坦/倒挂**：
- 市场对长期信用风险乐观（平坦）
- 短期流动性危机/再融资困境（倒挂），警示信号

**信用利差与国债收益率的相关性**：
- 经济扩张：信用利差收窄（风险偏好上升）
- 经济衰退/信用事件：信用利差走阔
- "逃向质量"效应：国债收益率下行+信用利差扩大，双重打击高收益债

---

### 4.3 信用利差变化的驱动因素

**宏观因素**：
- GDP增速、PMI：预期改善→利差收窄
- 货币政策宽松：流动性溢价下降
- 信用事件（违约潮）：系统性利差走阔

**行业因素**：
- 行业政策（如地产调控、城投化债）
- 行业景气周期
- 再融资环境

**个券因素**：
- 评级调整（下调→利差跳升）
- 财务数据变化
- 到期压力（临近到期→流动性利差增加）

---

### 4.4 信用利差交易策略

**利差压缩交易（Spread Tightening）**：
做多被低估（高利差）信用债，做空国债对冲利率风险。
- 适用场景：经济复苏初期、央行宽松周期

**利差扩大交易（Spread Widening）**：
做空信用债（通过CDS），做多国债。
- 适用场景：经济下行、信用事件频发

**跨评级利差交易**：
做多高收益/做空投资级（利差压缩时），或相反。

**蝶式利差交易（Butterfly）**：
做多中期、做空短端和长端，获利于信用曲线中段的相对价值。

**中国特色工具**：
- 信用风险缓释工具（CRMW/CDS）：对冲信用风险
- 国债期货：对冲利率久期风险

---

## 五、Python 代码模板

### 5.1 债券定价与久期计算

```python
import numpy as np
from scipy.optimize import brentq


def bond_price(face: float, coupon_rate: float, ytm: float,
               n_periods: int, freq: int = 1) -> float:
    """附息债券净现值定价。

    Args:
        face: 面值，通常100
        coupon_rate: 年票面利率（小数形式，如0.05表示5%）
        ytm: 年到期收益率（小数形式）
        n_periods: 剩余付息期数
        freq: 每年付息次数（1=年付，2=半年付）

    Returns:
        债券全价（脏价）

    Examples:
        >>> bond_price(100, 0.05, 0.04, 5)  # 5年期、5%票息、YTM=4%
        104.4518...
    """
    c = face * coupon_rate / freq
    y = ytm / freq
    if y == 0:
        return c * n_periods + face
    pv_coupons = c * (1 - (1 + y) ** (-n_periods)) / y
    pv_face = face / (1 + y) ** n_periods
    return pv_coupons + pv_face


def ytm_solve(price: float, face: float, coupon_rate: float,
              n_periods: int, freq: int = 1) -> float:
    """给定市场价格反求YTM（数值解法）。

    Args:
        price: 债券市场价格（脏价）
        face: 面值
        coupon_rate: 年票面利率
        n_periods: 剩余付息期数
        freq: 每年付息次数

    Returns:
        年化YTM（小数形式）

    Raises:
        ValueError: 无法在合理范围内找到解时
    """
    def pv_diff(y):
        return bond_price(face, coupon_rate, y, n_periods, freq) - price

    try:
        return brentq(pv_diff, -0.5, 10.0)
    except ValueError as e:
        raise ValueError(f"无法求解YTM，检查输入参数: {e}")


def macaulay_duration(face: float, coupon_rate: float, ytm: float,
                      n_periods: int, freq: int = 1) -> float:
    """Macaulay久期（单位：期数，除以freq得年数）。

    Args:
        face: 面值
        coupon_rate: 年票面利率
        ytm: 年到期收益率
        n_periods: 剩余付息期数
        freq: 每年付息次数

    Returns:
        Macaulay久期（年）
    """
    c = face * coupon_rate / freq
    y = ytm / freq
    price = bond_price(face, coupon_rate, ytm, n_periods, freq)

    weighted_sum = sum(
        t * (c / (1 + y) ** t)
        for t in range(1, n_periods)
    ) + n_periods * ((c + face) / (1 + y) ** n_periods)

    return (weighted_sum / price) / freq


def modified_duration(face: float, coupon_rate: float, ytm: float,
                      n_periods: int, freq: int = 1) -> float:
    """修正久期。

    Returns:
        修正久期（对ytm的价格弹性，取负号后）
    """
    d_mac = macaulay_duration(face, coupon_rate, ytm, n_periods, freq)
    return d_mac / (1 + ytm / freq)


def convexity(face: float, coupon_rate: float, ytm: float,
              n_periods: int, freq: int = 1) -> float:
    """债券凸性。

    Returns:
        凸性（年²）
    """
    c = face * coupon_rate / freq
    y = ytm / freq
    price = bond_price(face, coupon_rate, ytm, n_periods, freq)

    conv_sum = sum(
        t * (t + 1) * (c / (1 + y) ** (t + 2))
        for t in range(1, n_periods)
    ) + n_periods * (n_periods + 1) * ((c + face) / (1 + y) ** (n_periods + 2))

    return (conv_sum / price) / (freq ** 2)


def dv01(face: float, coupon_rate: float, ytm: float,
         n_periods: int, freq: int = 1, par_amount: float = 1_000_000) -> float:
    """DV01（每百万面值的基点价值）。

    Args:
        par_amount: 持仓面值，默认100万

    Returns:
        每1bp利率变动对应的价格变化（元）
    """
    d_mod = modified_duration(face, coupon_rate, ytm, n_periods, freq)
    price = bond_price(face, coupon_rate, ytm, n_periods, freq)
    return d_mod * (price / 100) * 0.0001 * par_amount
```

---

### 5.2 收益率曲线拟合（Nelson-Siegel / Svensson）

```python
import numpy as np
from scipy.optimize import minimize
from typing import Tuple


def nelson_siegel(tau: np.ndarray, beta0: float, beta1: float,
                  beta2: float, lambda1: float) -> np.ndarray:
    """Nelson-Siegel 即期利率模型。

    Args:
        tau: 期限数组（年）
        beta0: 长期利率水平（level）
        beta1: 斜率因子（slope）
        beta2: 曲率因子（curvature）
        lambda1: 曲线衰减速度

    Returns:
        各期限即期利率数组
    """
    factor1 = (1 - np.exp(-tau / lambda1)) / (tau / lambda1)
    factor2 = factor1 - np.exp(-tau / lambda1)
    return beta0 + beta1 * factor1 + beta2 * factor2


def svensson(tau: np.ndarray, beta0: float, beta1: float,
             beta2: float, beta3: float,
             lambda1: float, lambda2: float) -> np.ndarray:
    """Svensson 模型（NS扩展，双曲率因子）。

    Args:
        tau: 期限数组（年）
        beta0-beta3: 参数
        lambda1, lambda2: 两个衰减速度参数

    Returns:
        各期限即期利率数组
    """
    f1 = (1 - np.exp(-tau / lambda1)) / (tau / lambda1)
    f2 = f1 - np.exp(-tau / lambda1)
    f3 = (1 - np.exp(-tau / lambda2)) / (tau / lambda2) - np.exp(-tau / lambda2)
    return beta0 + beta1 * f1 + beta2 * f2 + beta3 * f3


def fit_yield_curve(maturities: np.ndarray, yields: np.ndarray,
                    model: str = "svensson") -> Tuple[np.ndarray, callable]:
    """拟合收益率曲线并返回插值函数。

    Args:
        maturities: 已知债券期限（年），如 [0.25, 0.5, 1, 2, 3, 5, 7, 10]
        yields: 对应YTM（小数），如 [0.02, 0.021, ...]
        model: "nelson_siegel" 或 "svensson"

    Returns:
        (最优参数, 插值函数)

    Raises:
        ValueError: 未知模型名称
    """
    if model == "nelson_siegel":
        def objective(params):
            fitted = nelson_siegel(maturities, *params)
            return np.sum((fitted - yields) ** 2)
        x0 = [0.04, -0.02, 0.01, 1.5]
        bounds = [(0, 0.2), (-0.2, 0.2), (-0.2, 0.2), (0.1, 10)]
        result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
        return result.x, lambda t: nelson_siegel(np.array(t), *result.x)

    elif model == "svensson":
        def objective(params):
            fitted = svensson(maturities, *params)
            return np.sum((fitted - yields) ** 2)
        x0 = [0.04, -0.02, 0.01, 0.01, 1.5, 5.0]
        bounds = [(0, 0.2), (-0.2, 0.2), (-0.2, 0.2), (-0.2, 0.2),
                  (0.1, 10), (0.1, 20)]
        result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
        return result.x, lambda t: svensson(np.array(t), *result.x)

    else:
        raise ValueError(f"未知模型: {model}，支持 nelson_siegel / svensson")
```

---

### 5.3 Altman Z-Score 计算

```python
import pandas as pd


def altman_z_score(working_capital: float, retained_earnings: float,
                   ebit: float, market_cap: float, total_debt: float,
                   revenue: float, total_assets: float,
                   model: str = "original") -> dict:
    """Altman Z-Score 违约风险评估。

    Args:
        working_capital: 营运资本（流动资产-流动负债）
        retained_earnings: 留存收益
        ebit: 息税前利润
        market_cap: 股权市值（original）或账面净资产（prime/double_prime）
        total_debt: 总债务
        revenue: 营业收入
        total_assets: 总资产
        model: "original"（上市制造业）| "prime"（私有企业）| "double_prime"（非制造业）

    Returns:
        含Z-Score、各分项、风险等级的字典
    """
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_debt
    x5 = revenue / total_assets

    if model == "original":
        z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
        safe_zone = z > 2.99
        distress_zone = z < 1.81
    elif model == "prime":
        z = 0.717*x1 + 0.847*x2 + 3.107*x3 + 0.420*x4 + 0.998*x5
        safe_zone = z > 2.90
        distress_zone = z < 1.23
    elif model == "double_prime":
        # 去掉X5（非制造业资产周转率意义不同）
        z = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
        safe_zone = z > 2.60
        distress_zone = z < 1.10
    else:
        raise ValueError(f"未知模型: {model}")

    if safe_zone:
        risk_level = "安全区（低违约风险）"
    elif distress_zone:
        risk_level = "危险区（高违约风险）"
    else:
        risk_level = "灰色区（需深入分析）"

    return {
        "z_score": round(z, 4),
        "risk_level": risk_level,
        "components": {
            "X1_流动性": round(x1, 4),
            "X2_盈利积累": round(x2, 4),
            "X3_盈利能力": round(x3, 4),
            "X4_杠杆": round(x4, 4),
            "X5_效率": round(x5, 4) if model != "double_prime" else "N/A",
        }
    }
```

---

### 5.4 信用利差时序分析

```python
import pandas as pd
import numpy as np
from typing import Optional


def credit_spread_analysis(
    bond_yields: pd.Series,
    risk_free_yields: pd.Series,
    window: int = 252,
    issuer_name: Optional[str] = None
) -> pd.DataFrame:
    """信用利差时序分析（Z-Score标准化 + 历史分位数）。

    Args:
        bond_yields: 信用债收益率时间序列（%，日频）
        risk_free_yields: 对应期限无风险利率（%，日频）
        window: 滚动窗口（交易日数），默认252（1年）
        issuer_name: 发行人名称，用于输出标注

    Returns:
        含信用利差、Z-Score、历史分位数的DataFrame

    Raises:
        ValueError: 输入序列长度不一致时
    """
    if len(bond_yields) != len(risk_free_yields):
        raise ValueError("收益率序列长度必须一致")

    spread = bond_yields - risk_free_yields
    spread.name = f"{issuer_name or '未知发行人'}_信用利差(bp)"
    spread_bp = spread * 100  # 转换为基点

    result = pd.DataFrame({"信用利差_bp": spread_bp})

    # 滚动统计
    result["滚动均值"] = spread_bp.rolling(window).mean()
    result["滚动标准差"] = spread_bp.rolling(window).std()
    result["Z-Score"] = (spread_bp - result["滚动均值"]) / result["滚动标准差"]

    # 历史分位数（使用全样本）
    result["历史分位数"] = spread_bp.rank(pct=True)

    # 利差变化
    result["日变化_bp"] = spread_bp.diff()
    result["月变化_bp"] = spread_bp.diff(21)

    # 信号生成
    result["利差信号"] = "中性"
    result.loc[result["Z-Score"] < -1.5, "利差信号"] = "偏贵（利差偏低）"
    result.loc[result["Z-Score"] > 1.5, "利差信号"] = "偏便宜（利差偏高）"

    return result


def spread_term_structure(
    issuers: dict,
    risk_free_curve: pd.Series
) -> pd.DataFrame:
    """信用利差期限结构分析。

    Args:
        issuers: {发行人: {期限: 收益率}} 字典
            例：{"AAA城投": {1: 0.025, 3: 0.028, 5: 0.032}}
        risk_free_curve: 无风险利率曲线 {期限: 收益率}

    Returns:
        信用利差期限结构矩阵（行=发行人，列=期限）
    """
    records = []
    for issuer, ytm_curve in issuers.items():
        row = {"发行人": issuer}
        for term, ytm in ytm_curve.items():
            rf = risk_free_curve.get(term, np.nan)
            row[f"{term}Y利差(bp)"] = round((ytm - rf) * 10000, 1)
        records.append(row)
    return pd.DataFrame(records).set_index("发行人")
```

---

### 5.5 Merton 模型违约概率

```python
import numpy as np
from scipy.stats import norm
from scipy.optimize import fsolve
from typing import Tuple


def merton_model(
    equity_value: float,
    equity_vol: float,
    debt_face: float,
    risk_free: float,
    T: float
) -> dict:
    """Merton结构化模型：估算违约概率和信用利差。

    Args:
        equity_value: 股权市值（亿元）
        equity_vol: 股权年化波动率（小数）
        debt_face: 债务面值（亿元，简化为零息债）
        risk_free: 无风险利率（小数）
        T: 债务到期年限

    Returns:
        含资产价值、距违约距离、违约概率、信用利差的字典
    """
    def equations(params):
        V, sigma_V = params
        d1 = (np.log(V / debt_face) + (risk_free + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
        d2 = d1 - sigma_V * np.sqrt(T)

        # 方程1：股权=资产看涨期权
        eq1 = V * norm.cdf(d1) - debt_face * np.exp(-risk_free * T) * norm.cdf(d2) - equity_value
        # 方程2：股权波动率=资产波动率的杠杆放大
        eq2 = norm.cdf(d1) * sigma_V * V - equity_vol * equity_value
        return [eq1, eq2]

    # 初始值估计
    V0 = equity_value + debt_face
    sigma_V0 = equity_vol * equity_value / V0

    solution = fsolve(equations, [V0, sigma_V0], full_output=True)
    V_star, sigma_V_star = solution[0]

    d1 = (np.log(V_star / debt_face) + (risk_free + 0.5 * sigma_V_star**2) * T) / (sigma_V_star * np.sqrt(T))
    d2 = d1 - sigma_V_star * np.sqrt(T)

    # 风险中性违约概率
    pd_rn = norm.cdf(-d2)

    # 距违约距离（真实世界近似，用无风险利率代替真实漂移）
    dd = d2

    # 信用利差（简化估算）
    debt_value = debt_face * np.exp(-risk_free * T) * norm.cdf(d2) + V_star * norm.cdf(-d1)
    if debt_value > 0 and T > 0:
        credit_spread = -np.log(debt_value / (debt_face * np.exp(-risk_free * T))) / T
    else:
        credit_spread = np.nan

    return {
        "资产价值_亿": round(V_star, 2),
        "资产波动率": round(sigma_V_star, 4),
        "距违约距离_DD": round(dd, 3),
        "违约概率_RN": f"{pd_rn*100:.2f}%",
        "信用利差_bp": round(credit_spread * 10000, 1) if not np.isnan(credit_spread) else "N/A",
    }
```

---

## 六、中国固收市场特色

### 6.1 市场结构

#### 银行间市场 vs 交易所市场

| 维度 | 银行间市场（CFETS） | 交易所市场（上交所/深交所） |
|------|---------------------|--------------------------|
| 监管机构 | 人民银行 | 证监会 |
| 主要参与者 | 银行、保险、基金、外资 | 券商、基金、个人投资者 |
| 交易方式 | 询价（OTC）+ 匿名点击 | 集中撮合 + 大宗交易 |
| 主要品种 | 国债、政金债、信用债、ABS | 企业债、公司债、可转债 |
| 规模占比 | ~90%（以交易量计） | ~10% |
| 结算方式 | T+0/T+1（DVP） | T+1 |
| 流动性 | 高（国债/政金债） | 高（可转债）/低（纯债） |

#### 主要债券品种

| 品种 | 发行主体 | 监管/注册 | 信用风险 |
|------|----------|-----------|----------|
| 国债（CGBs） | 财政部 | 无限制 | 无（主权信用） |
| 地方政府债 | 各省市政府 | 财政部审批 | 极低 |
| 政策性银行债（国开/农发/进出口） | 政策行 | 无限制 | 极低（准主权） |
| 同业存单（NCD） | 银行 | 央行 | 低（银行信用） |
| 超短期融资券（SCP）/ 短融（CP）/ 中票（MTN） | 非金融企业 | 交易商协会（NAFMII） | 中 |
| 企业债 | 企业 | 发改委 | 中高 |
| 公司债 | 上市公司 | 证监会 | 中高 |
| 城投债 | 地方融资平台 | 多元 | 中高（隐性政府背书） |
| ABS/ABN | SPV | NAFMII/证监会 | 取决于底层资产 |

---

### 6.2 城投债深度分析要点

**一级市场分析**（发行定价）：
1. 核查发行人层级和区域（省/市/区县）
2. 审查主业占比（基础设施业务vs商业化业务比例）
3. 评估区域一般公共预算收入和政府负债率
4. 分析近3年城投流转资产的真实性（往来款异常）

**二级市场分析**（持仓估值）：
1. 跟踪利差变化（vs 同评级同期限）
2. 关注舆情事件（技术性违约/商票逾期/评级下调）
3. 监测再融资节奏（到期压力 vs 新发节奏）
4. 关注区域政策（化债名单、债务置换进度）

**风险预警信号（红线）**：
- 货币资金/短期债务 < 0.3
- 非标融资/有息负债 > 40%
- 商票逾期被纳入系统（票据失信名单）
- 所在区域城投整体再融资受阻
- 管理层人事变动叠加区域评级负面展望

---

### 6.3 理财/资管产品信用分析

**净值化转型后的底层穿透分析**：
- 混合型理财：需分别评估权益端（市值波动）和固收端（信用风险）
- 固收+策略：主体80%+债券，20%-以内权益/可转债
- FOF型理财：两层嵌套穿透，需评估底层基金持仓

**流动性分析框架**：
```
产品层面流动性 = f(底层资产流动性, 赎回条款, 摊余成本法 vs 市值法)
```
- 摊余成本法：价格稳定但隐藏风险（不适用净值化产品）
- 市值法：反映真实价值，但波动暴露可能引发赎回潮

**底层信用评估步骤**：
1. 获取债券持仓明细（季报/半年报披露）
2. 按评级/行业/城投/非城投分类
3. 计算加权信用利差
4. 识别集中度风险（单券 > 5%为高集中度）
5. 评估流动性梯度（高流动→低流动覆盖度）

---

### 6.4 违约案例分析方法论

**违约类型**：
| 类型 | 特征 | 中国典型案例 |
|------|------|------------|
| 流动性违约 | 资产健康但现金流断裂 | 部分中小房企 |
| 技术性违约 | 触发条款（交叉违约/加速到期） | 多见于弱资质主体 |
| 经营性违约 | 主业恶化导致还款能力下降 | 永煤、华晨（2020） |
| 欺诈性违约 | 财务造假/资产腾挪 | 康美药业、蓝盛博 |

**违约前沿信号（Precursor Signals）**：

```
财务层面：
  - 应收账款/总资产 异常增高（虚增收入）
  - 货币资金余额高但受限比例高
  - 商誉/无形资产占比持续增大
  - 关联方交易占比异常

市场层面：
  - 二级市场价格持续下跌（跌破90）
  - 信用利差快速走阔（单周>50bp）
  - 主承销商更换或不参与后续发行
  - CDS报价（如有）快速上升

评级层面：
  - 评级列入负面观察
  - 多家评级机构下调
  - 展望由稳定下调至负面
```

**事后分析框架（Post-Default Analysis）**：
1. 违约触发时点与资金流向重构
2. 资产负债表"真实性"评估（区分真实资产 vs 账面资产）
3. 债权优先级梳理（担保顺序、抵质押品）
4. 处置预期回收率估算（Recovery Rate）
5. 系统性风险传染路径（交叉持有、同类主体）

**中国市场回收率参考**：
- 城投债（技术性违约后化解）：接近100%
- 房企违约：约20%-50%（取决于土储质量）
- 工业企业违约：约30%-60%
- 金融机构（非银）：约40%-70%（监管介入程度）

---

## 七、与其他 Skill 的关联

| 相关 Skill | 互补关系 |
|------------|----------|
| `convertible-bond` | 可转债转股期权部分由 convertible-bond skill 处理，本 skill 负责纯债定价和信用风险 |
| `macro-analysis` | 宏观利率环境和信用周期判断由 macro skill 提供输入 |
| `risk-management` | 组合层面信用风险（VaR/CVaR）参考 risk-management skill |
| `equity-fundamental` | 信用分析与股权估值共享财务报表分析框架，Altman Z-Score两侧均适用 |

---

## 八、快速参考

### 常用公式速查

```
YTM 近似公式：
  YTM ≈ [C + (F-P)/n] / [(F+P)/2]

久期与价格变化：
  ΔP ≈ -D_mod × P × Δy + 0.5 × CX × P × (Δy)²

DV01 = D_mod × P × 0.0001 × 持仓面值

信用利差 = 债券YTM - 同期限国债YTM

Z-Score 风险信号：
  Z > 2.99 → 安全   1.81 < Z < 2.99 → 灰色   Z < 1.81 → 危险

违约距离 DD → EDF：
  DD > 4: EDF < 0.1%
  DD 2-4: EDF 0.1%-1%
  DD 1-2: EDF 1%-5%
  DD < 1: EDF > 5%
```

### 中国固收数据源

| 数据类型 | 推荐来源 |
|----------|----------|
| 国债收益率曲线 | 中央结算公司（CCDC）、财政部官网 |
| 信用债行情 | Wind、DM数据 |
| 城投财务数据 | 发债主体年报、Wind |
| 评级报告 | 中诚信、联合资信、东方金诚官网 |
| 违约数据 | Wind、中国债券信息网（chinamoney.com.cn） |
| ABS数据 | CNABS（中国资产证券化分析网） |
