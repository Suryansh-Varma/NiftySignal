"""
Sector-Specialized Model Retraining Script
==========================================
Trains one ensemble ML model per market sector (Banking, Tech, Pharma, etc.)
using Nifty 50 index-relative features for each stock grouping.

Each sector model learns the unique patterns of its industry segment,
significantly boosting prediction accuracy compared to a single global model.

Usage:
    python scripts/retrain_sector_models.py
"""

import sys
import pickle
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

from app.config import MODELS_DIR, RESULTS_DIR, DATA_PROCESSED_DIR, TradingConfig
from app.features.technical import prepare_features
from app.signals.ml_signals import MLSignalGenerator
from app.signals.sector_models import SectorModelManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SECTOR_MODELS_DIR = MODELS_DIR / "sector_models"
SECTOR_MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "=" * 70)
print("SECTOR-SPECIALIZED MODEL TRAINING")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ============================================================================
# STEP 1: LOAD RECENT DATA
# ============================================================================
print("\n[1] Loading data...")

data_path = DATA_PROCESSED_DIR / "universe_data.csv"
if not data_path.exists():
    print(f"ERROR: Data file not found at {data_path}")
    sys.exit(1)

df = pd.read_csv(data_path)
df["date"] = pd.to_datetime(df["date"])

cutoff_date = datetime.now() - timedelta(days=365)  # 1 year for full market cycles
df_recent = df[df["date"] >= cutoff_date].copy()

print(f"Total rows:  {len(df_recent)}")
print(
    f"Date range:  {df_recent['date'].min().date()} to {df_recent['date'].max().date()}"
)
print(f"Symbols:     {df_recent['symbol'].nunique()}")

# ============================================================================
# STEP 2: PREPARE FEATURES (includes Nifty 50 context)
# ============================================================================
print("\n[2] Preparing features (with Nifty 50 market context)...")


def _label_to_int(value: object) -> int:
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(float(value))
    return 0


try:
    X, y, df_ml = prepare_features(
        df_recent,
        forward_days=TradingConfig.FORWARD_DAYS,
        return_threshold=0.02,
    )
    print(f"Features:    {len(X.columns)}")
    print(f"Samples:     {len(X)}")
    print(f"Feature list: {list(X.columns)}")
    print(f"\nLabel distribution:")
    for label, count in y.value_counts().sort_index().items():
        label_int = _label_to_int(label)
        name = {-1: "SELL", 0: "HOLD", 1: "BUY"}.get(label_int, "?")
        print(f"  {name}: {count} ({count / len(y) * 100:.1f}%)")

