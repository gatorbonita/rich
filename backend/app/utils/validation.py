"""
Validation utilities and custom exceptions.
"""

from typing import List, Dict, Optional
import pandas as pd
import numpy as np


class ValidationError(Exception):
    """Base validation error."""
    pass


class DataQualityError(ValidationError):
    """Raised when data quality is insufficient."""
    pass


class InsufficientReturnError(ValidationError):
    """Raised when no portfolio meets minimum return requirement."""
    pass


class OptimizationTimeoutError(ValidationError):
    """Raised when optimization exceeds time limit."""
    pass


class ConstraintViolationError(ValidationError):
    """Raised when portfolio constraints are violated."""
    pass


def validate_tickers(tickers: List[str], available_tickers: List[str]) -> bool:
    """
    Validate that all tickers are available.

    Args:
        tickers: List of tickers to validate
        available_tickers: List of available tickers

    Returns:
        True if all tickers are valid

    Raises:
        ValidationError: If any ticker is invalid
    """
    invalid = [t for t in tickers if t not in available_tickers]

    if invalid:
        raise ValidationError(
            f"Invalid tickers: {', '.join(invalid)}"
        )

    return True


def validate_weights(weights: np.ndarray, tolerance: float = 1e-6) -> bool:
    """
    Validate portfolio weights.

    Args:
        weights: Array of weights
        tolerance: Tolerance for sum check

    Returns:
        True if weights are valid

    Raises:
        ValidationError: If weights are invalid
    """
    # Check for negative weights
    if (weights < 0).any():
        raise ValidationError("Weights cannot be negative")

    # Check if weights sum to ~1
    weight_sum = weights.sum()
    if abs(weight_sum - 1.0) > tolerance:
        raise ValidationError(
            f"Weights sum to {weight_sum:.4f}, expected 1.0"
        )

    return True


def validate_covariance_matrix(cov_matrix: pd.DataFrame) -> bool:
    """
    Validate covariance matrix.

    Args:
        cov_matrix: Covariance matrix

    Returns:
        True if matrix is valid

    Raises:
        ValidationError: If matrix is invalid
    """
    # Check symmetry
    if not np.allclose(cov_matrix, cov_matrix.T):
        raise ValidationError("Covariance matrix is not symmetric")

    # Check positive semi-definite
    eigenvalues = np.linalg.eigvalsh(cov_matrix)
    if (eigenvalues < -1e-8).any():
        raise ValidationError(
            "Covariance matrix is not positive semi-definite"
        )

    # Check for NaN or inf
    if cov_matrix.isnull().any().any():
        raise ValidationError("Covariance matrix contains NaN values")

    if np.isinf(cov_matrix.values).any():
        raise ValidationError("Covariance matrix contains infinite values")

    return True


def validate_returns(returns: pd.DataFrame) -> bool:
    """
    Validate returns data.

    Args:
        returns: DataFrame with returns

    Returns:
        True if returns are valid

    Raises:
        ValidationError: If returns are invalid
    """
    # Check for all NaN columns
    all_nan_cols = returns.columns[returns.isnull().all()]
    if len(all_nan_cols) > 0:
        raise DataQualityError(
            f"Columns with all NaN values: {', '.join(all_nan_cols)}"
        )

    # Check for excessive NaN values
    nan_pct = returns.isnull().sum() / len(returns) * 100
    high_nan = nan_pct[nan_pct > 20]
    if len(high_nan) > 0:
        raise DataQualityError(
            f"Columns with >20% NaN: {', '.join(high_nan.index)}"
        )

    # Check for inf values
    inf_cols = returns.columns[(np.isinf(returns)).any()]
    if len(inf_cols) > 0:
        raise DataQualityError(
            f"Columns with infinite values: {', '.join(inf_cols)}"
        )

    return True


def validate_prices(prices: pd.DataFrame) -> bool:
    """
    Validate price data.

    Args:
        prices: DataFrame with prices

    Returns:
        True if prices are valid

    Raises:
        ValidationError: If prices are invalid
    """
    # Check for negative or zero prices
    for col in prices.columns:
        non_nan_prices = prices[col].dropna()
        if (non_nan_prices <= 0).any():
            raise DataQualityError(
                f"{col} has non-positive prices"
            )

    # Check for sufficient data
    min_rows = 100  # Minimum data points
    for col in prices.columns:
        valid_data = prices[col].dropna()
        if len(valid_data) < min_rows:
            raise DataQualityError(
                f"{col} has only {len(valid_data)} valid data points (minimum: {min_rows})"
            )

    return True


def sanitize_float(value: float, default: float = 0.0) -> float:
    """
    Sanitize float values (handle NaN, inf).

    Args:
        value: Float value to sanitize
        default: Default value if invalid

    Returns:
        Sanitized float
    """
    if np.isnan(value) or np.isinf(value):
        return default
    return float(value)


def sanitize_series(series: pd.Series, default: float = 0.0) -> pd.Series:
    """
    Sanitize a pandas Series (handle NaN, inf).

    Args:
        series: Series to sanitize
        default: Default value for invalid entries

    Returns:
        Sanitized Series
    """
    return series.replace([np.inf, -np.inf], np.nan).fillna(default)


def validate_optimization_config(
    max_stocks: int,
    min_return: float,
    available_candidates: int
) -> bool:
    """
    Validate optimization configuration.

    Args:
        max_stocks: Maximum number of stocks
        min_return: Minimum return requirement
        available_candidates: Number of available candidates

    Returns:
        True if configuration is valid

    Raises:
        ValidationError: If configuration is invalid
    """
    if max_stocks < 1:
        raise ValidationError("max_stocks must be at least 1")

    if max_stocks > 20:
        raise ValidationError("max_stocks cannot exceed 20")

    if min_return < 0:
        raise ValidationError("min_return cannot be negative")

    if min_return > 1.0:
        raise ValidationError("min_return cannot exceed 100%")

    if available_candidates < max_stocks:
        raise ValidationError(
            f"Only {available_candidates} candidates available, "
            f"but {max_stocks} stocks requested"
        )

    return True


def check_data_freshness(
    data_timestamp: pd.Timestamp,
    max_age_hours: int = 24
) -> bool:
    """
    Check if data is fresh enough.

    Args:
        data_timestamp: Timestamp of data
        max_age_hours: Maximum age in hours

    Returns:
        True if data is fresh

    Raises:
        DataQualityError: If data is too old
    """
    import pandas as pd
    from datetime import datetime, timedelta

    age = datetime.now() - data_timestamp.to_pydatetime()
    max_age = timedelta(hours=max_age_hours)

    if age > max_age:
        raise DataQualityError(
            f"Data is {age.total_seconds() / 3600:.1f} hours old "
            f"(maximum: {max_age_hours} hours)"
        )

    return True
