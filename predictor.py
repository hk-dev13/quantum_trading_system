# Deskripsi: Fungsi untuk memprediksi return berdasarkan Moving Average.
#
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import NotFittedError

def predict_returns_ma(price_df, window):
    """
    Memprediksi return berdasarkan sinyal moving average sederhana.
    (Fungsi ini kita simpan untuk perbandingan jika diperlukan)
    """
    ma = price_df.rolling(window=window, min_periods=1).mean()
    signal = (price_df > ma).astype(int) - (price_df < ma).astype(int)
    preds = signal.iloc[-1]
    return preds

def predict_returns_ml(price_df):
    """
    Memprediksi return menggunakan model Logistic Regression sederhana.
    Model ini memprediksi apakah harga besok akan naik (1) atau tidak (-1).
    """
    predictions = {}
    
    for asset in price_df.columns:
        # 1. Feature Engineering: Gunakan return 1, 3, dan 5 hari sebelumnya
        returns = price_df[asset].pct_change().dropna()
        
        if len(returns) < 10: # Butuh data minimal untuk membuat fitur & melatih
            predictions[asset] = 0 # Tidak ada sinyal jika data kurang
            continue

        features = pd.DataFrame({
            'lag_1': returns.shift(1),
            'lag_3': returns.shift(3),
            'lag_5': returns.shift(5)
        })
        
        # 2. Target: Apakah return besok positif?
        target = (returns > 0).astype(int).shift(-1)
        
        # 3. Gabungkan dan bersihkan data
        full_data = pd.concat([features, target], axis=1).dropna()
        
        if len(full_data) < 2:
            predictions[asset] = 0
            continue
            
        X = full_data[['lag_1', 'lag_3', 'lag_5']]
        y = full_data.iloc[:, -1]

        # 4. Latih model dan prediksi
        model = LogisticRegression(solver='liblinear', random_state=42)
        model.fit(X, y)
        
        # Prediksi untuk hari berikutnya menggunakan data terakhir yang tersedia
        last_features = features.iloc[[-1]].fillna(0) # Isi NaN jika ada
        pred_proba = model.predict_proba(last_features)[0][1] # Probabilitas kelas '1' (naik)
        
        # Beri skor berdasarkan probabilitas, bukan hanya 0 atau 1
        # Skor antara -1 dan 1
        predictions[asset] = 2 * (pred_proba - 0.5)

    return pd.Series(predictions)