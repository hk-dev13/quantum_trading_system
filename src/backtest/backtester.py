# Deskripsi: Berisi fungsi untuk menjalankan backtest dan memplot hasilnya.
#
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_simple_backtest(price_df, daily_choices, initial_capital, config_module):
    """
    Menjalankan simulasi backtest sederhana dengan memperhitungkan biaya dan selip.
    """
    cash = initial_capital
    positions = {asset: 0.0 for asset in price_df.columns}
    portfolio_history = []
    
    # Variabel untuk melacak biaya
    total_fees = 0.0
    total_slippage_cost = 0.0
    trade_count = 0

    for date, target_assets in daily_choices.items():
        # Hitung nilai portofolio saat ini sebelum ada aksi
        current_portfolio_value = cash
        for asset, quantity in positions.items():
            current_portfolio_value += quantity * price_df.loc[date, asset]
        portfolio_history.append({'date': date, 'value': current_portfolio_value})

        # --- Logika Rebalancing ---
        current_assets = {asset for asset, qty in positions.items() if qty > 0}
        
        # Jual aset yang tidak lagi ada di target
        for asset in current_assets - set(target_assets):
            price = price_df.loc[date, asset]
            sell_price = price * (1 - config_module.SLIPPAGE_PCT)
            slippage_cost = positions[asset] * (price - sell_price)
            
            proceeds = positions[asset] * sell_price
            fee = proceeds * config_module.TRANSACTION_FEE_PCT
            
            cash += proceeds - fee
            total_fees += fee
            total_slippage_cost += slippage_cost
            positions[asset] = 0.0
            trade_count += 1

        # Beli aset baru atau sesuaikan posisi
        if target_assets:
            cash_per_asset = cash / len(target_assets)
            for asset in target_assets:
                if asset not in current_assets: # Hanya beli jika ini adalah posisi baru
                    price = price_df.loc[date, asset]
                    buy_price = price * (1 + config_module.SLIPPAGE_PCT)
                    slippage_cost = cash_per_asset / buy_price * (buy_price - price)
                    
                    fee = cash_per_asset * config_module.TRANSACTION_FEE_PCT
                    
                    quantity_to_buy = (cash_per_asset - fee) / buy_price
                    positions[asset] = quantity_to_buy
                    cash -= cash_per_asset # Kurangi cash yang dialokasikan
                    
                    total_fees += fee
                    total_slippage_cost += slippage_cost
                    trade_count += 1

    equity_curve = pd.DataFrame(portfolio_history).set_index('date')
    
    trade_stats = {
        "total_trades": trade_count,
        "total_fees_paid": total_fees,
        "total_slippage_cost": total_slippage_cost
    }
    
    return equity_curve, trade_stats

def calculate_metrics(equity_curve):
    """Menghitung metrik kinerja utama dari equity curve."""
    if equity_curve.empty or len(equity_curve) < 2:
        return {
            "Final Value ($)": 0, "Total Return (%)": 0,
            "Sharpe Ratio": 0, "Max Drawdown (%)": 0
        }
    
    returns = equity_curve['value'].pct_change().dropna()
    
    # Sharpe Ratio
    sharpe_ratio = 0
    if returns.std() > 0:
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()

    # Max Drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    metrics = {
        "Final Value ($)": round(equity_curve['value'].iloc[-1], 2),
        "Total Return (%)": round((equity_curve['value'].iloc[-1] / equity_curve['value'].iloc[0] - 1) * 100, 2),
        "Sharpe Ratio": round(sharpe_ratio, 2),
        "Max Drawdown (%)": round(max_drawdown * 100, 2)
    }
    return metrics

def plot_equity_curve(equity_curve, title, output_path=None):
    """Membuat plot equity curve dan menyimpannya jika path diberikan."""
    plt.figure(figsize=(14, 7))
    plt.plot(equity_curve.index, equity_curve['value'], label=title)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True)
    
    if output_path:
        plt.savefig(output_path)
        print(f"Grafik disimpan di: {output_path}")
    
    plt.show()