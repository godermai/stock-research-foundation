# Source Endpoint Catalog

## Phase 1 Reconnaissance Audit - Data Source Endpoint Catalog

This document details upstream data sources, main interfaces, output fields, authentication requirements, and known issues for each data source project.

---

## 1. AkShare (akshare)

### Upstream Data Sources
- **Primary Sources**: Web scraping from multiple financial websites (East Money, Sina Finance, Sohu Securities, Netease Finance)
- **Coverage**: A-shares, Hong Kong stocks, US stocks, futures, options, funds, bonds, forex, cryptocurrency
- **Data Nature**: Free public data, no official API token required

### Main Interface/Function Names
```python
# Stock historical data
ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20230101", end_date="20231231", adjust="")

# Real-time quotes
ak.stock_zh_a_spot_em()

# Financial data
ak.stock_financial_analysis(symbol="000001")

# Stock basic information
ak.stock_individual_info_em(symbol="000001")

# Macro economic data
ak.macro_china_gdp()
```

### Output Fields
- Historical K-line: `date, open, close, high, low, volume, amount, amplitude, change_pct, change_amount, turnover_rate`
- Real-time quotes: `code, name, latest_price, change_pct, change_amount, volume, amount`
- Financial data: `date, revenue, net_profit, ROE, debt_ratio` etc.

### Authentication Requirements
- **Token/Cookie**: No official token required
- **Anti-scraping**: Uses curl_cffi and mini-racer for JavaScript rendering
- **Rate limiting**: Add appropriate delays to avoid IP blocking

### Known Stability Issues
1. **Website structure changes**: Website redesigns may cause interface failures, requiring timely maintenance
2. **Rate limiting risk**: High-frequency requests may result in temporary IP blocks
3. **Data completeness**: Scraped data may have missing or incorrect values
4. **Maintenance dependency**: Active community, rapid problem resolution

---

## 2. EFinance (efinance)

### Upstream Data Sources
- **Primary Sources**: East Money (eastmoney.com) API
- **Coverage**: A-share real-time quotes, historical data, financial data, funds, futures, macro economics
- **Data Nature**: Free API interface, no official token required

### Main Interface/Function Names
```python
# Stock historical data
ef.stock.get_quote_history(stock_code='000001', beg='20230101', end='20231231')

# Real-time quotes
ef.stock.get_realtime_quotes()

# Financial statements
ef.stock.get_financials()

# Company basic information
ef.stock.get_base_info()

# Shareholder research
ef.stock.get_holder_changes()
```

### Output Fields
- Historical K-line: `date, open, close, high, low, volume, amount`
- Real-time data: `stock_code, stock_name, current_price, change_pct, volume`
- Financial data: `report_period, revenue, net_profit, ROE, current_ratio` etc.

