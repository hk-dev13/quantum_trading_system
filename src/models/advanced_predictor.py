# filepath: src/models/advanced_predictor.py
import pandas as pd
from sklearn.linear_model import LogisticRegression

def predict_returns_ml(price_df):
    """
    Memprediksi return menggunakan model Logistic Regression sederhana.
    """
    predictions = {}
    
    for asset in price_df.columns:
        returns = price_df[asset].pct_change().dropna()
        
        if len(returns) < 10:
            predictions[asset] = 0
            continue

        features = pd.DataFrame({
            'lag_1': returns.shift(1),
            'lag_3': returns.shift(3),
            'lag_5': returns.shift(5)
        })
        
        target = (returns > 0).astype(int).shift(-1)
        
        full_data = pd.concat([features, target], axis=1).dropna()
        
        if len(full_data) < 2:
            predictions[asset] = 0
            continue
            
        X = full_data[['lag_1', 'lag_3', 'lag_5']]
        y = full_data.iloc[:, -1]

        model = LogisticRegression(solver='liblinear', random_state=42)
        model.fit(X, y)
        
        last_features = features.iloc[[-1]].fillna(0)
        pred_proba = model.predict_proba(last_features)[0][1]
        
        predictions[asset] = 2 * (pred_proba - 0.5)

    return pd.Series(predictions)

