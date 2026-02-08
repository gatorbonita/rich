"""
Detailed diagnostic for data fetching issues.
"""
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

print(f"yfinance version: {yf.__version__}")
print("-" * 80)

# Test with a small batch of known good stocks
test_tickers = ['AAPL', 'MSFT', 'GOOGL']
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"Testing batch download for: {test_tickers}")
print(f"Date range: {start_date.date()} to {end_date.date()}")
print()

try:
    data = yf.download(
        test_tickers,
        start=start_date,
        end=end_date,
        progress=False,
        threads=False,
        group_by="ticker"
    )

    print(f"Download completed!")
    print(f"Data shape: {data.shape}")
    print(f"Data columns (first level): {data.columns.levels[0].tolist() if hasattr(data.columns, 'levels') else list(data.columns)}")
    print(f"Data index length: {len(data.index)}")
    print()

    # Try to extract Adj Close for each ticker
    print("Extracting Adj Close for each ticker:")
    prices = pd.DataFrame()

    if len(test_tickers) == 1:
        # Single ticker case
        if 'Adj Close' in data.columns:
            prices[test_tickers[0]] = data['Adj Close']
            print(f"  {test_tickers[0]}: {len(prices[test_tickers[0]])} rows")
    else:
        # Multiple tickers
        for ticker in test_tickers:
            try:
                if ticker in data.columns.levels[0]:
                    prices[ticker] = data[ticker]['Adj Close']
                    print(f"  {ticker}: {len(prices[ticker])} rows, sample: {prices[ticker].iloc[-1]:.2f}")
                else:
                    print(f"  {ticker}: NOT FOUND in data")
            except Exception as e:
                print(f"  {ticker}: ERROR - {e}")

    print()
    print("Combined prices DataFrame:")
    print(f"  Shape: {prices.shape}")
    print(f"  Columns: {list(prices.columns)}")
    print(f"  First 3 rows:")
    print(prices.head(3))
    print(f"  Last 3 rows:")
    print(prices.tail(3))
    print(f"  Missing values per column:")
    print(prices.isna().sum())

except Exception as e:
    print(f"ERROR during download: {e}")
    import traceback
    traceback.print_exc()
