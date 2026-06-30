# Skill: Announcement Event Research

## Trigger
User asks about events, filings, restatements, M&A, governance, or risk questions.

## Mandatory MCP Tools
- `get_announcements` — fetch announcement metadata
- `search_announcements` — text search across announcements
- `compare_sources` — verify announcement data across sources

## Source Priority
1. CNINFO/local announcement store → first and canonical
2. Exchange websites → verify if CNINFO is incomplete
3. AKShare CNINFO wrappers → fallback only

## Validation Rules
- Must cite document date, category, and local file path for each referenced announcement
- Must note if PDF text parse is partial or failed
- Must check for amendment/correction announcements
- Must flag if announcement count seems incomplete for the date range

## Forbidden Behavior
- **MAY NOT** summarize unseen files as certain
- **MAY NOT** claim to have read a PDF if text extraction was not done
- **MAY NOT** fabricate announcement content

## Output Contract
```
## Event Research: [symbol] [topic]
### Event Timeline
- [date] | [title] | [category] | [source] | [local_path]

### Key Findings
- [Summary of relevant announcements]

### Uncertainties
- [Unparsed PDFs, missing periods, amendment flags]

### Source Notes
- [Coverage, freshness, parse status]
```

## Hard Rules
1. Do not fabricate missing data
2. Prefer local curated tables
3. If data are stale, say how stale
4. If two sources disagree, surface the disagreement
