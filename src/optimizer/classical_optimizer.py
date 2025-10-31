import pandas as pd

def choose_assets_classical(momentum_df):
    """Select best assets for each day based on momentum signal, with handling for NaN values."""
    daily_choices = {}
    for date, daily_momentum in momentum_df.iterrows():
        # Skip row (day) if all momentum values are NaN.
        # This usually happens at the beginning of the period due to windowing.
        if daily_momentum.isna().all():
            daily_choices[date] = []
            continue

        # Select asset with strongest positive momentum
        strongest_asset = daily_momentum.idxmax()

        # Only select if momentum is positive.
        if daily_momentum[strongest_asset] > 0:
            daily_choices[date] = [strongest_asset]
        else:
            daily_choices[date] = []  # No choice if strongest momentum is not positive

    return daily_choices