except Exception as e:
    print(f"ERROR during feature preparation: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 3: TRAIN GLOBAL MODEL (baseline)
# ============================================================================
print("\n[3] Training global ensemble model (baseline)...")

global_model = MLSignalGenerator(
    model_type="ensemble",
    use_risk_adjustment=False,
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=0.02,
    test_size=0.2,
    random_state=42,
)

try:
    train_m, test_m = global_model.fit(X, y)
    print(f"  Train Accuracy: {train_m['accuracy']:.2%}")
    print(f"  Test  Accuracy: {test_m['accuracy']:.2%}")
    print(f"  Test  F1:       {test_m['f1']:.2%}")

    # Save global model
    global_model_path = MODELS_DIR / "trading_model.pkl"
    global_model.save(str(global_model_path))
    print(f"  Global model saved: {global_model_path}")

except Exception as e:
    print(f"ERROR during global training: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 4: TRAIN SECTOR MODELS
# ============================================================================
print("\n[4] Training per-sector models...")

manager = SectorModelManager(
    global_model=global_model,
    model_type="ensemble",
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=0.02,
)

sector_results = manager.fit_all_sectors(X, y, df_ml)

# Print sector summary
print("\n--- Sector Model Results ---")
for sector, stats in sorted(sector_results.items()):
    if stats.get("skipped"):
        print(f"  {sector:25s}: Skipped ({stats['n_samples']} samples < min)")
    elif "error" in stats:
        print(f"  {sector:25s}: ERROR — {stats['error']}")
    else:
        print(
            f"  {sector:25s}: "
            f"Train {stats['train_accuracy']:.2%}  "
            f"Test {stats['test_accuracy']:.2%}  "
            f"F1 {stats['test_f1']:.2%}  "
            f"({stats['n_samples']} samples)"
        )

# Save summary to JSON
summary_path = RESULTS_DIR / "sector_model_stats.json"
with open(summary_path, "w") as f:
    json.dump(sector_results, f, indent=4)
print(f"\nSector stats saved to: {summary_path}")

# ============================================================================
# STEP 5: GENERATE RECOMMENDATIONS (using sector models with fallback)
# ============================================================================
print("\n[5] Generating recommendations via sector models...")

training_features = list(X.columns)
X_latest = pd.DataFrame()
latest_symbols = []
latest_prices = []
latest_dates = []

for symbol in sorted(df["symbol"].unique()):
    symbol_data = df[df["symbol"] == symbol].copy()
    if len(symbol_data) < 50:
        continue
    symbol_data = symbol_data.sort_values("date")

    try:
        X_temp, _, _ = prepare_features(
            symbol_data,
            forward_days=TradingConfig.FORWARD_DAYS,
            return_threshold=0.02,
        )
    except Exception:
        continue

    if not X_temp.empty:
        # Only use training features, skip if any are missing
        available = [c for c in training_features if c in X_temp.columns]
        if len(available) < len(training_features) * 0.8:
            continue

        # Pad any missing columns with 0
        for col in training_features:
            if col not in X_temp.columns:
                X_temp[col] = 0.0

        latest_row = X_temp[training_features].iloc[-1:]
        X_latest = pd.concat([X_latest, latest_row])
        latest_symbols.append(symbol)
        latest_prices.append(symbol_data.iloc[-1]["close"])
        latest_dates.append(symbol_data.iloc[-1]["date"])

if not X_latest.empty:
    try:
        signals, confidences = manager.predict_batch(latest_symbols, X_latest)

        recommendations = pd.DataFrame(
            {
                "symbol": latest_symbols,
                "last_price": latest_prices,
                "last_date": latest_dates,
                "signal": signals,
                "confidence": np.round(confidences, 3),
            }
        )
        signal_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
        recommendations["recommendation"] = recommendations["signal"].map(signal_map)
        recommendations = recommendations.sort_values("confidence", ascending=False)

        # Save
        rec_path = RESULTS_DIR / "latest_recommendations.csv"
        recommendations.to_csv(rec_path, index=False)

        print(f"  Generated recommendations for {len(recommendations)} symbols")
        print(f"  BUY:  {(recommendations['signal'] == 1).sum()}")
        print(f"  HOLD: {(recommendations['signal'] == 0).sum()}")
        print(f"  SELL: {(recommendations['signal'] == -1).sum()}")
        print(f"  Saved to: {rec_path}")

        # Print top 10
        print("\n  Top picks:")
        buys = recommendations[recommendations["signal"] == 1].head(5)
        for _, row in buys.iterrows():
            print(f"    BUY  {row['symbol']:20s} conf={row['confidence']:.2%}")

    except Exception as e:
        print(f"ERROR generating recommendations: {e}")
        import traceback

        traceback.print_exc()

# ============================================================================
# STEP 6: FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("TRAINING COMPLETE")
print(f"  Global Model Test Accuracy: {test_m['accuracy']:.2%}")

# Find best sector
best_sector = max(
    {k: v for k, v in sector_results.items() if "test_accuracy" in v}.items(),
    key=lambda x: x[1]["test_accuracy"],
    default=("N/A", {"test_accuracy": 0}),
)
print(
    f"  Best Sector Model: {best_sector[0]} ({best_sector[1]['test_accuracy']:.2%} acc)"
)

if test_m["accuracy"] > 0.50:
    print("\n  [SUCCESS] Model crossed the 50% accuracy threshold!")
elif test_m["accuracy"] > 0.40:
    print("\n  [GOOD] Model exceeds baseline. Sector models provide specialization.")
else:
    print("\n  [CAUTION] Consider fetching more data and retraining.")

print("=" * 70 + "\n")
