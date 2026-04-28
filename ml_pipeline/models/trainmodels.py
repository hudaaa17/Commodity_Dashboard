from xgboost import XGBRegressor


def train_recursive_model(X, y):
    """Train 1-step ahead model"""

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.7,
        random_state=42
    )

    model.fit(X, y)

    return model

def train_direct_models(X, y, df_feat, horizons):
    """
    Train one model per horizon h — predicts price h days ahead directly.
    horizons: list of ints e.g. [1,2,3,...,30]
    """
    models = {}
    for h in horizons:
        df_h = df_feat.copy()
        df_h['target'] = df_h['price'].shift(-h)  # future price at horizon h
        df_h = df_h.dropna()

        model = XGBRegressor(
            n_estimators=300, learning_rate=0.03,
            max_depth=4, subsample=0.8,
            colsample_bytree=0.7, random_state=42
        )
        model.fit(X, y)
        models[h] = model

    return models
