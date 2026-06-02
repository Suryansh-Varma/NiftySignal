"""
Daily Recommendation Generator
================================
Loads the trained model and generates fresh BUY/HOLD/SELL recommendations
for all NIFTY-50 symbols using the latest available price data.

Designed to be:
  - Called by the scheduler every day at 6:45 PM IST (after data fetch + macro risk update)
  - Called on-demand via the API endpoint POST /api/refresh_recommendations
  - Safe to import without triggering side effects

Usage:
    python -m app.scripts.generate_recommendations
    python -m app.scripts.generate_recommendations --dry-run
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "trading_model.pkl"
DATA_PATH = BASE_DIR / "data" / "processed" / "universe_data.csv"
RESULTS_DIR = BASE_DIR / "results"
MACRO_RISK_FILE = BASE_DIR / "data" / "macro_risk_factor.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _load_macro_risk() -> Dict[str, Any]:
    """Read the latest macro risk JSON; return safe defaults on failure."""
    try:
        if MACRO_RISK_FILE.exists():
            with open(MACRO_RISK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read macro risk file: {e}")
    return {
        "adjusted_risk_factor": 0.5,
        "macro_risk_factor": 0.5,
        "risk_level": "MODERATE",
    }


def _adjust_signal_for_risk(signal: int, confidence: float, risk: float):
    """
    Attenuate BUY signals when macro risk is elevated.
    Mirror of app.features.risk_factors.adjust_signal_by_risk but self-contained
    so this script has no heavy imports.
    """
    adj_confidence = confidence * (1 - 0.5 * risk)
    if signal == 1 and risk > 0.85:
        adj_signal = 0 if risk < 0.95 else -1
    elif signal == -1 and risk > 0.75:
        adj_confidence = min(1.0, confidence + 0.15 * risk)
        adj_signal = signal
    else:
        adj_signal = signal
    return adj_signal, round(adj_confidence, 4)


def generate(dry_run: bool = False) -> Dict[str, Any]:
    """
    Core generation function.

    Returns a summary dict:
        {
            "generated_at": "...",
            "total": 50,
            "BUY": 5, "HOLD": 40, "SELL": 5,
            "model_accuracy": 0.62,
            "macro_risk": 0.63,
            "risk_level": "HIGH",
        }
    """
    # ---- Load model -------------------------------------------------------- #
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. "
            "Run scripts/retrain_model_recent.py first."
        )

    from app.signals.ml_signals import MLSignalGenerator

    logger.info(f"Loading model from {MODEL_PATH}...")
    model = MLSignalGenerator.load(str(MODEL_PATH))
    test_accuracy = (model.test_metrics or {}).get("accuracy", None)
    training_features = model.feature_columns

    # ---- Load price data --------------------------------------------------- #
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Universe data not found at {DATA_PATH}. Run the data fetch script first."
        )

    logger.info(f"Loading price data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    logger.info(
        f"Loaded {len(df)} rows, {df['symbol'].nunique()} symbols, "
        f"date range {df['date'].min().date()} → {df['date'].max().date()}"
    )

    # ---- Load macro risk ---------------------------------------------------- #
    macro_data = _load_macro_risk()
    macro_risk = float(
        macro_data.get("adjusted_risk_factor")
        or macro_data.get("macro_risk_factor")
        or 0.5
    )
    risk_level = macro_data.get("risk_level", "MODERATE")
    logger.info(f"Macro risk: {macro_risk:.4f} ({risk_level})")

    # ---- Prepare features -------------------------------------------------- #
    from app.features.technical import prepare_features

    X_rows = []
    meta_rows = []

    for symbol in sorted(df["symbol"].unique()):
        sym_df = df[df["symbol"] == symbol].copy().sort_values("date")
        if len(sym_df) < 60:
            continue
        try:
            X_temp, _, _ = prepare_features(
                sym_df,
                forward_days=5,
                return_threshold=0.015,
            )
        except Exception as e:
            logger.debug(f"Feature prep failed for {symbol}: {e}")
            continue

        if X_temp.empty:
            continue

        # Align to training feature set
        missing = set(training_features) - set(X_temp.columns)
        if missing:
            for col in missing:
                X_temp[col] = 0.0
        X_latest = X_temp[training_features].iloc[-1:]

        X_rows.append(X_latest)
        meta_rows.append(
            {
                "symbol": symbol,
                "last_price": round(float(sym_df.iloc[-1]["close"]), 2),
                "last_date": str(sym_df.iloc[-1]["date"].date()),
            }
        )

    if not X_rows:
        raise RuntimeError("No feature rows could be prepared — check price data.")

    X_all = pd.concat(X_rows, ignore_index=True)
    logger.info(f"Prepared features for {len(X_all)} symbols")

    # ---- Predict ----------------------------------------------------------- #
    raw_signals = model.predict(X_all)
    raw_proba = model.predict_proba(X_all)  # shape: (n, 3)

    signal_map = {1: "BUY", -1: "SELL", 0: "HOLD"}

    records = []
    for i, meta in enumerate(meta_rows):
        raw_sig = int(raw_signals[i])
        raw_conf = float(np.max(raw_proba[i]))
        buy_prob = (
            float(raw_proba[i][list(model.model.classes_).index(1)])
            if 1 in model.model.classes_
            else 0.0
        )
        sell_prob = (
            float(raw_proba[i][list(model.model.classes_).index(-1)])
            if -1 in model.model.classes_
            else 0.0
        )

        # Apply live macro risk adjustment
        adj_sig, adj_conf = _adjust_signal_for_risk(raw_sig, raw_conf, macro_risk)

        records.append(
            {
                "symbol": meta["symbol"],
                "last_price": meta["last_price"],
                "last_date": meta["last_date"],
                "signal": adj_sig,
                "recommendation": signal_map.get(adj_sig, "HOLD"),
                "confidence": adj_conf,
                "buy_prob": round(buy_prob, 4),
                "sell_prob": round(sell_prob, 4),
                "macro_risk": macro_risk,
                "risk_level": risk_level,
                "close": meta["last_price"],  # alias — API reads 'close'
                "date": meta["last_date"],  # alias
            }
        )

    recs_df = pd.DataFrame(records).sort_values("confidence", ascending=False)

    # ---- Save -------------------------------------------------------------- #
    if not dry_run:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = RESULTS_DIR / "latest_recommendations.csv"
        recs_df.to_csv(out_path, index=False, float_format="%.4f")
        logger.info(f"Saved {len(recs_df)} recommendations → {out_path}")
    else:
        logger.info(f"[DRY RUN] Would save {len(recs_df)} recommendations")

    # ---- Summary ----------------------------------------------------------- #
    counts = recs_df["recommendation"].value_counts().to_dict()
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total": len(recs_df),
        "BUY": counts.get("BUY", 0),
        "HOLD": counts.get("HOLD", 0),
        "SELL": counts.get("SELL", 0),
        "model_accuracy": test_accuracy,
        "macro_risk": macro_risk,
        "risk_level": risk_level,
    }
    logger.info(
        f"Done — BUY:{summary['BUY']} HOLD:{summary['HOLD']} "
        f"SELL:{summary['SELL']}  model_accuracy={test_accuracy}"
    )
    return summary


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Generate fresh daily recommendations")
    parser.add_argument(
        "--dry-run", action="store_true", help="Predict but do not write CSV"
    )
    args = parser.parse_args()

    summary = generate(dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS GENERATED")
    print("=" * 60)
    print(f"  Generated at    : {summary['generated_at']}")
    print(f"  Total symbols   : {summary['total']}")
    print(f"  BUY             : {summary['BUY']}")
    print(f"  HOLD            : {summary['HOLD']}")
    print(f"  SELL            : {summary['SELL']}")
    print(
        f"  Model Accuracy  : {summary['model_accuracy']:.2%}"
        if summary["model_accuracy"]
        else "  Model Accuracy  : unknown"
    )
    print(f"  Macro Risk      : {summary['macro_risk']:.4f} ({summary['risk_level']})")
    print("=" * 60)
