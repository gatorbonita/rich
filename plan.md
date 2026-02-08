# Portfolio Optimization Web App — Plan File

## 1. Objective

Build a web application that constructs a low-risk stock portfolio by selecting up to 10 stocks from the U.S. equity market under the following constraints:

- Stocks are selected from 11 sectors
- Each sector contributes top-performing candidates
- Portfolio must meet a minimum expected return
- Portfolio risk is minimized using historical price correlation
- The system must be fast, explainable, and suitable for real-time web usage

**This is not a trading system.** It is a portfolio construction & decision-support tool.

---

## 2. High-Level Architecture

```
Frontend (React / Next.js)
  └── Portfolio Config UI
  └── Results Visualization

Backend (FastAPI)
  ├── Data Layer
  │    ├── Price Fetching
  │    ├── Caching
  │    └── Feature Engineering
  ├── Candidate Selection
  ├── Risk Modeling
  ├── Optimization Engine
  └── API Layer

Storage
  ├── In-memory cache (Redis or local)
  └── Optional SQLite for metadata
```

---

## 3. Core Financial Logic

### 3.1 Universe Definition

U.S. equities grouped into 11 sectors.

Sector mapping provided via:
- Static JSON, or
- External dataset (e.g. GICS-style)

**Example:**
```json
{
  "Technology": ["AAPL", "MSFT", "NVDA", ...],
  "Financials": ["JPM", "BAC", "GS", ...]
}
```

---

## 4. Data Layer

### 4.1 Market Data Source

**Library:** yfinance

**Data pulled:**
- Adjusted Close prices
- Daily frequency

### 4.2 Time Windows

| Metric | Window | Purpose |
|--------|--------|---------|
| Return ranking | 3 months | Momentum signal |
| Volatility | 6–12 months | Risk estimation |
| Correlation | 9–12 months | Diversification |

### 4.3 Data Quality & Error Handling

**Validation Pipeline:**

1. **Pre-fetch validation**:
   - Check yfinance API availability
   - Validate ticker symbols
   - Test network connectivity

2. **Post-fetch validation**:
   - Check for missing dates (gaps > 5 days)
   - Validate price reasonableness (no zeros, extreme jumps)
   - Ensure sufficient history (min 252 trading days)

3. **Graceful degradation**:
   - Skip stocks with insufficient data
   - Use shorter window if long window unavailable
   - Cache last valid data as fallback

4. **Rate limiting**:
   - Max 50 tickers per batch
   - Add 0.5s delay between batches
   - Exponential backoff on errors

**Error logging:**
- Log all data fetch failures
- Track API response times
- Alert on systematic failures

---

## 5. Feature Engineering

### 5.1 Returns

```python
returns = prices.pct_change().dropna()
```

### 5.2 Volatility

Annualized rolling volatility:

```python
vol = returns.rolling(60).std() * sqrt(252)
```

### 5.3 Expected Return

Simple mean return over 3 months. Used only for ranking & constraints.

---

## 6. Candidate Selection Pipeline

### Step 1: Sector Filtering

For each of the 11 sectors:

1. Rank stocks by 3-month return
2. Apply basic quality filters:
   - Minimum liquidity
   - No missing data
3. Select Top 5 stocks per sector

**Result:** ~55 candidate stocks

### Step 2: Risk De-duplication via Correlation

1. Compute correlation matrix on 9–12 months of returns
2. Convert to distance matrix:
   ```
   distance = 1 - correlation
   ```
3. Apply hierarchical clustering
4. From each cluster:
   - Select max 1–2 stocks
   - Prefer higher return / lower volatility

**Purpose:**
- Remove highly correlated "clones"
- Reduce systemic risk concentration

---

## 7. Risk Model

### 7.1 Covariance Matrix

Based on daily returns. Use shrinkage for stability:

```python
from sklearn.covariance import LedoitWolf
cov = LedoitWolf().fit(returns).covariance_
```

### 7.2 Portfolio Risk Metric

Primary risk metric:

```
portfolio_variance = wᵀ Σ w
```

Where:
- w = equal-weight vector
- Σ = covariance matrix

---

## 8. Optimization Engine

### 8.1 Portfolio Constraints

- Number of stocks ≤ 10
- Equal-weighted portfolio
- Expected return ≥ user-defined minimum
- Sector exposure limits (soft constraints):
  - Max 2 stocks per sector
  - Minimum 6 sectors represented

### 8.2 Optimization Strategy (Web-Safe)

**No exact solvers. No MIP.**

**Enhanced Algorithm: Weighted Random + Greedy**

1. **Smart Sampling** (not pure random):
   - Pre-compute Sharpe ratio for each candidate
   - Sample with probability proportional to Sharpe
   - Ensure sector diversity in sampling

2. **Greedy Refinement**:
   - For each sampled portfolio, try single-stock swaps
   - Keep improvements that reduce risk while maintaining return

3. **Parallel Evaluation**:
   - Run multiple optimization threads
   - Track best solutions across all threads

