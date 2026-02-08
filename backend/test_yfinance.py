"""
Simple test script to debug yfinance data fetching.
"""
import yfinance as yf
import requests
from datetime import datetime, timedelta

# Create session with proper headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

print("Testing yfinance with a single stock (AAPL)...")
print("-" * 50)

# Calculate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"Start date: {start_date.date()}")
print(f"End date: {end_date.date()}")
print()

# Method 1: Using download
print("Method 1: yf.download() with session")
try:
    data = yf.download(
        'AAPL',
        start=start_date,
        end=end_date,
        progress=False,
        session=session
    )
    print(f"Success! Got {len(data)} rows")
    print(f"Columns: {list(data.columns)}")
    print(f"First few rows:")
    print(data.head())
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")

print()
print("-" * 50)

# Method 2: Using Ticker object
print("Method 2: yf.Ticker() with session")
try:
    ticker = yf.Ticker('AAPL', session=session)
    hist = ticker.history(start=start_date, end=end_date)
    print(f"Success! Got {len(hist)} rows")
    print(f"Columns: {list(hist.columns)}")
    print(f"First few rows:")
    print(hist.head())
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")

print()
print("-" * 50)

# Method 3: Just get basic info
print("Method 3: Getting ticker info")
try:
    ticker = yf.Ticker('AAPL', session=session)
    info = ticker.info
    print(f"Success! Got info")
    print(f"Company: {info.get('longName', 'N/A')}")
    print(f"Sector: {info.get('sector', 'N/A')}")
    print(f"Current Price: {info.get('currentPrice', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
