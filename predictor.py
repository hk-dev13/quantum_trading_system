# filepath: predictor.py
import pandas as pd

def predict_returns_ma(price_df, window):
    """
    Memprediksi return berdasarkan sinyal moving average sederhana.
    Return positif jika harga saat ini di atas MA, dan sebaliknya.
    """
    # Hitung moving average untuk setiap aset
    ma = price_df.rolling(window=window, min_periods=1).mean()
    
    # Buat sinyal: 1 jika harga > MA, -1 jika harga < MA
    signal = (price_df > ma).astype(int) - (price_df < ma).astype(int)
    
    # Ambil sinyal terakhir sebagai prediksi
    # Kita tidak melakukan clip(lower=0) lagi, sesuai rencana kita
    preds = signal.iloc[-1]
    
    return preds