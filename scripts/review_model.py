import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path.cwd()))
from app.signals.ml_signals import MLSignalGenerator

print("\n" + "=" * 80)
print("MODEL REVIEW & DIAGNOSTICS - JANUARY 29, 2026")
print("=" * 80)

# Check model files
print("\n📁 MODEL FILES FOUND:")
models_dir = Path("models")
if models_dir.exists():
    model_files = list(models_dir.glob("*.pkl"))
    for mf in model_files:
        size_kb = mf.stat().st_size / 1024
        mtime = mf.stat().st_mtime
        from datetime import datetime

        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"   ✓ {mf.name:35s} {size_kb:8.1f} KB  (Updated: {mtime_str})")
else:
    print("   ❌ Models directory not found")

# Load and analyze the trading model
print("\n" + "=" * 80)
print("TRADING MODEL ANALYSIS")
print("=" * 80)

try:
    with open("models/trading_model.pkl", "rb") as f:
        model_obj = pickle.load(f)
    model_wrapper = MLSignalGenerator.load("models/trading_model.pkl")
    model = model_wrapper.model
    feature_columns = model_wrapper.feature_columns

    print(f"\n✅ Model loaded successfully")
    print(f"   Model Type: {type(model).__name__}")
    print(f"   Features: {len(feature_columns) if feature_columns else 'Unknown'}")

    if feature_columns:
        print(f"\n📊 FEATURE LIST ({len(feature_columns)} features):")
        for i, feat in enumerate(feature_columns[:15], 1):
            print(f"      {i:2d}. {feat}")
        if len(feature_columns) > 15:
            print(f"      ... and {len(feature_columns) - 15} more")

    # Check model parameters
    if hasattr(model, "n_estimators"):
        print(f"\n⚙️  MODEL PARAMETERS:")
        print(f"   n_estimators: {model.n_estimators}")

    if hasattr(model, "max_depth"):
        print(f"   max_depth: {model.max_depth}")

    if hasattr(model, "learning_rate"):
        print(f"   learning_rate: {model.learning_rate}")

    if hasattr(model, "min_samples_split"):
        print(f"   min_samples_split: {model.min_samples_split}")

except Exception as e:
    print(f"\n❌ Error loading trading model: {e}")

# Check latest recommendations
print("\n" + "=" * 80)
print("LATEST PREDICTIONS ANALYSIS")
print("=" * 80)

try:
    recommendations = pd.read_csv("results/latest_recommendations.csv")

    print(f"\n✅ Latest recommendations loaded: {len(recommendations)} stocks")

    # Analyze recommendations
    print(f"\n📊 RECOMMENDATION DISTRIBUTION:")
    rec_dist = recommendations["recommendation"].value_counts()
    for rec, count in rec_dist.items():
        pct = (count / len(recommendations)) * 100
        print(f"   {rec:15s}: {count:3d} ({pct:5.1f}%)")

    # Analyze signals
    print(f"\n📊 SIGNAL DISTRIBUTION:")
    if "signal" in recommendations.columns:
        signal_dist = recommendations["signal"].value_counts().sort_index()
        for sig, count in signal_dist.items():
            pct = (count / len(recommendations)) * 100
            sig_label = {-1: "SELL", 0: "HOLD", 1: "BUY"}.get(sig, str(sig))
            print(f"   {sig_label:15s}: {count:3d} ({pct:5.1f}%)")

    # Confidence analysis
    print(f"\n🎯 CONFIDENCE METRICS:")
    print(f"   Mean:     {recommendations['confidence'].mean():.3f} (Target: >0.6)")
    print(f"   Median:   {recommendations['confidence'].median():.3f}")
    print(f"   Std Dev:  {recommendations['confidence'].std():.3f}")
    print(f"   Min:      {recommendations['confidence'].min():.3f}")
    print(f"   Max:      {recommendations['confidence'].max():.3f}")

    # Confidence by recommendation
    if "recommendation" in recommendations.columns:
        print(f"\n📊 CONFIDENCE BY RECOMMENDATION:")
        for rec in rec_dist.index:
            subset = recommendations[recommendations["recommendation"] == rec]
            mean_conf = subset["confidence"].mean()
            print(f"   {rec:15s}: {mean_conf:.3f}")

except Exception as e:
    print(f"\n❌ Error loading recommendations: {e}")

