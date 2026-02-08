"""
Pydantic models for portfolio optimization API.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime


class OptimizeRequest(BaseModel):
    """Request model for portfolio optimization."""

    max_stocks: int = Field(
        default=10,
        ge=5,
        le=15,
        description="Maximum number of stocks in portfolio"
    )

    min_return: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Minimum required annual return (as decimal, e.g., 0.10 for 10%)"
    )

    risk_window_months: int = Field(
        default=12,
        ge=6,
        le=24,
        description="Number of months for risk/correlation calculation"
    )

    return_window_months: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Number of months for return calculation"
    )

    top_k_per_sector: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Number of top stocks to consider per sector"
    )

    correlation_threshold: float = Field(
        default=0.75,
        ge=0.5,
        le=0.95,
        description="Correlation threshold for de-duplication"
    )

    @validator('min_return')
    def validate_min_return(cls, v):
        if v < 0:
            raise ValueError("Minimum return cannot be negative")
        if v > 1.0:
            raise ValueError("Minimum return cannot exceed 100%")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "max_stocks": 10,
                "min_return": 0.15,
                "risk_window_months": 12,
                "return_window_months": 3,
                "top_k_per_sector": 5,
                "correlation_threshold": 0.75
            }
        }


class StockDetail(BaseModel):
    """Detailed information about a stock in the portfolio."""

    ticker: str = Field(description="Stock ticker symbol")
    sector: str = Field(description="Stock sector")
    weight: float = Field(description="Portfolio weight (as decimal)")
    expected_return: float = Field(description="Expected annual return")
    volatility: float = Field(description="Annual volatility")
    sharpe_ratio: float = Field(description="Sharpe ratio")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "sector": "Technology",
                "weight": 0.1,
                "expected_return": 0.21,
                "volatility": 0.25,
                "sharpe_ratio": 0.84
            }
        }


class AlternativePortfolio(BaseModel):
    """Alternative portfolio option."""

    portfolio: List[str] = Field(description="List of ticker symbols")
    expected_return: float = Field(description="Expected annual return")
    risk_score: float = Field(description="Portfolio volatility")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    sector_breakdown: Dict[str, int] = Field(description="Number of stocks per sector")


class OptimizationMetadata(BaseModel):
    """Metadata about the optimization process."""

    optimization_time_ms: int = Field(description="Optimization time in milliseconds")
    data_freshness: datetime = Field(description="Timestamp of price data")
    candidates_evaluated: int = Field(description="Number of candidate stocks")
    total_iterations: int = Field(description="Number of optimization iterations")
    valid_portfolios_found: int = Field(description="Number of valid portfolios found")


class OptimizeResponse(BaseModel):
    """Response model for successful optimization."""

    success: bool = Field(default=True, description="Whether optimization succeeded")

    portfolio: List[str] = Field(description="List of selected ticker symbols")

    expected_return: float = Field(description="Expected annual return")
    risk_score: float = Field(description="Portfolio volatility (std dev)")
    variance: float = Field(description="Portfolio variance")
    volatility: float = Field(description="Portfolio volatility (same as risk_score)")
    sharpe_ratio: float = Field(description="Portfolio Sharpe ratio")
    max_drawdown: float = Field(description="Maximum historical drawdown")

    sector_breakdown: Dict[str, int] = Field(
        description="Number of stocks per sector"
    )

    correlation_score: float = Field(
        description="Average pairwise correlation between stocks"
    )

    stock_details: List[StockDetail] = Field(
        description="Detailed information for each stock"
    )

    alternatives: List[AlternativePortfolio] = Field(
        default=[],
        description="Alternative portfolio options"
    )

    warnings: List[str] = Field(
        default=[],
        description="Any warnings or notes about the optimization"
    )

    metadata: OptimizationMetadata = Field(
        description="Optimization process metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "portfolio": ["AAPL", "JPM", "XOM", "UNH", "AMZN", "NEE", "LIN", "PLD", "WMT", "GOOG"],
                "expected_return": 0.162,
                "risk_score": 0.184,
                "variance": 0.034,
                "volatility": 0.184,
                "sharpe_ratio": 0.77,
                "max_drawdown": 0.23,
                "sector_breakdown": {
                    "Technology": 2,
                    "Financials": 1,
                    "Energy": 1,
                    "Healthcare": 1,
                    "Consumer Discretionary": 1,
                    "Utilities": 1,
                    "Materials": 1,
                    "Real Estate": 1,
                    "Consumer Staples": 1
                },
                "correlation_score": 0.31,
                "stock_details": [],
                "alternatives": [],
                "warnings": [],
                "metadata": {
                    "optimization_time_ms": 1847,
                    "data_freshness": "2024-02-05T10:30:00Z",
                    "candidates_evaluated": 42,
                    "total_iterations": 1000,
                    "valid_portfolios_found": 247
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for optimization errors."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    best_available: Optional[Dict] = Field(
        default=None,
        description="Best available portfolio if applicable"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "insufficient_return",
                "message": "No portfolio found meeting minimum return of 15%. Maximum achievable: 12.3%",
                "best_available": {
                    "portfolio": ["AAPL", "MSFT", "GOOGL"],
                    "expected_return": 0.123
                }
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(description="Health status")
    version: str = Field(description="API version")
    cache_stats: Dict = Field(description="Cache statistics")
    timestamp: datetime = Field(description="Current timestamp")


class UniverseResponse(BaseModel):
    """Response model for universe endpoint."""

    sectors: Dict[str, List[str]] = Field(description="Stocks grouped by sector")
    total_stocks: int = Field(description="Total number of stocks")
    total_sectors: int = Field(description="Total number of sectors")


class StockInfoResponse(BaseModel):
    """Response model for individual stock information."""

    ticker: str = Field(description="Stock ticker symbol")
    sector: str = Field(description="Stock sector")
    current_price: Optional[float] = Field(None, description="Current price")
    expected_return: float = Field(description="Expected annual return")
    volatility: float = Field(description="Annual volatility")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    max_drawdown: float = Field(description="Historical max drawdown")
    beta: Optional[float] = Field(None, description="Beta vs market")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "sector": "Technology",
                "current_price": 185.50,
                "expected_return": 0.21,
                "volatility": 0.25,
                "sharpe_ratio": 0.84,
                "max_drawdown": 0.32,
                "beta": 1.15
            }
        }
