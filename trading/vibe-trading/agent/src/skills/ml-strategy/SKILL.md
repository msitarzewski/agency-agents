---
name: ml-strategy
description: Machine-learning predictive strategy based on sklearn walk-forward training, feature engineering, and signal generation. Suitable for any OHLCV data.
category: strategy
---
# Machine-Learning Predictive Strategy

## Purpose

Use sklearn machine-learning models (`RandomForest` / `GradientBoosting` / `Ridge`) to predict the direction of future returns and generate trading signals. Walk-forward training is used to avoid future data leakage, and feature engineering extracts useful factors from OHLCV data.

## Signal Logic

1. **Validate input**: check OHLCV columns, minimum row count, NaN ratio — skip symbols that fail
2. **Feature engineering**: build multi-dimensional factors from raw OHLCV data (momentum, volatility, RSI, moving-average ratios, volume ratio, and more). All features are sanitized (inf removed, division-by-zero guarded)
3. **Label construction**: future N-day return > 0 is the positive class (`1`), < 0 is the negative class (`0`)
4. **Walk-forward training**: use an expanding or sliding window, train on historical data only, and roll forward day by day for prediction
5. **Signal generation**: map `predict_proba[:, 1]` to `[-1.0, 1.0]`, or use discrete signals from `predict` in `{-1, 0, 1}`. Output is guaranteed clean (no NaN, clipped to range)

## Complete SignalEngine Example

