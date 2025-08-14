# filepath: data_fetcher.py
import requests
import pandas as pd
import datetime
import time
import os

# --- KONFIGURASI CACHE ---
CACHE_DIR = 'data'
CACHE_FILE = os.path.join(CACHE_DIR, 'price_history_cache.csv')
CACHE_AGE_LIMIT_SECONDS = 24 * 60 * 60  # 24 jam

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
    """Membangun DataFrame harga, menggunakan cache jika tersedia dan masih baru."""
    # Buat direktori cache jika belum ada
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    # Cek apakah cache ada dan masih valid
    if os.path.exists(CACHE_FILE):
        file_mod_time = os.path.getmtime(CACHE_FILE)
        if (time.time() - file_mod_time) < CACHE_AGE_LIMIT_SECONDS:
            print(f"Memuat data dari cache yang masih baru: {CACHE_FILE}")
            cached_df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
            # Pastikan semua aset yang diminta ada di cache
            if all(asset in cached_df.columns for asset in assets):
                return cached_df[assets]
            else:
                print("Beberapa aset tidak ditemukan di cache. Mengambil data baru...")

    # Jika cache tidak valid atau tidak ada, ambil dari API
    print("Mengambil data dari API CoinGecko...")
    all_prices = []
    for asset in assets:
        print(f"Fetching {asset}...")
        price_series = fetch_price_history(asset, days)
        if price_series is not None:
            all_prices.append(price_series)
        time.sleep(1.5)  # Tingkatkan jeda sedikit untuk lebih aman

    if not all_prices:
        print("Gagal mengambil data dari API.")
        return pd.DataFrame()

    price_df = pd.concat(all_prices, axis=1)
    price_df = price_df[~price_df.index.duplicated(keep='first')]
    price_df.ffill(inplace=True)

    # Simpan DataFrame baru ke cache
    print(f"Menyimpan data baru ke cache: {CACHE_FILE}")
    price_df.to_csv(CACHE_FILE)
    
    return price_df
