FEATURE_COLS = [
    'lag_1','lag_2','lag_3','lag_5','lag_7','lag_14',
    'roll_mean_7','roll_mean_14','roll_mean_21',
    'roll_std_7','roll_std_14','roll_std_21',
    'ret_1d','ret_3d','ret_7d','vol_ratio','rsi'
]

def build_regression_features(df, price_col='price'):
    df = df.copy().sort_values('date').reset_index(drop=True)
    p = df[price_col]

    # Lag features
    for i in [1, 2, 3, 5, 7, 14]:
        df[f'lag_{i}'] = p.shift(i)

    # Rolling stats
    for w in [7, 14, 21]:
        df[f'roll_mean_{w}'] = p.shift(1).rolling(w).mean()
        df[f'roll_std_{w}']  = p.shift(1).rolling(w).std()

    # Momentum (FIXED)
    df['ret_1d'] = p.pct_change(1).shift(1)
    df['ret_3d'] = p.pct_change(3).shift(1)
    df['ret_7d'] = p.pct_change(7).shift(1)

    # Volatility ratio (FIXED)
    vol7  = df['ret_1d'].rolling(7).std()
    vol21 = df['ret_1d'].rolling(21).std()
    df['vol_ratio'] = vol7 / (vol21 + 1e-9)

    # RSI (FIXED)
    delta = p.diff().shift(1)
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-9)))

    # Target
    df['target'] = p  # or p.shift(-1) depending on setup

    df = df.dropna().reset_index(drop=True)

    X = df[FEATURE_COLS]
    y = df['target']

    return X, y, df