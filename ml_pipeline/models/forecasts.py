from ml_pipeline.features.lag_features import build_regression_features
import pandas as pd
import numpy as np

FEATURE_COLS = [
    'lag_1','lag_2','lag_3','lag_5','lag_7','lag_14',
    'roll_mean_7','roll_mean_14','roll_mean_21',
    'roll_std_7','roll_std_14','roll_std_21',
    'ret_1d','ret_3d','ret_7d','vol_ratio','rsi'
]

def recursive_forecast(df, model, forecast_days=30, price_col='price'):
    """
    Predict iteratively — each prediction feeds back as input.
    """
    temp_df = df.copy()
    preds = []

    for _ in range(forecast_days):
        X, _, feat_df = build_regression_features(temp_df, price_col)
        if len(feat_df) == 0:
            break

        latest_features = X.iloc[[-1]]
        next_price = model.predict(latest_features)[0]
        preds.append(next_price)

        # Append predicted row back to history
        next_date = temp_df['date'].iloc[-1] + pd.Timedelta(days=1)
        new_row = pd.DataFrame({'date': [next_date], price_col: [next_price]})
        temp_df = pd.concat([temp_df, new_row], ignore_index=True)

    return np.array(preds)

def direct_forecast(df, direct_models, forecast_days=30, price_col='price'):
    """
    Each horizon uses its own dedicated model — no error accumulation.
    """
    X, _, df_feat = build_regression_features(df, price_col)
    latest_features = X.iloc[[-1]]

    preds = []
    for h in range(1, forecast_days + 1):
        if h in direct_models:
            pred = direct_models[h].predict(latest_features)[0]
        else:
            pred = preds[-1]  # fallback: carry forward
        preds.append(pred)

    return np.array(preds)


def combined_forecast(recursive_preds, direct_preds, forecast_days=30):
    """
    Blend recursive + direct with horizon-aware weights.

    Logic:
    - Short term (days 1-7):   trust recursive more (less accumulated error yet)
    - Medium term (days 8-20): equal blend
    - Long term (days 21+):    trust direct more (recursive error too high)
    """
    combined = []
    for i in range(forecast_days):
        h = i + 1  # horizon (1-indexed)

        if h <= 7:
            w_recursive = 0.70
            w_direct    = 0.30
        elif h <= 20:
            # Linear interpolation from 70/30 → 30/70
            t = (h - 7) / (20 - 7)
            w_recursive = 0.70 - t * 0.40
            w_direct    = 1 - w_recursive
        else:
            w_recursive = 0.25
            w_direct    = 0.75

        blended = w_recursive * recursive_preds[i] + w_direct * direct_preds[i]
        combined.append(blended)

    return np.array(combined)