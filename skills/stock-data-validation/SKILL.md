# Skill: Stock Data Validation

## Trigger
User asks "is this data reliable?" or before producing a major report.

## Mandatory MCP Tools
- `compare_sources` — cross-source consistency check
- `run_data_quality_check` — schema and unit validation
- `get_data_freshness` — staleness assessment

## Source Priority
1. Local curated tables → primary truth
2. Secondary source diffs → Tushare vs AKShare vs BaoStock
3. Official verify → CNINFO/exchange for announcements

## Validation Rules
- Must state row counts for each table checked
- Must report diff tolerances and any breaches
- Must list failed checks with remediation hints
- Must state data freshness (last sync time, latest data date)

## Forbidden Behavior
- **MAY NOT** silently average conflicting sources
- **MAY NOT** hide failed checks
- **MAY NOT** claim data is "verified" without running DQ checks

## Output Contract
```
## Validation Summary
- Tables checked: [list]
- Freshness: [table -> last_sync, latest_data_date]
- DQ results: [suite, pass/fail counts]
- Cross-source diffs: [table, symbol, max_diff, tolerance, breach?]
- Caveats: [list of warnings]
- Verdict: [PASS / PASS_WITH_CAVEATS / FAIL]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
