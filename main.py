# filepath: main.py
import config
from data_fetcher import build_price_df
from predictor import predict_returns_ma
from optimizer import optimize_portfolio_classical, optimize_portfolio_qaoa
from backtester import run_simple_backtest, plot_equity_curves

def run_simulation_loop(price_data, optimizer_func):
    """Menjalankan loop simulasi historis untuk satu fungsi optimizer."""
    daily_choices = {}
    # Kita mulai dari hari ke-MA_WINDOW agar punya cukup data untuk prediksi pertama
    for i in range(config.MA_WINDOW, len(price_data)):
        historical_slice = price_data.iloc[:i]
        predictions = predict_returns_ma(historical_slice, config.MA_WINDOW)
        chosen_assets, _ = optimizer_func(predictions)
        current_date = price_data.index[i]
        daily_choices[current_date] = chosen_assets
        # Kita bisa nonaktifkan print harian agar output lebih bersih
        # print(f"Decision for {current_date.date()}: Choose {chosen_assets}")
    return daily_choices

def run_comparison_backtest():
    """Menjalankan backtest untuk membandingkan strategi klasik dan kuantum."""
    print("1. Fetching full historical data for backtest...")
    price_data = build_price_df(config.ASSETS, config.DAYS_HISTORY)
    
    if price_data.empty:
        print("Exiting due to data fetching failure.")
        return

    print("\n2. Running Classical Strategy Simulation...")
    classical_choices = run_simulation_loop(price_data, optimize_portfolio_classical)
    classical_equity = run_simple_backtest(price_data, classical_choices, config.INITIAL_CAPITAL)

    print("\n3. Running Quantum Strategy (QAOA) Simulation... (This will be slow)")
    qaoa_choices = run_simulation_loop(price_data, optimize_portfolio_qaoa)
    qaoa_equity = run_simple_backtest(price_data, qaoa_choices, config.INITIAL_CAPITAL)

    print("\n--- Backtest Comparison Result ---")
    print(f"Initial Capital: ${config.INITIAL_CAPITAL:,.2f}")
    print(f"Final Value (Classical): ${classical_equity.iloc[-1]:,.2f}")
    print(f"Final Value (QAOA):      ${qaoa_equity.iloc[-1]:,.2f}")
    
    # Tampilkan kedua grafik pertumbuhan modal
    plot_equity_curves({
        "Classical Optimizer": classical_equity,
        "QAOA Optimizer": qaoa_equity
    })

if __name__ == "__main__":
    run_comparison_backtest()