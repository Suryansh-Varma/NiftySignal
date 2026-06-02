import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent))

from app.config import DATA_PROCESSED_DIR, TradingConfig
from app.features.technical import prepare_features
from app.signals.ml_signals import MLSignalGenerator
from sklearn.model_selection import train_test_split


def evaluate_confidence():
    # Load data
    data_path = DATA_PROCESSED_DIR / "universe_data.csv"
    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"])

    # 1-year window
    cutoff_date = datetime.now() - timedelta(days=365)
    df_recent = df[df["date"] >= cutoff_date].copy()

    # Prepare features
    X, y, _ = prepare_features(
        df_recent,
        forward_days=TradingConfig.FORWARD_DAYS,
        return_threshold=TradingConfig.RETURN_THRESHOLD,
    )

    # Load model
    model = MLSignalGenerator.load("models/trading_model.pkl")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )

    # Get predictions & probabilities
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)
    confs = np.max(probs, axis=1)

    print("\nAccuracy @ Confidence Level:")
    print("-" * 30)
    for threshold in [0.4, 0.5, 0.6, 0.7, 0.8]:
        mask = confs >= threshold
        if np.sum(mask) == 0:
            print(f"Conf >= {threshold:.2f}: No samples")
            continue

        acc = np.mean(preds[mask] == y_test[mask])
        count = np.sum(mask)
        pct = count / len(y_test) * 100
        print(f"Conf >= {threshold:.2f}: Acc {acc:.2%}, Count {count} ({pct:.1f}%)")


if __name__ == "__main__":
    evaluate_confidence()
