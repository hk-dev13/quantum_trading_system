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

# Add project root directory to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# --- Imports ---
from configs import config
from src.ingestion.data_fetcher import build_price_df
from src.models.predictor import predict_momentum
from src.optimizer.classical_optimizer import choose_assets_classical
from src.optimizer.quantum_optimizer import optimize_portfolio_qaoa
from src.backtest.backtester import run_simple_backtest, calculate_metrics, plot_equity_curve
from src.monitoring.logger import log_event

def create_run_artifact_dir(strategy_name, seed):
    """Create unique directory to save artifacts from a run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{timestamp}_{strategy_name}_seed{seed}"
    path = os.path.join('data', 'artifacts', dir_name)
    os.makedirs(path, exist_ok=True)
    print(f"Artifact directory created: {path}")
    return path

def run_momentum_strategy(price_df, config_module):
    """Run complete workflow for momentum strategy."""
    print("\nStep 2: Running momentum prediction...")
    momentum_df = predict_momentum(price_df, config_module.MA_WINDOW)
    
    print("\nStep 3: Selecting assets based on momentum signal...")
    daily_choices = choose_assets_classical(momentum_df)
    
    print("\nStep 4: Running backtest (with costs & slippage)...")
    equity_curve, trade_stats = run_simple_backtest(price_df, daily_choices, config_module.INITIAL_CAPITAL, config_module)
    return equity_curve, trade_stats

def run_qaoa_strategy(price_df, config_module):
    """Run complete workflow for AI-QAOA hybrid strategy."""
    print("\nStep 2: Running prediction (using momentum model)...")
    momentum_df = predict_momentum(price_df, config_module.MA_WINDOW)

    print("\nStep 3: Selecting assets with QAOA for each day...")
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

    print("\nStep 4: Running backtest (with costs & slippage)...")
    equity_curve, trade_stats = run_simple_backtest(price_df, daily_choices, config_module.INITIAL_CAPITAL, config_module)
    return equity_curve, trade_stats

def main():
    parser = argparse.ArgumentParser(description="Run backtest for trading strategy.")
    parser.add_argument('--strategy', type=str, required=True, choices=['momentum', 'qaoa'], help="Select strategy.")
    parser.add_argument('--seed', type=int, default=None, help="Seed for reproducibility.")
    args = parser.parse_args()
    
    STRATEGY = args.strategy
    SEED = args.seed if args.seed is not None else random.randint(0, 10000)
    
    if SEED is not None:
        print(f"*** Running with deterministic seed: {SEED} ***")
        random.seed(SEED)
        np.random.seed(SEED)

    print(f"\n--- Starting Backtest Workflow for Strategy: {STRATEGY.upper()} ---")
    
    # Create artifact directory
    artifact_path = create_run_artifact_dir(STRATEGY, SEED)
    
    log_event("start_run", {"strategy": STRATEGY, "seed": SEED, "artifact_path": artifact_path})

    print("\nStep 1: Loading historical data...")
    price_df = build_price_df(config.ASSETS, config.DAYS_HISTORY)
    
    if STRATEGY == 'momentum':
        equity_curve, trade_stats = run_momentum_strategy(price_df, config)
    elif STRATEGY == 'qaoa':
        equity_curve, trade_stats = run_qaoa_strategy(price_df, config)

    print("\nStep 5: Analyzing and saving results...")
    if equity_curve.empty:
        print("Empty equity curve, nothing to analyze or plot.")
        log_event("end_run", {"status": "failed", "reason": "empty_equity_curve"})
        return

    metrics = calculate_metrics(equity_curve)
    
    # Combine performance metrics with trading statistics
    final_results = {**metrics, **trade_stats}
    
    # Log more detailed final results
    log_event("end_run", {"status": "success", "results": final_results})

    print("\n--- Final Backtest Results (Net after Costs & Slippage) ---")
    print(f"Strategy: {STRATEGY.upper()}")
    for key, value in final_results.items():
        print(f"{key}: {value}")
    
    # Save JSON results
    results_json_path = os.path.join(artifact_path, 'results.json')
    with open(results_json_path, 'w') as f:
        json.dump(final_results, f, indent=4)
    print(f"Metrics results saved at: {results_json_path}")

    # Save plot
    plot_title = f"{STRATEGY.title()} Strategy Performance (Net of Costs)"
    plot_path = os.path.join(artifact_path, 'equity_curve.png')
    plot_equity_curve(equity_curve, plot_title, plot_path)

    print("\n--- Workflow Complete ---")

if __name__ == "__main__":
    main()
