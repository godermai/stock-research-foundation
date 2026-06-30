# Skill: Industry Supply Chain Research

## Trigger
User asks about industry membership, peer sets, cyclicality, or supply chain mapping.

## Mandatory MCP Tools
- `get_industry_members` — fetch industry/sector membership
- `get_market_history` — pull peer price data
- `get_financial_metrics` — compare peer fundamentals

## Source Priority
1. Local industry tables → primary membership
2. Official/AKShare supplements → fill gaps
3. CSI/SW industry standards → classification authority

## Validation Rules
- Must identify which industry standard is used (SW, CSI, CNINFO)
- Must state the as-of date for industry membership
- Must not mix sector classifications without explicit notice
- Must list peer companies with their canonical symbols

## Forbidden Behavior
- **MAY NOT** mix sector classifications without saying so
- **MAY NOT** assume industry membership is static
- **MAY NOT** fabricate supply chain relationships without evidence

## Output Contract
```
## Industry Research: [industry] ([standard])
### Industry Map
- Standard: [SW/CSI/CNINFO]
- As-of date: [YYYY-MM-DD]
- Member count: [N]

### Peer Table
[symbol | name | market_cap | revenue | net_margin]

### Catalysts
- [Industry-level events, policy changes]

### Data Basis
- [Source, freshness, coverage notes]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
