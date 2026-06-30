# Skill: Investment Thesis Falsification

## Trigger
User presents a thesis and asks for disproof, risk analysis, or stress testing.

## Mandatory MCP Tools
- `compare_sources` — cross-source verification
- `get_announcements` — check for disconfirming events
- `get_financial_metrics` — verify or challenge fundamental claims
- `run_data_quality_check` — ensure data reliability before falsification

## Source Priority
1. Local curated tables → verify claims against data
2. Official documents (CNINFO) → check for material events
3. Cross-source comparison → detect data inconsistencies

## Validation Rules
- Must produce at least 3 disconfirming checks before endorsing a thesis
- Must explicitly state which assumptions are testable and which are not
- Must check for announcements that contradict the thesis
- Must verify data quality before drawing conclusions

## Forbidden Behavior
- **MAY NOT** produce one-sided bull or bear cases
- **MAY NOT** ignore disconfirming evidence
- **MAY NOT** present assumptions as facts

## Output Contract
```
## Thesis Falsification: [thesis statement]
### Thesis Assumptions
1. [assumption] — testable/untestable
2. [assumption] — testable/untestable

### Disconfirming Checks
1. [check] → [result] → [PASS/FAIL/BROKEN]
2. [check] → [result] → [PASS/FAIL/BROKEN]
3. [check] → [result] → [PASS/FAIL/BROKEN]

### Broken Assumptions
- [list of assumptions contradicted by data]

### Unresolved Unknowns
- [list of questions that cannot be answered with available data]

### Verdict
- [SUPPORTED / PARTIALLY_SUPPORTED / NOT_SUPPORTED / INCONCLUSIVE]
- [Confidence level and key caveats]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
