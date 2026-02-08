"""
API routes for portfolio optimization service.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging
import time
from typing import Dict

from app.models.portfolio import (
    OptimizeRequest,
    OptimizeResponse,
    ErrorResponse,
    HealthResponse,
    UniverseResponse,
    StockInfoResponse,
    StockDetail,
    AlternativePortfolio,
    OptimizationMetadata
)
from app.services.data_service import (
    fetch_and_validate_prices,
    get_cache_stats,
    DataQualityError
)
from app.services.feature_service import (
    compute_returns,
    compute_volatility,
    compute_sharpe_ratio,
    compute_expected_return,
    compute_features_summary
)
from app.services.risk_service import compute_max_drawdown
from app.services.candidate_selector import (
    select_portfolio_candidates,
    load_universe,
    get_sector_allocation
)
from app.services.optimizer import (
    optimize_portfolio,
    OptimizationError,
    InsufficientReturnError
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        cache_stats=get_cache_stats(),
        timestamp=datetime.now()
    )


@router.get("/universe", response_model=UniverseResponse)
async def get_universe():
    """Get the stock universe grouped by sectors."""
    try:
        universe = load_universe()

        total_stocks = sum(len(tickers) for tickers in universe.values())

        return UniverseResponse(
            sectors=universe,
            total_stocks=total_stocks,
            total_sectors=len(universe)
        )
    except Exception as e:
        logger.error(f"Error loading universe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load stock universe"
        )


@router.get("/stock/{ticker}", response_model=StockInfoResponse)
async def get_stock_info(ticker: str):
    """Get information about a specific stock."""
    try:
        # Load universe to get sector
        universe = load_universe()
        ticker_to_sector = {}
        for sector, tickers in universe.items():
            for t in tickers:
                ticker_to_sector[t] = sector

        if ticker.upper() not in ticker_to_sector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticker {ticker} not found in universe"
            )

        sector = ticker_to_sector[ticker.upper()]

        # Fetch data
        prices, valid_tickers, _ = fetch_and_validate_prices(
            [ticker.upper()],
            months=settings.volatility_window_months
        )

        if ticker.upper() not in valid_tickers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insufficient data for {ticker}"
            )

        # Compute features
        returns = compute_returns(prices)
        features = compute_features_summary(prices)

        stock_features = features.loc[ticker.upper()]

        current_price = float(prices[ticker.upper()].iloc[-1])

        return StockInfoResponse(
            ticker=ticker.upper(),
            sector=sector,
            current_price=current_price,
            expected_return=float(stock_features['expected_return']),
            volatility=float(stock_features['volatility']),
            sharpe_ratio=float(stock_features['sharpe_ratio']),
            max_drawdown=compute_max_drawdown(prices[ticker.upper()]),
            beta=None  # Would need market data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stock information: {str(e)}"
        )


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(request: OptimizeRequest):
    """
    Optimize portfolio based on request parameters.

    Returns a diversified portfolio that minimizes risk while meeting return constraints.
    """
    start_time = time.time()
    optimization_start = time.time()

    try:
        logger.info(f"Optimization request: {request.dict()}")

        # Load universe
        universe = load_universe()

        # Get all tickers
        all_tickers = []
        for tickers in universe.values():
            all_tickers.extend(tickers)

        # Fetch and validate data
        logger.info(f"Fetching data for {len(all_tickers)} stocks...")
        prices, valid_tickers, validation_results = fetch_and_validate_prices(
            all_tickers,
            months=request.risk_window_months,
            use_cache=True
        )

        if len(valid_tickers) < request.max_stocks:
            raise DataQualityError(
                f"Only {len(valid_tickers)} stocks have sufficient data"
            )

        logger.info(f"Valid data for {len(valid_tickers)} stocks")

        # Compute returns
        returns = compute_returns(prices)

        # Select candidates
        candidates, candidate_metadata = select_portfolio_candidates(
            prices=prices,
            returns=returns,
            top_k_per_sector=request.top_k_per_sector,
            correlation_threshold=request.correlation_threshold
        )

        if len(candidates) < request.max_stocks:
            raise OptimizationError(
                f"Only {len(candidates)} candidates available, need at least {request.max_stocks}"
            )

        logger.info(f"Selected {len(candidates)} candidates for optimization")

        # Optimize
        portfolios = optimize_portfolio(
            candidates=candidates,
            prices=prices,
            returns=returns,
            max_stocks=request.max_stocks,
            min_return=request.min_return,
            universe=universe
        )

        optimization_time_ms = int((time.time() - optimization_start) * 1000)

        # Prepare response for best portfolio
        best = portfolios[0]

        # Compute features for stock details
        features = compute_features_summary(prices[best.tickers])

        stock_details = []
        for ticker in best.tickers:
            sector = get_sector_allocation([ticker], universe)
            sector_name = list(sector.keys())[0] if sector else "Unknown"

            stock_features = features.loc[ticker]

            stock_details.append(
                StockDetail(
                    ticker=ticker,
                    sector=sector_name,
                    weight=float(1.0 / len(best.tickers)),  # Equal weight
                    expected_return=float(stock_features['expected_return']),
                    volatility=float(stock_features['volatility']),
                    sharpe_ratio=float(stock_features['sharpe_ratio'])
                )
            )

        # Prepare alternatives
        alternatives = []
        for portfolio in portfolios[1:]:
            alternatives.append(
                AlternativePortfolio(
                    portfolio=portfolio.tickers,
                    expected_return=float(portfolio.expected_return),
                    risk_score=float(portfolio.risk),
                    sharpe_ratio=float(portfolio.sharpe_ratio),
                    sector_breakdown=portfolio.sector_allocation
                )
            )

        # Create metadata
        metadata = OptimizationMetadata(
            optimization_time_ms=optimization_time_ms,
            data_freshness=datetime.now(),
            candidates_evaluated=len(candidates),
            total_iterations=settings.n_iterations,
            valid_portfolios_found=len(portfolios)
        )

        # Warnings
        warnings = []
        if best.correlation_score > 0.6:
            warnings.append(
                "Portfolio has relatively high average correlation (>60%). "
                "Consider reviewing diversification."
            )
        if best.max_drawdown > 0.3:
            warnings.append(
                f"Historical maximum drawdown is {best.max_drawdown:.1%}. "
                "This portfolio has experienced significant declines in the past."
            )

        response = OptimizeResponse(
            success=True,
            portfolio=best.tickers,
            expected_return=float(best.expected_return),
            risk_score=float(best.risk),
            variance=float(best.variance),
            volatility=float(best.risk),
            sharpe_ratio=float(best.sharpe_ratio),
            max_drawdown=float(best.max_drawdown),
            sector_breakdown=best.sector_allocation,
            correlation_score=float(best.correlation_score),
            stock_details=stock_details,
            alternatives=alternatives,
            warnings=warnings,
            metadata=metadata
        )

        total_time = time.time() - start_time
        logger.info(f"Request completed in {total_time:.2f}s")

        return response

    except InsufficientReturnError as e:
        logger.warning(f"Insufficient return: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "insufficient_return",
                "message": str(e),
                "best_available": None
            }
        )

    except DataQualityError as e:
        logger.error(f"Data quality error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "data_quality_error",
                "message": f"Data quality issues: {str(e)}",
                "best_available": None
            }
        )

    except OptimizationError as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "optimization_error",
                "message": str(e),
                "best_available": None
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "internal_error",
                "message": "An unexpected error occurred during optimization",
                "best_available": None
            }
        )


@router.post("/validate", status_code=status.HTTP_200_OK)
async def validate_config(request: OptimizeRequest) -> Dict:
    """
    Validate configuration before optimization.

    Returns warnings and estimates without running full optimization.
    """
    warnings = []

    if request.min_return > 0.25:
        warnings.append("Target return above 25% may be difficult to achieve")

    if request.risk_window_months < 9:
        warnings.append("Short risk window may lead to unstable estimates")

    if request.correlation_threshold > 0.85:
        warnings.append("High correlation threshold may not filter enough stocks")

    return {
        "valid": True,
        "warnings": warnings,
        "estimated_candidates": request.top_k_per_sector * 11 * 0.7,  # Approximate
        "configuration": request.dict()
    }
