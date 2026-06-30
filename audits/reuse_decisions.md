# Reuse Decisions

## Phase 1 Reconnaissance Audit - Repository Reuse Decisions

This document provides clear reuse decisions for each target repository, including decision rationale, reusable code/patterns, non-reusable parts, and integration recommendations.

---

## 1. AkShare (akshare) - FORK

### Decision Rationale
AkShare is the largest Chinese financial data interface library with 27k+ stars and active community maintenance. It requires no official token, uses web scraping on public data, and has the widest coverage (stocks, futures, funds, bonds, forex, crypto). While scraped data stability is relatively poor, as a free data source it offers excellent value. The high community activity and prompt problem resolution make it suitable as one of the primary data sources for this project.

### Reusable Code/Patterns
- **HTTP client wrapping**: `requests` + `curl_cffi` for JavaScript rendering
- **Anti-scraping strategies**: User-Agent rotation, Cookie management, request header disguising
- **Data parsing patterns**: BeautifulSoup + lxml for HTML parsing, jsonpath for JSON extraction
- **Modular design**: Module division by data source (`stock/`, `fund/`, `bond/`)
- **Error handling**: Retry mechanisms, exception handling, logging patterns

### Non-Reusable Parts
- **Overall architecture**: Overly large codebase, many modules unused
- **Scraping implementations**: Frequent website structure changes, high maintenance cost
- **Dependency management**: Complex dependencies that can be simplified
- **Test framework**: Incomplete test coverage, needs redesign

### Integration Recommendations
1. **Selective borrowing**: Only borrow core modules (stock quotes, financial data)
2. **Interface simplification**: Simplify API interfaces, standardize parameter naming
3. **Data validation**: Add data quality checks and outlier handling
4. **Local-first priority**: Prioritize storage of scraped data to local database
5. **Monitoring mechanisms**: Establish interface availability monitoring for timely issue detection

---

## 2. EFinance (efinance) - BORROW

### Decision Rationale
EFinance focuses on East Money data sources with high code quality and 3.8k stars. Based on East Money official API interfaces, data quality is superior to scraping and suitable for real-time data acquisition. While rate limiting issues exist, the community is developing server-side solutions. Active project maintenance makes it suitable as the primary source for real-time quotes and financial data.

### Reusable Code/Patterns
- **API call patterns**: East Money API call parameters and response parsing
- **Session management**: requests.Session connection pool management
- **Real-time data streams**: WebSocket or long-polling real-time data acquisition patterns
- **Financial data interfaces**: Standardized financial statement data structures
- **Rate limiting handling**: Rate limiting detection based on response headers and status codes

### Non-Reusable Parts
- **Overall architecture**: Relatively simple project structure, not modular enough
- **Caching mechanisms**: Lacks comprehensive caching strategies
- **Error recovery**: Incomplete error handling
- **Documentation**: API documentation lacks detail

### Integration Recommendations
1. **API interfaces**: Directly reuse East Money API call code
2. **Rate limiting optimization**: Add intelligent rate limiting and request queue management
3. **Data normalization**: Convert data formats to project standard format
4. **Local caching**: Prioritize caching API results to local storage
5. **Monitoring alerts**: Monitor API availability and rate limiting status

---

## 3. Mootdx (mootdx) - ADOPT

### Decision Rationale
Mootdx is a wrapper based on TongDaXin (TDX) data with 2k stars. TDX servers are stable and reliable, providing real-time and historical K-line data with high code quality and good maintenance. As a Python interface to TDX data, it's the optimal choice for K-line data acquisition, especially suitable for local deployment.

### Reusable Code/Patterns
- **TDX protocol**: pytdx protocol implementation and wrapping
- **Server selection**: Automatic optimal server matching algorithm
- **Connection management**: Connection pool management and reconnection mechanisms
- **K-line data**: Standardized K-line data format
- **Multi-market support**: A-shares, Hong Kong stocks, futures market data interfaces

### Non-Reusable Parts
- **Financial data**: Limited financial data interfaces, not comprehensive enough
- **Missing documentation**: API documentation not detailed enough
- **Test coverage**: Test cases not comprehensive enough
- **pytdx dependency**: pytdx library updates not active enough

### Integration Recommendations
1. **K-line data**: Primarily used for historical K-line and real-time quote acquisition
2. **Connection optimization**: Optimize connection pool, reduce connection overhead
3. **Data validation**: Add quality checks for K-line data
4. **Local storage**: Prioritize K-line data storage to local database
5. **Backup solution**: Use as backup data source for EFinance

---

## 4. Tushare (tushare) - FORK

### Decision Rationale
Tushare is a professional financial data interface with 11k+ stars and the highest data quality, but requires paid tokens. Limited free quota (120 calls per day) makes it unsuitable for high-frequency use. After forking, can use free interface portions or use as reference for data quality validation. Official maintenance with comprehensive documentation, but cost considerations make it unsuitable as primary data source.

