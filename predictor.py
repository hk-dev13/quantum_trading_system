# Deskripsi: Fungsi untuk memprediksi return berdasarkan Moving Average.
#
import pandas as pd

def predict_returns_ma(price_df, window):
    """
    Memprediksi return berdasarkan sinyal moving average sederhana.
    Return positif jika harga saat ini di atas MA, dan sebaliknya.
    """
    ma = price_df.rolling(window=window, min_periods=1).mean()
    signal = (price_df > ma).astype(int) - (price_df < ma).astype(int)
    preds = signal.iloc[-1]
    return preds