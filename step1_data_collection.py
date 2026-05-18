import requests
import pandas as pd

USERNAME = "moizmahesar@gmail.com"
PASSWORD = "Editor1!"
BASE_URL = "https://webservices.iso-ne.com/api/v1.1"
LOCATION_ID = 4000
DATE = "20250624"

def fetch_da_lmp():
    url = f"{BASE_URL}/hourlylmp/da/final/day/{DATE}/location/{LOCATION_ID}.json"
    try:
        response = requests.get(url, timeout=10, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        data = response.json()
        prices = [0.0] * 24
        for lmp in data['HourlyLmps']['HourlyLmp']:
            hour = int(lmp['BeginDate'][11:13]) - 1
            prices[hour] = float(lmp['LmpTotal'])
        return prices
    except Exception as e:
        print(f"✗ Failed to get DA prices: {e}")
        return None

def fetch_rt_lmp():
    url = f"{BASE_URL}/hourlylmp/rt/final/day/{DATE}/location/{LOCATION_ID}.json"
    try:
        response = requests.get(url, timeout=10, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        data = response.json()
        prices = [0.0] * 24
        for lmp in data['HourlyLmps']['HourlyLmp']:
            hour = int(lmp['BeginDate'][11:13]) - 1
            prices[hour] = float(lmp['LmpTotal'])
        return prices
    except Exception as e:
        print(f"✗ Failed to get RT prices: {e}")
        return None

def fetch_tmnsr():
    url = f"{BASE_URL}/daasreservedata/day/{DATE}.json"
    try:
        response = requests.get(url, timeout=10, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        data = response.json()
        prices = [0.0] * 24
        for reserve in data['isone_web_services']['day_ahead_reserves']['day_ahead_reserve']:
            hour = int(reserve['market_hour']['local_hour_end']) - 1
            prices[hour] = float(reserve['tmnsr_clearing_price'])
        return prices
    except Exception as e:
        print(f"✗ Failed to get TMNSR prices: {e}")
        return None

def fetch_strike_prices():
    url = f"{BASE_URL}/daasstrikeprices/day/{DATE}.json"
    try:
        response = requests.get(url, timeout=10, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        data = response.json()
        prices = [0.0] * 24
        for strike in data['isone_web_services']['day_ahead_strike_prices']['day_ahead_strike_price']:
            hour = int(strike['market_hour']['local_hour_end']) - 1
            prices[hour] = float(strike['strike_price'])
        return prices
    except Exception as e:
        print(f"✗ Failed to get strike prices: {e}")
        return None

print("=" * 60)
print("FETCHING PRICING DATA FOR JUNE 24, 2025")
print("=" * 60)

print("\nFetching DA prices...")
da_prices = fetch_da_lmp()

print("Fetching RT prices...")
rt_prices = fetch_rt_lmp()

print("Fetching TMNSR prices...")
tmnsr_prices = fetch_tmnsr()

print("Fetching strike prices...")
strike_prices = fetch_strike_prices()

if all([da_prices, rt_prices, tmnsr_prices, strike_prices]):
    df = pd.DataFrame({
        'hour': range(1, 25),
        'da_lmp': da_prices,
        'rt_lmp': rt_prices,
        'tmnsr_price': tmnsr_prices,
        'strike_price': strike_prices
    })
    df.to_csv('pricing_data.csv', index=False)
    print("\n✓ Done fetching")
    print("\nSample data:")
    print(df.head(10))
else:
    print("\nSomething went wrong – check errors above") 