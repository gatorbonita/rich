"""
Direct test of Yahoo Finance API to see what's being returned.
"""
import requests
from datetime import datetime, timedelta
import time

# Create session with proper headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
})

ticker = 'AAPL'
end_date = int(datetime.now().timestamp())
start_date = int((datetime.now() - timedelta(days=365)).timestamp())

# Yahoo Finance v8 API endpoint
url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
params = {
    'period1': start_date,
    'period2': end_date,
    'interval': '1d',
    'events': 'div,splits',
}

print(f"Testing direct Yahoo Finance API call...")
print(f"URL: {url}")
print(f"Params: {params}")
print("-" * 80)

try:
    response = session.get(url, params=params, timeout=10)

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print()
    print(f"Response Content Length: {len(response.content)} bytes")
    print()

    if response.status_code == 200:
        print("First 500 characters of response:")
        print(response.text[:500])
        print()

        # Try to parse JSON
        try:
            data = response.json()
            print("JSON parsed successfully!")
            print(f"Keys in response: {list(data.keys())}")
            if 'chart' in data:
                print(f"Keys in chart: {list(data['chart'].keys())}")
                if 'result' in data['chart'] and data['chart']['result']:
                    print(f"Got {len(data['chart']['result'])} results")
                    result = data['chart']['result'][0]
                    if 'timestamp' in result:
                        print(f"Number of timestamps: {len(result['timestamp'])}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print(f"Error response:")
        print(response.text[:500])

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    print(f"Error type: {type(e)}")

print()
print("-" * 80)
print("Testing with yfinance version...")
import yfinance
print(f"yfinance version: {yfinance.__version__}")