**Pseudocode:**
```python
# Pre-compute
sharpe_ratios = compute_sharpe(candidates)
sampling_weights = softmax(sharpe_ratios)

# Optimization loop
best_portfolios = []
for i in N iterations:
  # Weighted sampling (not uniform random)
  stocks = weighted_sample(candidates, 10, weights=sampling_weights)

  # Ensure sector diversity
  if not meets_sector_constraints(stocks):
    continue

  # Compute metrics
  portfolio_return = expected_return(stocks)
  if portfolio_return < threshold:
    continue

  portfolio_risk = compute_risk(stocks, cov_matrix)

  # Greedy improvement
  for _ in range(5):  # quick local search
    improved = try_single_swap(stocks, candidates)
    if improved:
      stocks = improved
      portfolio_risk = compute_risk(stocks, cov_matrix)

  # Store best
  best_portfolios.append((stocks, portfolio_risk, portfolio_return))

return lowest_risk_portfolios(best_portfolios, top_k=3)
```

### 8.3 Performance Targets

- Optimization time < 2 seconds
- Parallelizable (use ProcessPoolExecutor)
- Early stopping allowed
- Return top 3 alternative portfolios (not just 1)

---

## 8.4 Edge Case Handling

**Critical edge cases to handle:**

1. **No portfolio meets minimum return**:
   - Return best available portfolio with warning
   - Suggest lowering return threshold
   - Show what return is achievable

2. **Insufficient data**:
   - Some stocks have missing/incomplete history
   - Fallback: use shorter window or exclude stock
   - Always validate data completeness before optimization

3. **Market hours vs closed**:
   - Cache last valid portfolio during market hours
   - Show "last updated" timestamp
   - Avoid rate limiting yfinance

4. **Delisted/invalid stocks**:
   - Validate tickers before optimization
   - Remove dead tickers from universe
   - Log and report data issues

5. **High correlation scenario**:
   - All candidates are correlated (market crisis)
   - Return best diversification possible
   - Show correlation warning to user

---

## 9. Backend API Design (FastAPI)

### 9.1 Endpoint: /optimize

**POST**

```json
{
  "max_stocks": 10,
  "min_return": 0.15,
  "risk_window_months": 12,
  "return_window_months": 3
}
```

### 9.2 Response

```json
{
  "success": true,
  "portfolio": ["AAPL", "JPM", "XOM", ...],
  "expected_return": 0.162,
  "risk_score": 0.084,
  "volatility": 0.18,
  "sharpe_ratio": 0.89,
  "max_drawdown": 0.15,
  "sector_breakdown": {
    "Technology": 2,
    "Financials": 1
  },
  "correlation_score": 0.31,
  "stock_details": [
    {
      "ticker": "AAPL",
      "sector": "Technology",
      "weight": 0.1,
      "expected_return": 0.21,
      "volatility": 0.25
    }
  ],
  "alternatives": [
    {
      "portfolio": ["MSFT", "JPM", ...],
      "risk_score": 0.086,
      "expected_return": 0.158
    }
  ],
  "warnings": [],
  "metadata": {
    "optimization_time_ms": 1847,
    "data_freshness": "2024-02-05T10:30:00Z",
    "candidates_evaluated": 55
  }
}
```

### 9.3 Error Responses

```json
{
  "success": false,
  "error": "insufficient_return",
  "message": "No portfolio found meeting minimum return of 15%. Maximum achievable: 12.3%",
  "best_available": {
    "portfolio": ["AAPL", ...],
    "expected_return": 0.123
  }
}
```

### 9.4 Additional Endpoints

- `GET /health` - Health check
- `GET /universe` - Get available stocks by sector
- `GET /stock/{ticker}` - Get individual stock metrics
- `POST /validate` - Validate configuration before optimization

---

## 10. Frontend (Simple but Pretty)

### Tech Stack

- React + Vite or Next.js
- Tailwind CSS
- Recharts / Chart.js

### UI Sections

| # | Section | Description |
|---|---------|-------------|
| 1️⃣ | Configuration Panel | Max number of stocks (slider), Target return (%), Risk profile (Low / Medium / High) |
| 2️⃣ | Results View | Selected stock cards, Sector badges, Risk & return metrics |
| 3️⃣ | Visualization | Correlation heatmap, Sector allocation donut, Risk vs Return scatter |

---

## 11. UX Principles

- **No financial jargon in UI**
- **Explain risk as:** "How likely stocks move together"
- **Always show:**
  - Sector diversity
  - Correlation score
- **Disclaimer:** Educational use only. No guarantee of returns.

---

## 12. Testing Strategy

### 12.1 Unit Tests

**Data Layer:**
- Test price fetching with mock responses
- Test missing data handling
- Test date range calculations

**Financial Logic:**
- Test return calculations
- Test volatility calculations
- Test Sharpe ratio computation
- Test covariance matrix shrinkage

**Optimization:**
- Test weighted sampling
- Test constraint satisfaction
- Test greedy improvement logic

