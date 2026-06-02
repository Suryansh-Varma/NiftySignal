import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(".").absolute()))
from app.features.technical import prepare_features
from app.config import TradingConfig, DATA_PROCESSED_DIR
from app.signals.ml_signals import MLSignalGenerator

model_path = Path("models/trading_model.pkl")
model = MLSignalGenerator.load(str(model_path))

scaler = model.scaler
features = model.feature_columns

print(f"Scaler expects {scaler.n_features_in_} features")
print(f"Model dictionary says features are: {features}")
if features:
    print(f"Feature count in list: {len(features)}")

# Test on one symbol
data_path = DATA_PROCESSED_DIR / "universe_data.csv"
df = pd.read_csv(data_path)
symbol = df["symbol"].unique()[0]
symbol_data = df[df["symbol"] == symbol].copy()

X_all, _, _ = prepare_features(
    symbol_data,
    feature_columns=features,
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=TradingConfig.RETURN_THRESHOLD,
)

print(f"Prepared X for {symbol} has shape {X_all.shape}")
print(f"Columns in prepared X: {list(X_all.columns)}")
