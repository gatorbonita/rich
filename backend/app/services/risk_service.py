"""
Risk modeling service for portfolio optimization.
Implements covariance estimation, portfolio risk, and drawdown calculations.
"""

import pandas as pd
import numpy as np
from sklearn.covariance import LedoitWolf
from typing import List, Dict, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def compute_covariance_matrix(
    returns: pd.DataFrame,
    method: str = "ledoit_wolf"
) -> pd.DataFrame:
    """
    Compute covariance matrix with shrinkage for stability.

    Args:
        returns: DataFrame with daily returns
        method: Method to use ('ledoit_wolf', 'sample', 'shrunk')

    Returns:
        DataFrame with covariance matrix
    """
    if method == "ledoit_wolf":
        # Ledoit-Wolf shrinkage estimator
        lw = LedoitWolf()
        cov_matrix = lw.fit(returns.fillna(0)).covariance_

        # Convert to DataFrame with proper labels
        cov_df = pd.DataFrame(
            cov_matrix,
            index=returns.columns,
            columns=returns.columns
        )

    elif method == "shrunk":
        # Simple shrinkage toward diagonal
        sample_cov = returns.cov()
        shrinkage = 0.2  # Shrinkage parameter

        # Target: diagonal matrix
        target = np.diag(np.diag(sample_cov))

        cov_df = (1 - shrinkage) * sample_cov + shrinkage * target

    else:  # sample
        # Standard sample covariance
        cov_df = returns.cov()

    # Annualize
    cov_df = cov_df * settings.trading_days_per_year

    return cov_df


def compute_portfolio_risk(
    weights: np.ndarray,
    cov_matrix: pd.DataFrame,
    annualized: bool = True
) -> float:
    """
    Compute portfolio variance/volatility.

    Args:
        weights: Array of portfolio weights
        cov_matrix: Covariance matrix
        annualized: Whether covariance is already annualized

    Returns:
        Portfolio volatility (standard deviation)
    """
    # Ensure weights sum to 1
    weights = weights / weights.sum()

    # Portfolio variance: w^T * Σ * w
    portfolio_variance = weights.T @ cov_matrix.values @ weights

    # Return volatility (std dev)
    portfolio_risk = np.sqrt(portfolio_variance)

    return float(portfolio_risk)


def compute_portfolio_variance(
    weights: np.ndarray,
    cov_matrix: pd.DataFrame
) -> float:
    """
    Compute portfolio variance.

    Args:
        weights: Array of portfolio weights
        cov_matrix: Covariance matrix

    Returns:
        Portfolio variance
    """
    weights = weights / weights.sum()
    portfolio_variance = weights.T @ cov_matrix.values @ weights
    return float(portfolio_variance)


def compute_max_drawdown(prices: pd.Series) -> float:
    """
    Compute maximum drawdown for a price series.

    Args:
        prices: Series of prices

    Returns:
        Maximum drawdown as a decimal (e.g., 0.15 for 15%)
    """
    # Compute cumulative returns
    cumulative = (prices / prices.iloc[0])

    # Running maximum
    running_max = cumulative.expanding().max()

    # Drawdown
    drawdown = (cumulative - running_max) / running_max

    # Maximum drawdown
    max_dd = drawdown.min()

    return abs(float(max_dd))


def compute_portfolio_max_drawdown(
    prices: pd.DataFrame,
    weights: np.ndarray
) -> float:
    """
    Compute maximum drawdown for a portfolio.

    Args:
        prices: DataFrame with prices for each asset
        weights: Array of portfolio weights

    Returns:
        Maximum drawdown
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Compute portfolio value over time
    returns = prices.pct_change().fillna(0)
    portfolio_returns = (returns * weights).sum(axis=1)

    # Cumulative portfolio value
    portfolio_value = (1 + portfolio_returns).cumprod()

    # Compute drawdown
    running_max = portfolio_value.expanding().max()
    drawdown = (portfolio_value - running_max) / running_max

    max_dd = abs(drawdown.min())

    return float(max_dd)


def compute_var(
    returns: pd.DataFrame,
    weights: np.ndarray,
    confidence: float = 0.95
) -> float:
    """
    Compute Value at Risk (VaR) for a portfolio.

    Args:
        returns: DataFrame with daily returns
        weights: Array of portfolio weights
        confidence: Confidence level (e.g., 0.95 for 95%)

    Returns:
        VaR as a decimal
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Portfolio returns
    portfolio_returns = (returns * weights).sum(axis=1)

    # VaR at confidence level
    var = portfolio_returns.quantile(1 - confidence)

    return abs(float(var))


