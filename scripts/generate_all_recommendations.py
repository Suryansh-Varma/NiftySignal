"""
Generate ML-based trading recommendations for ALL NSE-listed stocks (~2,671 companies).
This script:
1. Fetches all NSE stock symbols
2. Downloads historical data (2 years)
3. Computes technical indicators for all stocks
4. Trains a model on liquid stocks
5. Generates buy/sell/hold recommendations for ALL stocks
6. Outputs: latest_recommendations.csv with 2,671+ recommendations

Runtime: ~15-30 minutes depending on data availability
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import pickle
import json

sys.path.append(str(Path(__file__).parent.parent))

from app.config import (
    MODELS_DIR, RESULTS_DIR, DATA_PROCESSED_DIR,
    TradingConfig, DataValidationConfig, get_all_nse_stocks
)
from app.signals.ml_signals import MLSignalGenerator
from app.data.loaders import fetch_history_nselib, get_all_nse_equities
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_recommendations_all_stocks():
    """Generate recommendations for all 2,671+ NSE stocks."""
    
    logger.info("="*70)
    logger.info("GENERATING RECOMMENDATIONS FOR ALL NSE STOCKS (2,671+)")
    logger.info("="*70)
    
    # Step 1: Get all NSE stocks
    logger.info("\n[STEP 1] Loading all NSE stocks...")
    try:
        all_symbols = get_all_nse_stocks()
        logger.info(f"[SUCCESS] Loaded {len(all_symbols)} NSE stocks")
    except Exception as e:
        logger.error(f"[ERROR] Failed to load NSE stocks: {e}")
        logger.info("Fallback: Using cached universe...")
        from app.config import NIFTY_50_UNIVERSE
        all_symbols = NIFTY_50_UNIVERSE
        logger.warning(f"Fallback to NIFTY_50 ({len(all_symbols)} stocks)")
    
    # Step 2: Fetch data for all stocks
    logger.info(f"\n[STEP 2] Fetching historical data for {len(all_symbols)} stocks...")
    logger.info("(This may take 5-15 minutes on first run)")
    
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")  # 2 years
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        df_all = fetch_history_nselib(all_symbols, start=start_date, end=end_date, include_delivery=False)
        logger.info(f"[SUCCESS] Fetched data: {df_all.shape[0]} rows, {df_all['symbol'].nunique()} symbols")
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch data: {e}")
        logger.info("Falling back to available data...")
        df_all = None
    
    if df_all is None or df_all.empty:
        logger.error("No data available. Exiting.")
        return
    
    # Step 3: Filter stocks with sufficient data
    logger.info(f"\n[STEP 3] Filtering stocks with minimum {DataValidationConfig.MIN_DATA_POINTS_PER_SYMBOL} data points...")
    
    symbol_counts = df_all.groupby('symbol').size()
    valid_symbols = symbol_counts[symbol_counts >= DataValidationConfig.MIN_DATA_POINTS_PER_SYMBOL].index.tolist()
    
    logger.info(f"[SUCCESS] {len(valid_symbols)}/{len(all_symbols)} stocks have sufficient data")
    
    df_valid = df_all[df_all['symbol'].isin(valid_symbols)].copy()
    
    # Step 4: Engineer features for ALL stocks
    logger.info(f"\n[STEP 4] Engineering features for {len(valid_symbols)} stocks...")
    
    generator = MLSignalGenerator()
    df_features = generator.prepare_features(df_valid)
    
    if df_features is None or df_features.empty:
        logger.error("[ERROR] Feature engineering failed")
        return
    
    logger.info(f"[SUCCESS] Features engineering complete: {df_features.shape}")
    
    # Step 5: Load trained model
    logger.info(f"\n[STEP 5] Loading trained model...")
    
    model_path = MODELS_DIR / "trading_model.pkl"
    if not model_path.exists():
        logger.error(f"[ERROR] Model not found at {model_path}")
        logger.info("Please run: python retrain_model_recent.py")
        return
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"[SUCCESS] Model loaded successfully")
        logger.info(f"Model type: {type(model).__name__}")
        logger.info(f"Model classes: {model.classes_}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to load model: {e}")
        return
    
    # Step 6: Generate predictions for ALL stocks
    logger.info(f"\n[STEP 6] Generating predictions for {len(valid_symbols)} stocks...")
    
    # Prepare features for prediction (latest data per stock)
    feature_cols = generator.feature_names
    
    # Get features matrix
    X = df_features[feature_cols].fillna(0).values
    
    try:
        # Get predictions
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        logger.info(f"[SUCCESS] Generated {len(predictions)} predictions")
    except Exception as e:
        logger.error(f"[ERROR] Prediction failed: {e}")
        return
    
    # Step 7: Build recommendations dataframe
    logger.info(f"\n[STEP 7] Building recommendations dataframe...")
    
    # Map predictions to signals
    signal_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
    
    recommendations = []
    
    for idx, row in df_features.iterrows():
        symbol = row['symbol']
        last_price = row['close']
        pred_idx = idx - df_features.index[0]  # Adjust for feature dataframe index
        
        if pred_idx >= len(predictions):
            continue
        
        pred_signal = signal_map.get(predictions[pred_idx], 'HOLD')
        pred_probs = probabilities[pred_idx]
        
        # Confidence is max probability
        confidence = float(np.max(pred_probs))
        
        # Risk score (inverse of probability)
        risk_score = 1.0 - confidence
        
        recommendations.append({
            'symbol': symbol,
            'recommendation': pred_signal,
            'confidence': confidence,
            'risk_score': risk_score,
            'last_price': last_price,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    df_recommendations = pd.DataFrame(recommendations)
    
    # Step 8: Sort by signal and confidence
    logger.info(f"\n[STEP 8] Sorting recommendations...")
    
    signal_order = {'BUY': 0, 'SELL': 1, 'HOLD': 2}
    df_recommendations['signal_order'] = df_recommendations['recommendation'].map(signal_order)
    df_recommendations = df_recommendations.sort_values(
        ['signal_order', 'confidence'],
        ascending=[True, False]
    ).drop('signal_order', axis=1)
    
    # Step 9: Save recommendations
    logger.info(f"\n[STEP 9] Saving recommendations...")
    
    csv_path = RESULTS_DIR / "latest_recommendations.csv"
    df_recommendations.to_csv(csv_path, index=False)
    
    logger.info(f"[SUCCESS] Saved {len(df_recommendations)} recommendations to {csv_path}")
    
    # Step 10: Summary statistics
    logger.info(f"\n[STEP 10] Summary Statistics:")
    logger.info("="*70)
    
    buy_count = len(df_recommendations[df_recommendations['recommendation'] == 'BUY'])
    sell_count = len(df_recommendations[df_recommendations['recommendation'] == 'SELL'])
    hold_count = len(df_recommendations[df_recommendations['recommendation'] == 'HOLD'])
    
    logger.info(f"Total Recommendations: {len(df_recommendations)}")
    logger.info(f"  • BUY:  {buy_count} stocks")
    logger.info(f"  • SELL: {sell_count} stocks")
    logger.info(f"  • HOLD: {hold_count} stocks")
    
    if buy_count > 0:
        logger.info(f"\nTop 5 BUY recommendations:")
        top_buy = df_recommendations[df_recommendations['recommendation'] == 'BUY'].head(5)
        for idx, row in top_buy.iterrows():
            logger.info(f"  {row['symbol']:15} | Price: ₹{row['last_price']:10.2f} | Confidence: {row['confidence']:.1%}")
    
    if sell_count > 0:
        logger.info(f"\nTop 5 SELL recommendations:")
        top_sell = df_recommendations[df_recommendations['recommendation'] == 'SELL'].head(5)
        for idx, row in top_sell.iterrows():
            logger.info(f"  {row['symbol']:15} | Price: ₹{row['last_price']:10.2f} | Confidence: {row['confidence']:.1%}")
    
    logger.info("="*70)
    logger.info("\n[COMPLETE] Recommendations generation finished successfully!")
    logger.info(f"Next: Update frontend to display all {len(df_recommendations)} recommendations")

if __name__ == "__main__":
    try:
        generate_recommendations_all_stocks()
    except Exception as e:
        logger.error(f"[FATAL] Unexpected error: {e}", exc_info=True)
        sys.exit(1)