### Reusable Code/Patterns
- **Data structures**: Standardized financial data field definitions
- **API design**: RESTful API design patterns
- **Authentication mechanisms**: Token authentication and permission management
- **Rate limiting algorithms**: API call frequency limit implementation
- **Error handling**: Standardized error response handling

### Non-Reusable Parts
- **Paid dependency**: Most features require paid tokens
- **Free restrictions**: Free quota too small, practical utility limited
- **Cost considerations**: High long-term usage cost
- **Closed dependency**: Overly dependent on tushare platform

### Integration Recommendations
1. **Free interfaces**: Only use free interface portions
2. **Data validation**: Use to validate data quality from other sources
3. **Supplementary data**: Supplement when other data sources are missing
4. **Cost evaluation**: Evaluate cost-effectiveness of paid usage
5. **Backup solution**: Use as optional extension for advanced features

---

## 5. BaoStock (baostock) - ADOPT

### Decision Rationale
BaoStock provides free API access with historical data focus. Server reliability issues exist but no cost. Adopt as backup source, implement robust retry logic and local fallback. Completely free, suitable for personal research and historical K-line analysis.

### Reusable Code/Patterns
- **Session management**: Login/session-based connection handling
- **Historical data**: Standardized historical K-line data interfaces
- **Data formatting**: Consistent data format across different time periods
- **Error handling**: Connection error handling and retry logic

### Non-Reusable Parts
- **Limited real-time**: Not suitable for real-time data
- **Server instability**: Occasional server reliability issues
- **Documentation**: API documentation could be more comprehensive
- **Limited coverage**: Mainly historical data, limited real-time capabilities

### Integration Recommendations
1. **Historical focus**: Use primarily for historical K-line data backfill
2. **Robust retry**: Implement comprehensive retry logic with exponential backoff
3. **Local fallback**: Cache all data locally for server outage resilience
4. **Data validation**: Cross-validate with other sources when possible
5. **Backup role**: Use as secondary source behind Mootdx

---

## 6. CNINFO Scrapers (cninfo-scrapers) - FORK

### Decision Rationale
Specialized CNINFO disclosure scrapers with narrow focus but valuable for regulatory filings. Fork to extract announcement parsing logic and PDF handling. Essential for compliance and regulatory research requiring official company announcements.

### Reusable Code/Patterns
- **Announcement parsing**: CNINFO announcement content extraction
- **PDF handling**: Financial report PDF download and processing
- **Regulatory categorization**: Announcement type classification
- **Date normalization**: Standardized announcement date handling

### Non-Reusable Parts
- **Fragile dependencies**: Heavy reliance on CNINFO website structure
- **Limited scope**: Only covers announcements, not general market data
- **Maintenance burden**: High maintenance due to website changes
- **Processing complexity**: PDF parsing requires additional tools

### Integration Recommendations
1. **Extract parsers**: Isolate announcement parsing logic for reuse
2. **PDF processing**: Implement robust PDF download and parsing pipeline
3. **Caching strategy**: Cache announcements locally to reduce scraping needs
4. **Monitoring**: Track CNINFO website structure changes
5. **Specialized use**: Deploy only when regulatory filing analysis is needed

---

## 7. Multi-Source Aggregator (multi-source-aggregator) - BORROW

### Decision Rationale
Aggregator pattern with local caching and good architecture reference. Borrow data fusion and caching patterns, not the web dependencies. Provides excellent blueprint for building local-first data architecture with unified multi-source interfaces.

### Reusable Code/Patterns
- **Data fusion**: Multi-source data combination and conflict resolution
- **Caching architecture**: Local DuckDB/Parquet caching implementation
- **Fallback mechanisms**: Automatic source switching on failures
- **Quality scoring**: Data quality assessment and source ranking
- **Unified interfaces**: Consistent API across multiple data sources

### Non-Reusable Parts
- **Web dependencies**: External API dependencies to be replaced
- **Complex coordination**: Multi-source orchestration complexity
- **Maintenance overhead**: Need to track changes in all underlying sources
- **Performance overhead**: Aggregation layer performance considerations

### Integration Recommendations
1. **Architecture blueprint**: Use as reference for local data architecture
2. **Pattern borrowing**: Adopt caching and data fusion patterns
3. **Local-first**: Replace external sources with local data storage
4. **Simplified coordination**: Start with fewer sources, expand gradually
5. **Performance focus**: Optimize caching and query performance

---

## 8. EFinance Wrapper (efinance-wrapper) - REJECT

### Decision Rationale
Thin wrapper around efinance with no added functionality. Redundant dependency layer that adds complexity without value. Reject - use efinance directly instead of adding unnecessary abstraction.

### Non-Reusable Parts
- **No added value**: Pure wrapper with no additional functionality
- **Redundant layer**: Unnecessary dependency indirection
- **Maintenance burden**: Additional code to maintain for no benefit
- **Version coupling**: Tied to efinance version changes

### Integration Recommendation
Use efinance directly; this wrapper adds no value.

---

## 9. AkShare Lite (akshare-lite) - REJECT

