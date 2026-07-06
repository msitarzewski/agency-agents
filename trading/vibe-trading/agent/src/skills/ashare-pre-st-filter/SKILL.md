---
name: ashare-pre-st-filter
description: A 股 ST/*ST 风险预测框架 — 基于最新中报/三季报或业绩预告/快报，预测下一财年是否会因营收、利润、净资产、分红不达标而被风险警示，并将新浪监管处罚记录作为独立证据面纳入风险等级。仅适用于 A 股，不预测财务造假。
category: risk-analysis
---

> **依赖**：本 skill 必须配合 [tushare skill](../tushare/SKILL.md) 使用，缺数据时回退到 [akshare skill](../akshare/SKILL.md)。

# A 股 ST/*ST 风险预测

## 适用范围

- 仅 A 股**主板 / 创业板 / 科创板**。港股、美股、加密、商品、**北交所**（`8xxxxx.BJ` 监管规则与本 skill 阈值不一致）均不适用，本 skill 直接拒绝。
- 仅做"下一财年是否会被 ST/*ST"的前瞻预测，不做财务造假预测。
- 输出双轴结果：**触线风险等级** + **预测可信度**。

## 触发条件

用户提问形如：
- "分析 000729.SZ 的 ST 风险"
- "600xxx 下个年报会不会被 ST"
- "帮我看一下 300xxx 是否有退市风险"

收到此类请求时，按下面"分析流程"执行；其他场景不要主动启用本 skill。

## 数据获取规范（tushare 优先 → akshare 兜底）

**铁律**：

1. **所有财务/基本面/分红/审计/ST 状态数据，必须先调用 [tushare skill](../tushare/SKILL.md)**，按下表指定的接口名、`ts_code`、`period` 拉取。
2. 当 tushare 接口因积分不足、token 缺失或返回空时，**回退到 [akshare skill](../akshare/SKILL.md)** 对应函数。
3. **akshare 兜底数据必须在最终输出"备注"中显式标注**：`数据源：akshare（非官方聚合，不保证完整性，建议核对原始公告）`。**不允许只用 akshare 给出"高可信度"预测**——akshare 兜底的红线项可信度强制降一档（高→中高，中高→中，中→低）。
4. 监管处罚（E2）走本 skill 自带的 [scripts/fetch_sina_penalties.py](scripts/fetch_sina_penalties.py)，不经过 tushare/akshare。

### 数据需求映射表

| 数据需求 | tushare 接口（首选） | 抓取参数 / 时间窗口 | akshare 兜底 | akshare 注意事项 |
|---------|---------------------|-------------------|-------------|----------------|
| 当前 ST 状态 | `stock_st` | 最近一个交易日 | `stock_zh_a_st_em()` | 仅返回当前 ST/退市整理板列表，历史不可查 |
| 历史改名 | `namechange` | `ts_code` 全历史 | `stock_zh_a_new_em()`（仅新股，无改名） | akshare 无完整改名接口，必要时跳过 |
| 股票基础信息（板块判断） | `stock_basic` | `list_status='L'` | `stock_individual_info_em(symbol)` | 字段名不同，需自行映射 |
| 业绩预告 | `forecast` | `ts_code` + 最近 2 个 period（`{Y}0630`/`{Y}0930`/`{Y}1231`） | `stock_yjyg_em(date='YYYYMMDD')` | 按报告期日期反查，需先按 period 拉全市场再筛 ts_code |
| 业绩快报 | `express` | 同上，最近 2 个 period | `stock_yjbb_em(date='YYYYMMDD')` | 同上，全市场快照需筛 |
| 利润表 | `income` | `ts_code` + 最近 5 个 period（过去 4 年年报 `{Y}1231` + 最新中报/三季报） | `stock_financial_report_sina(stock='sh600000', symbol='利润表')` | 单位不一致（万元 vs 元），需做归一；季报缺失常见 |
| 资产负债表 | `balancesheet` | 同上 | `stock_financial_report_sina(stock='sh600000', symbol='资产负债表')` | 同上 |
| 现金流量表 | `cashflow` | 同上 | `stock_financial_report_sina(stock='sh600000', symbol='现金流量表')` | 同上 |
| 财务指标（扣非净利润等） | `fina_indicator` | `ts_code` + 最近 5 个 period | `stock_financial_analysis_indicator(symbol='600000')` | 字段中文，扣非字段名为"扣除非经常性损益后的净利润" |
| 审计意见 | `fina_audit` | `ts_code` + 最近 2 个年报 period | **akshare 无对应接口** | 缺失时在输出中标注"审计意见数据缺失"，**不得跳过**——必须提示用户去官网查 |
| 分红 | `dividend` | `ts_code` + 近 5 年 `div_proc='实施'` | `stock_history_dividend_detail(symbol='600000', indicator='分红')` | 字段中文，需把"派息"金额×总股本得到现金分红总额 |
| 日线行情（1 元退市预警） | `daily` | `ts_code` + 最近 30 个交易日 | `stock_zh_a_hist(symbol='600000', period='daily', adjust='')` | 必须用**不复权**价格判断 1 元退市线 |
| 每日指标（市值） | `daily_basic` | `ts_code` + 最近一个交易日 | `stock_zh_a_spot_em()` 全市场快照筛 `代码=600000` | 字段名为"总市值"（**单位：元**，东方财富 push2 原始口径，akshare 不做缩放），换算成亿元需 `/1e8`。⚠️ 不要与 tushare `daily_basic.total_mv`（万元）混淆——本列是 akshare 兜底口径 |
| 财报披露日期 | `disclosure_date` | `ts_code` + 当前年度 | **akshare 无对应接口** | 缺失时按经验估算（4/30 年报、8/31 中报、10/31 三季报） |
| 监管处罚 | — | — | **走本 skill 自带 sina 脚本** | 见 E2 章节 |

### 时间窗口口径统一

按数据类型分别处理，**禁止用单一 60 天经验值统一对齐**：

- **财务报表（income / balancesheet / cashflow / fina_indicator）**：以 `disclosure_date` 实际公告日为准；该接口不可用时按法定截止日（年报 4/30、中报 8/31、三季报 10/31、一季报 4/30）做兜底。在公告日 +1 天起方可视该 period 为"最新可得"。
- **"过去 N 年年报"**：一律 `period = {Y}1231`，不要用日历年起止。
- **业绩预告 forecast / 业绩快报 express**：只取 `ann_date ≥ 当前年度 1 月 1 日` 的记录；按 `ann_date` 倒序取最新一条，老 period 的预告对预测无效。
- **dividend**：按 `(end_date, ann_date, cash_div_tax)` 三元组**强制去重**——tushare 同一笔分红会出现 3-4 行（预案/股东大会通过/实施），直接累加会三倍误算。

## 第一步：当前状态核查（M0）

**判断公司当前是否已被风险警示，并据此调整分析方向（不一刀切结束）**：

调用顺序：
1. 优先调用 `stock_st`（tushare skill，3000 积分），按当前最近交易日查询；记录 `type` / `type_name`。
2. 如积分不足，回退到 `namechange`（免费）：拉取 `ts_code` 全部历史改名记录，取按 `start_date` 排序的最新一条；判断 `name` 前缀。
3. 兜底用 `stock_basic.name` 做名称确认。

**分支处理**：

| 当前状态 | 分析方向 | 是否继续 |
|---------|---------|---------|
| 正常股票 | 预测下一财年是否会被 ST/*ST | **是**（默认流程） |
| 已 ST（普通） | 改为预测：是否会进一步转 *ST 或退市；R1-R4 阈值需更严格（亏损链门槛降一年） | **是** |
| 已 *ST | 改为预测：是否会被强制退市；重点看 R1 营收 + R2 净资产 + E1 审计意见 | **是** |
| 已退市整理期 / 已摘牌 | 直接结束 | **否** |

## 第二步：板块阈值表（决定红线）

**先用 `ts_code` 前缀判断板块，再套用对应阈值。不要混用。**

| 板块 | 代码识别 | 营收红线 | 市值退市线 | 三年累计分红阈值 |
|------|---------|---------|-----------|----------------|
| 主板 | `60xxxx.SH` / `00xxxx.SZ`（除 30 / 688 开头外） | 净利润为负 且 营收 < 3 亿 | 市值 < 5 亿 | 累计 < 5000 万 且 < 年均净利润 30% |
| 创业板 | `30xxxx.SZ` | 净利润为负 且 营收 < 1 亿 | 市值 < 3 亿 | 累计 < 3000 万 且 < 年均净利润 30%（研发豁免：研发投入占营收 ≥ 5% 或近三年累计 ≥ 6000 万） |
| 科创板 | `688xxx.SH` | 净利润为负 且 营收 < 1 亿 | 市值 < 3 亿 | 累计 < 3000 万 且 < 年均净利润 30%（研发豁免：研发投入占营收 ≥ 5% 或近三年累计 ≥ 6000 万） |

## 第三步：预测时点选择

按"最新可得证据"原则确定基准时点，从下到上择优：

| 基准时点 | 数据接口 | 可信度基线 | 适用季节 |
|---------|---------|-----------|---------|
| **业绩预告 forecast** | `forecast` | **高** | 1 月底 / 7 月中旬 / 10 月底高发期 |
| **业绩快报 express** | `express` | **高** | 1-4 月年报前夕 |
| **三季报** | `income/balancesheet/cashflow` (`period=YYYYMMDD`，9 月末) | **中高** | 10 月底披露后到次年年报前 |
| **中报** | 同上，6 月末 period | **中** | 8 月底披露后到三季报前 |
| **去年年报** | 同上，12 月末 period | **低** | 仅作为基准对照 |

**证据优先级**（同一指标多个来源时，高的覆盖低的）：

```
forecast / express > 三季报 > 中报 > 去年年报 > 经验外推
```

输出时**必须在每个预测项明示采用了哪一级证据**。如果存在 forecast 给出的全年净利润区间，**禁止再用三季报机械年化覆盖**。

## 第四步：四项可预测红线

### R1 营收 + 净利润红线

**目标**：预测全年营收、归母净利润和**扣非净利润**，按监管口径"扣非前后孰低者"判定。

**口径关键**：监管原文是 `min(n_income, profit_dedt) < 0` 且 `revenue < 板块阈值` —— **必须同时预测扣非净利润**，不能只用归母。仅看归母会漏掉"归母为正但扣非为负"的造壳公司。

**预测方法（按基准时点选用，至少一种）**：

- **forecast 直采法**：若 `forecast` 给出 `net_profit_min` / `net_profit_max`，直接取区间作为全年归母预测；扣非用过去两年扣非率（`profit_dedt / n_income` 中位数）折算；可信度=高。营收红线仍需结合最新报表外推。
- **express 直采法**：若 `express` 已披露，`revenue` / `n_income` 即为全年快报值；扣非同样按过去两年率折算（express 一般无扣非字段）；可信度=高。
- **Q4 单季回补法**（三季报基准）：
  - `Q1Q3_revenue` = 三季报营业收入
  - `Q4_revenue_est` = 过去两年 Q4 营收占全年比例的中位数 × 当前年化预估值
  - `revenue_full_year_est = Q1Q3_revenue + Q4_revenue_est`
  - `n_income` / `profit_dedt` 同法处理
  - 可信度=中高
- **下半年情景外推法**（中报基准，强季节性公司必须用）：
  - 取过去两年 H2 营收占全年比例均值，给出悲观/基准/乐观三情景
  - `revenue_full_year_est = H1_revenue / H1_share_avg`
  - 可信度=中
- **同比延续法**（中报基准，弱季节性公司可用）：
  - `revenue_full_year_est = H1_revenue × (last_year_full_revenue / last_year_H1_revenue)`
  - 可信度=中

**禁止**：H1 直接乘 2、Q1-Q3 直接乘 4/3。任何机械年化**强制降到"低"可信度**并在输出中注明。

**触线判定**（口径：`worst_profit = min(n_income_est, profit_dedt_est)`）：
- 高风险：`worst_profit < 0` 且 `revenue_est < 板块阈值`
- 中风险：`worst_profit < 0` 但营收达标；或营收逼近阈值（< 阈值 × 1.2）
- 低风险：上述均不满足

> **系数说明**：R1 中风险的 1.2 是预测项预警 buffer（预测本身有误差，需窄 buffer）；R4 高风险的 1.5 是双年联动判定 buffer（两年都亏且营收接近阈值才是真退市信号，需宽 buffer）。两个系数不同是有意为之，**不要错误地统一**。

### R2 年末净资产红线

**目标**：判断年末归母股东权益是否可能转负。

**方法**：
1. 取最新一期 `balancesheet.total_hldr_eqy_exc_min_int`（最新中报或三季报），记为 `current_eq`。
2. 计算 `eq_year_end_est = current_eq + 剩余季度净利润预测 − 当前年度已实施现金分红总额`。
   - 剩余季度净利润：中报基准用 R1 的 H2 预测，三季报基准用 R1 的 Q4 预测。
   - 已实施分红总额：见 R3 的去重 + 量纲公式 `cash_div_tax / 10 × total_share`。

**触线判定**（统一相对阈值，单位：元）：
- 高风险：`current_eq < 0` 或 `eq_year_end_est < 0`
- 中风险：`0 ≤ eq_year_end_est < 1e8`（1 亿元）
- 低风险：`eq_year_end_est ≥ 1e8`

**注意**：商誉减值、长期股权投资减值在 Q3/Q4 集中确认，应在备注提示"若计提大额减值，净资产可能进一步下行"，但**不得在没有公告依据时擅自减值**。

### R3 分红达标前瞻

**目标**：判断"近三年累计现金分红 < 年均净利润 30% 且 < 板块累计阈值"是否会在下一次年度考核时同时满足（监管原文：两条件**同时**触发才警示）。

**单笔分红量纲公式**（**必须用此公式，不要用 `cash_div_tax × base_share`**）：

```
cash_dividend_total = cash_div_tax / 10 × total_share
```

其中 `cash_div_tax` 来自 `dividend`（每 10 股派现金额，含税），`total_share` 来自 `daily_basic.total_share`（最新总股本，单位万股 → 需 ×1e4 换成股）或 `stock_basic`。tushare `dividend.base_share` 字段对很多公司为 None，**禁止直接使用**。

**方法**：
1. 用 `dividend` 拉取该 `ts_code` 近五年记录，按 `(end_date, ann_date, cash_div_tax)` 三元组**强制去重**——同一笔分红 tushare 会返回"预案/股东大会通过/实施"3-4 行。
2. 折算系数（按 `div_proc` 状态）：`实施=1.0` / `股东大会通过=0.7` / `预案=0.5`；同一 `end_date` 取系数最高那条。
3. 用 `income` 拉取近三年完整年度归母净利润（period=YYYY1231）。
4. 计算考核窗口 = `[当前年-2, 当前年]`，即"过去两年已落地分红 + 本年度预计分红"。
5. 本年度预计分红：
   - 若 `dividend` 已查到本年度记录：按上面折算系数计入。
   - 否则用"过去两年平均分红率"× R1 预测全年净利润（基准情景）做估算，可信度降一档。
6. 与年均净利润比较：
   - 条件 A：`cumulative_div_3y < 30% × avg_n_income_3y`
   - 条件 B：`cumulative_div_3y < 板块累计阈值`
7. 创业板 / 科创板若研发投入占比满足豁免条件，备注提示"研发达标可能豁免"。

**触线判定**：
- 高风险：A 和 B 同时满足 **且** 过去三年至少一年净利润为正（即"盈利年份未达标"——监管以盈利年为基准）。
- 中风险：仅一个条件满足；或本年度分红尚未公告。
- 低风险：累计分红已稳定达标；或过去三年累计净利润 ≤ 0（无分红基础，按 R1 联动）。

**禁止**：本年度尚未公告分红时，不得断言"必然不达标"，只能给出概率。

### R4 连续亏损 / 扣非亏损链

**目标**：判断是否会触发"连续两年扣非前后净利润孰低者为负" → *ST。

**口径关键**：监管原文是**连续两年**（不是三年），且 *ST 财务类强制退市的法定条件是 **"亏损 + 营收<板块阈值" 必须同时满足**——只看亏损链会系统性高估风险（实证：闻泰科技 2024 年亏损但营收超千亿，不会被 *ST）。

**方法**：
1. 取过去一年完整年报的 `n_income`、`fina_indicator.profit_dedt`，记 `worst_last = min(n_income, profit_dedt)`、`revenue_last`。
2. 用 R1 已经预测好的 `worst_profit_est` 和 `revenue_full_year_est`（基准情景），对应当前年度。
3. 检查两年的 `worst < 0` 组合，**并叠加营收联动条件**。

**触线判定**（双条件，亏损链 + 营收联动）：
- 高风险：`worst_last < 0` 且 `worst_profit_est < 0`，**且**（R1 当前年命中高风险 **或** `revenue_full_year_est < 板块阈值 × 1.5`）——即两年均亏 + 营收处于退市风险区间。
- 中风险：(a) 连续两年均亏但营收远超阈值（≥ 阈值 × 1.5）——亏损链成立但不会触发财务类 *ST，仍可能因经营恶化转 ST；(b) 仅 `worst_profit_est < 0`（当前年预测亏损，去年盈利，未形成连续）；(c) 仅 `worst_last < 0` 但当前年预测为正且接近 0（< 板块阈值 × 0.5）。
- 低风险：`worst_last ≥ 0` 且 `worst_profit_est ≥ 0`。

**为什么要叠加营收**：A 股 *ST 财务类强制退市的法定条件是"扣非前后净利润孰低 < 0 **且** 营收 < 板块阈值"，二者必须同时满足。仅亏损不达营收阈值的公司（如大型周期股短期亏损）会被市场和监管视作"周期性亏损"而非"持续经营存疑"。

## 第五步：三项事实/临界证据面（不参与预测可信度）

### E1 审计意见（事实）

调用 `fina_audit`，取最近 2 个完整年报：
- 高风险：最新年报 `audit_result` 含"无法表示意见"或"否定意见"；**或单次出现"保留意见"**（实证支持：上交所近年规范类 *ST 案例多为单次保留即触发）。
- 中风险：连续两年同一负面结论但本期已修正；或带强调事项段的无保留意见涉及持续经营。
- 低风险：标准无保留意见。

**禁止预测下一份审计意见**——审计是事后行为。

**akshare 兜底缺失时的人工核查路径**（`fina_audit` 无 akshare 替代接口，必须给出可点击 URL）：

| 来源 | URL 模板 | 查询方式 |
|------|---------|---------|
| 巨潮资讯网（公告原文，权威） | `http://www.cninfo.com.cn/new/disclosure/stock?orgId=&stockCode={code6}` | 进入页面后筛选"定期报告 → 年度报告"，下载 PDF 在第十节"财务报告 → 审计报告"查 `审计意见类型` |
| 巨潮高级搜索（按关键词） | `http://www.cninfo.com.cn/new/fulltextSearch/full?searchkey={code6}+审计报告&sdate=&edate=&isfulltext=false&sortName=time&sortType=desc` | 直接命中含"审计报告"标题的公告 |
| 上交所信息披露 | `http://www.sse.com.cn/disclosure/listedinfo/regular/?stockCode={code6}` | 仅限 60xxxx / 688xxx |
| 深交所信息披露 | `http://www.szse.cn/disclosure/listed/notice/index.html?stock={code6}` | 仅限 00xxxx / 30xxxx |

其中 `{code6}` 为 6 位股票代码（去掉 `.SH` / `.SZ` 后缀）。**强制要求**：当 `fina_audit` 返回空时，输出报告的"备注"必须列出上面巨潮的两条 URL 之一，便于用户人工核查；不得只写一句"审计意见数据缺失"了事。

### E2 监管处罚（事实，双窗口：上一财年 + 过去 12 个月）

**这是本 skill 的关键证据面。**

**窗口规则（双窗口策略，单次抓取在内存中切片）**：

- 窗口 A — `[当前年-1 的 1 月 1 日, 当前年-1 的 12 月 31 日]`（上一个完整财年）：用于 reason_normalized 单条评级。
- 窗口 B — `[分析日 - 365 天, 分析日]`（过去 12 个月滚动）：用于**频次增强规则**。
- 若分析时点已经在 5 月之后且最新年报已披露完毕，窗口 A 可改为 `[最新年报 end_date - 365 天, 最新年报 end_date]`。

**调用方式（推荐：单次拉全量 + 内存切片）**：

```bash
python agent/src/skills/ashare-pre-st-filter/scripts/fetch_sina_penalties.py \
  --ts-code 000729.SZ --stock-name 燕京啤酒 --no-filter
```

返回页面全量记录后，由 LLM 在内存中按窗口 A、窗口 B 切两份。也可以用 `--start-date / --end-date` 单独抓取，但同一次分析**避免发起两次 HTTP**。

输出 JSON 列表，字段：`ann_date / event_type / title / reason / reason_normalized / content / issuer / issuer_normalized / subject_normalized / target_relevance / e2_countable / source_url`。

**相关性铁律**：调用脚本时必须传入 `--stock-name {股票简称}`（来自 `stock_basic.name`），必要时用 `--alias` 补充曾用名/简称。新浪页面可能收录“某个人证券账户交易列表里出现目标股票”的记录，这类记录只说明目标股票被交易过，**不是上市公司/股东/董监高处罚**。脚本会将其标为 `target_relevance=security_mention_only` 且 `e2_countable=false`，E2 频次统计必须排除。

**`subject_normalized` 字段**（用于频次权重折算）：
- `company` — 处罚主体是公司本身（默认；不含个人身份关键词时归此类）
- `shareholder` — 控股股东 / 实控人 / 5% 以上大股东
- `officer` — 董事 / 监事 / 高管（董事长、总经理、董秘、财务总监等）

**风险等级判定**：

| 命中 `reason_normalized` | 等级贡献 |
|---|---|
| 财务造假 / 虚假陈述 / 信息披露违规 | 高（强烈预警） |
| 违规担保 / 占用资金 | 高（直接触及 ST 红线） |
| 内幕交易 / 市场操纵 / 违规减持 | 中 |
| 其他/unknown | 低（仅作背景） |

**频次增强规则（治理质量预警，窗口 B）**：

监管函本身反映公司治理与内控质量，密集出现是"规范类 ST"（保留意见、内控非标、信披重大缺陷）的强领先指标。但**处罚主体不同，治理含义不同**：股东减持违规、董监高短线交易反映的是个人合规问题，不应等同于"公司治理失序"。

**主体加权计数**（按 `subject_normalized` 折算后再查表）：

```
加权条数 = Σ 单条权重
  其中：subject_normalized == "company"     → 权重 1.0
        subject_normalized == "officer"     → 权重 0.5
        subject_normalized == "shareholder" → 权重 0.5
```

| 过去 12 个月监管函/问询/警示函**加权条数** | 频次等级 |
|---|---|
| ≥ 5.0 | **极高** |
| 3.0 - 4.5 | 高 |
| 2.0 - 2.5 | 中 |
| < 2.0 | 低 |

**判定来源**：仅当 `e2_countable=true` 时，脚本输出的 `event_type ∈ {警示, 问讯, 监管关注, 监管函}` 或 `issuer_normalized ∈ {上交所, 深交所, 北交所, 证监会, 地方证监局}` 才计入条数；条数按 `subject_normalized` 折算后再查表。`target_relevance=security_mention_only` 的记录必须排除。

**输出要求**：必须同时给出"原始条数"和"加权条数"两个数字，便于用户审阅折算逻辑。例如：`窗口 B 命中 6 条（公司 2 条 + 股东 3 条 + 高管 1 条 → 加权 4.0 条），频次等级：高`。

**E2 综合等级合成规则**（解决单条评级与频次叠加的问题）：

```
E2_单条等级 = 窗口 A 内所有 reason_normalized 单条等级的最大值
E2_频次等级 = 窗口 B 频次表查得
E2_综合等级 = max(E2_单条等级, E2_频次等级)
```

**叠加加成**：若同时满足 `E2_频次等级 ≥ 高` 且 `E2_单条等级 ≥ 高`（含财务造假/虚假陈述/违规担保/占用资金）→ **直升极高**。

**为什么要这条规则**：纯量化红线只能捕捉"财务类 ST"，无法预警"规范类 ST"。频次规则把"治理失序"作为前瞻信号纳入。

**注意**：处罚证据**只抬升风险等级，不影响预测可信度**——这是事实证据，不是预测项。

### E3 交易类临界预警（事实）

调用 `daily`（近 30 个交易日，**必须 `adjust=''` 不复权**）和 `daily_basic`（最新一日，单位：万元）：

**1 元退市预警**（用 `daily.close`，**不复权**）：
- 高风险：近 20 个交易日中收盘价 < 1 元的天数 ≥ 10
- 中风险：≥ 1 但 < 10
- 低风险：0 天

**市值退市预警**（用 `daily_basic.total_mv`，单位万元 → ×1e4 换算成元 → /1e8 换算成亿元）：

| 板块 | 高风险阈值 | 中风险阈值 |
|---|---|---|
| 主板 | < 5 亿 | < 5 × 1.5 = 7.5 亿 |
| 创业板 / 科创板 | < 3 亿 | < 3 × 1.5 = 4.5 亿 |

## 第六步：双轴输出模板

每次分析必须按下面模板输出。**风险等级 + 可信度两个维度都要给**。

```markdown
## ST 风险预测：{name}（{ts_code}）

### 当前状态
- 是否已 ST/*ST：{是 / 否}
- 板块：{主板 / 创业板 / 科创板}
- 基准预测时点：{forecast / express / 三季报（period） / 中报（period）}

### 量化红线预测（双轴）

| 红线 | 基准情景结论 | 风险等级 | 可信度 | 主要证据 |
|------|-------------|---------|-------|---------|
| R1 营收+净利润 | 全年营收预测 X 亿，净利润 Y 亿 | 高/中/低 | 高/中高/中/低 | forecast/三季报/... |
| R2 年末净资产 | 当前 X 亿，年末预计 Y 亿 | 高/中/低 | 高/中高/中/低 | balancesheet + R1 |
| R3 分红达标 | 三年累计预计 X，对应阈值 Y | 高/中/低 | 中/低 | dividend + income |
| R4 连续亏损链 | 过去两年 + 当前年是否均亏 | 高/中/低 | 同 R1 | income + fina_indicator |

### 事实证据面（不参与预测可信度）

| 证据 | 结论 | 影响 |
|------|------|------|
| E1 审计意见 | 最新结论 | 抬升/无影响 |
| E2 监管处罚（窗口 A 上一财年 / 窗口 B 过去 12 个月） | A 命中 Na 条（最高单条等级：…），B 原始 Nb_raw 条 / 加权 Nb_w 条（公司 a + 股东 b + 高管 c → a×1.0+b×0.5+c×0.5），频次等级：…，E2_综合等级：… | 抬升/无影响 |
| E3 交易类临界 | 收盘价/市值情况 | 抬升/无影响 |

### 综合结论
- **下一财年被 ST/*ST 风险等级**：{极高 / 高 / 中 / 低}
- **预测综合可信度**：{高 / 中高 / 中 / 低}
- **关键风险点**（最多 3 条）：...
- **缓解信号**（如有）：...

### 备注
- 数据时点：{所用最新报告期}
- 已忽略的不可预测项：财务造假、未来审计意见
- 季节性提醒（如适用）：...
```

## 禁止事项

1. 不预测财务造假（事前不可知）。
2. 不预测下一份审计意见（事后才出）。
3. 不在没有公告依据时擅自计提减值。
4. 不混用板块阈值（主板 vs 创业板/科创板的营收/市值/分红阈值不同）。
5. 不把机械年化（H1×2、Q1Q3×4/3）伪装成"高可信度"。
6. 不在港股 / 美股 / 加密 / **北交所**（`8xxxxx.BJ`，监管规则与本 skill 阈值不一致）上启用本 skill。
7. 不把"违规处罚记录"计入预测可信度（仅抬升风险等级）。
8. 不在 R3 分红计算中使用 `cash_div_tax × base_share`（base_share 经常为 None，会得 0）；必须用 `cash_div_tax / 10 × total_share`，且按 `(end_date, ann_date, cash_div_tax)` 三元组去重。
9. 不在 R1 触线判定中只用 `n_income`；必须用 `min(n_income, profit_dedt)`，否则会漏掉造壳公司。
10. 不把 R4 写成"连续三年"；监管原文是"连续两年"。**且 R4 高风险必须叠加营收联动条件**——仅"连续两年亏损"不构成 *ST 财务类强制退市，必须同时满足"营收 < 板块阈值 × 1.5"或 R1 已命中高风险，否则只能给中风险。
11. 不把 E2 监管处罚"按主体一刀切"计数——必须用 `subject_normalized` 加权（公司 ×1.0 / 股东 ×0.5 / 董监高 ×0.5），否则股东动荡的公司会被系统性高估。

## 依赖的 tushare 接口清单

| 用途 | 接口 | 备注 |
|------|------|------|
| 当前 ST 状态 | `stock_st` | 3000 积分；不可用时回退 `namechange` |
| 历史改名 | `namechange` | 免费 |
| 板块判断 | `stock_basic` | 免费 |
| 利润表 | `income` | 2000 积分，多 period 拉取 |
| 资产负债表 | `balancesheet` | 2000 积分 |
| 财务指标（扣非等） | `fina_indicator` | 2000 积分 |
| 业绩预告 | `forecast` | 2000 积分 |
| 业绩快报 | `express` | 2000 积分 |
| 审计意见 | `fina_audit` | 500 积分 |
| 分红 | `dividend` | 2000 积分 |
| 日线 | `daily` | 免费 |
| 每日指标（市值） | `daily_basic` | 免费 |
| 财报披露日期 | `disclosure_date` | 500 积分 |

## 自带脚本

- [scripts/fetch_sina_penalties.py](scripts/fetch_sina_penalties.py) — 抓取新浪财经 vGP_GetOutOfLine 处罚页，stdlib 实现，无外部依赖；reason / issuer 标准化。

调用方式：

```bash
# 单次拉全量（推荐：本 skill 双窗口策略由 LLM 在内存中切片）
python agent/src/skills/ashare-pre-st-filter/scripts/fetch_sina_penalties.py \
  --ts-code 000729.SZ --stock-name 燕京啤酒 --no-filter

# 或指定单一窗口
python agent/src/skills/ashare-pre-st-filter/scripts/fetch_sina_penalties.py \
  --ts-code 000729.SZ --stock-name 燕京啤酒 --start-date 2025-01-01 --end-date 2025-12-31
```

正常情况下输出 JSON 到 stdout；网络/解析失败或参数非法时返回 `{"source": "unavailable", "error": "..."}` 到 stdout 并以非零退出码结束（不抛 traceback），便于 LLM 兜底处理。

## 端到端调用伪代码

用于减少 LLM 调用顺序漂移，按下列骨架组织：

```python
import os, json, subprocess
import tushare as ts

ts_code = '000729.SZ'
pro = ts.pro_api(os.environ['TUSHARE_TOKEN'])

# === Step 0: M0 当前状态 ===
basic = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,market').to_dict('records')[0]
st_hit = pro.stock_st()  # 失败则回退 namechange
name_chg = pro.namechange(ts_code=ts_code).sort_values('start_date', ascending=False)

# === Step 1: 板块判断 ===
board = '科创板' if ts_code.startswith('688') else '创业板' if ts_code.startswith('30') else '主板'
threshold_revenue = 1e8 if board != '主板' else 3e8
threshold_mv = 3e8 if board != '主板' else 5e8

# === Step 2: 拉财务（最新 5 期 + 过去 4 年年报） ===
income = pro.income(ts_code=ts_code).sort_values('end_date', ascending=False).drop_duplicates('end_date')
balance = pro.balancesheet(ts_code=ts_code).sort_values('end_date', ascending=False).drop_duplicates('end_date')
fina_ind = pro.fina_indicator(ts_code=ts_code).sort_values('end_date', ascending=False).drop_duplicates('end_date')
forecast = pro.forecast(ts_code=ts_code).sort_values('ann_date', ascending=False)
express = pro.express(ts_code=ts_code).sort_values('ann_date', ascending=False)

# === Step 3: R1-R4 计算（按各章节口径，注意 min(n_income, profit_dedt)） ===
# ... 略

# === Step 4: E1 审计 ===
audit = pro.fina_audit(ts_code=ts_code).sort_values('end_date', ascending=False).head(2)

# === Step 5: E2 监管处罚（双窗口 + 主体加权）===
from datetime import date, timedelta
result = subprocess.run([
    'python', 'agent/src/skills/ashare-pre-st-filter/scripts/fetch_sina_penalties.py',
    '--ts-code', ts_code, '--stock-name', basic['name'], '--no-filter',
], capture_output=True, text=True)
penalties = json.loads(result.stdout).get('records', [])

# 在内存中切双窗口（避免两次 HTTP）
this_year = date.today().year
win_a_start, win_a_end = f'{this_year-1}-01-01', f'{this_year-1}-12-31'
win_b_start = (date.today() - timedelta(days=365)).isoformat()
win_b_end   = date.today().isoformat()

def _in(rec, s, e):
    d = rec.get('ann_date') or ''
    return bool(d) and s <= d <= e

win_a = [r for r in penalties if _in(r, win_a_start, win_a_end)]
win_b = [r for r in penalties if _in(r, win_b_start, win_b_end)]

# 窗口 A：单条等级取最高
REASON_LEVEL = {
    '财务造假': 3, '虚假陈述': 3, '信息披露违规': 3,
    '违规担保': 3, '占用资金': 3,
    '内幕交易': 2, '市场操纵': 2, '违规减持': 2,
}
levels_a = [REASON_LEVEL.get(r['reason_normalized'], 1) for r in win_a]
e2_single = max(levels_a) if levels_a else 0

# 窗口 B：原始条数 + 主体加权条数
FREQ_EVENT_TYPES = {'警示', '问讯', '监管关注', '监管函', '警示函'}
FREQ_ISSUERS = {'上交所', '深交所', '北交所', '证监会', '地方证监局'}
SUBJECT_WEIGHT = {'company': 1.0, 'shareholder': 0.5, 'officer': 0.5}

freq_pool = [r for r in win_b
             if r.get('e2_countable', True)
             and (r['event_type'] in FREQ_EVENT_TYPES
                  or r['issuer_normalized'] in FREQ_ISSUERS)]
nb_raw = len(freq_pool)
nb_weighted = round(sum(SUBJECT_WEIGHT.get(r['subject_normalized'], 1.0)
                        for r in freq_pool), 1)

# 频次等级（基于加权条数）
if nb_weighted >= 5.0:    e2_freq = 4   # 极高
elif nb_weighted >= 3.0:  e2_freq = 3   # 高
elif nb_weighted >= 2.0:  e2_freq = 2   # 中
else:                     e2_freq = 1   # 低

e2_overall = max(e2_single, e2_freq)
# 叠加加成：频次高 + 单条高同时命中 → 直升极高
if e2_freq >= 3 and e2_single >= 3:
    e2_overall = 4

# === Step 6: E3 交易临界 ===
daily = pro.daily(ts_code=ts_code).sort_values('trade_date', ascending=False).head(30)
daily_basic = pro.daily_basic(ts_code=ts_code).sort_values('trade_date', ascending=False).head(1).iloc[0]
total_mv_yi = daily_basic['total_mv'] * 1e4 / 1e8  # 万元 → 亿元

# === Step 7: 双轴合成输出 ===
# 风险等级 = max(R1, R2, R3, R4, E1, E2_综合, E3)
# 可信度 = 加权平均(R1, R2, R3, R4 各项可信度)，akshare 兜底项降一档
```
