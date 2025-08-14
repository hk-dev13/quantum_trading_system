# filepath: src/models/lstm_predictor.py
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

N_STEPS = 10  # Berapa banyak hari sebelumnya yang digunakan untuk memprediksi hari berikutnya

def create_lstm_model():
    """Membuat dan mengompilasi model LSTM baru. Dipanggil sekali per aset."""
    model = Sequential([
        LSTM(50, activation='relu', input_shape=(N_STEPS, 1)),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def _create_sequences(data, n_steps):
    """Mengubah data time-series menjadi urutan (sequences) untuk LSTM."""
    X, y = [], []
    for i in range(len(data)):
        end_ix = i + n_steps
        if end_ix > len(data) - 1:
            break
        seq_x, seq_y = data[i:end_ix], data[end_ix]
        X.append(seq_x)
        y.append(seq_y)
    return np.array(X), np.array(y)

def train_and_predict(model, price_history):
    """Melatih model LSTM yang ada dan membuat prediksi untuk satu langkah ke depan."""
    # 1. Preprocessing Data
    scaler = MinMaxScaler(feature_range=(0, 1))
    asset_prices = price_history.values.reshape(-1, 1)
    scaled_prices = scaler.fit_transform(asset_prices)
    
    # 2. Buat Urutan Data
    X, y = _create_sequences(scaled_prices, N_STEPS)
    if X.shape[0] < 2:
        return 0  # Tidak cukup data untuk melatih, prediksi netral

    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    # 3. Latih Model
    model.fit(X, y, epochs=20, batch_size=1, verbose=0)
    
    # 4. Buat Prediksi
    last_sequence = scaled_prices[-N_STEPS:].reshape((1, N_STEPS, 1))
    predicted_price_scaled = model.predict(last_sequence, verbose=0)
    
    predicted_price = scaler.inverse_transform(predicted_price_scaled)[0][0]
    current_price = asset_prices[-1][0]
    
    # Prediksi return: positif jika harga diprediksi naik, negatif jika turun
    return (predicted_price - current_price) / current_price

