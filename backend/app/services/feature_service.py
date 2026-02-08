"""
Feature engineering service for portfolio optimization.
Computes returns, volatility, Sharpe ratios, correlations, etc.
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily returns from prices.

    Args:
        prices: DataFrame with prices (dates as index, tickers as columns)

    Returns:
        DataFrame with daily returns
    """
    returns = prices.pct_change().dropna()
    return returns


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute log returns from prices.

    Args:
        prices: DataFrame with prices

    Returns:
        DataFrame with log returns
    """
    log_returns = np.log(prices / prices.shift(1)).dropna()
    return log_returns


def compute_volatility(
    returns: pd.DataFrame,
    window: Optional[int] = None,
    annualize: bool = True
) -> pd.Series:
    """
    Compute volatility (standard deviation of returns).

    Args:
        returns: DataFrame with daily returns
        window: Rolling window size (if None, uses full history)
        annualize: Whether to annualize the volatility

    Returns:
        Series with volatility for each ticker
    """
    if window is not None:
        # Rolling volatility - take the most recent value
        vol = returns.rolling(window=window).std().iloc[-1]
    else:
        # Full history volatility
        vol = returns.std()

    if annualize:
        vol = vol * np.sqrt(settings.trading_days_per_year)

    return vol


def compute_sharpe_ratio(
    returns: pd.DataFrame,
    risk_free_rate: Optional[float] = None,
    annualize: bool = True
) -> pd.Series:
    """
    Compute Sharpe ratio for each ticker.

    Args:
        returns: DataFrame with daily returns
        risk_free_rate: Annual risk-free rate (if None, uses config default)
        annualize: Whether to annualize the Sharpe ratio

    Returns:
        Series with Sharpe ratio for each ticker
    """
    if risk_free_rate is None:
        risk_free_rate = settings.risk_free_rate

    # Daily risk-free rate
    daily_rf = risk_free_rate / settings.trading_days_per_year

    # Mean excess return
    excess_returns = returns - daily_rf
    mean_excess = excess_returns.mean()

    # Volatility
    vol = returns.std()

    # Sharpe ratio
    sharpe = mean_excess / vol

    if annualize:
        sharpe = sharpe * np.sqrt(settings.trading_days_per_year)

    return sharpe


def compute_correlation_matrix(
    returns: pd.DataFrame,
    window: Optional[int] = None
) -> pd.DataFrame:
    """
    Compute correlation matrix of returns.

    Args:
        returns: DataFrame with daily returns
        window: Rolling window size (if None, uses full history)

    Returns:
        DataFrame with correlation matrix
    """
    if window is not None:
        # Use most recent window
        recent_returns = returns.iloc[-window:]
        corr_matrix = recent_returns.corr()
    else:
        corr_matrix = returns.corr()

    # Fill NaN values with 0 (no correlation)
    corr_matrix = corr_matrix.fillna(0)

    # Ensure diagonal is 1
    np.fill_diagonal(corr_matrix.values, 1.0)

    return corr_matrix


def compute_expected_return(
    returns: pd.DataFrame,
    window: Optional[int] = None,
    annualize: bool = True
) -> pd.Series:
    """
    Compute expected return (mean return) for each ticker.

    Args:
        returns: DataFrame with daily returns
        window: Window size in trading days (if None, uses full history)
        annualize: Whether to annualize the return

    Returns:
        Series with expected return for each ticker
    """
    if window is not None:
        recent_returns = returns.iloc[-window:]
        expected_ret = recent_returns.mean()
    else:
        expected_ret = returns.mean()

    if annualize:
        expected_ret = expected_ret * settings.trading_days_per_year

    return expected_ret


def compute_cumulative_return(prices: pd.DataFrame) -> pd.Series:
    """
    Compute cumulative return over the entire period.

    Args:
        prices: DataFrame with prices

    Returns:
        Series with cumulative return for each ticker
    """
    cum_return = (prices.iloc[-1] / prices.iloc[0]) - 1
    return cum_return


def compute_downside_deviation(
    returns: pd.DataFrame,
    threshold: float = 0.0,
    annualize: bool = True
) -> pd.Series:
    """
    Compute downside deviation (volatility of negative returns).

    Args:
        returns: DataFrame with daily returns
        threshold: Threshold for downside (default 0)
        annualize: Whether to annualize

    Returns:
        Series with downside deviation for each ticker
    """
    # Only consider returns below threshold
    downside_returns = returns.copy()
    downside_returns[downside_returns > threshold] = 0

    # Compute standard deviation
    downside_dev = np.sqrt((downside_returns ** 2).mean())

    if annualize:
        downside_dev = downside_dev * np.sqrt(settings.trading_days_per_year)

    return downside_dev


def compute_sortino_ratio(
    returns: pd.DataFrame,
    risk_free_rate: Optional[float] = None,
    threshold: float = 0.0,
    annualize: bool = True
) -> pd.Series:
    """
    Compute Sortino ratio (like Sharpe but uses downside deviation).

    Args:
        returns: DataFrame with daily returns
        risk_free_rate: Annual risk-free rate
        threshold: Threshold for downside
        annualize: Whether to annualize

    Returns:
        Series with Sortino ratio for each ticker
    """
    if risk_free_rate is None:
        risk_free_rate = settings.risk_free_rate

    daily_rf = risk_free_rate / settings.trading_days_per_year

    # Mean excess return
    excess_returns = returns - daily_rf
    mean_excess = excess_returns.mean()

    # Downside deviation
    downside_dev = compute_downside_deviation(returns, threshold, annualize=False)

    # Sortino ratio
    sortino = mean_excess / downside_dev

    if annualize:
        sortino = sortino * np.sqrt(settings.trading_days_per_year)

    return sortino


def compute_beta(returns: pd.DataFrame, market_returns: pd.Series) -> pd.Series:
    """
    Compute beta relative to market.

    Args:
        returns: DataFrame with stock returns
        market_returns: Series with market returns (same dates)

    Returns:
        Series with beta for each ticker
    """
    # Align dates
    aligned_data = returns.join(market_returns, how='inner')
    market_col = aligned_data.columns[-1]

    betas = {}
    for ticker in returns.columns:
        if ticker in aligned_data.columns:
            # Covariance with market / variance of market
            cov = aligned_data[ticker].cov(aligned_data[market_col])
            market_var = aligned_data[market_col].var()
            betas[ticker] = cov / market_var if market_var > 0 else 1.0

    return pd.Series(betas)


def compute_information_coefficient(
    returns: pd.DataFrame,
    periods: int = 63
) -> pd.Series:
    """
    Compute information coefficient (IC) - correlation between returns in consecutive periods.
    Useful for momentum analysis.

    Args:
        returns: DataFrame with daily returns
        periods: Number of periods to look back

    Returns:
        Series with IC for each ticker
    """
    ic = {}
    for ticker in returns.columns:
        ticker_returns = returns[ticker].dropna()
        if len(ticker_returns) > periods * 2:
            # Correlation between past and future returns
            past_returns = ticker_returns.iloc[:-periods].values
            future_returns = ticker_returns.iloc[periods:].values

            if len(past_returns) > 0 and len(future_returns) > 0:
                ic[ticker] = np.corrcoef(past_returns, future_returns)[0, 1]
            else:
                ic[ticker] = 0.0
        else:
            ic[ticker] = 0.0

    return pd.Series(ic)


def compute_features_summary(
    prices: pd.DataFrame,
    return_window_days: Optional[int] = None,
    vol_window_days: Optional[int] = None
) -> pd.DataFrame:
    """
    Compute a comprehensive summary of features for all tickers.

    Args:
        prices: DataFrame with prices
        return_window_days: Window for return calculation
        vol_window_days: Window for volatility calculation

    Returns:
        DataFrame with all features (tickers as index, features as columns)
    """
    returns = compute_returns(prices)

    # Default windows
    if return_window_days is None:
        return_window_days = settings.return_window_months * 21  # Approximate trading days

    if vol_window_days is None:
        vol_window_days = settings.volatility_window_months * 21

    features = pd.DataFrame()
    features['expected_return'] = compute_expected_return(returns, window=return_window_days)
    features['volatility'] = compute_volatility(returns, window=vol_window_days)
    features['sharpe_ratio'] = compute_sharpe_ratio(returns)
    features['cumulative_return'] = compute_cumulative_return(prices)
    features['downside_deviation'] = compute_downside_deviation(returns)
    features['sortino_ratio'] = compute_sortino_ratio(returns)

    # Handle NaN and inf values
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)

    return features