def compute_cvar(
    returns: pd.DataFrame,
    weights: np.ndarray,
    confidence: float = 0.95
) -> float:
    """
    Compute Conditional Value at Risk (CVaR) - Expected Shortfall.

    Args:
        returns: DataFrame with daily returns
        weights: Array of portfolio weights
        confidence: Confidence level

    Returns:
        CVaR as a decimal
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Portfolio returns
    portfolio_returns = (returns * weights).sum(axis=1)

    # VaR threshold
    var_threshold = portfolio_returns.quantile(1 - confidence)

    # CVaR: mean of returns below VaR
    cvar = portfolio_returns[portfolio_returns <= var_threshold].mean()

    return abs(float(cvar))


def compute_portfolio_beta(
    returns: pd.DataFrame,
    weights: np.ndarray,
    market_returns: pd.Series
) -> float:
    """
    Compute portfolio beta relative to market.

    Args:
        returns: DataFrame with asset returns
        weights: Portfolio weights
        market_returns: Series with market returns

    Returns:
        Portfolio beta
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Portfolio returns
    portfolio_returns = (returns * weights).sum(axis=1)

    # Align dates
    aligned = pd.DataFrame({
        'portfolio': portfolio_returns,
        'market': market_returns
    }).dropna()

    # Beta = Cov(portfolio, market) / Var(market)
    cov = aligned['portfolio'].cov(aligned['market'])
    market_var = aligned['market'].var()

    beta = cov / market_var if market_var > 0 else 1.0

    return float(beta)


def compute_tracking_error(
    returns: pd.DataFrame,
    weights: np.ndarray,
    benchmark_returns: pd.Series
) -> float:
    """
    Compute tracking error relative to benchmark.

    Args:
        returns: DataFrame with asset returns
        weights: Portfolio weights
        benchmark_returns: Series with benchmark returns

    Returns:
        Annualized tracking error
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Portfolio returns
    portfolio_returns = (returns * weights).sum(axis=1)

    # Align dates
    aligned = pd.DataFrame({
        'portfolio': portfolio_returns,
        'benchmark': benchmark_returns
    }).dropna()

    # Tracking difference
    tracking_diff = aligned['portfolio'] - aligned['benchmark']

    # Tracking error (annualized std dev)
    tracking_error = tracking_diff.std() * np.sqrt(settings.trading_days_per_year)

    return float(tracking_error)


def compute_diversification_ratio(
    weights: np.ndarray,
    volatilities: pd.Series,
    cov_matrix: pd.DataFrame
) -> float:
    """
    Compute diversification ratio.
    Ratio of weighted sum of volatilities to portfolio volatility.

    Args:
        weights: Portfolio weights
        volatilities: Individual asset volatilities
        cov_matrix: Covariance matrix

    Returns:
        Diversification ratio (higher is better)
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Weighted average volatility
    weighted_vol = (weights * volatilities.values).sum()

    # Portfolio volatility
    portfolio_vol = compute_portfolio_risk(weights, cov_matrix)

    # Diversification ratio
    div_ratio = weighted_vol / portfolio_vol if portfolio_vol > 0 else 1.0

    return float(div_ratio)


def compute_risk_contribution(
    weights: np.ndarray,
    cov_matrix: pd.DataFrame
) -> pd.Series:
    """
    Compute marginal risk contribution of each asset.

    Args:
        weights: Portfolio weights
        cov_matrix: Covariance matrix

    Returns:
        Series with risk contribution for each asset
    """
    # Normalize weights
    weights = weights / weights.sum()

    # Portfolio volatility
    portfolio_vol = compute_portfolio_risk(weights, cov_matrix)

    # Marginal contribution: (Σ * w) / σ_p
    marginal_contrib = (cov_matrix.values @ weights) / portfolio_vol

    # Risk contribution: w_i * MC_i
    risk_contrib = weights * marginal_contrib

    return pd.Series(risk_contrib, index=cov_matrix.index)


def compute_risk_metrics(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    tickers: List[str],
    weights: Optional[np.ndarray] = None
) -> Dict:
    """
    Compute comprehensive risk metrics for a portfolio.

    Args:
        prices: DataFrame with prices
        returns: DataFrame with returns
        tickers: List of tickers in portfolio
        weights: Portfolio weights (if None, uses equal weights)

    Returns:
        Dictionary with risk metrics
    """
    # Filter to portfolio
    portfolio_prices = prices[tickers]
    portfolio_returns = returns[tickers]

    # Default to equal weights
    if weights is None:
        weights = np.ones(len(tickers)) / len(tickers)

    # Covariance matrix
    cov_matrix = compute_covariance_matrix(portfolio_returns)

    # Compute metrics
    metrics = {
        "portfolio_volatility": compute_portfolio_risk(weights, cov_matrix),
        "portfolio_variance": compute_portfolio_variance(weights, cov_matrix),
        "max_drawdown": compute_portfolio_max_drawdown(portfolio_prices, weights),
        "var_95": compute_var(portfolio_returns, weights, confidence=0.95),
        "cvar_95": compute_cvar(portfolio_returns, weights, confidence=0.95),
    }

    return metrics
