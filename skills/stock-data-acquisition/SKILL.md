# Skill: Stock Data Acquisition

## Trigger
User asks to ingest, refresh, or build data tables.

## Mandatory MCP Tools
- `get_data_freshness` — check current state before syncing
- `run_data_quality_check` — verify data after sync
- `export_dataset` — produce extract if requested

## Source Priority
1. Local metadata → check what's stale
2. Upstream adapters (Tushare primary, AKShare/BaoStock secondary) → only if stale
3. CNINFO → for announcements

## Validation Rules
- Must report which tables were refreshed and which remain stale
- Must cite row counts and latest dates after sync
- Must run DQ checks after any sync operation

## Forbidden Behavior
- **MAY NOT** claim sync succeeded without freshness evidence
- **MAY NOT** fabricate data counts or dates
- **MAY NOT** skip DQ checks after loading new data

## Output Contract
```
## Sync Report
- Run ID: [run_id]
- Tables refreshed: [list with row counts]
- Tables still stale: [list with reason]
- DQ check results: [pass/fail summary]
- Next action: [recommended next step]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
