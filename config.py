# Deskripsi: Konfigurasi utama untuk proyek.
#
ASSETS = ["bitcoin", "ethereum", "solana"]
DAYS_HISTORY = 90
MA_WINDOW = 7
INITIAL_CAPITAL = 10000


#
# File: data_fetcher.py
# Deskripsi: Fungsi untuk mengambil data harga dari CoinGecko API.
#
import requests
import pandas as pd
import datetime

def fetch_price_history(asset_id, days):
    """Mengambil data harga historis untuk satu aset dari CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        prices = data['prices']
        timestamps = [datetime.datetime.fromtimestamp(p[0] / 1000).date() for p in prices]
        values = [p[1] for p in prices]
        
        price_series = pd.Series(values, index=pd.to_datetime(timestamps), name=asset_id)
        return price_series
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {asset_id}: {e}")
        return None

def build_price_df(assets, days):
    """Membangun DataFrame harga untuk beberapa aset."""
    all_prices = []
    for asset in assets:
        print(f"Fetching {asset}...")
        price_series = fetch_price_history(asset, days)
        if price_series is not None:
            all_prices.append(price_series)
    
    if not all_prices:
        print("Failed to fetch any data.")
        return pd.DataFrame()

    price_df = pd.concat(all_prices, axis=1)
    price_df = price_df[~price_df.index.duplicated(keep='first')]
    price_df.ffill(inplace=True)
    return price_df