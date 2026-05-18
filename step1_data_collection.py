"""
Fetch ISO-NE pricing data for June 24, 2025
Credentials via environment variables (not in repo)
"""
import os
import pandas as pd
import requests
from config import ISO_NE_BASE_URL, MASS_HUB_ID, ANALYSIS_DATE

USERNAME = os.getenv("ISO_NE_USER")
PASSWORD = os.getenv("ISO_NE_PASS")

if not USERNAME or not PASSWORD:
    raise ValueError(
        "Missing ISO-NE credentials. Set ISO_NE_USER and ISO_NE_PASS environment variables."
    )

print("\n" + "="*80)
print(f"Fetching ISO-NE data for {ANALYSIS_DATE}")
print("="*80 + "\n")

auth = (USERNAME, PASSWORD)

def fetch(url):
    """Fetch JSON from ISO-NE API with proper error handling"""
    response = requests.get(
        url,
        auth=auth,
        headers={"Accept": "application/json"},
        timeout=30
    )
    print(f"{response.status_code} | {url}")
    response.raise_for_status()
    return response.json()

try:
    da = fetch(f"{ISO_NE_BASE_URL}/hourlylmp/da/final/day/{ANALYSIS_DATE}/location/{MASS_HUB_ID}/")
    rt = fetch(f"{ISO_NE_BASE_URL}/hourlylmp/rt/final/day/{ANALYSIS_DATE}/location/{MASS_HUB_ID}/")
    tmnsr = fetch(f"{ISO_NE_BASE_URL}/daasreservedata/day/{ANALYSIS_DATE}/")
    strike = fetch(f"{ISO_NE_BASE_URL}/daasstrikeprices/day/{ANALYSIS_DATE}/")
except Exception as e:
    print(f"API Error: {e}")
    raise

data = {h: {} for h in range(24)}

if da and 'HourlyLmps' in da:
    for lmp in da['HourlyLmps']['HourlyLmp']:
        h = int(lmp['BeginDate'][11:13]) - 1
        if 0 <= h < 24:
            data[h]['da_lmp'] = float(lmp['LmpTotal'])

if rt and 'HourlyLmps' in rt:
    for lmp in rt['HourlyLmps']['HourlyLmp']:
        h = int(lmp['BeginDate'][11:13]) - 1
        if 0 <= h < 24:
            data[h]['rt_lmp'] = float(lmp['LmpTotal'])

if tmnsr and 'isone_web_services' in tmnsr:
    for r in tmnsr['isone_web_services']['day_ahead_reserves']['day_ahead_reserve']:
        h = int(r['market_hour']['local_hour_end']) - 1
        if 0 <= h < 24:
            data[h]['tmnsr_price'] = float(r['tmnsr_clearing_price'])

if strike and 'isone_web_services' in strike:
    for s in strike['isone_web_services']['day_ahead_strike_prices']['day_ahead_strike_price']:
        h = int(s['market_hour']['local_hour_end']) - 1
        if 0 <= h < 24:
            data[h]['strike_price'] = float(s['strike_price'])

df = pd.DataFrame([
    {
        'hour': h + 1,
        'da_lmp': data[h].get('da_lmp'),
        'rt_lmp': data[h].get('rt_lmp'),
        'tmnsr_price': data[h].get('tmnsr_price'),
        'strike_price': data[h].get('strike_price')
    }
    for h in range(24)
])

# Validate
required_cols = ['da_lmp', 'rt_lmp', 'tmnsr_price', 'strike_price']
if df[required_cols].isna().any().any():
    print("\n⚠ Missing pricing data:")
    print(df[df[required_cols].isna().any(axis=1)])
    raise ValueError("Missing pricing data. Check API parsing.")

df.to_csv('pricing_data.csv', index=False)
print("\n✓ pricing_data.csv saved\n")