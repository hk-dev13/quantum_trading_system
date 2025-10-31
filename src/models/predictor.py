import pandas as pd

def predict_momentum(price_df, window):
    """Calculate simple momentum signal based on Moving Average (MA)."""
    # Calculate daily returns
    returns = price_df.pct_change()
    # Calculate MA of returns
    momentum = returns.rolling(window=window).mean()
    return momentum
