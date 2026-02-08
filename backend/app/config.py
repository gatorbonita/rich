"""
Configuration management for the portfolio optimization application.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    app_debug: bool = Field(default=True, env="APP_DEBUG")

    # Cache
    cache_dir: str = Field(default="./cache", env="CACHE_DIR")
    cache_ttl_hours: int = Field(default=24, env="CACHE_TTL_HOURS")

    # Data windows (in months)
    return_window_months: int = Field(default=3, env="RETURN_WINDOW_MONTHS")
    volatility_window_months: int = Field(default=12, env="VOLATILITY_WINDOW_MONTHS")
    correlation_window_months: int = Field(default=12, env="CORRELATION_WINDOW_MONTHS")

    # Optimization
    max_optimization_time_seconds: int = Field(default=2, env="MAX_OPTIMIZATION_TIME_SECONDS")
    n_iterations: int = Field(default=1000, env="N_ITERATIONS")
    top_k_portfolios: int = Field(default=3, env="TOP_K_PORTFOLIOS")

    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        env="CORS_ORIGINS"
    )

    # Risk-free rate for Sharpe ratio (annual)
    risk_free_rate: float = Field(default=0.02, env="RISK_FREE_RATE")

    # Trading days per year
    trading_days_per_year: int = 252

    # Minimum data requirements
    min_trading_days: int = 252  # 1 year of data minimum
    max_missing_days: int = 5  # Max consecutive missing days

    # Portfolio constraints
    max_stocks_per_sector: int = 2
    min_sectors: int = 6

    # Data fetching
    batch_size: int = 20  # Max tickers per batch (reduced to avoid rate limiting)
    batch_delay_seconds: float = 1.5  # Delay between batches (increased for reliability)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def cache_path(self) -> Path:
        """Get the cache directory path."""
        path = Path(self.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_path(self) -> Path:
        """Get the data directory path."""
        return Path(__file__).parent.parent / "data"

    @property
    def universe_file(self) -> Path:
        """Get the stock universe file path."""
        return self.data_path / "universe.json"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
