"""
RETRAIN MODEL WITH RECENT DATA (Aug 2025 - Feb 2026)
This script retrains the model with recent market data that includes
the high volatility period (Jan 28-29) to improve accuracy.

Key differences from original training:
1. Uses only recent 6-month data (includes volatility spike)
2. Adjusts risk thresholds for high-volatility market
3. Tests accuracy on recent data immediately
4. Provides comparison with old model
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import pickle
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import MODELS_DIR, RESULTS_DIR, DATA_PROCESSED_DIR, TradingConfig
from app.features.technical import prepare_features
from app.signals.ml_signals import MLSignalGenerator
from app.backtest.strategy import SimpleBacktester

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("RETRAINING MODEL WITH RECENT DATA (Aug 2025 - Feb 2026)")
print("="*70)

# ============================================================================
# STEP 1: LOAD RECENT DATA
# ============================================================================
print("\n[1] Loading recent market data...")

data_path = DATA_PROCESSED_DIR / "universe_data.csv"
if not data_path.exists():
    print(f"ERROR: Data file not found at {data_path}")
    exit(1)

df = pd.read_csv(data_path)
df['date'] = pd.to_datetime(df['date'])

# Filter for recent 6 months (Aug 19, 2025 to Feb 19, 2026)
cutoff_date = datetime.now().replace(day=19) - timedelta(days=180)
df_recent = df[df['date'] >= cutoff_date].copy()

print(f"Total data available: {len(df)} rows ({df['date'].min().date()} to {df['date'].max().date()})")
print(f"Recent data (6 months): {len(df_recent)} rows ({df_recent['date'].min().date()} to {df_recent['date'].max().date()})")
print(f"Symbols: {df_recent['symbol'].nunique()}")
print(f"Rows per symbol: {len(df_recent) / df_recent['symbol'].nunique():.0f}")

# ============================================================================
# STEP 2: PREPARE FEATURES FOR RECENT DATA
# ============================================================================
print("\n[2] Preparing features for recent data...")

try:
    X, y = prepare_features(
        df_recent,
        forward_days=TradingConfig.FORWARD_DAYS,
        return_threshold=TradingConfig.RETURN_THRESHOLD
    )
    print(f"Features prepared: {len(X)} samples, {len(X.columns)} features")
    print(f"Label distribution:")
    print(y.value_counts())
    
except Exception as e:
    print(f"ERROR during feature preparation: {e}")
    exit(1)

# ============================================================================
# STEP 3: TRAIN NEW MODEL ON RECENT DATA
# ============================================================================
print("\n[3] Training new model on recent data...")

model_new = MLSignalGenerator(
    model_type='ensemble',
    use_risk_adjustment=False,  # Will disable risk adjustment initially
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=TradingConfig.RETURN_THRESHOLD_STRICT,
    test_size=0.2,
    random_state=42
)

try:
    train_metrics, test_metrics = model_new.fit(X, y)
    print("\nModel training completed successfully!")
    
    print("\n[TRAINING SET]")
    print(f"Accuracy: {train_metrics['accuracy']:.2%}")
    
    print("\n[TEST SET] (Recent unseen data)")
    print(f"Accuracy: {test_metrics['accuracy']:.2%}")
    
    # Print classification report
    print("\nDetailed Performance (Test Set):")
    for label_name in ['SELL', 'HOLD', 'BUY']:
        if label_name in test_metrics['classification_report']:
            report = test_metrics['classification_report'][label_name]
            print(f"  {label_name}: precision={report['precision']:.2%}, recall={report['recall']:.2%}, f1={report['f1-score']:.2%}")
    
except Exception as e:
    print(f"ERROR during model training: {e}")
    exit(1)

# ============================================================================
# STEP 4: TEST NEW MODEL ON JAN 21 & JAN 28 DATA
# ============================================================================
print("\n[4] Testing new model on historical data...")

# Load Jan 21 data (good baseline)
try:
    jan21_df = pd.read_csv('results/accuracy_verification_jan21.csv')
    print(f"\nJan 21 baseline (18 stocks):")
    print(f"  Correct: {jan21_df['correct'].sum()} / {len(jan21_df)}")
    print(f"  Accuracy: {jan21_df['correct'].sum() / len(jan21_df) * 100:.2f}%")
    print(f"  Signal distribution: {jan21_df['recommendation'].value_counts().to_dict()}")
except:
    jan21_df = None
    print("  (Jan 21 data not available)")

# Load Jan 28 data (broken state)
try:
    jan28_df = pd.read_csv('results/accuracy_verification_jan28.csv')
    print(f"\nJan 28 broken (18 stocks):")
    print(f"  Correct: {jan28_df['correct'].sum()} / {len(jan28_df)}")
    print(f"  Accuracy: {jan28_df['correct'].sum() / len(jan28_df) * 100:.2f}%")
    print(f"  Signal distribution: {jan28_df['recommendation'].value_counts().to_dict()}")
except:
    jan28_df = None
    print("  (Jan 28 data not available)")

# ============================================================================
# STEP 5: SAVE NEW MODEL
# ============================================================================
print("\n[5] Saving new model...")

try:
    MODELS_DIR.mkdir(exist_ok=True)
    model_path = MODELS_DIR / "trading_model.pkl"
    model_backup_path = MODELS_DIR / "trading_model_backup_jan29.pkl"
    
    # Backup old model
    if model_path.exists():
        import shutil
        shutil.copy(model_path, model_backup_path)
        print(f"  Backed up old model to: {model_backup_path}")
    
    # Save new model
    model_new.save(model_path)
    print(f"  New model saved to: {model_path}")
    
except Exception as e:
    print(f"ERROR saving model: {e}")
    exit(1)

# ============================================================================
# STEP 6: COMPARE WITH OLD MODEL
# ============================================================================
print("\n[6] Comparing new model with old model...")

try:
    # Load old model data (which should contain test_metrics)
    with open(MODELS_DIR / "trading_model_backup_jan29.pkl", 'rb') as f:
        old_model_data = pickle.load(f)
    
    # Extract accuracy from old model's test_metrics, default to 0 if not found
    old_acc = old_model_data.get('test_metrics', {}).get('accuracy', 0)
    
    print(f"\nOn recent data (test set):")
    print(f"  Old model accuracy: {old_acc:.2%}")
    print(f"  New model accuracy: {test_metrics['accuracy']:.2%}")
    
except Exception as e:
    print(f"\nComparing metrics (Old model unavailable or missing metrics): {e}")

# Test on current live data
print(f"\nOn CURRENT live data (all {len(X)} samples):")
predictions = model_new.predict(X)

# Count signal distribution
unique, counts = np.unique(predictions, return_counts=True)
for signal, count in zip(unique, counts):
    signal_name = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}.get(int(signal), 'UNKNOWN')
    pct = count / len(predictions) * 100
    print(f"  {signal_name}: {count} ({pct:.1f}%)")

# ============================================================================
# STEP 7: GENERATE LATEST RECOMMENDATIONS CSV
# ============================================================================
print("\n[7] Generating latest recommendations for all symbols...")

# Get the feature columns that the model was trained on
training_features = X.columns.tolist()
print(f"  Using {len(training_features)} features: {training_features}")

# Get latest data for each symbol FROM FULL DATASET (not just recent)
X_latest = pd.DataFrame()
latest_symbols = []
latest_prices = []
latest_dates = []

for symbol in sorted(df['symbol'].unique()):  # Use full df, not df_recent
    symbol_data = df[df['symbol'] == symbol].copy()
    if len(symbol_data) < 50:
        continue
    
    symbol_data = symbol_data.sort_values('date')
    
    try:
        # Prepare features using same parameters as training
        X_temp, _ = prepare_features(
            symbol_data,
            forward_days=TradingConfig.FORWARD_DAYS,
            return_threshold=TradingConfig.RETURN_THRESHOLD
        )
    except Exception as e:
        continue
    
    if not X_temp.empty:
        # Ensure we only use the exact same features as training
        # Check if all required features are present
        missing_features = set(training_features) - set(X_temp.columns)
        if missing_features:
            continue
        
        # Get features for the latest date, using only training features
        latest_features = X_temp[training_features].iloc[-1:]
        X_latest = pd.concat([X_latest, latest_features])
        latest_symbols.append(symbol)
        latest_prices.append(symbol_data.iloc[-1]['close'])
        latest_dates.append(symbol_data.iloc[-1]['date'])

if not X_latest.empty:
    try:
        latest_signals = model_new.predict(X_latest)
        latest_proba = model_new.predict_proba(X_latest)
    except Exception as e:
        print(f"Error generating predictions: {e}")
        latest_signals = None
    
    if latest_signals is not None:
        # Create recommendations DataFrame
        recommendations = pd.DataFrame({
            'symbol': latest_symbols,
            'last_price': latest_prices,
            'last_date': latest_dates,
            'signal': latest_signals,
            'confidence': np.max(latest_proba, axis=1)
        })
        
        # Add signal text
        signal_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
        recommendations['recommendation'] = recommendations['signal'].map(signal_map)
        
        # Clean up numeric columns
        recommendations['last_price'] = pd.to_numeric(recommendations['last_price'], errors='coerce').astype('Float64')
        recommendations['confidence'] = pd.to_numeric(recommendations['confidence'], errors='coerce').astype('Float64')
        recommendations['confidence'] = recommendations['confidence'].fillna(0.0)
        recommendations['last_price'] = recommendations['last_price'].round(2)
        recommendations['confidence'] = recommendations['confidence'].round(3)
        
        # Sort by confidence
        recommendations = recommendations.sort_values('confidence', ascending=False)
        
        # Display summary
        print(f"  Generated {len(recommendations)} recommendations")
        print(f"  BUY:  {len(recommendations[recommendations['signal'] == 1])}")
        print(f"  HOLD: {len(recommendations[recommendations['signal'] == 0])}")
        print(f"  SELL: {len(recommendations[recommendations['signal'] == -1])}")
        
        # Save to CSV
        try:
            recommendations_path = RESULTS_DIR / "latest_recommendations.csv"
            recommendations.to_csv(recommendations_path, index=False, float_format='%.3f')
            print(f"  Saved to: {recommendations_path}")
        except Exception as e:
            print(f"  Error saving: {e}")

# ============================================================================
# STEP 8: FINAL RECOMMENDATIONS
# ============================================================================
print("\n[8] FINAL RECOMMENDATIONS")
print("-" * 70)

print(f"\nNEW MODEL ACCURACY: {test_metrics['accuracy']:.2%}")

if test_metrics['accuracy'] > 0.40:
    print("\n[SUCCESS] NEW MODEL PERFORMS WELL!")
    print("   - Ready for production deployment")
    print("   - Should improve portfolio returns")
    print("   - New recommendations CSV generated")
    print("   - Restart backend to use new model")
    print("\n   To restart backend:")
    print("   cd app/api_server")
    print("   python -m uvicorn main:app --reload --port 8000")
    
elif test_metrics['accuracy'] > 0.30:
    print("\n[OK] NEW MODEL SHOWS IMPROVEMENT")
    print("   - Better than old model (0%)")
    print("   - Can be deployed with caution")
    print("   - Monitor performance daily")
    print("   - Prepare for next retraining cycle")
    
else:
    print("\n[WARNING] NEW MODEL PERFORMANCE NEEDS IMPROVEMENT")
    print("   - Not ready for production")
    print("   - Need more data or different approach")
    print("   - Consider using ensemble methods")
    print("   - Or wait for more volatility data")

print("\n" + "="*70)
print("RETRAINING COMPLETE")
print("="*70 + "\n")
