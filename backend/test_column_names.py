"""
Check exact column structure in yfinance 1.1.0
"""
import yfinance as yf
from datetime import datetime, timedelta

test_tickers = ['AAPL', 'MSFT']
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print("Downloading data...")
data = yf.download(
    test_tickers,
    start=start_date,
    end=end_date,
    progress=False,
    threads=False,
    group_by="ticker"
)

print(f"\nData shape: {data.shape}")
print(f"\nColumn structure:")
print(f"Type: {type(data.columns)}")
print(f"Columns: {data.columns}")
print(f"\nAll column names:")
for col in data.columns:
    print(f"  {col}")

print(f"\nFirst few rows:")
print(data.head(3))

print(f"\nTrying to access AAPL columns:")
if 'AAPL' in data.columns.levels[0]:
    print(f"AAPL sub-columns: {data['AAPL'].columns.tolist()}")
    print(f"\nAAPL data sample:")
    print(data['AAPL'].head(3))
