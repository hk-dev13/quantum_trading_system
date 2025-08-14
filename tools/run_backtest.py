#!/usr/bin/env python
# filepath: tools/run_backtest.py

import sys
import os
import pandas as pd
import argparse
import random
import numpy as np
import matplotlib.pyplot as plt

# Tambahkan direktori root proyek ke dalam PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# --- Impor Konfigurasi ---
from configs import config 

# --- Impor Modul dari 'src' ---
from src.ingestion.data_fetcher import build_price_df
from src.models.predictor import predict_momentum
from src.optimizer.classical_optimizer import choose_assets_classical
from src.optimizer.quantum_optimizer import optimize_portfolio_qaoa
from src.backtest.backtester import (
    run_simple_backtest,
    plot_equity_curves,
    calculate_sharpe_ratio,
    calculate_max_drawdown
)
from src.monitoring.logger import log_event

# Impor modul spesifik strategi berdasarkan pilihan
def run_momentum_strategy(price_df, config_module):
    """Menjalankan alur kerja lengkap untuk strategi momentum."""
    print("\nLangkah 2: Menjalankan prediksi momentum...")
    momentum_df = predict_momentum(price_df, config_module.MA_WINDOW)
    log_event("prediction_ready", {
        "model": "momentum",
        "last_index": str(momentum_df.index[-1]) if not momentum_df.empty else None
    })
    
    print("\nLangkah 3: Memilih aset berdasarkan sinyal momentum...")
    # PERBAIKAN: Gunakan nama fungsi yang benar yang diimpor
    daily_choices = choose_assets_classical(momentum_df) 
    
    print("\nLangkah 4: Menjalankan backtest...")
    equity_curve = run_simple_backtest(price_df, daily_choices, config_module.INITIAL_CAPITAL)
    return equity_curve

# --- GANTI FUNGSI PLACEHOLDER INI ---
def run_qaoa_strategy(price_df, config_module):
    """Menjalankan alur kerja lengkap untuk strategi hibrid AI-QAOA."""
    print("\nLangkah 2: Menjalankan prediksi (menggunakan model momentum)...")
    momentum_df = predict_momentum(price_df, config_module.MA_WINDOW)
    log_event("prediction_ready", {"model": "momentum_for_qaoa"})

    print("\nLangkah 3: Memilih aset dengan QAOA untuk setiap hari...")
    daily_choices = {}
    # Mulai dari hari di mana kita punya cukup data momentum
    start_day = config_module.MA_WINDOW 
    for i in range(start_day, len(price_df)):
        current_date = price_df.index[i]
        
        # Ambil prediksi untuk hari ini
        todays_predictions = momentum_df.loc[current_date]
        
        if todays_predictions.isna().all():
            daily_choices[current_date] = []
            continue

        # --- Logika Hibrid AI-Kuantum ---
        # 1. Filter N kandidat teratas berdasarkan prediksi
        top_n_preds = todays_predictions.nlargest(config_module.QAOA_TOP_N_ASSETS)
        
        # 2. Siapkan data harga historis hanya untuk kandidat tersebut
        historical_slice = price_df.loc[:current_date]
        relevant_prices = historical_slice[top_n_preds.index]
        
        # 3. Jalankan optimizer QAOA pada masalah yang lebih kecil
        chosen_assets = optimize_portfolio_qaoa(
            top_n_preds, 
            relevant_prices, 
            config_module.OBJECTIVE_Q_FACTOR
        )
        daily_choices[current_date] = chosen_assets

    print("\nLangkah 4: Menjalankan backtest...")
    equity_curve = run_simple_backtest(price_df, daily_choices, config_module.INITIAL_CAPITAL)
    return equity_curve
# ------------------------------------

def main():
    """Fungsi utama untuk menjalankan alur kerja backtest secara lengkap."""
    
    # --- SETUP PARSER ARGUMEN ---
    parser = argparse.ArgumentParser(description="Menjalankan backtest untuk strategi trading.")
    parser.add_argument(
        '--strategy', 
        type=str, 
        required=True, 
        choices=['momentum', 'qaoa'],
        help="Pilih strategi yang akan dijalankan: 'momentum' atau 'qaoa'."
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=None,
        help="Seed untuk random number generator agar hasil bisa direproduksi."
    )
    args = parser.parse_args()
    
    STRATEGY = args.strategy
    SEED = args.seed

    # --- SET SEED UNTUK REPRODUCIBILITY ---
    if SEED is not None:
        print(f"*** Menjalankan dengan seed deterministik: {SEED} ***")
        random.seed(SEED)
        np.random.seed(SEED)
        # Jika menggunakan TensorFlow/PyTorch, seed juga harus di-set di sini
        # import tensorflow as tf
        # tf.random.set_seed(SEED)
    
    print(f"--- Memulai Alur Kerja Backtest untuk Strategi: {STRATEGY.upper()} ---")

    # 1. PENGAMBILAN DATA
    print(f"\nLangkah 1: Mengambil data historis...")
    # Tambahkan 20 hari ekstra untuk pemanasan model ML jika menggunakan QAOA
    days_to_fetch = config.DAYS_HISTORY + 20 if STRATEGY == 'qaoa' else config.DAYS_HISTORY
    # Log awal run
    log_event("start_run", {
        "strategy": STRATEGY,
        "seed": SEED, # <-- Tambahkan seed ke log
        "assets": config.ASSETS,
        "days_to_fetch": days_to_fetch
    })

    price_df = build_price_df(config.ASSETS, days_to_fetch)
    if price_df.empty:
        print("Gagal mengambil data. Proses dihentikan.")
        log_event("error", {"reason": "data_fetch_failed"})
        return
    print("Pengambilan data berhasil.")
    log_event("data_fetched", {"rows": int(price_df.shape[0]), "cols": list(price_df.columns)})

    # Pilih dan jalankan strategi
    if STRATEGY == 'momentum':
        equity_curve = run_momentum_strategy(price_df, config)
        title = "Kinerja Strategi Momentum Sederhana"
    elif STRATEGY == 'qaoa':
        equity_curve = run_qaoa_strategy(price_df, config)
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
        
        # Log hasil backtest
        log_event("backtest_result", {
            "strategy": STRATEGY,
            "final_value": float(equity_curve.iloc[-1]),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_dd)
        })
        
        plot_equity_curves({title: equity_curve}, title=title)
    else:
        print("Equity curve kosong, tidak ada yang bisa dianalisis atau di-plot.")
        log_event("warning", {"reason": "empty_equity_curve", "strategy": STRATEGY})
        
    log_event("end_run", {"strategy": STRATEGY})
    print("\n--- Alur Kerja Selesai ---")

if __name__ == "__main__":
    main()
