"""
Generate recommendations for ALL NSE stocks using existing trained model.
Much faster - just needs feature engineering for available data.

Run with: python generate_recommendations_fast.py
Expected time: 2-5 minutes
Output: latest_recommendations.csv with ALL available stocks
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from app.config import MODELS_DIR, RESULTS_DIR, DataValidationConfig
from app.data.loaders import fetch_history_nselib, get_all_nse_equities
from app.signals.ml_signals import MLSignalGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("FAST: Generate recommendations for ALL available NSE stocks")
    logger.info("=" * 70)

    # Step 1: Get all NSE stocks
    logger.info("\n[STEP 1] Loading all NSE stocks...")
    all_symbols = get_all_nse_equities()
    logger.info(f"[SUCCESS] Loaded {len(all_symbols)} NSE stocks")

    # Step 2: Fetch data
    logger.info(f"\n[STEP 2] Fetching data for {len(all_symbols)} stocks...")
    start_date = (datetime.now() - timedelta(days=730)).strftime("%d-%m-%Y")
    end_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")

    try:
        df = fetch_history_nselib(
            all_symbols, start=start_date, end=end_date, include_delivery=False
        )
        logger.info(
            f"[SUCCESS] Fetched {len(df)} rows for {df['symbol'].nunique()} symbols"
        )
    except Exception as e:
        logger.error(f"[ERROR] Fetch failed: {e}")
        return

    # Step 3: Filter stocks with sufficient data
    logger.info(f"\n[STEP 3] Filtering stocks...")
    symbol_counts = df.groupby("symbol").size()
    valid = symbol_counts[symbol_counts >= 60].index.tolist()
    df = df[df["symbol"].isin(valid)]
    logger.info(f"[SUCCESS] {len(valid)} stocks have 60+ days of data")

    # Step 4: Engineer features
    logger.info(f"\n[STEP 4] Loading model and engineering features...")
    model_path = MODELS_DIR / "trading_model.pkl"

    try:
        model = MLSignalGenerator.load(str(model_path))
        feature_columns = model.feature_columns
        logger.info(
            f"[SUCCESS] Model loaded, using {len(feature_columns) if feature_columns else 'default'} features"
        )
    except Exception as e:
        logger.error(f"[ERROR] Model load failed: {e}")
        return

    from app.features.technical import prepare_features

    try:
        # Prepare features for all symbols using the model's exact feature set
        X_all, _, df_feat = prepare_features(
            df,
            feature_columns=feature_columns,
            forward_days=model.forward_days,
            return_threshold=model.return_threshold,
        )
        # Use labelled frame for metadata columns (symbol/close) and align with X rows
        df_feat = df_feat.loc[X_all.index]
        logger.info(f"[SUCCESS] Engineered features for {len(df_feat)} samples")
    except Exception as e:
        logger.error(f"[ERROR] Feature engineering failed: {e}")
        return

    # Step 5: (Skipped, already loaded in Step 4)
    # Step 6: Predict
    logger.info(f"\n[STEP 6] Generating predictions...")
    X = X_all.fillna(0)

    try:
        preds = model.predict(X)
        probs = model.predict_proba(X)
        logger.info(f"[SUCCESS] {len(preds)} predictions")
    except Exception as e:
        logger.error(f"[ERROR] Prediction failed: {e}")
        return

    # Step 7: Build results
    logger.info(f"\n[STEP 7] Building results...")
    # The model returns labels [-1, 0, 1] for [SELL, HOLD, BUY]
    signal_map = {-1: "SELL", 0: "HOLD", 1: "BUY"}

    results = []
    for i, row in df_feat.iterrows():
        pred_idx = i - df_feat.index[0]
        if pred_idx >= len(preds):
            continue

        signal = signal_map.get(preds[pred_idx], "HOLD")
        conf = float(np.max(probs[pred_idx]))
        risk = 1.0 - conf

        results.append(
            {
                "symbol": row["symbol"],
                "recommendation": signal,
                "confidence": conf,
                "risk_score": risk,
                "last_price": row["close"],
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    df_res = pd.DataFrame(results)

    # Step 8: Sort and save
    logger.info(f"\n[STEP 8] Sorting and saving...")
    signal_order = {"BUY": 0, "SELL": 1, "HOLD": 2}
    df_res["order"] = df_res["recommendation"].map(signal_order)
    df_res = df_res.sort_values(["order", "confidence"], ascending=[True, False]).drop(
        "order", axis=1
    )

    csv_path = RESULTS_DIR / "latest_recommendations.csv"
    df_res.to_csv(csv_path, index=False)

    # Step 9: Summary
    logger.info(f"\n[STEP 9] SUMMARY")
    logger.info("=" * 70)
    buy = len(df_res[df_res["recommendation"] == "BUY"])
    sell = len(df_res[df_res["recommendation"] == "SELL"])
    hold = len(df_res[df_res["recommendation"] == "HOLD"])

    logger.info(f"Total Recommendations: {len(df_res)}")
    logger.info(f"  • BUY:  {buy} stocks")
    logger.info(f"  • SELL: {sell} stocks")
    logger.info(f"  • HOLD: {hold} stocks")

    if buy > 0:
        logger.info(f"\nTop 5 BUY:")
        for idx, r in df_res[df_res["recommendation"] == "BUY"].head(5).iterrows():
            logger.info(
                f"  {r['symbol']:15} | ₹{r['last_price']:8.2f} | {r['confidence']:.1%} confidence"
            )

    if sell > 0:
        logger.info(f"\nTop 5 SELL:")
        for idx, r in df_res[df_res["recommendation"] == "SELL"].head(5).iterrows():
            logger.info(
                f"  {r['symbol']:15} | ₹{r['last_price']:8.2f} | {r['confidence']:.1%} confidence"
            )

    logger.info("=" * 70)
    logger.info(f"\n[COMPLETE] Saved to: {csv_path}")
    logger.info("Restart backend to see updates")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"[FATAL] {e}", exc_info=True)
        sys.exit(1)
