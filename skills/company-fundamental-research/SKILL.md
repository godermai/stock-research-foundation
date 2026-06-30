# Skill: Company Fundamental Research

## Trigger
User asks about company quality, growth, cash flow, or balance sheet analysis.

## Mandatory MCP Tools
- `search_security` — find the company
- `get_financial_statements` — pull income/balance/cashflow
- `get_financial_metrics` — compact metrics panel
- `get_announcements` — check for recent material announcements

## Source Priority
1. Local curated financial_statement → primary numbers
2. CNINFO docs → verify disclosure dates and amendments
3. Tushare lineage → trace data provenance

## Validation Rules
- Must separate reported (cumulative) numbers from derived single-quarter values
- Must state the report period and announcement date for each data point
- Must check for amendment announcements that may change prior figures
- Must note if any quarter's single-quarter value is NULL (missing prior cumulative)

## Forbidden Behavior
- **MAY NOT** invent missing quarter data
- **MAY NOT** mix cumulative and single-quarter values without labeling
- **MAY NOT** compare financials across different accounting standards without noting

## Output Contract
```
## Company Fundamental Analysis: [symbol] [name]
### Data Basis
- Source: [tushare/cninfo]
- Latest report period: [YYYY-MM-DD]
- Data freshness: [last sync time]

### Key Financials (single-quarter)
[Table: period | revenue | net_profit | operating_cf]

### Red Flags
- [List of concerns: declining margins, rising debt, etc.]

### Source Notes
- [Provenance, caveats, amendment history]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
