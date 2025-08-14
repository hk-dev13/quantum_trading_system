#!/usr/bin/env python
# filepath: tools/run_backtest.py

import sys
import os
import pandas as pd
import argparse
import random
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime

# Tambahkan direktori root proyek ke dalam PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# --- Impor ---
from configs import config
from src.ingestion.data_fetcher import build_price_df
from src.models.predictor import predict_momentum
from src.optimizer.classical_optimizer import choose_assets_classical
from src.optimizer.quantum_optimizer import optimize_portfolio_qaoa
from src.backtest.backtester import run_simple_backtest, calculate_metrics, plot_equity_curve
from src.monitoring.logger import log_event

def create_run_artifact_dir(strategy_name, seed):
    """Membuat direktori unik untuk menyimpan artefak dari sebuah run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{timestamp}_{strategy_name}_seed{seed}"
    path = os.path.join('data', 'artifacts', dir_name)
    os.makedirs(path, exist_ok=True)
    print(f"Direktori artefak dibuat: {path}")
    return path

def run_momentum_strategy(price_df, config_module):
    """Menjalankan alur kerja lengkap untuk strategi momentum."""
    print("\nLangkah 2: Menjalankan prediksi momentum...")
    momentum_df = predict_momentum(price_df, config_module.MA_WINDOW)
    
    print("\nLangkah 3: Memilih aset berdasarkan sinyal momentum...")
    daily_choices = choose_assets_classical(momentum_df)
    
    print("\nLangkah 4: Menjalankan backtest (dengan biaya & selip)...")
    equity_curve, trade_stats = run_simple_backtest(price_df, daily_choices, config_module.INITIAL_CAPITAL, config_module)
    return equity_curve, trade_stats

def run_qaoa_strategy(price_df, config_module):
    """Menjalankan alur kerja lengkap untuk strategi hibrid AI-QAOA."""
    print("\nLangkah 2: Menjalankan prediksi (menggunakan model momentum)...")
    momentum_df = predict_momentum(price_df, config_module.MA_WINDOW)

    print("\nLangkah 3: Memilih aset dengan QAOA untuk setiap hari...")
    daily_choices = {}
    start_day = config_module.MA_WINDOW
    for i in range(start_day, len(price_df)):
        current_date = price_df.index[i]
        todays_predictions = momentum_df.loc[current_date]
        if todays_predictions.isna().all():
            daily_choices[current_date] = []
            continue
        top_n_preds = todays_predictions.nlargest(config_module.QAOA_TOP_N_ASSETS)
        historical_slice = price_df.loc[:current_date]
        relevant_prices = historical_slice[top_n_preds.index]
        chosen_assets = optimize_portfolio_qaoa(top_n_preds, relevant_prices, config_module.OBJECTIVE_Q_FACTOR)
        daily_choices[current_date] = chosen_assets

    print("\nLangkah 4: Menjalankan backtest (dengan biaya & selip)...")
    equity_curve, trade_stats = run_simple_backtest(price_df, daily_choices, config_module.INITIAL_CAPITAL, config_module)
    return equity_curve, trade_stats

def main():
    parser = argparse.ArgumentParser(description="Menjalankan backtest untuk strategi trading.")
    parser.add_argument('--strategy', type=str, required=True, choices=['momentum', 'qaoa'], help="Pilih strategi.")
    parser.add_argument('--seed', type=int, default=None, help="Seed untuk reproduktibilitas.")
    args = parser.parse_args()
    
    STRATEGY = args.strategy
    SEED = args.seed if args.seed is not None else random.randint(0, 10000)
    
    if SEED is not None:
        print(f"*** Menjalankan dengan seed deterministik: {SEED} ***")
        random.seed(SEED)
        np.random.seed(SEED)

    print(f"\n--- Memulai Alur Kerja Backtest untuk Strategi: {STRATEGY.upper()} ---")
    
    # Buat direktori artefak
    artifact_path = create_run_artifact_dir(STRATEGY, SEED)
    
    log_event("start_run", {"strategy": STRATEGY, "seed": SEED, "artifact_path": artifact_path})

    print("\nLangkah 1: Mengambil data historis...")
    price_df = build_price_df(config.ASSETS, config.DAYS_HISTORY)
    
    if STRATEGY == 'momentum':
        equity_curve, trade_stats = run_momentum_strategy(price_df, config)
    elif STRATEGY == 'qaoa':
        equity_curve, trade_stats = run_qaoa_strategy(price_df, config)

    print("\nLangkah 5: Menganalisis dan menyimpan hasil...")
    if equity_curve.empty:
        print("Equity curve kosong, tidak ada yang bisa dianalisis atau di-plot.")
        log_event("end_run", {"status": "failed", "reason": "empty_equity_curve"})
        return

    metrics = calculate_metrics(equity_curve)
    
    # Gabungkan metrik kinerja dengan statistik trading
    final_results = {**metrics, **trade_stats}
    
    # Log hasil akhir yang lebih detail
    log_event("end_run", {"status": "success", "results": final_results})

    print("\n--- Hasil Akhir Backtest (Net setelah Biaya & Selip) ---")
    print(f"Strategi: {STRATEGY.upper()}")
    for key, value in final_results.items():
        print(f"{key}: {value}")
    
    # Simpan hasil JSON
    results_json_path = os.path.join(artifact_path, 'results.json')
    with open(results_json_path, 'w') as f:
        json.dump(final_results, f, indent=4)
    print(f"Hasil metrik disimpan di: {results_json_path}")

    # Simpan grafik
    plot_title = f"Kinerja Strategi {STRATEGY.title()} (Net of Costs)"
    plot_path = os.path.join(artifact_path, 'equity_curve.png')
    plot_equity_curve(equity_curve, plot_title, plot_path)

    print("\n--- Alur Kerja Selesai ---")

if __name__ == "__main__":
    main()
