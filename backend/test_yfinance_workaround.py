"""
Test yfinance with proper initialization and workarounds.
"""
import yfinance as yf
from datetime import datetime, timedelta

print(f"yfinance version: {yf.__version__}")
print("-" * 80)

# Calculate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print("Testing Method 1: Ticker.history() - recommended approach")
print(f"Fetching AAPL from {start_date.date()} to {end_date.date()}")
try:
    ticker = yf.Ticker('AAPL')
    # Use history method which is more reliable
    hist = ticker.history(
        start=start_date,
        end=end_date,
        auto_adjust=True,  # Use adjusted prices
        actions=False  # Don't include dividends/splits
    )

    print(f"✓ Success! Got {len(hist)} rows")
    if len(hist) > 0:
        print(f"Columns: {list(hist.columns)}")
        print(f"\nFirst 3 rows:")
        print(hist.head(3))
        print(f"\nLast 3 rows:")
        print(hist.tail(3))
        print(f"\nData types:")
        print(hist.dtypes)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("-" * 80)
print("Testing Method 2: Multiple tickers with Ticker objects")
tickers_list = ['AAPL', 'MSFT', 'GOOGL']
print(f"Fetching {tickers_list}")

results = {}
for symbol in tickers_list:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date, auto_adjust=True, actions=False)
        results[symbol] = hist['Close'] if len(hist) > 0 else None
        print(f"✓ {symbol}: {len(hist)} rows")
    except Exception as e:
        print(f"✗ {symbol}: {e}")

if results:
    import pandas as pd
    # Combine into single DataFrame
    combined = pd.DataFrame(results)
    print(f"\nCombined DataFrame shape: {combined.shape}")
    print(f"Columns: {list(combined.columns)}")
    print(combined.head(3))
