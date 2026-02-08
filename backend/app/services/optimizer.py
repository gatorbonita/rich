"""
Portfolio optimization engine.
Implements weighted random sampling + greedy local search algorithm.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
import time
from dataclasses import dataclass

from app.config import settings
from app.services.feature_service import (
    compute_returns,
    compute_expected_return,
    compute_sharpe_ratio
)
from app.services.risk_service import (
    compute_covariance_matrix,
    compute_portfolio_risk,
    compute_portfolio_variance,
    compute_portfolio_max_drawdown
)
from app.services.candidate_selector import check_sector_constraints, get_sector_allocation

logger = logging.getLogger(__name__)


@dataclass
class PortfolioResult:
    """Result of portfolio optimization."""
    tickers: List[str]
    weights: np.ndarray
    expected_return: float
    risk: float
    variance: float
    sharpe_ratio: float
    max_drawdown: float
    sector_allocation: Dict[str, int]
    correlation_score: float


class OptimizationError(Exception):
    """Raised when optimization fails."""
    pass


class InsufficientReturnError(OptimizationError):
    """Raised when no portfolio meets minimum return requirement."""
    pass


def softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """
    Compute softmax probabilities.

    Args:
        x: Input array
        temperature: Temperature parameter (higher = more uniform)

    Returns:
        Probability array
    """
    # Shift for numerical stability
    x = x - np.max(x)

    # Apply temperature
    x = x / temperature

    # Softmax
    exp_x = np.exp(x)
    probs = exp_x / exp_x.sum()

    return probs


def compute_sampling_weights(
    candidates: List[str],
    sharpe_ratios: pd.Series,
    temperature: float = 2.0
) -> np.ndarray:
    """
    Compute sampling weights based on Sharpe ratios.

    Args:
        candidates: List of candidate tickers
        sharpe_ratios: Series with Sharpe ratios
        temperature: Temperature for softmax (higher = more exploration)

    Returns:
        Array of sampling weights
    """
    # Get Sharpe ratios for candidates
    sharpe_values = sharpe_ratios[candidates].values

    # Handle negative/inf values
    sharpe_values = np.nan_to_num(sharpe_values, nan=0.0, posinf=5.0, neginf=-5.0)

    # Shift to positive (add minimum + 1)
    sharpe_values = sharpe_values - sharpe_values.min() + 1.0

    # Apply softmax
    weights = softmax(sharpe_values, temperature=temperature)

    return weights


def weighted_sample_portfolio(
    candidates: List[str],
    n_stocks: int,
    weights: np.ndarray,
    ensure_diversity: bool = True
) -> List[str]:
    """
    Sample a portfolio using weighted random sampling.

    Args:
        candidates: List of candidate tickers
        n_stocks: Number of stocks to select
        weights: Sampling weights
        ensure_diversity: Whether to ensure sector diversity

    Returns:
        List of selected tickers
    """
    # Sample without replacement
    n_stocks = min(n_stocks, len(candidates))
    indices = np.random.choice(
        len(candidates),
        size=n_stocks,
        replace=False,
        p=weights
    )

    portfolio = [candidates[i] for i in indices]

    return portfolio


def check_constraints(
    portfolio: List[str],
    expected_returns: pd.Series,
    min_return: float,
    universe: Optional[Dict[str, List[str]]] = None
) -> Tuple[bool, str]:
    """
    Check if portfolio satisfies all constraints.

    Args:
        portfolio: List of tickers
        expected_returns: Series with expected returns
        min_return: Minimum required return
        universe: Stock universe

    Returns:
        Tuple of (is_valid, reason)
    """
    # Check return constraint
    # Equal weights
    weights = np.ones(len(portfolio)) / len(portfolio)
    portfolio_return = (expected_returns[portfolio].values * weights).sum()

    if portfolio_return < min_return:
        return False, f"Return {portfolio_return:.3f} < {min_return:.3f}"

    # Check sector constraints
    if not check_sector_constraints(portfolio, universe):
        return False, "Sector constraints violated"

    return True, "OK"


def greedy_improve(
    portfolio: List[str],
    candidates: List[str],
    cov_matrix: pd.DataFrame,
    expected_returns: pd.Series,
    min_return: float,
    max_iterations: int = 5,
    universe: Optional[Dict[str, List[str]]] = None
) -> List[str]:
    """
    Improve portfolio using greedy single-stock swaps.

    Args:
        portfolio: Current portfolio
        candidates: All candidates
        cov_matrix: Covariance matrix
        expected_returns: Expected returns
        min_return: Minimum return constraint
        max_iterations: Maximum swap iterations
        universe: Stock universe

    Returns:
        Improved portfolio
    """
    n = len(portfolio)
    weights = np.ones(n) / n

    current_risk = compute_portfolio_risk(weights, cov_matrix[portfolio].loc[portfolio])
    best_portfolio = portfolio.copy()
    best_risk = current_risk

    for iteration in range(max_iterations):
        improved = False

        # Try swapping each stock
        for i, stock_to_remove in enumerate(best_portfolio):
            # Candidates not in portfolio
            available = [c for c in candidates if c not in best_portfolio]

            if not available:
                continue

            # Try each candidate
            for stock_to_add in available[:10]:  # Limit to 10 candidates per position
                # Create new portfolio
                new_portfolio = best_portfolio.copy()
                new_portfolio[i] = stock_to_add

                # Check constraints
                is_valid, _ = check_constraints(
                    new_portfolio,
                    expected_returns,
                    min_return,
                    universe
                )

                if not is_valid:
                    continue

                # Compute risk
                try:
                    new_risk = compute_portfolio_risk(
                        weights,
                        cov_matrix[new_portfolio].loc[new_portfolio]
                    )

                    # If better, update
                    if new_risk < best_risk:
                        best_risk = new_risk
                        best_portfolio = new_portfolio
                        improved = True
                        break  # Move to next position
                except:
                    continue

            if improved:
                break  # Restart iteration

        if not improved:
            break  # No improvement found

    return best_portfolio


def optimize_portfolio(
    candidates: List[str],
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    max_stocks: int = 10,
    min_return: float = 0.10,
    n_iterations: Optional[int] = None,
    top_k: Optional[int] = None,
    universe: Optional[Dict[str, List[str]]] = None
) -> List[PortfolioResult]:
    """
    Optimize portfolio using weighted random sampling + greedy search.

    Args:
        candidates: List of candidate tickers
        prices: DataFrame with prices
        returns: DataFrame with returns
        max_stocks: Maximum number of stocks in portfolio
        min_return: Minimum required annual return
        n_iterations: Number of optimization iterations
        top_k: Number of top portfolios to return
        universe: Stock universe

    Returns:
        List of top portfolio results

    Raises:
        OptimizationError: If optimization fails
        InsufficientReturnError: If no portfolio meets return requirement
    """
    if n_iterations is None:
        n_iterations = settings.n_iterations

    if top_k is None:
        top_k = settings.top_k_portfolios

    logger.info(
        f"Starting optimization: {len(candidates)} candidates, "
        f"{max_stocks} stocks, min_return={min_return:.2%}"
    )

    start_time = time.time()

    # Pre-compute features
    sharpe_ratios = compute_sharpe_ratio(returns[candidates])
    expected_returns = compute_expected_return(
        returns[candidates],
        window=settings.return_window_months * 21
    )
    cov_matrix = compute_covariance_matrix(returns[candidates])

    # Compute sampling weights
    sampling_weights = compute_sampling_weights(candidates, sharpe_ratios)

    # Store best portfolios
    best_portfolios = []
    valid_portfolios_found = 0

    for i in range(n_iterations):
        # Check timeout
        if time.time() - start_time > settings.max_optimization_time_seconds:
            logger.warning(f"Optimization timeout after {i} iterations")
            break

        # Sample portfolio
        portfolio = weighted_sample_portfolio(
            candidates,
            max_stocks,
            sampling_weights
        )

        # Check constraints
        is_valid, reason = check_constraints(
            portfolio,
            expected_returns,
            min_return,
            universe
        )

        if not is_valid:
            continue

        valid_portfolios_found += 1

        # Greedy improvement
        portfolio = greedy_improve(
            portfolio,
            candidates,
            cov_matrix,
            expected_returns,
            min_return,
            max_iterations=3,
            universe=universe
        )

        # Compute final metrics
        n_stocks = len(portfolio)
        weights = np.ones(n_stocks) / n_stocks

        try:
            port_cov = cov_matrix[portfolio].loc[portfolio]
            port_risk = compute_portfolio_risk(weights, port_cov)
            port_variance = compute_portfolio_variance(weights, port_cov)
            port_return = (expected_returns[portfolio].values * weights).sum()
            port_sharpe = (port_return - settings.risk_free_rate) / port_risk if port_risk > 0 else 0
            port_max_dd = compute_portfolio_max_drawdown(prices[portfolio], weights)

            # Correlation score (average pairwise correlation)
            port_corr = returns[portfolio].corr()
            # Get upper triangle (excluding diagonal)
            mask = np.triu(np.ones_like(port_corr, dtype=bool), k=1)
            avg_corr = port_corr.where(mask).mean().mean()

            sector_allocation = get_sector_allocation(portfolio, universe)

            result = PortfolioResult(
                tickers=portfolio,
                weights=weights,
                expected_return=port_return,
                risk=port_risk,
                variance=port_variance,
                sharpe_ratio=port_sharpe,
                max_drawdown=port_max_dd,
                sector_allocation=sector_allocation,
                correlation_score=avg_corr
            )

            best_portfolios.append(result)

        except Exception as e:
            logger.debug(f"Error computing metrics: {e}")
            continue

    elapsed = time.time() - start_time
    logger.info(
        f"Optimization complete: {valid_portfolios_found} valid portfolios "
        f"in {elapsed:.2f}s"
    )

    if not best_portfolios:
        # Try to find best available portfolio without return constraint
        logger.warning("No portfolio found meeting constraints, finding best available...")

        # Find highest return achievable
        best_attempt = None
        best_attempt_return = -np.inf

        for _ in range(min(200, n_iterations)):
            portfolio = weighted_sample_portfolio(
                candidates,
                max_stocks,
                sampling_weights
            )

            if not check_sector_constraints(portfolio, universe):
                continue

            weights = np.ones(len(portfolio)) / len(portfolio)
            port_return = (expected_returns[portfolio].values * weights).sum()

            if port_return > best_attempt_return:
                best_attempt = portfolio
                best_attempt_return = port_return

        if best_attempt:
            raise InsufficientReturnError(
                f"No portfolio found meeting minimum return of {min_return:.2%}. "
                f"Maximum achievable: {best_attempt_return:.2%}"
            )
        else:
            raise OptimizationError("Could not find any valid portfolio")

    # Sort by risk (lower is better) and return top K
    best_portfolios.sort(key=lambda x: x.risk)
    top_portfolios = best_portfolios[:top_k]

    logger.info(
        f"Top portfolio: {len(top_portfolios[0].tickers)} stocks, "
        f"return={top_portfolios[0].expected_return:.2%}, "
        f"risk={top_portfolios[0].risk:.2%}"
    )

    return top_portfolios
