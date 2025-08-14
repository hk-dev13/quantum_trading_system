#!/usr/bin/env python
# filepath: tools/run_backtest.py

import sys
import os
import pandas as pd

# Tambahkan direktori root proyek ke dalam PYTHONPATH
# Ini memungkinkan kita untuk mengimpor modul dari src dan configs
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Impor dari modul-modul yang sudah kita refaktor
from src.ingestion.data_fetcher import build_price_df
from src.models.predictor import predict_momentum
from src.optimizer.optimizer import choose_assets
from src.backtest.backtester import (
    run_simple_backtest,
    plot_equity_curves,
    calculate_sharpe_ratio,
    calculate_max_drawdown
)
import configs.config as config

def main():
    """
    Fungsi utama untuk menjalankan alur kerja backtest secara lengkap.
    """
    print("--- Memulai Alur Kerja Backtest ---")

    # 1. PENGAMBILAN DATA
    print(f"\nLangkah 1: Mengambil data historis untuk {len(config.ASSETS)} aset selama {config.DAYS_HISTORY} hari...")
    price_df = build_price_df(config.ASSETS, config.DAYS_HISTORY)
    if price_df.empty or price_df.shape[1] != len(config.ASSETS):
        print("Gagal mengambil data yang cukup. Proses dihentikan.")
        return
    print("Pengambilan data berhasil.")

    # 2. PREDIKSI
    print(f"\nLangkah 2: Menjalankan prediksi momentum dengan window {config.MA_WINDOW} hari...")
    momentum_df = predict_momentum(price_df, config.MA_WINDOW)
    print("Prediksi momentum selesai.")
    
    # 3. OPTIMISASI (Pemilihan Aset)
    print("\nLangkah 3: Memilih aset berdasarkan sinyal momentum...")
    daily_choices = choose_assets(momentum_df)
    # Hapus hari-hari di mana tidak ada aset yang dipilih untuk menyederhanakan logging
    num_decision_days = len([d for d in daily_choices.values() if d])
    print(f"Pemilihan aset selesai. Keputusan dibuat untuk {num_decision_days} hari.")

    # 4. BACKTEST
    print(f"\nLangkah 4: Menjalankan backtest dengan modal awal ${config.INITIAL_CAPITAL:,.2f}...")
    equity_curve = run_simple_backtest(price_df, daily_choices, config.INITIAL_CAPITAL)
    print("Backtest selesai.")

    # 5. ANALISIS & PLOTTING
    print("\nLangkah 5: Menganalisis dan memvisualisasikan hasil...")
    if not equity_curve.empty:
        sharpe = calculate_sharpe_ratio(equity_curve)
        max_dd = calculate_max_drawdown(equity_curve)
        
        print("\n--- Hasil Akhir Backtest ---")
        print(f"Nilai Akhir Portofolio: ${equity_curve.iloc[-1]:,.2f}")
        print(f"Sharpe Ratio Tahunan: {sharpe:.2f}")
        print(f"Maximum Drawdown: {max_dd:.2%}")
        
        # Plotting
        plot_equity_curves(
            {'Momentum Strategy': equity_curve},
            title="Kinerja Strategi Momentum Sederhana"
        )
    else:
        print("Equity curve kosong, tidak ada yang bisa dianalisis atau di-plot.")
        
    print("\n--- Alur Kerja Selesai ---")


if __name__ == "__main__":
    main()