### Authentication Requirements
- **Token/Cookie**: No official token required, uses public API
- **Rate limiting**: Rate limiting issues exist, discussed in community (#216)
- **Session management**: Uses requests.Session for connection management

### Known Stability Issues
1. **Rate limiting**: High-frequency requests are throttled, server-side solution in development
2. **API changes**: East Money API parameters may change
3. **Real-time performance**: Real-time data has delays
4. **Data quality**: Overall good data quality, active maintenance

---

## 3. Mootdx (mootdx)

### Upstream Data Sources
- **Primary Sources**: TongDaXin (TDX) servers
- **Coverage**: A-shares, Hong Kong stocks, futures, options real-time quotes and historical K-lines
- **Data Nature**: Free TDX server data

### Main Interface/Function Names
```python
# Historical K-line
from mootdx.quotes import Quotes
quotes = Quotes.factory(market='std', timeout=10)
quotes.history(symbol='000001', start=0, offset=100)

# Real-time quotes
from mootdx.quotes import Quotes
quotes = Quotes.factory(market='std', timeout=10)
quotes.quotes(['000001'])

# Financial data
from mootdx.financial import Financial
financial = Financial.factory(timeout=10)
financial.forecast(['000001'])
```

### Output Fields
- Historical K-line: `date, open, close, high, low, volume, amount`
- Real-time quotes: `code, name, latest_price, change_pct, volume`
- Financial data: `code, name, report_period, forecast_performance`

### Authentication Requirements
- **Token/Cookie**: No token required, TDX public servers
- **Server connection**: Automatic optimal server matching
- **Connection pool**: Supports multi-server connection pool

### Known Stability Issues
1. **Server availability**: TDX servers relatively stable but occasional maintenance
2. **Data scope**: Mainly quote data, limited financial data
3. **Network dependency**: Relies on network connection to TDX servers
4. **pytdx dependency**: Wrapper based on pytdx, inherits its limitations

---

## 4. Tushare (tushare)

### Upstream Data Sources
- **Primary Sources**: Tushare Pro API (official interface)
- **Coverage**: Full A-share market data including quotes, financial, macro economics, company announcements
- **Data Nature**: Requires paid token, has free tier

### Main Interface/Function Names
```python
import tushare as ts

# Token initialization required
ts.set_token('your_token_here')
pro = ts.pro_api()

# Stock list
pro.stock_basic(exchange='', list_status='L')

# Historical quotes
pro.daily(ts_code='000001.SZ', start_date='20230101', end_date='20231231')

# Financial data
pro.income(ts_code='000001.SZ', period='20231231')

# Company announcements
pro.disclosure_announcement()
```

### Output Fields
- Stock list: `ts_code, symbol, name, area, industry, market`
- Historical quotes: `ts_code, trade_date, open, high, low, close, pre_close, vol, amount`
- Financial data: `ts_code, ann_date, f_ann_date, end_date, report_type, comp_type` etc.

### Authentication Requirements
- **Token**: **Must** have Tushare Pro token
- **Free quota**: 120 API calls per day (points limit)
- **Paid plans**: Different point levels for different permissions
- **API throttling**: Strict call frequency limits

### Known Stability Issues
1. **Token cost**: Full functionality requires payment, high cost
2. **Free restrictions**: Limited free quota, not suitable for high-frequency use
3. **Data quality**: Official data quality is high, timely updates
4. **Community activity**: Official maintenance, comprehensive documentation

---

## 5. BaoStock (baostock)

### Upstream Data Sources
- **Primary Sources**: BaoStock servers
- **Coverage**: A-share historical K-lines (daily, weekly, monthly, 5-min, 15-min, 30-min, 60-min)
- **Data Nature**: Free API interface

### Main Interface/Function Names
```python
import baostock as bs

# Login to system
lg = bs.login()

# Historical K-line
rs = bs.query_history_k_data_plus("000001.SZ",
    "date,code,open,high,low,close,preclose,volume,amount",
    start_date='2023-01-01', end_date='2023-12-31',
    frequency="d", adjustflag="2")

# Logout
bs.logout()
```

### Output Fields
- Basic fields: `date, code, open, high, low, close, preclose, volume, amount, adjustflag, turn, tradestatus`
- Extended fields: `pctChg, peTTM, psTTM, pcfNttm, pbMRQ` etc.

### Authentication Requirements
- **Token**: No token required, but requires login/logout
- **Session management**: Session-based connection management
- **Connection limits**: Single query max ~3 years trading days

### Known Stability Issues
1. **Server stability**: BaoStock servers relatively stable
2. **Data freshness**: Certain delays, not real-time data
3. **Query limits**: Single query time range limited
4. **Free use**: Completely free, suitable for personal research

---

## 6. CNINFO Scrapers (cninfo-scrapers)

### Upstream Data Sources
- **Primary Sources**: CNINFO (巨潮资讯) official disclosure website
- **Coverage**: Listed company announcements, financial reports, regulatory filings
- **Data Nature**: Free public disclosure data

### Main Interface/Function Names
```python
# Announcement list
scrape_announcements(stock_code="000001", start_date="2023-01-01")

# Financial report download
download_financial_report(stock_code="000001", year=2023)

# Regulatory filings
get_regulatory_filing(category="annual_report")
```

### Output Fields
- Announcements: `announcement_id, stock_code, title, publish_date, attachment_url`
- Financial reports: `report_id, stock_code, report_type, period, download_url`
- Regulatory filings: `filing_type, submit_date, status, pdf_url`

### Authentication Requirements
- **Token/Cookie**: No token required
- **Anti-scraping**: May need cookie handling for PDF downloads
- **Rate limiting**: Strict limits on announcement PDF downloads

### Known Stability Issues
1. **Website changes**: CNINFO website structure changes may break scrapers
2. **PDF parsing**: Financial report PDFs require OCR or parsing tools
3. **Update frequency**: Real-time announcement tracking requires frequent polling
4. **Data volume**: Historical announcements large, storage considerations needed

---

## 7. Multi-Source Aggregator (multi-source-aggregator)

### Upstream Data Sources
- **Primary Sources**: Aggregates multiple sources (AkShare, EFinance, Tushare)
- **Coverage**: Combined data from multiple providers
- **Data Nature**: Unified API wrapper with local caching

### Main Interface/Function Names
```python
# Unified historical data
get_stock_data(symbol="000001", start_date="2023-01-01", source="auto")

# Unified real-time quotes
get_realtime_quotes(symbols=["000001", "000002"], fallback=True)

# Financial data fusion
get_financial_analysis(symbol="000001", consolidated=True)
```

### Output Fields
- Unified schema: `symbol, date, open, high, low, close, volume, source, data_quality`
- Metadata: `fetch_timestamp, source_reliability, data_completeness`

### Authentication Requirements
- **Token**: Depends on underlying sources
- **Caching**: Local DuckDB/Parquet caching layer
- **Fallback**: Automatic source switching on failures

### Known Stability Issues
1. **Complexity**: Multiple source coordination adds complexity
2. **Data consistency**: Different sources may have conflicting data
3. **Maintenance**: Need to track changes in all underlying sources
4. **Performance**: Aggregation overhead, caching critical

---

## Data Source Comparison Summary

| Data Source | Cost | Data Quality | Stability | Coverage | Real-time | Recommended Use |
|-------------|------|-------------|-----------|----------|-----------|-----------------|
| AkShare | Free | Medium | Medium | Widest | Near real-time | Comprehensive data |
| EFinance | Free | High | Good | Broad | Near real-time | East Money data |
| Mootdx | Free | High | High | Narrow | Real-time | K-line quote data |
| Tushare | Paid | Highest | Highest | Most complete | Delayed | Professional applications |
| BaoStock | Free | High | High | Medium | Delayed | Historical K-line research |
| CNINFO | Free | High | Medium | Narrow | Delayed | Regulatory filings |

---

## Recommended Data Source Combination Strategy

### 1. Historical K-line Data
- **Primary**: Mootdx (TDX) or BaoStock
- **Backup**: AkShare historical interfaces

### 2. Real-time Quotes
- **Primary**: EFinance (East Money)
- **Backup**: Mootdx real-time interface

### 3. Financial Data
- **Primary**: EFinance
- **Backup**: AkShare financial interfaces

### 4. Announcement Data
- **Primary**: Dedicated CNINFO scrapers
- **Backup**: AkShare announcement interfaces

### 5. Macro Economics
- **Recommended**: AkShare macro data interfaces
- **Characteristics**: Comprehensive data sources, active maintenance

---

## Token and Authentication Strategy

### Free Data Sources Priority
1. **AkShare**: No token, scraping mode
2. **EFinance**: No token, public API
3. **Mootdx**: No token, TDX servers
4. **BaoStock**: No token, login session

### Paid Data Sources as Supplement
1. **Tushare**: Suitable for scenarios requiring highest data quality
2. **Cost consideration**: Free quota may meet personal research needs

---

## Technical Implementation Points

### HTTP Client Selection
- **Recommended**: `requests` + `curl_cffi` (handle JS rendering)
- **Advantages**: Good compatibility, strong anti-scraping capability

### Caching Strategy
- **Local cache**: DuckDB + Parquet
- **Cache layers**: Bronze (raw) → Silver (normalized)
- **Freshness management**: Timestamp + incremental updates

### Rate Limiting
- **Delay strategy**: Random delay + exponential backoff
- **Concurrency control**: Limit concurrent requests
- **Error retry**: Intelligent retry mechanism

---

*This document is based on Phase 1 reconnaissance audit results; strategies should be adjusted based on actual testing results during implementation*