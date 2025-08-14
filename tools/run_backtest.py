#!/usr/bin/env python
# filepath: tools/run_backtest.py

import sys
import os
import pandas as pd

# --- PILIH STRATEGI ---
# Ganti nilai ini ke 'qaoa' untuk menjalankan strategi kuantum
STRATEGY = 'qaoa'  # Pilihan: 'momentum' atau 'qaoa'
# ---------------------

# Tambahkan direktori root proyek ke dalam PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Impor modul dasar
from src.ingestion.data_fetcher import build_price_df
from src.backtest.backtester import (
    run_simple_backtest,
    plot_equity_curves,
    calculate_sharpe_ratio,
    calculate_max_drawdown
)
import configs.config as config

# Impor modul spesifik strategi berdasarkan pilihan
if STRATEGY == 'momentum':
    from src.models.predictor import predict_momentum
    from src.optimizer.optimizer import choose_assets
elif STRATEGY == 'qaoa':
    from src.models.lstm_predictor import create_lstm_model, train_and_predict
    from src.optimizer.quantum_optimizer import optimize_portfolio_qaoa

def run_momentum_strategy(price_df):
    """Menjalankan alur kerja lengkap untuk strategi berbasis momentum."""
    print("\nLangkah 2: Menjalankan prediksi momentum...")
    momentum_df = predict_momentum(price_df, config.MA_WINDOW)
    
    print("\nLangkah 3: Memilih aset berdasarkan sinyal momentum...")
    daily_choices = choose_assets(momentum_df)
    
    print("\nLangkah 4: Menjalankan backtest...")
    equity_curve = run_simple_backtest(price_df, daily_choices, config.INITIAL_CAPITAL)
    return equity_curve

def run_qaoa_strategy(price_df):
    """Menjalankan alur kerja lengkap untuk strategi berbasis QAOA."""
    # Buat satu model LSTM untuk setiap aset SEBELUM loop
    print("\nLangkah 2: Membuat model LSTM untuk setiap aset...")
    models = {asset: create_lstm_model() for asset in price_df.columns}
    print("Model berhasil dibuat.")

    daily_choices = {}
    start_day = 15  # Perlu lebih banyak data untuk pemanasan LSTM
    
    print(f"\nLangkah 3: Memulai loop simulasi harian dari hari ke-{start_day}...")
    for i in range(start_day, len(price_df)):
        historical_slice = price_df.iloc[:i]
        current_date = price_df.index[i - 1]
        
        # Latih model dan buat prediksi untuk setiap aset
        predictions = {}
        for asset in price_df.columns:
            model = models[asset]
            asset_history = historical_slice[asset]
            # Hanya latih dan prediksi jika ada cukup data unik
            if asset_history.nunique() > 1:
                predictions[asset] = train_and_predict(model, asset_history)
            else:
                predictions[asset] = 0 # Prediksi netral jika data tidak beragam
        
        predictions = pd.Series(predictions)
        
        # Optimalkan portofolio menggunakan QAOA
        chosen_assets, _ = optimize_portfolio_qaoa(predictions, historical_slice)
        
        daily_choices[current_date] = chosen_assets
        print(f"  - {current_date.date()}: Memilih {len(chosen_assets)} aset -> {chosen_assets}")

    print("\nLangkah 4: Menjalankan backtest...")
    equity_curve = run_simple_backtest(price_df, daily_choices, config.INITIAL_CAPITAL)
    return equity_curve

def main():
    """Fungsi utama untuk menjalankan alur kerja backtest secara lengkap."""
    print(f"--- Memulai Alur Kerja Backtest untuk Strategi: {STRATEGY.upper()} ---")

    # 1. PENGAMBILAN DATA
    print(f"\nLangkah 1: Mengambil data historis...")
    # Tambahkan 20 hari ekstra untuk pemanasan model ML jika menggunakan QAOA
    days_to_fetch = config.DAYS_HISTORY + 20 if STRATEGY == 'qaoa' else config.DAYS_HISTORY
    price_df = build_price_df(config.ASSETS, days_to_fetch)
    if price_df.empty:
        print("Gagal mengambil data. Proses dihentikan.")
        return
    print("Pengambilan data berhasil.")

    # Pilih dan jalankan strategi
    if STRATEGY == 'momentum':
        equity_curve = run_momentum_strategy(price_df)
        title = "Kinerja Strategi Momentum Sederhana"
    elif STRATEGY == 'qaoa':
        equity_curve = run_qaoa_strategy(price_df)
        title = "Kinerja Strategi Hibrid AI-QAOA"
    else:
        print(f"Strategi '{STRATEGY}' tidak dikenali. Proses dihentikan.")
        return

    # 5. ANALISIS & PLOTTING
    print("\nLangkah 5: Menganalisis dan memvisualisasikan hasil...")
    if not equity_curve.empty:
        sharpe = calculate_sharpe_ratio(equity_curve)
        max_dd = calculate_max_drawdown(equity_curve)
        
        print("\n--- Hasil Akhir Backtest ---")
        print(f"Strategi: {STRATEGY.upper()}")
        print(f"Nilai Akhir Portofolio: ${equity_curve.iloc[-1]:,.2f}")
        print(f"Sharpe Ratio Tahunan: {sharpe:.2f}")
        print(f"Maximum Drawdown: {max_dd:.2%}")
        
        plot_equity_curves({title: equity_curve}, title=title)
    else:
        print("Equity curve kosong, tidak ada yang bisa dianalisis atau di-plot.")
        
    print("\n--- Alur Kerja Selesai ---")

if __name__ == "__main__":
    main()
