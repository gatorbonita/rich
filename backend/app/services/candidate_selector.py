"""
Candidate selection service for portfolio optimization.
Implements sector-based filtering and correlation-based de-duplication.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
import logging
import json

from app.config import settings
from app.services.feature_service import compute_returns, compute_expected_return, compute_sharpe_ratio
from app.services.risk_service import compute_covariance_matrix

logger = logging.getLogger(__name__)


def load_universe() -> Dict[str, List[str]]:
    """
    Load stock universe from JSON file.

    Returns:
        Dictionary mapping sector names to lists of tickers
    """
    with open(settings.universe_file, 'r') as f:
        universe = json.load(f)
    return universe


def select_candidates_by_sector(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    universe: Dict[str, List[str]],
    top_k: int = 5,
    return_window_days: int = 63
) -> Dict[str, List[str]]:
    """
    Select top candidates from each sector based on returns.

    Args:
        prices: DataFrame with price data
        returns: DataFrame with return data
        universe: Dictionary mapping sectors to tickers
        top_k: Number of top stocks to select per sector
        return_window_days: Window for return calculation

    Returns:
        Dictionary mapping sectors to selected tickers
    """
    # Compute expected returns for ranking
    expected_returns = compute_expected_return(returns, window=return_window_days)

    sector_candidates = {}

    for sector, tickers in universe.items():
        # Filter to tickers we have data for
        available_tickers = [t for t in tickers if t in prices.columns]

        if not available_tickers:
            logger.warning(f"No data available for sector {sector}")
            continue

        # Rank by return
        sector_returns = expected_returns[available_tickers].sort_values(ascending=False)

        # Select top K
        top_tickers = sector_returns.head(top_k).index.tolist()

        sector_candidates[sector] = top_tickers

        logger.info(f"{sector}: Selected {len(top_tickers)} candidates")

    return sector_candidates


def deduplicate_by_correlation(
    candidates_by_sector: Dict[str, List[str]],
    returns: pd.DataFrame,
    correlation_threshold: float = 0.8,
    max_per_cluster: int = 2
) -> List[str]:
    """
    Remove highly correlated stocks using hierarchical clustering.

    Args:
        candidates_by_sector: Dictionary of candidates by sector
        returns: DataFrame with return data
        correlation_threshold: Correlation threshold for clustering
        max_per_cluster: Maximum stocks to keep per cluster

    Returns:
        List of deduplicated tickers
    """
    # Flatten to single list
    all_candidates = []
    for tickers in candidates_by_sector.values():
        all_candidates.extend(tickers)

    # Remove duplicates while preserving order
    all_candidates = list(dict.fromkeys(all_candidates))

    # Filter to candidates we have returns for
    all_candidates = [t for t in all_candidates if t in returns.columns]

    if len(all_candidates) <= 10:
        # Too few candidates, return all
        return all_candidates

    logger.info(f"De-duplicating {len(all_candidates)} candidates...")

    # Compute correlation matrix
    candidate_returns = returns[all_candidates]
    corr_matrix = candidate_returns.corr()

    # Convert correlation to distance: distance = 1 - correlation
    distance_matrix = 1 - corr_matrix.abs()

    # Convert to condensed distance matrix for hierarchical clustering
    # Only use upper triangle (excluding diagonal)
    condensed_dist = squareform(distance_matrix, checks=False)

    # Hierarchical clustering
    linkage_matrix = linkage(condensed_dist, method='average')

    # Form clusters
    distance_threshold = 1 - correlation_threshold
    clusters = fcluster(linkage_matrix, distance_threshold, criterion='distance')

    # Group tickers by cluster
    cluster_groups = {}
    for ticker, cluster_id in zip(all_candidates, clusters):
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(ticker)

    logger.info(f"Formed {len(cluster_groups)} clusters")

    # Select best stocks from each cluster
    # Rank by Sharpe ratio
    sharpe_ratios = compute_sharpe_ratio(returns[all_candidates])

    deduplicated = []
    for cluster_id, cluster_tickers in cluster_groups.items():
        # Sort by Sharpe ratio
        cluster_sharpe = sharpe_ratios[cluster_tickers].sort_values(ascending=False)

        # Take top stocks from cluster
        selected = cluster_sharpe.head(max_per_cluster).index.tolist()
        deduplicated.extend(selected)

        logger.debug(
            f"Cluster {cluster_id}: {len(cluster_tickers)} stocks -> "
            f"selected {len(selected)}"
        )

    logger.info(f"After de-duplication: {len(deduplicated)} candidates")

    return deduplicated


def apply_quality_filters(
    candidates: List[str],
    returns: pd.DataFrame,
    prices: pd.DataFrame,
    min_sharpe: float = -1.0,
    min_avg_volume: float = 0  # Not implemented - would need volume data
) -> List[str]:
    """
    Apply quality filters to candidates.

    Args:
        candidates: List of candidate tickers
        returns: DataFrame with returns
        prices: DataFrame with prices
        min_sharpe: Minimum Sharpe ratio
        min_avg_volume: Minimum average volume (not implemented)

    Returns:
        List of tickers passing filters
    """
    filtered = []

    # Compute Sharpe ratios
    sharpe_ratios = compute_sharpe_ratio(returns[candidates])

    for ticker in candidates:
        # Check Sharpe ratio
        if sharpe_ratios[ticker] < min_sharpe:
            logger.debug(f"Filtered {ticker}: Sharpe {sharpe_ratios[ticker]:.2f} < {min_sharpe}")
            continue

        # Check for sufficient data
        ticker_data = prices[ticker].dropna()
        if len(ticker_data) < settings.min_trading_days:
            logger.debug(f"Filtered {ticker}: Insufficient data")
            continue

        filtered.append(ticker)

    logger.info(f"Quality filters: {len(filtered)}/{len(candidates)} passed")

    return filtered


def select_portfolio_candidates(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    top_k_per_sector: int = 5,
    correlation_threshold: float = 0.75,
    max_per_cluster: int = 2
) -> Tuple[List[str], Dict]:
    """
    Complete pipeline for selecting portfolio candidates.

    Args:
        prices: DataFrame with price data
        returns: DataFrame with return data
        top_k_per_sector: Number of top stocks per sector
        correlation_threshold: Correlation threshold for de-duplication
        max_per_cluster: Max stocks per correlation cluster

    Returns:
        Tuple of (candidate_list, metadata)
    """
    logger.info("Starting candidate selection pipeline...")

    # Load universe
    universe = load_universe()
    logger.info(f"Loaded universe with {len(universe)} sectors")

    # Step 1: Select top performers by sector
    sector_candidates = select_candidates_by_sector(
        prices=prices,
        returns=returns,
        universe=universe,
        top_k=top_k_per_sector,
        return_window_days=settings.return_window_months * 21
    )

    total_sector_candidates = sum(len(v) for v in sector_candidates.values())
    logger.info(f"Sector filtering: Selected {total_sector_candidates} candidates")

    # Step 2: De-duplicate by correlation
    candidates = deduplicate_by_correlation(
        candidates_by_sector=sector_candidates,
        returns=returns,
        correlation_threshold=correlation_threshold,
        max_per_cluster=max_per_cluster
    )

    # Step 3: Apply quality filters
    candidates = apply_quality_filters(
        candidates=candidates,
        returns=returns,
        prices=prices,
        min_sharpe=-1.0  # Allow some negative Sharpe
    )

    # Create metadata
    metadata = {
        "total_sectors": len(universe),
        "sectors_with_candidates": len(sector_candidates),
        "candidates_before_dedup": total_sector_candidates,
        "candidates_after_dedup": len(candidates),
        "correlation_threshold": correlation_threshold
    }

    logger.info(f"Candidate selection complete: {len(candidates)} final candidates")

    return candidates, metadata


def get_sector_allocation(
    tickers: List[str],
    universe: Optional[Dict[str, List[str]]] = None
) -> Dict[str, int]:
    """
    Get sector allocation for a list of tickers.

    Args:
        tickers: List of ticker symbols
        universe: Stock universe (if None, loads from file)

    Returns:
        Dictionary mapping sectors to counts
    """
    if universe is None:
        universe = load_universe()

    # Create reverse mapping: ticker -> sector
    ticker_to_sector = {}
    for sector, sector_tickers in universe.items():
        for ticker in sector_tickers:
            ticker_to_sector[ticker] = sector

    # Count by sector
    sector_counts = {}
    for ticker in tickers:
        sector = ticker_to_sector.get(ticker, "Unknown")
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return sector_counts


def check_sector_constraints(
    tickers: List[str],
    universe: Optional[Dict[str, List[str]]] = None,
    max_per_sector: Optional[int] = None,
    min_sectors: Optional[int] = None
) -> bool:
    """
    Check if a portfolio meets sector constraints.

    Args:
        tickers: List of ticker symbols
        universe: Stock universe
        max_per_sector: Maximum stocks per sector
        min_sectors: Minimum number of sectors

    Returns:
        True if constraints are met
    """
    if max_per_sector is None:
        max_per_sector = settings.max_stocks_per_sector

    if min_sectors is None:
        min_sectors = settings.min_sectors

    sector_allocation = get_sector_allocation(tickers, universe)

    # Check max per sector
    for count in sector_allocation.values():
        if count > max_per_sector:
            return False

    # Check min sectors
    if len(sector_allocation) < min_sectors:
        return False

    return True
