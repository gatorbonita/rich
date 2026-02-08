# Portfolio Optimizer

A full-stack web application for constructing low-risk, diversified stock portfolios using AI-powered optimization.

![Portfolio Optimizer](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![React](https://img.shields.io/badge/react-18+-blue)
![FastAPI](https://img.shields.io/badge/fastapi-0.109+-teal)

## Features

- **Smart Optimization**: Weighted random sampling + greedy local search algorithm
- **Risk Minimization**: Ledoit-Wolf covariance shrinkage for stable estimates
- **Sector Diversification**: Ensures representation across 11 GICS sectors
- **Comprehensive Metrics**: Sharpe ratio, max drawdown, volatility, VaR, CVaR
- **Multiple Solutions**: Returns top 3 alternative portfolios
- **Beautiful UI**: Responsive React interface with Tailwind CSS
- **Interactive Visualizations**: Sector allocation, risk-return scatter plots
- **Real-time Optimization**: Completes in < 2 seconds
- **Data Caching**: 24-hour cache for improved performance

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  React Frontend │────────▶│  FastAPI Backend │
│   (Vite + TW)   │  HTTP   │   (Python 3.11)  │
└─────────────────┘         └──────────────────┘
                                      │
                            ┌─────────┴─────────┐
                            ▼                   ▼
                      ┌───────────┐      ┌──────────┐
                      │  yfinance │      │  diskcache│
                      │  (Yahoo)  │      │  (Cache)  │
                      └───────────┘      └──────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## Usage

1. **Configure Portfolio Parameters**:
   - Number of stocks (5-15)
   - Target annual return (5-30%)
   - Risk profile (Low/Medium/High)
   - Advanced options (risk window, correlation threshold)

2. **Click "Optimize Portfolio"**:
   - Algorithm analyzes 165 stocks across 11 sectors
   - Selects top performers per sector
   - Removes highly correlated stocks
   - Finds optimal low-risk portfolio

3. **Review Results**:
   - Portfolio metrics (return, risk, Sharpe ratio)
   - Individual stock details
   - Sector allocation visualization
   - Alternative portfolio options

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **yfinance**: Market data from Yahoo Finance
- **pandas & numpy**: Data manipulation
- **scikit-learn**: Ledoit-Wolf covariance shrinkage
- **scipy**: Hierarchical clustering
- **diskcache**: Fast disk-based caching

### Frontend
- **React 18**: UI library
- **Vite**: Build tool
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Axios**: HTTP client

## Project Structure

```
portfolio-optimizer/
├── backend/
│   ├── app/
│   │   ├── services/        # Business logic
│   │   ├── models/          # Pydantic models
│   │   ├── api/             # API routes
│   │   ├── utils/           # Utilities
│   │   └── main.py          # FastAPI app
│   ├── data/
│   │   └── universe.json    # Stock universe
│   ├── tests/               # Unit tests
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API service
│   │   ├── App.jsx          # Main app
│   │   └── main.jsx         # Entry point
│   └── package.json
│
├── plan.md                  # Original plan
├── DEPLOYMENT.md            # Deployment guide
└── README.md
```

## API Endpoints

- `POST /api/optimize` - Optimize portfolio
- `GET /api/health` - Health check
- `GET /api/universe` - Get stock universe
- `GET /api/stock/{ticker}` - Get stock info
- `POST /api/validate` - Validate config

## Algorithm Details

### Optimization Strategy

1. **Candidate Selection**:
   - Select top 5 stocks per sector by 3-month return
   - Apply quality filters (Sharpe ratio, data completeness)
   - ~55 candidates from 11 sectors

2. **Correlation-Based De-duplication**:
   - Compute correlation matrix (9-12 months)
   - Hierarchical clustering with distance = 1 - correlation
   - Select max 2 stocks per cluster
   - ~30-40 diverse candidates

3. **Weighted Random Sampling**:
   - Compute Sharpe ratios for all candidates
   - Generate sampling probabilities (softmax)
   - Sample portfolio with sector diversity constraints

4. **Greedy Local Search**:
   - Try single-stock swaps
   - Keep improvements that reduce risk
   - Iterate 3-5 times

5. **Return Top 3 Portfolios**:
   - Sort by risk (lower is better)
   - Ensure all meet return constraint

### Risk Model

- **Covariance**: Ledoit-Wolf shrinkage estimator
- **Portfolio Risk**: σ_p = √(w^T Σ w)
- **Max Drawdown**: Largest peak-to-trough decline
- **VaR/CVaR**: 95% confidence interval

## Configuration

### Backend (`.env`)

```bash
APP_ENV=development
CACHE_DIR=./cache
CACHE_TTL_HOURS=24
N_ITERATIONS=1000
MAX_OPTIMIZATION_TIME_SECONDS=2
CORS_ORIGINS=http://localhost:5173
```

### Frontend (`.env`)

```bash
VITE_API_URL=http://localhost:8000
```

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Docker

```bash
docker-compose up -d
```

### Production

- **Backend**: Deploy to Render, Fly.io, or AWS
- **Frontend**: Deploy to Vercel, Netlify

## Performance

- **Optimization Time**: < 2 seconds
- **Candidates Evaluated**: 30-50 stocks
- **Iterations**: 1000 (configurable)
- **Cache Hit Rate**: ~80% (with 24h TTL)

## Limitations

- **Data Source**: Yahoo Finance (free, but rate-limited)
- **Historical Data**: Past performance ≠ future results
- **Educational Use**: Not a trading system
- **U.S. Markets Only**: S&P 500 stocks

## Future Enhancements

- [ ] User authentication & portfolio saving
- [ ] Backtesting module
- [ ] Additional risk metrics (CVaR, tail risk)
- [ ] Custom weighting schemes
- [ ] International markets
- [ ] Real-time updates (WebSocket)
- [ ] ESG scoring integration

## Disclaimer

⚠️ **Educational Tool Only**

This application is for educational and research purposes. It is not financial advice. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting

## Acknowledgments

- Market data: Yahoo Finance (via yfinance)
- Optimization algorithm: Inspired by modern portfolio theory
- Covariance estimation: Ledoit-Wolf (scikit-learn)

---

**Built with ❤️ using Python, React, and Claude AI**
