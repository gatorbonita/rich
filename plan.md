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

Algorithm:
1. Randomized portfolio sampling
2. Greedy improvement

**Pseudocode:**
```
for i in N iterations:
  sample 10 stocks
  compute return
  if return < threshold: skip
  compute risk
  store best portfolios
return lowest-risk portfolios
```

### 8.3 Performance Targets

- Optimization time < 2 seconds
- Parallelizable
- Early stopping allowed

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
  "portfolio": ["AAPL", "JPM", "XOM", ...],
  "expected_return": 0.162,
  "risk_score": 0.084,
  "sector_breakdown": {
    "Technology": 2,
    "Financials": 1
  },
  "correlation_score": 0.31
}
```

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

## 12. Performance & Caching

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

## 15. Guiding Principles (Critical)

- **Fast > Perfect**
- **Explainable > Complex**
- **Stable > Overfitted**
- **Diversification is behavioral, not cosmetic**
