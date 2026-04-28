import numpy as np

from ml_pipeline.data_loader.load_data import load_commodity_data
from ml_pipeline.features.lag_features import build_regression_features

from ml_pipeline.models.trainmodels import (
    train_recursive_model,
    train_direct_models
)

from ml_pipeline.models.forecasts import (
    recursive_forecast,
    direct_forecast,
    combined_forecast
)


# ----------------------------
# MAIN ML PIPELINE
# ----------------------------
def run_ml_pipeline(
    commodity,
    spreadsheet_id,
    forecast_days=30,
    horizons=[1, 3, 7, 14, 30]
):
    """
    Full ML pipeline for one commodity
    """

    # ----------------------------
    # 1. Load Data
    # ----------------------------
    df = load_commodity_data(commodity, spreadsheet_id)

    if df.empty or len(df) < 50:
        raise ValueError(f"Not enough data for {commodity}")

    # ----------------------------
    # 2. Feature Engineering
    # ----------------------------
    X, y, df_feat = build_regression_features(df)

    if len(X) < 30:
        raise ValueError("Insufficient feature rows after engineering")

    # ----------------------------
    # 3. Train Models
    # ----------------------------
    rec_model = train_recursive_model(X, y)

    direct_models = train_direct_models(
        X, y, df_feat, horizons=horizons
    )

    # ----------------------------
    # 4. Forecasts
    # ----------------------------
    rec_preds = recursive_forecast(
        df_feat, rec_model,
        forecast_days=forecast_days
    )

    dir_preds = direct_forecast(
        df_feat, direct_models,
        forecast_days=forecast_days
    )

    comb_preds = combined_forecast(
        rec_preds, dir_preds,
        forecast_days=forecast_days
    )

    # ----------------------------
    # 5. Build Output
    # ----------------------------
    last_price = df["price"].iloc[-1]

    result = {
        "commodity": commodity,
        "last_price": float(last_price),
        "next_day_prediction": float(comb_preds[0]),
        "recursive_forecast": rec_preds.tolist(),
        "direct_forecast": dir_preds.tolist(),
        "combined_forecast": comb_preds.tolist(),
        "forecast_days": list(range(1, forecast_days + 1))
    }

    return result