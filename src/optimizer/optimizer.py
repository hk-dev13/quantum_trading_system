import pandas as pd

def choose_assets(momentum_df):
    """Memilih aset terbaik untuk setiap hari berdasarkan sinyal momentum, dengan penanganan untuk nilai NaN."""
    daily_choices = {}
    for date, daily_momentum in momentum_df.iterrows():
        # Lompati baris (hari) jika semua nilai momentum adalah NaN.
        # Ini biasanya terjadi di awal periode karena windowing.
        if daily_momentum.isna().all():
            daily_choices[date] = []
            continue

        # Pilih aset dengan momentum positif terkuat
        strongest_asset = daily_momentum.idxmax()

        # Hanya pilih jika momentumnya positif.
        if daily_momentum[strongest_asset] > 0:
            daily_choices[date] = [strongest_asset]
        else:
            daily_choices[date] = []  # Tidak ada pilihan jika momentum terkuat tidak positif

    return daily_choices
