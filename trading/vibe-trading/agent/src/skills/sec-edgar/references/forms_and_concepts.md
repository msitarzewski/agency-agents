# Common SEC forms & XBRL us-gaap concepts

Reference values for the `form` and `metric` parameters of `get_sec_filings`.

## Frequently used form types

Pass to the tool's `form` parameter (case-insensitive).

| Form | What it is | Cadence |
|------|------------|---------|
| `10-K` | Annual report — full-year financials, risk factors, MD&A | Annual |
| `10-Q` | Quarterly report — interim financials and MD&A | Quarterly |
| `8-K` | Current report — material events (M&A, exec change, guidance, restatement) | Event-driven |
| `DEF 14A` | Definitive proxy statement — exec comp, board, shareholder proposals | Annual |
| `4` | Insider transaction (Section 16) — insider buys/sells | Within ~2 business days |
| `13F-HR` | Institutional holdings (>$100M AUM) | Quarterly |
| `SC 13D` | >5% activist/strategic ownership stake | Event-driven |
| `SC 13G` | >5% passive ownership stake | Event-driven |
| `S-1` | Registration statement (IPO) | One-time |
| `424B` | Prospectus | As filed |
| `20-F` | Annual report for foreign private issuers | Annual |
| `6-K` | Foreign-issuer current report | Event-driven |

Omit `form` to return all recent forms newest-first.

## Frequently used us-gaap concepts

Pass to the tool's `metric` parameter. These are **exact, case-sensitive** XBRL taxonomy element names. A company reports only the concepts relevant to it, so a given name may be absent (the tool then returns an empty `points` list).

### Income statement

| Concept | Meaning |
|---------|---------|
| `Revenues` | Total revenue (some filers use `RevenueFromContractWithCustomerExcludingAssessedTax`) |
| `CostOfRevenue` | Cost of revenue / COGS |
| `GrossProfit` | Gross profit |
| `OperatingIncomeLoss` | Operating income |
| `NetIncomeLoss` | Net income |
| `EarningsPerShareBasic` | Basic EPS |
| `EarningsPerShareDiluted` | Diluted EPS |
| `ResearchAndDevelopmentExpense` | R&D expense |

### Balance sheet

| Concept | Meaning |
|---------|---------|
| `Assets` | Total assets |
| `Liabilities` | Total liabilities |
| `StockholdersEquity` | Shareholders' equity |
| `CashAndCashEquivalentsAtCarryingValue` | Cash & equivalents |
| `LongTermDebtNoncurrent` | Long-term debt (noncurrent) |
| `Goodwill` | Goodwill |

### Cash flow

| Concept | Meaning |
|---------|---------|
| `NetCashProvidedByUsedInOperatingActivities` | Operating cash flow |
| `NetCashProvidedByUsedInInvestingActivities` | Investing cash flow |
| `NetCashProvidedByUsedInFinancingActivities` | Financing cash flow |
| `PaymentsToAcquirePropertyPlantAndEquipment` | CapEx |
| `PaymentsForRepurchaseOfCommonStock` | Share buybacks |

## Notes

- Concept naming varies by filer and over time; if `Revenues` returns empty, try `RevenueFromContractWithCustomerExcludingAssessedTax`.
- Each metric point carries `end`, `val`, `fiscal_year`, `fiscal_period`, `form`, `accession`, and `frame`; use `fiscal_period` (`FY`, `Q1`–`Q4`) to separate annual from quarterly observations.
- The tool reports the unit bucket with the most rows (usually `USD` for monetary concepts, `USD/shares` for per-share concepts).