This is the recommended full pipeline. Copy and customise — safety is built in.

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def validate_data(df: pd.DataFrame, min_rows: int = 300) -> bool:
    """Check that OHLCV data meets minimum quality for ML training.

    Args:
        df: DataFrame with DatetimeIndex.
        min_rows: Minimum number of rows required.

    Returns:
        True if data is usable.
    """
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        return False
    if len(df) < min_rows:
        return False
    if df["close"].isnull().mean() > 0.2:
        return False
    return True


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build a machine-learning feature matrix from OHLCV data.

    All features are guarded against division-by-zero and sanitized
    (inf replaced with NaN) so downstream code never sees inf values.

    Args:
        df: DataFrame containing open, high, low, close, and volume columns.

    Returns:
        DataFrame with feature columns prefixed by 'f_'.
    """
    c = df["close"]
    v = df["volume"]
    ret = c.pct_change()

    features = pd.DataFrame(index=df.index)
    features["f_ret_5d"] = c.pct_change(5)
    features["f_ret_20d"] = c.pct_change(20)
    features["f_vol_20d"] = ret.rolling(20).std()
    features["f_ma_ratio"] = c / c.rolling(20).mean()
    features["f_volume_ratio"] = v / v.rolling(20).mean()

    # RSI(14) — guard: loss=0 in zero-volatility periods produces inf
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    features["f_rsi_14"] = 100 - (100 / (1 + rs))

    # Bollinger Band position — guard: bb_upper == bb_lower when std=0
    ma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    bb_upper = ma20 + 2 * std20
    bb_lower = ma20 - 2 * std20
    bb_range = (bb_upper - bb_lower).replace(0, np.nan)
    features["f_bb_position"] = (c - bb_lower) / bb_range

    # Intraday features
    features["f_high_low_ratio"] = (df["high"] - df["low"]) / c
    features["f_close_open_ratio"] = (c - df["open"]) / df["open"]
    features["f_skew_20d"] = ret.rolling(20).skew()

    # Sanitize: replace all inf with NaN (NaN handled by walk-forward)
    features = features.replace([np.inf, -np.inf], np.nan)
    return features


def walk_forward_predict(
    features: pd.DataFrame,
    labels: pd.Series,
    min_train_size: int = 252,
    retrain_freq: int = 20,
    model_type: str = "random_forest",
    window_type: str = "expanding",
    sliding_size: int = 504,
) -> pd.Series:
    """Walk-forward training and prediction to avoid future data leakage.

    Args:
        features: Feature matrix aligned with labels by row index.
        labels: Binary labels (0/1), representing the direction of future N-day returns.
        min_train_size: Minimum training-set size in trading days.
        retrain_freq: Retrain the model every N days.
        model_type: One of "random_forest" / "gradient_boosting" / "ridge".
        window_type: "expanding" uses all history; "sliding" uses a fixed lookback.
        sliding_size: Lookback window size when window_type is "sliding".

    Returns:
        Predicted signal series with range [-1.0, 1.0], no NaN values.
    """
    predictions = pd.Series(0.0, index=features.index)
    model = None
    scaler = None

    for i in range(min_train_size, len(features)):
        # Retrain every retrain_freq days
        if model is None or (i - min_train_size) % retrain_freq == 0:
            start = max(0, i - sliding_size) if window_type == "sliding" else 0
            X_train = features.iloc[start:i].values
            y_train = labels.iloc[start:i].values

            # Drop rows with NaN
            valid = ~(np.isnan(X_train).any(axis=1) | np.isnan(y_train))
            X_train = X_train[valid]
            y_train = y_train[valid]

            if len(X_train) < 50:
                continue

            # Standardization: fit only on training set
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)

            # Build the model
            if model_type == "random_forest":
                model = RandomForestClassifier(
                    n_estimators=100, max_depth=5, random_state=42,
                )
            elif model_type == "gradient_boosting":
                model = GradientBoostingClassifier(
                    n_estimators=100, max_depth=3, learning_rate=0.05,
                    random_state=42,
                )
            elif model_type == "ridge":
                model = LogisticRegression(penalty="l2", C=1.0, random_state=42)
            else:
                raise ValueError(f"Unsupported model_type: {model_type}")

            model.fit(X_train, y_train)

        # Predict today
        X_today = features.iloc[i : i + 1].values
        if np.isnan(X_today).any():
            predictions.iloc[i] = 0.0
            continue

        X_today = scaler.transform(X_today)

        if hasattr(model, "predict_proba"):
            prob = model.predict_proba(X_today)[0, 1]
            predictions.iloc[i] = prob * 2 - 1  # [0,1] -> [-1,1]
        else:
            predictions.iloc[i] = float(model.predict(X_today)[0])

    # Output contract: no NaN, clipped to [-1, 1]
    predictions = predictions.fillna(0.0).clip(-1.0, 1.0)
    return predictions


class SignalEngine:
    """Complete ML strategy with built-in data validation and safety."""

    def generate(self, data_map: dict) -> dict:
        """Generate signals for each symbol.

        Args:
            data_map: code -> OHLCV DataFrame.

        Returns:
            code -> signal Series in [-1.0, 1.0].
        """
        signals = {}
        for code, df in data_map.items():
            if not validate_data(df):
                print(f"[WARN] {code}: data quality insufficient, skipping")
                continue

            features = build_features(df)
            labels = (df["close"].pct_change(5).shift(-5) > 0).astype(int)
            signal = walk_forward_predict(features, labels)
            signals[code] = signal

        return signals
```

## Feature Engineering Reference

The table below lists all default features. Add or remove features as needed — `build_features()` is the customisation point.

| Feature Name | Formula | Meaning |
|--------|---------|------|
| ret_5d | `close.pct_change(5)` | Past 5-day return (short-term momentum) |
| ret_20d | `close.pct_change(20)` | Past 20-day return (medium-term momentum) |
| vol_20d | `returns.rolling(20).std()` | 20-day volatility |
| rsi_14 | See RSI formula in code | Relative Strength Index (division-by-zero guarded) |
| ma_ratio | `close / close.rolling(20).mean()` | Degree of deviation from the 20-day moving average |
| volume_ratio | `volume / volume.rolling(20).mean()` | Volume ratio (current volume vs 20-day average) |
| bb_position | `(close - bb_lower) / (bb_upper - bb_lower)` | Bollinger Band position (zero-bandwidth guarded) |
| high_low_ratio | `(high - low) / close` | Intraday range ratio |
| close_open_ratio | `(close - open) / open` | Intraday return |
| skew_20d | `returns.rolling(20).skew()` | Return skewness |

## Model Selection Guide

| Model | Advantages | Disadvantages | Applicable Scenario |
|------|------|------|---------|
| RandomForestClassifier | Hard to overfit, robust to hyperparameters, can output feature importance | Weaker at capturing trend-style features | Default first-choice model, medium data size |
| GradientBoostingClassifier | High accuracy, captures complex nonlinear relationships | Easy to overfit, slow to train, requires careful tuning | Sufficient data and tuning experience |
| Ridge / LogisticRegression | Fast training, interpretable, difficult to overfit | Captures only linear relationships | Fast baseline, few features, small dataset |

## Parameters

| Parameter | Default | Description |
|------|--------|------|
| model_type | `"random_forest"` | Model type: `random_forest` / `gradient_boosting` / `ridge` |
| min_train_size | 252 | Minimum training-set size (starting length of the expanding window) |
| retrain_freq | 20 | Retraining frequency (every N trading days) |
| prediction_horizon | 5 | Prediction horizon (future N-day return) |
| n_estimators | 100 | Number of trees for tree-based models |
| max_depth | 5 | Maximum tree depth (prevents overfitting) |
| threshold | 0.0 | Signal filtering threshold (`abs(signal) < threshold` is set to 0) |
| window_type | `"expanding"` | Training window: `expanding` (all history) or `sliding` (fixed lookback) |
| sliding_size | 504 | Lookback size for sliding window (2 years of trading days) |

## Common Pitfalls

The pipeline code above already handles data leakage, standardization leakage, inf/NaN propagation, and retraining frequency. The following pitfalls still require your judgement:

1. **Overfitting**: trees that are too deep (`max_depth > 10`), too many features, or too small a training set. Keep `max_depth=3~5` and feature count `< 15`
2. **Class imbalance**: in bull markets the up/down ratio may be 7:3, so the model may prefer predicting the majority class. Use `class_weight="balanced"` or SMOTE if needed
3. **Look-ahead bias (non-leakage form)**: computing features from today's close and predicting today's signal. Make sure features use only data from T-1 and earlier

## Dependencies

```bash
pip install scikit-learn pandas numpy
```

## Signal Convention

- `predict_proba[:, 1]` mapped through `prob * 2 - 1` to `[-1.0, 1.0]` (continuous-strength signal)
- Or discrete signals from `predict()` in `{-1, 0, 1}` (short, neutral, long)
- Positive values = bullish direction, negative values = bearish direction, absolute value = confidence strength
- Output is guaranteed: no NaN, no inf, clipped to `[-1.0, 1.0]`