### Decision Rationale
Subset of akshare with web scraping focus. No advantage over full akshare. Reject - use main akshare if needed; this lite version provides no benefits.

### Non-Reusable Parts
- **Limited functionality**: Subset with no clear advantages
- **Maintenance duplication**: Duplicates maintenance effort
- **Unclear differentiation**: No compelling reason to use over full akshare

### Integration Recommendation
Use full akshare or other libraries; this lite version serves no purpose.

---

## 10. Stock Quant API (stock-quant-api) - REJECT

### Decision Rationale
Unmaintained web scraping project. Last release 2023. Reject - code too stale for reuse, likely broken dependencies and outdated scraping logic.

### Non-Reusable Parts
- **Stale codebase**: 2+ years without updates
- **Broken dependencies**: Likely incompatible with current Python/packages
- **Outdated scraping**: Website structures likely changed significantly
- **No maintenance**: Abandoned project with no support

### Integration Recommendation
Avoid entirely; use actively maintained alternatives.

---

## 11. Eastmoney Bridge (eastmoney-bridge) - REJECT

### Decision Rationale
Bridge to East Money private APIs. Requires reverse engineering. Reject - too fragile, use official efinance instead of unofficial API bridges.

### Non-Reusable Parts
- **Fragile reverse engineering**: Likely to break without notice
- **Unsupported APIs**: No official support or documentation
- **Legal concerns**: Terms of service violations possible
- **Unnecessary risk**: Official efinance provides similar functionality

### Integration Recommendation
Use official efinance library; avoid unsupported private API bridges.

---

## 12. China Stock Data (china-stock-data) - REJECT

### Decision Rationale
Web scraping wrapper around East Money. Adds no value over efinance, less mature. Reject - use efinance patterns directly instead of less mature wrapper.

### Non-Reusable Parts
- **Redundant functionality**: Duplicates efinance capabilities
- **Less mature**: Less developed than established alternatives
- **No differentiation**: No compelling features over efinance

### Integration Recommendation
Use efinance directly; this wrapper provides no advantages.

---

## Overall Integration Strategy

### Primary Data Source Combination
1. **Real-time quotes**: EFinance (primary) + Mootdx (backup)
2. **Historical K-lines**: Mootdx (primary) + BaoStock (backup)
3. **Financial data**: EFinance (primary) + AkShare (backup)
4. **Announcement data**: Dedicated scrapers + AkShare reference
5. **Macro economic**: AkShare (primary)

### MCP Architecture
1. **Foundation**: Fork akshare-one-mcp as base
2. **Tool expansion**: Extend with 11 localized tools
3. **Multi-source support**: Unified interface supporting multiple data sources
4. **Configuration management**: Comprehensive config and environment management

### Local Storage Architecture
1. **Data lake**: DuckDB + Parquet
2. **Layered design**: Bronze (raw) → Silver (normalized)
3. **Incremental updates**: Timestamp-based incremental updates
4. **Data quality**: Comprehensive data quality checks

### Skills Architecture
1. **Template**: Based on baostock-skill template
2. **7 Skills**: Develop 7 specialized skills per requirements
3. **Unified format**: Consistent SKILL.md format
4. **Example code**: Complete examples for each skill

---

## Implementation Priorities

### High Priority (Immediate Adoption)
1. **AkShare**: Primary data acquisition interface
2. **EFinance**: Real-time and financial data
3. **Mootdx**: K-line data acquisition
4. **akshare-one-mcp**: MCP server foundation

### Medium Priority (Reference Use)
1. **BaoStock**: Backup K-line data source
2. **investment_data**: Data pipeline design reference
3. **baostock-skill**: Skill development template

### Low Priority (Cautious Reference)
1. **Tushare**: Free interface portions only
2. **zer0share**: Factor calculation reference
3. **tushare_MCP**: Interface definition reference

### Not Adopted (Concept Reference Only)
1. **TushareDB**: Data storage design concepts
2. **CnInfoReports**: Announcement processing concepts
3. **Annualreport_tools**: Annual report processing concepts

---

## Decision Categories Explained

### ADOPT
- **Criteria**: High-quality, actively maintained, aligns with local-first architecture
- **Usage**: Direct integration into project as core dependency
- **Examples**: Mootdx, BaoStock, akshare-one-mcp

### FORK
- **Criteria**: Valuable components but requires modification for local-first use
- **Usage**: Fork repository, remove external dependencies, adapt to local architecture
- **Examples**: AkShare, Tushare, CNINFO scrapers

### BORROW
- **Criteria**: Good patterns/design but not suitable as direct dependency
- **Usage**: Extract specific patterns or code segments, reimplement in project context
- **Examples**: EFinance, Multi-source aggregator

### REJECT
- **Criteria**: Low quality, unmaintained, redundant, or requires external dependencies
- **Usage**: Avoid entirely; use alternatives
- **Examples**: EFinance wrapper, AkShare Lite, Eastmoney bridge

---

*This document is based on Phase 1 reconnaissance audit results; decisions should be adjusted based on actual testing during implementation*