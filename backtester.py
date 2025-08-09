import pandas as pd
import numpy as np

def run_simple_backtest(price_df, daily_choices, initial_capital):
    """
    Menjalankan backtest sederhana.
    
    Args:
        price_df: DataFrame harga historis lengkap.
        daily_choices: Dictionary {tanggal: [aset_terpilih]}.
        initial_capital: Modal awal.
        
    Returns:
        Series pandas yang berisi nilai portofolio dari waktu ke waktu (equity curve).
    """
    capital = initial_capital
    portfolio_value = pd.Series(index=price_df.index, dtype=float)
    portfolio_value.iloc[0] = capital
    
    # Asumsikan kita memegang aset dari hari t ke t+1
    for i in range(1, len(price_df)):
        prev_day = price_df.index[i-1]
        current_day = price_df.index[i]
        
        # Ambil pilihan aset dari hari sebelumnya
        chosen_assets = daily_choices.get(prev_day, [])
        
        if not chosen_assets:
            # Jika tidak ada aset yang dipilih, nilai portofolio tidak berubah
            portfolio_value[current_day] = portfolio_value[prev_day]
            continue
            
        # Hitung return rata-rata dari aset yang dipilih
        prev_prices = price_df.loc[prev_day, chosen_assets]
        current_prices = price_df.loc[current_day, chosen_assets]
        
        # Hindari pembagian dengan nol jika harga sebelumnya adalah nol
        returns = (current_prices - prev_prices) / prev_prices.replace(0, np.nan)
        
        # --- BLOK DEBUGGING BARU ---
        print(f"    - Debug: Returns Series for {current_day.date()}: {returns.to_dict()}")
        
        # Hitung return RATA-RATA dari semua aset yang dipilih hari itu.
        daily_return = returns.mean(skipna=True)
        
        print(f"    - Debug: Calculated Mean Return: {daily_return}") # Ini harus satu angka
        
        if pd.isna(daily_return):
            daily_return = 0
        
        # Perbarui nilai portofolio
        portfolio_value[current_day] = portfolio_value[prev_day] * (1 + daily_return)

    return portfolio_value.dropna()

def plot_equity_curves(equity_curves, title='Strategy Performance Comparison'):
    """Membuat plot beberapa equity curve pada satu grafik."""
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(12, 6))
    for label, curve in equity_curves.items():
        curve.plot(label=label) # Menambahkan label untuk legenda
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.legend() # Menampilkan legenda untuk membedakan garis
    plt.show()