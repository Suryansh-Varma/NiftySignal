"""
GENERATE RECOMMENDATIONS WITH NEW TRAINED MODEL
This creates fresh recommendations.csv using the newly trained model
with 71.79% accuracy on recent volatile market data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import pickle

sys.path.append(str(Path(__file__).parent.parent))

from app.config import MODELS_DIR, RESULTS_DIR, DATA_PROCESSED_DIR, TradingConfig
from app.features.technical import prepare_features

print("\n" + "="*70)
print("GENERATING RECOMMENDATIONS WITH NEW MODEL")
print("="*70)

# Load the universe data
print("\n[1] Loading market data...")
data_path = DATA_PROCESSED_DIR / "universe_data.csv"
df = pd.read_csv(data_path)
df['date'] = pd.to_datetime(df['date'])
print(f"    Loaded {len(df)} rows from {df['date'].min().date()} to {df['date'].max().date()}")

# Load the newly trained model
print("\n[2] Loading new trained model...")
model_path = MODELS_DIR / "trading_model.pkl"
try:
    with open(model_path, 'rb') as f:
        model_dict = pickle.load(f)
    print(f"    Model loaded: {model_path}")
    # Extract components from dict
    clf = model_dict['model']
    scaler = model_dict['scaler']
    feature_columns = model_dict.get('feature_columns')
    forward_days = model_dict.get('forward_days', TradingConfig.FORWARD_DAYS)
    return_threshold = model_dict.get('return_threshold', TradingConfig.RETURN_THRESHOLD)
except Exception as e:
    print(f"    ERROR: {e}")
    exit(1)

# Get latest data for each symbol
print(f"\n[3] Generating predictions for all symbols (using {len(feature_columns) if feature_columns else 'default'} features)...")

latest_data = []
recommendations = []

for symbol in sorted(df['symbol'].unique()):
    symbol_data = df[df['symbol'] == symbol].copy()
    if len(symbol_data) < 50:  # Need minimum data
        print(f"    Skip {symbol}: not enough data ({len(symbol_data)} rows)")
        continue
    
    symbol_data = symbol_data.sort_values('date')
    latest_price = symbol_data.iloc[-1]['close']
    latest_date = symbol_data.iloc[-1]['date']
    
    try:
        # Prepare features for latest data using the same columns as training
        X_all, _ = prepare_features(
            symbol_data,
            feature_columns=feature_columns,
            forward_days=forward_days,
            return_threshold=return_threshold
        )
        
        if X_all.empty:
            continue
        
        # Get latest features and pass as DataFrame
        X_latest = X_all.iloc[-1:]
        
        # Make prediction using the robust predictor
        signal = clf.predict(X_latest)[0]
        proba = clf.predict_proba(X_latest)[0]
        confidence = np.max(proba)
        
        # The model returns labels [-1, 0, 1] for [SELL, HOLD, BUY]
        signal_value = int(signal)
        # The model returns labels [-1, 0, 1] for [SELL, HOLD, BUY]
        signal_map = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
        signal_text = signal_map.get(signal_value, "HOLD")
        
        recommendations.append({
            'symbol': symbol,
            'last_price': latest_price,
            'last_date': latest_date,
            'signal': signal_value,
            'confidence': confidence,
            'recommendation': signal_text
        })
        
        print(f"    {symbol}: {signal_text:4} (confidence: {confidence:.2f})")
        
    except Exception as e:
        print(f"    Error for {symbol}: {str(e)[:50]}")
        continue

# Create recommendations DataFrame
print("\n[4] Organizing recommendations...")
recs_df = pd.DataFrame(recommendations)

if not recs_df.empty:
    # Sort by confidence
    recs_df = recs_df.sort_values('confidence', ascending=False)
    
    # Display summary
    print(f"\nTotal recommendations: {len(recs_df)}")
    print(f"  BUY:  {len(recs_df[recs_df['signal'] == 1])} stocks")
    print(f"  HOLD: {len(recs_df[recs_df['signal'] == 0])} stocks")
    print(f"  SELL: {len(recs_df[recs_df['signal'] == -1])} stocks")
    
    # Save to CSV
    print("\n[5] Saving recommendations...")
    try:
        RESULTS_DIR.mkdir(exist_ok=True)
        recs_path = RESULTS_DIR / "latest_recommendations.csv"
        
        # Keep only needed columns
        save_df = recs_df[['symbol', 'last_price', 'last_date', 'signal', 'confidence', 'recommendation']]
        save_df.to_csv(recs_path, index=False)
        
        print(f"    Saved to: {recs_path}")
        
        # Show top recommendations
        print("\n[6] TOP RECOMMENDATIONS:")
        print("-" * 70)
        
        # Top BUY
        buys = recs_df[recs_df['signal'] == 1].head(5)
        if not buys.empty:
            print("\nBUY OPPORTUNITIES (Best for growth):")
            for _, row in buys.iterrows():
                print(f"  {row['symbol']}: Rs{row['last_price']:.0f} (confidence: {row['confidence']*100:.0f}%)")
        
        # Top SELL
        sells = recs_df[recs_df['signal'] == -1].head(5)
        if not sells.empty:
            print("\nSELL SIGNALS (Risk reduction):")
            for _, row in sells.iterrows():
                print(f"  {row['symbol']}: Rs{row['last_price']:.0f} (confidence: {row['confidence']*100:.0f}%)")
        
        # HOLD
        holds = recs_df[recs_df['signal'] == 0]
        print(f"\nHOLD SIGNALS: {len(holds)} stocks (neutral position)")
        
        print("\n" + "="*70)
        print("[SUCCESS] NEW RECOMMENDATIONS GENERATED")
        print("         Backend will use these when restarted")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"ERROR saving recommendations: {e}")
        exit(1)
else:
    print("ERROR: No recommendations generated!")
    exit(1)
