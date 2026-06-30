# Skill: Valuation and Earnings Sensitivity

## Trigger
User asks about valuation, scenario analysis, or forward sensitivity.

## Mandatory MCP Tools
- `get_market_history` — price data for valuation
- `get_financial_metrics` — earnings and fundamentals
- `get_corporate_actions` — dividend/split/adjustment context

## Source Priority
1. Local curated tables → primary
2. No upstream calls unless explicitly requested

## Validation Rules
- Must state whether prices are raw, qfq, or hfq
- Must state whether earnings are trailing twelve months or reported period
- Must state the adjustment basis for any valuation multiple
- Must disclose if corporate actions affect comparability

## Forbidden Behavior
- **MAY NOT** compare mixed adjustment modes (raw vs qfq vs hfq) without conversion
- **MAY NOT** use stale earnings without noting the report period
- **MAY NOT** fabricate forward estimates as if they were data

## Output Contract
```
## Valuation Analysis: [symbol] [name]
### Base Case
- Price (as of [date], [adjustment]): [close]
- EPS (TTM, [report_period]): [value]
- PE: [value]

### Sensitivity Table
[scenario | EPS assumption | PE assumption | target price]

### Data Basis
- Price source: [source, adjustment, date]
- Earnings source: [source, period, cumulative/single_quarter]
- Corporate actions: [any recent splits/dividends]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
