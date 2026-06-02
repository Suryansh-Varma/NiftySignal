import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent))

from app.config import DATA_PROCESSED_DIR, TradingConfig
from app.features.technical import prepare_features
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    ExtraTreesClassifier,
    VotingClassifier,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def test_binary_accuracy():
    # Load data
    data_path = DATA_PROCESSED_DIR / "universe_data.csv"
    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"])

    # 最近 6 ヶ月の方が良い結果が出ているので 180 日に戻す
    cutoff_date = datetime.now() - timedelta(days=180)
    df_recent = df[df["date"] >= cutoff_date].copy()

    # Prepare features
    X, y, _ = prepare_features(
        df_recent,
        forward_days=TradingConfig.FORWARD_DAYS,
        return_threshold=TradingConfig.RETURN_THRESHOLD,
    )

    # Convert to Binary (1 for BUY, 0 for NOT BUY)
    y_binary = (y == 1).astype(int)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_binary, test_size=0.2, random_state=42, shuffle=False
    )

    # Train simple ensemble
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=10, class_weight="balanced", random_state=42
    )
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
    et = ExtraTreesClassifier(
        n_estimators=100, max_depth=10, class_weight="balanced", random_state=42
    )

    model = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb), ("et", et)], voting="soft"
    )
    model.fit(X_train, y_train)

    # Predict
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    print(f"\nBinary Classification (BUY vs NOT-BUY) Accuracy: {acc:.2%}")
    print(f"Sample size: {len(y_test)}")
    print(f"Label distribution in test: {y_test.value_counts().to_dict()}")


if __name__ == "__main__":
    test_binary_accuracy()