**Coverage target:** 80%+

### 12.2 Integration Tests

- Test full API endpoints with cached data
- Test error responses
- Test validation logic
- Test concurrent requests

### 12.3 End-to-End Tests

**Scenarios:**
1. Normal case: standard optimization request
2. Edge case: impossible return constraint
3. Edge case: insufficient data
4. Stress test: concurrent requests
5. Performance test: optimization under 2s

### 12.4 Mock Data

Create fixture data for testing:
- `mock_prices.json` - Sample price history
- `mock_universe.json` - Test stock universe
- Mock covariance matrices

**Tools:**
- pytest
- pytest-asyncio
- pytest-mock
- httpx (for API testing)

---

## 13. Performance & Caching

- **Cache:**
  - Price data (daily refresh)
  - Covariance matrices
  - Avoid repeated downloads
- Precompute sector-level features

---

## 13. Deployment

### Backend

- Dockerized FastAPI
- Optional Redis
- Deploy on AWS / Fly.io / Render

### Frontend

- Static build
- Deploy on Vercel / Netlify

---

## 14. Future Enhancements (Out of Scope for v1)

- User portfolios & login
- Backtesting module
- Downside risk (CVaR)
- Custom weighting schemes
- International markets

---

## 16. Implementation Roadmap

### Phase 1: Backend Core (v1 MVP)
**Goal:** Working API with basic optimization

**Week 1-2:**
- [ ] Project setup (FastAPI, dependencies)
- [ ] Data layer: yfinance integration
- [ ] Caching layer (simple file-based)
- [ ] Feature engineering (returns, vol, correlation)
- [ ] Universe definition (S&P 500 + GICS sectors)

**Week 2-3:**
- [ ] Candidate selection pipeline
- [ ] Risk model (covariance + Ledoit-Wolf)
- [ ] Optimization engine (weighted sampling + greedy)
- [ ] API endpoints (`/optimize`, `/health`)
- [ ] Error handling & validation

**Week 3:**
- [ ] Unit tests (core logic)
- [ ] Integration tests (API)
- [ ] Documentation (API specs)

### Phase 2: Frontend (v1)
**Goal:** Clean, functional UI

**Week 4:**
- [ ] React + Vite setup
- [ ] Tailwind CSS configuration
- [ ] Configuration panel
- [ ] Results display
- [ ] API integration

**Week 5:**
- [ ] Visualizations (Recharts)
  - Sector allocation donut
  - Correlation heatmap
  - Risk/return scatter
- [ ] Loading states & error handling
- [ ] Responsive design
- [ ] Disclaimer text

### Phase 3: Polish & Deploy
**Goal:** Production-ready

**Week 6:**
- [ ] Performance optimization
- [ ] Redis caching (optional)
- [ ] Docker setup
- [ ] Backend deployment (Render/Fly.io)
- [ ] Frontend deployment (Vercel)
- [ ] End-to-end testing
- [ ] Monitoring setup

### Phase 4: Enhancements (Post v1)
- [ ] Progressive results (WebSocket)
- [ ] Local storage for history
- [ ] Additional risk metrics (CVaR, max drawdown)
- [ ] "Why this stock?" explanations
- [ ] Simple backtest visualization
- [ ] Compare to S&P 500 benchmark

---

## 17. Tech Stack Summary

### Backend
- **Framework:** FastAPI 0.109+
- **Data:** yfinance, pandas, numpy
- **ML:** scikit-learn (Ledoit-Wolf)
- **Caching:** Redis (optional) or diskcache
- **Testing:** pytest, pytest-asyncio
- **Validation:** pydantic

### Frontend
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **HTTP:** axios or fetch
- **State:** React Context (no Redux needed for v1)

### DevOps
- **Backend Container:** Docker
- **Backend Host:** Render / Fly.io
- **Frontend Host:** Vercel / Netlify
- **Monitoring:** Sentry (optional)

---

## 18. File Structure

```
rich/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── portfolio.py       # Pydantic models
│   │   │   └── stock.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── data_service.py    # Data fetching
│   │   │   ├── feature_service.py  # Feature engineering
│   │   │   ├── risk_service.py     # Risk calculations
│   │   │   └── optimizer.py        # Optimization engine
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py           # API endpoints
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── cache.py
│   │       └── validation.py
│   ├── data/
│   │   └── universe.json           # Stock universe
│   ├── tests/
│   │   ├── test_data_service.py
│   │   ├── test_optimizer.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConfigPanel.jsx
│   │   │   ├── ResultsView.jsx
│   │   │   ├── StockCard.jsx
│   │   │   └── Visualizations/
│   │   │       ├── SectorDonut.jsx
│   │   │       ├── CorrelationHeatmap.jsx
│   │   │       └── RiskReturnScatter.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── plan.md
├── LICENSE
└── README.md
```

---

## 19. Guiding Principles (Critical)

- **Fast > Perfect**
- **Explainable > Complex**
- **Stable > Overfitted**
- **Diversification is behavioral, not cosmetic**
