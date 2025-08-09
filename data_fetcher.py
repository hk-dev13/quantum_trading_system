# filepath: data_fetcher.py
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
        response.raise_for_status()  # Akan error jika status code bukan 2xx
        data = response.json()
        
        # Ubah data menjadi pandas Series dengan timestamp yang benar
        prices = data['prices']
        timestamps = [datetime.datetime.fromtimestamp(p[0] / 1000).date() for p in prices]
        values = [p[1] for p in prices]
        
        # Buat Series dengan nama aset
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

    # Gabungkan semua series menjadi satu DataFrame dan isi nilai yang hilang
    price_df = pd.concat(all_prices, axis=1)
    
    # --- TAMBAHKAN BARIS INI UNTUK MEMBERSIHKAN DATA ---
    # Hapus baris dengan tanggal (indeks) yang duplikat, simpan yang pertama
    price_df = price_df[~price_df.index.duplicated(keep='first')]
    
    price_df.ffill(inplace=True) # Forward-fill untuk mengisi hari libur/data hilang
    return price_df