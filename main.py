# Deskripsi: Titik masuk utama untuk menjalankan sistem backtest.
#
import config
from data_fetcher import build_price_df
from predictor import predict_returns_ml
from optimizer import optimize_portfolio_classical, optimize_portfolio_qaoa
# Tambahkan plot_drawdown_curves ke impor
from backtester import run_simple_backtest, plot_equity_curves, calculate_sharpe_ratio, calculate_max_drawdown, plot_drawdown_curves

def run_simulation_loop(price_data, optimizer_func, is_qaoa=False):
    """
    Menjalankan loop simulasi historis.
    Jika is_qaoa=True, terapkan filter Top-N sebelum optimasi.
    """
    daily_choices = {}
    start_day = 10 
    for i in range(start_day, len(price_data)):
        historical_slice = price_data.iloc[:i]
        predictions = predict_returns_ml(historical_slice) 
        
        # --- LOGIKA BARU UNTUK STRATEGI HIBRID ---
        if is_qaoa:
            # Pilih 3 aset teratas berdasarkan skor prediksi AI
            top_n_preds = predictions.nlargest(3)
            
            # Hanya optimalkan jika ada sinyal positif di antara top 3
            if (top_n_preds > 0).any():
                chosen_assets, _ = optimizer_func(top_n_preds)
            else:
                chosen_assets = []
        else: # Logika untuk strategi klasik (tetap menggunakan semua aset)
            if (predictions > 0).any():
                chosen_assets, _ = optimizer_func(predictions)
            else:
                chosen_assets = []

        current_date = price_data.index[i-1]
        daily_choices[current_date] = chosen_assets
    return daily_choices

def run_comparison_backtest():
    """Menjalankan backtest untuk membandingkan strategi klasik dan kuantum."""
    print("1. Fetching full historical data for backtest...")
    price_data = build_price_df(config.ASSETS, config.DAYS_HISTORY + 20) # Ambil data lebih untuk pemanasan model
    
    if price_data.empty:
        print("Exiting due to data fetching failure.")
        return

    print("\n2. Running Classical Strategy Simulation (on all assets)...")
    # Jalankan strategi klasik pada semua aset
    classical_choices = run_simulation_loop(price_data, optimize_portfolio_classical, is_qaoa=False)
    classical_equity = run_simple_backtest(price_data, classical_choices, config.INITIAL_CAPITAL)

    print("\n3. Running Hybrid AI-Quantum Strategy (Top-3 assets)...")
    # Jalankan strategi kuantum hanya pada 3 aset terbaik pilihan AI
    qaoa_choices = run_simulation_loop(price_data, optimize_portfolio_qaoa, is_qaoa=True)
    qaoa_equity = run_simple_backtest(price_data, qaoa_choices, config.INITIAL_CAPITAL)

    # --- HASIL LAMA ---
    print("\n--- Backtest Comparison Result ---")
    print(f"Initial Capital: ${config.INITIAL_CAPITAL:,.2f}")
    print(f"Final Value (Classical): ${classical_equity.iloc[-1]:,.2f}")
    print(f"Final Value (QAOA):      ${qaoa_equity.iloc[-1]:,.2f}")

    # --- METRIK BARU ---
    print("\n--- Performance Metrics ---")
    print(f"{'Metric':<20} | {'Classical':>15} | {'QAOA':>15}")
    print("-" * 55)
    
    sharpe_c = calculate_sharpe_ratio(classical_equity)
    sharpe_q = calculate_sharpe_ratio(qaoa_equity)
    print(f"{'Sharpe Ratio':<20} | {sharpe_c:15.2f} | {sharpe_q:15.2f}")

    drawdown_c = calculate_max_drawdown(classical_equity)
    drawdown_q = calculate_max_drawdown(qaoa_equity)
    print(f"{'Max Drawdown (%)':<20} | {drawdown_c*100:14.2f}% | {drawdown_q*100:14.2f}%")
    
    # Gabungkan hasil untuk plotting
    all_curves = {
        "Classical Optimizer": classical_equity,
        "QAOA Optimizer": qaoa_equity
    }

    # Tampilkan kedua grafik pertumbuhan modal
    plot_equity_curves(all_curves, title="Strategy Performance Comparison (ML Predictor)")

    # Tampilkan grafik drawdown
    plot_drawdown_curves(all_curves, title="Strategy Drawdown Comparison (ML Predictor)")

if __name__ == "__main__":
    run_comparison_backtest()