# Check training data
print("\n" + "=" * 80)
print("TRAINING DATA ANALYSIS")
print("=" * 80)

try:
    data_path = Path("data/processed/universe_data.csv")
    if data_path.exists():
        df = pd.read_csv(data_path)
        print(f"\n✅ Training data found")
        print(f"   Rows: {len(df):,}")
        print(f"   Symbols: {df['symbol'].nunique()}")
        print(f"   Avg rows/symbol: {len(df) / df['symbol'].nunique():.1f}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Columns: {len(df.columns)}")
    else:
        print(f"\n❌ Training data not found at {data_path}")

except Exception as e:
    print(f"\n❌ Error checking training data: {e}")

# Key issues analysis
print("\n" + "=" * 80)
print("🚨 IDENTIFIED ISSUES & ROOT CAUSES")
print("=" * 80)

print("\n1️⃣  ZERO ACCURACY (0% → Was 33.33%)")
print("   Root Causes:")
print("   • Model may have been retrained on limited/biased data")
print("   • Data distribution changed (market regime shift)")
print("   • Feature engineering breakdown (NaN values, scaling issues)")
print("   • Labels generation problem (all same class)")
print("   • Model convergence to default (always predicts HOLD)")

print("\n2️⃣  ALL PREDICTIONS DEFAULTING TO HOLD")
print("   Root Causes:")
print("   • Class imbalance problem: Too many 0 (HOLD) samples")
print("   • Threshold misconfiguration: return_threshold too high/low")
print("   • Model trained on biased labels")
print("   • Feature importance near zero (model unable to discriminate)")

print("\n3️⃣  OVERCONFIDENCE + LOW ACCURACY")
print("   Root Causes:")
print("   • Model confidence not calibrated to actual accuracy")
print("   • Probability outputs not properly scaled")
print("   • Risk adjustment layer not functioning")
print("   • Prediction probabilities all near 0.5")

print("\n4️⃣  MARKET REGIME CHANGE (Jan 21 → Jan 28)")
print("   Evidence:")
print("   • Model trained on historical data that may not fit current market")
print("   • Volatility increased (macro risk: 0.68)")
print("   • Stock behavior patterns changed")
print("   • Technical indicators less predictive in high volatility")

print("\n" + "=" * 80)
print("DIAGNOSTIC RECOMMENDATIONS")
print("=" * 80)

print("\n✅ IMMEDIATE CHECKS:")
print("   1. Verify training data quality:")
print("      - Check for NaN values in features")
print("      - Check label distribution (should be mixed, not all 0s)")
print("      - Verify forward returns calculated correctly")

print("\n   2. Check label generation:")
print('      - Run: python -c "from app.features.technical import prepare_features"')
print("      - Verify return_threshold is appropriate (2% default)")
print("      - Count signal distribution (-1, 0, 1)")

print("\n   3. Validate features:")
print("      - All 15 features should be different and informative")
print("      - Check for NaN/Inf values in feature set")
print("      - Verify feature scaling is working")

print("\n✅ ROOT CAUSE ANALYSIS:")
print("   1. Load training data and check signal distribution")
print("   2. Compare current vs previous model accuracy")
print("   3. Check if data was updated (universe_data.csv)")
print("   4. Review feature importance - which features matter most?")
print("   5. Test on historical data to see if model was trained correctly")

print("\n✅ FIXES TO IMPLEMENT:")
print("   1. Retrain model with:")
print("      - Proper train/test split")
print("      - Class weight balancing")
print("      - Cross-validation for accuracy")
print("      - Wider return threshold if needed")

print("\n   2. Add validation checks:")
print("      - Minimum samples per class check")
print("      - Feature NaN percentage check")
print("      - Prediction distribution validation")

print("\n   3. Implement safeguards:")
print("      - Don't use model if test accuracy < 50%")
print("      - Require signal diversity (not all HOLD)")
print("      - Validate on out-of-sample data before deployment")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)

print("\n1. RUN DIAGNOSTIC SCRIPT: python review_model_detailed.py")
print("2. ANALYZE DATA: python check_data.py")
print("3. RETRAIN MODEL: python app/api/train_model.py")
print("4. VALIDATE SIGNALS: Check if diverse (not all HOLD)")
print("5. BACKTEST: Test on historical data")
print("6. DEPLOY: Only if accuracy > 50% and signals are diverse")

print("\n" + "=" * 80)
