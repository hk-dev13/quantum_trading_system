import pandas as pd

def predict_momentum(price_df, window):
    """Menghitung sinyal momentum sederhana berdasarkan Moving Average (MA)."""
    # Hitung return harian
    returns = price_df.pct_change()
    # Hitung MA dari return
    momentum = returns.rolling(window=window).mean()
    return momentum
