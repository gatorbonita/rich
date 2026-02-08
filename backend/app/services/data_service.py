"""
Data service for fetching and caching stock price data.
Handles yfinance integration, validation, and error handling.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import time
from diskcache import Cache
import logging

from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize cache
cache = Cache(str(settings.cache_path))


class DataQualityError(Exception):
    """Raised when data quality issues are detected."""
    pass


class DataValidationResult:
    """Result of data validation."""

    def __init__(self, is_valid: bool, issues: List[str], ticker: str):
        self.is_valid = is_valid
        self.issues = issues
        self.ticker = ticker

    def __repr__(self):
        status = "✓" if self.is_valid else "✗"
        return f"{status} {self.ticker}: {', '.join(self.issues) if self.issues else 'OK'}"


def fetch_prices(
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch adjusted close prices for given tickers.

    Args:
        tickers: List of ticker symbols
        start_date: Start date for price data
        end_date: End date for price data
        use_cache: Whether to use cached data

    Returns:
        DataFrame with dates as index and tickers as columns

    Raises:
        DataQualityError: If data quality is insufficient
    """
    cache_key = f"prices_{'-'.join(sorted(tickers))}_{start_date.date()}_{end_date.date()}"

    # Check cache first
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached data for {len(tickers)} tickers")
            return cached_data

    logger.info(f"Fetching price data for {len(tickers)} tickers...")

    # Fetch in batches to avoid rate limiting
    all_prices = []
    for i in range(0, len(tickers), settings.batch_size):
        batch = tickers[i:i + settings.batch_size]
        logger.info(f"Fetching batch {i // settings.batch_size + 1}: {len(batch)} tickers")

        try:
            # Download data - yfinance 1.1.0+ handles sessions internally with curl_cffi
            data = yf.download(
                batch,
                start=start_date,
                end=end_date,
                progress=False,
                threads=False,  # Disable threading to avoid rate limiting
                group_by="ticker"
            )

            # Extract close prices (yfinance 1.1.0+ returns adjusted prices in 'Close' column)
            if len(batch) == 1:
                # Single ticker - different structure
                if 'Close' in data.columns:
                    prices = data[['Close']].copy()
                    prices.columns = [batch[0]]
                elif 'Adj Close' in data.columns:
                    # Fallback for older yfinance versions
                    prices = data[['Adj Close']].copy()
                    prices.columns = [batch[0]]
                else:
                    logger.warning(f"No data for {batch[0]}")
                    continue
            else:
                # Multiple tickers
                prices = pd.DataFrame()
                for ticker in batch:
                    try:
                        if ticker in data.columns.levels[0]:
                            # Try 'Close' first (yfinance 1.1.0+), then 'Adj Close' (older versions)
                            if 'Close' in data[ticker].columns:
                                prices[ticker] = data[ticker]['Close']
                            elif 'Adj Close' in data[ticker].columns:
                                prices[ticker] = data[ticker]['Adj Close']
                    except (KeyError, AttributeError) as e:
                        logger.warning(f"Could not extract data for {ticker}: {e}")
                        continue

            all_prices.append(prices)

            # Rate limiting delay
            if i + settings.batch_size < len(tickers):
                time.sleep(settings.batch_delay_seconds)

        except Exception as e:
            logger.error(f"Error fetching batch: {e}")
            continue

    if not all_prices:
        raise DataQualityError("No data could be fetched for any ticker")

    # Combine all batches
    prices_df = pd.concat(all_prices, axis=1)

    # Remove duplicate columns if any
    prices_df = prices_df.loc[:, ~prices_df.columns.duplicated()]

    # Sort by date
    prices_df = prices_df.sort_index()

    # Cache the result
    if use_cache:
        cache.set(
            cache_key,
            prices_df,
            expire=settings.cache_ttl_hours * 3600
        )

    logger.info(f"Fetched {len(prices_df)} days of data for {len(prices_df.columns)} tickers")

    return prices_df


def validate_data(prices: pd.DataFrame, ticker: str) -> DataValidationResult:
    """
    Validate price data quality for a single ticker.

    Args:
        prices: DataFrame with price data
        ticker: Ticker symbol to validate

    Returns:
        DataValidationResult with validation status and issues
    """
    issues = []

    if ticker not in prices.columns:
        return DataValidationResult(False, ["Ticker not found in data"], ticker)

    ticker_data = prices[ticker]

    # Check for insufficient data
    valid_data = ticker_data.dropna()
    if len(valid_data) < settings.min_trading_days:
        issues.append(
            f"Insufficient data: {len(valid_data)} days (minimum: {settings.min_trading_days})"
        )

    # Check for too many missing values
    missing_pct = ticker_data.isna().sum() / len(ticker_data) * 100
    if missing_pct > 10:
        issues.append(f"Too many missing values: {missing_pct:.1f}%")

    # Check for consecutive missing days
    is_missing = ticker_data.isna()
    if is_missing.any():
        # Find consecutive missing days
        missing_groups = (is_missing != is_missing.shift()).cumsum()[is_missing]
        if len(missing_groups) > 0:
            max_consecutive = missing_groups.value_counts().max()
            if max_consecutive > settings.max_missing_days:
                issues.append(
                    f"Too many consecutive missing days: {max_consecutive} "
                    f"(max: {settings.max_missing_days})"
                )

    # Check for zero or negative prices
    if (valid_data <= 0).any():
        issues.append("Contains zero or negative prices")

    # Check for extreme price jumps (>50% in one day)
    pct_changes = valid_data.pct_change().abs()
    extreme_moves = (pct_changes > 0.5).sum()
    if extreme_moves > 0:
        issues.append(f"Contains {extreme_moves} extreme price movements (>50%)")

    # Check for suspiciously low volatility (might indicate stale data)
    if len(valid_data) > 20:
        volatility = valid_data.pct_change().std()
        if volatility < 0.0001:  # Essentially no movement
            issues.append("Suspiciously low volatility - possible stale data")

    is_valid = len(issues) == 0

    return DataValidationResult(is_valid, issues, ticker)


def validate_all_data(prices: pd.DataFrame) -> Tuple[List[str], Dict[str, DataValidationResult]]:
    """
    Validate all tickers in the price DataFrame.

    Args:
        prices: DataFrame with price data

    Returns:
        Tuple of (valid_tickers, validation_results)
    """
    valid_tickers = []
    validation_results = {}

    for ticker in prices.columns:
        result = validate_data(prices, ticker)
        validation_results[ticker] = result

        if result.is_valid:
            valid_tickers.append(ticker)
        else:
            logger.warning(f"Validation failed for {ticker}: {', '.join(result.issues)}")

    logger.info(f"Validation: {len(valid_tickers)}/{len(prices.columns)} tickers passed")

    return valid_tickers, validation_results


def get_date_range(months: int) -> Tuple[datetime, datetime]:
    """
    Get start and end dates for data fetching.

    Args:
        months: Number of months of historical data

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 31)  # Approximate
    return start_date, end_date


def fetch_and_validate_prices(
    tickers: List[str],
    months: int = 12,
    use_cache: bool = True
) -> Tuple[pd.DataFrame, List[str], Dict[str, DataValidationResult]]:
    """
    Fetch and validate price data for tickers.

    Args:
        tickers: List of ticker symbols
        months: Number of months of historical data
        use_cache: Whether to use cached data

    Returns:
        Tuple of (prices_df, valid_tickers, validation_results)
    """
    start_date, end_date = get_date_range(months)

    # Fetch prices
    prices = fetch_prices(tickers, start_date, end_date, use_cache=use_cache)

    # Validate
    valid_tickers, validation_results = validate_all_data(prices)

    # Return only valid tickers
    valid_prices = prices[valid_tickers].copy()

    return valid_prices, valid_tickers, validation_results


def clear_cache():
    """Clear all cached data."""
    cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> Dict:
    """Get cache statistics."""
    return {
        "size": len(cache),
        "volume": cache.volume(),
    }
