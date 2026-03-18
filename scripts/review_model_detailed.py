import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path.cwd()))

print("\n" + "="*80)
print("DETAILED MODEL DIAGNOSTIC - DATA & TRAINING ANALYSIS")
print("="*80)

# Load training data
try:
    df = pd.read_csv("data/processed/universe_data.csv")
    df['date'] = pd.to_datetime(df['date'])
    print(f"\n✅ Training data loaded: {len(df)} rows, {df['symbol'].nunique()} symbols")
except Exception as e:
    print(f"\n❌ Error loading training data: {e}")
    sys.exit(1)

# Check data quality
print("\n" + "="*80)
print("DATA QUALITY CHECK")
print("="*80)

print(f"\n📊 Data shape: {df.shape}")
print(f"   Rows: {len(df):,}")
print(f"   Columns: {list(df.columns)}")

# Check for missing values
print(f"\n🔍 Missing values:")
missing = df.isnull().sum()
for col in df.columns:
    if missing[col] > 0:
        pct = (missing[col] / len(df)) * 100
        print(f"   {col:15s}: {missing[col]:5d} ({pct:5.2f}%)")

if missing.sum() == 0:
    print("   ✅ No missing values!")

# Now prepare features and check label distribution
print("\n" + "="*80)
print("FEATURE & LABEL ANALYSIS")
print("="*80)

try:
    from app.features.technical import prepare_features
    
    print("\n🔄 Preparing features...")
    X, y = prepare_features(
        df,
        forward_days=5,
        return_threshold=0.02
    )
    
    print(f"✅ Features prepared:")
    print(f"   X shape: {X.shape}")
    print(f"   y shape: {y.shape}")
    print(f"   Features: {list(X.columns)}")
    
    # Check X for NaN/Inf values
    print(f"\n🔍 Feature quality check:")
    nan_count = X.isnull().sum().sum()
    inf_count = np.isinf(X.select_dtypes(include=[np.number])).sum().sum()
    print(f"   NaN values in features: {nan_count}")
    print(f"   Inf values in features: {inf_count}")
    
    if nan_count > 0:
        print(f"\n   ⚠️  Columns with NaN:")
        for col in X.columns:
            nan_pct = (X[col].isnull().sum() / len(X)) * 100
            if nan_pct > 0:
                print(f"      {col:20s}: {nan_pct:5.1f}% NaN")
    
    # Check label distribution
    print(f"\n📊 Label distribution (y):")
    label_counts = pd.Series(y).value_counts().sort_index()
    total = len(y)
    for label, count in label_counts.items():
        label_name = {-1: "SELL", 0: "HOLD", 1: "BUY"}.get(label, str(label))
        pct = (count / total) * 100
        print(f"   {label_name:6s} (={label:2d}): {count:5d} ({pct:5.1f}%)")
    
    # Check imbalance
    if label_counts.max() > label_counts.min() * 2:
        print(f"\n   ⚠️  CLASS IMBALANCE DETECTED!")
        print(f"      Ratio: {label_counts.max() / label_counts.min():.1f}x")
        print(f"      This causes the model to predict the majority class")
    
    # Check feature statistics
    print(f"\n📊 Feature statistics:")
    print(f"   Min value: {X.select_dtypes(include=[np.number]).min().min():.6f}")
    print(f"   Max value: {X.select_dtypes(include=[np.number]).max().max():.6f}")
    print(f"   Mean: {X.select_dtypes(include=[np.number]).mean().mean():.6f}")
    print(f"   Std: {X.select_dtypes(include=[np.number]).std().mean():.6f}")
    
except Exception as e:
    print(f"\n❌ Error during feature preparation: {e}")
    import traceback
    traceback.print_exc()

# Check current model's latest predictions
print("\n" + "="*80)
print("MODEL OUTPUT ANALYSIS")
print("="*80)

try:
    recommendations = pd.read_csv("results/latest_recommendations.csv")
    
    print(f"\n✅ Loaded {len(recommendations)} recommendations")
    
    # Check prediction diversity
    if 'recommendation' in recommendations.columns:
        rec_dist = recommendations['recommendation'].value_counts()
        print(f"\n📊 Prediction diversity:")
        for rec, count in rec_dist.items():
            pct = (count / len(recommendations)) * 100
            print(f"   {rec:10s}: {count:3d} ({pct:5.1f}%)")
        
        # Flag if too imbalanced
        dominant = rec_dist.iloc[0]
        total = len(recommendations)
        if dominant > total * 0.95:
            print(f"\n   🚨 WARNING: Model is predicting same class {dominant/total*100:.1f}% of time!")
            print(f"      This indicates the model has not learned to discriminate")
    
    # Check confidence distribution
    if 'confidence' in recommendations.columns:
        print(f"\n📊 Confidence distribution:")
        print(f"   Mean: {recommendations['confidence'].mean():.3f}")
        print(f"   Median: {recommendations['confidence'].median():.3f}")
        print(f"   Std: {recommendations['confidence'].std():.3f}")
        
        # Check if confidences are diverse
        conf_std = recommendations['confidence'].std()
        if conf_std < 0.1:
            print(f"\n   ⚠️  WARNING: Confidences are too similar (std={conf_std:.3f})")
            print(f"      Model is not generating diverse predictions")

except Exception as e:
    print(f"\n❌ Error analyzing recommendations: {e}")

print("\n" + "="*80)
print("ROOT CAUSE IDENTIFICATION")
print("="*80)

print("\n🔍 Probable Issues:")
print("""
1. CLASS IMBALANCE (Most Likely)
   - 97.7% HOLD, 2.3% SELL predicts that training data was imbalanced
   - Model learned to always predict majority class
   - Fix: Use class_weight='balanced' in model training

2. RETURN THRESHOLD TOO HIGH
   - If return_threshold=0.02 is too high, most samples become HOLD
   - Few stocks return >2% in 5 days
   - Fix: Lower threshold to 0.01 or 0.015

3. FEATURE ENGINEERING ISSUE
   - NaN values in features cause poor learning
   - Scaling/normalization not working
   - Fix: Fill NaN properly, check feature ranges

4. MARKET REGIME CHANGE
   - Jan 21-28 market changed significantly (volatile)
   - Model trained on stable market data (2023-2026)
   - Technical indicators may not work in high volatility
   - Fix: Add volatility-adjusted features, retrain often
""")

print("\n" + "="*80)
print("RECOMMENDED FIXES")
print("="*80)

print("\n✅ IMMEDIATE FIXES (Will improve accuracy):")
print("""
1. RETRAIN WITH CLASS BALANCING:
   Edit app/api/train_model.py:
   model = MLSignalGenerator(..., class_weight='balanced')
   
2. ADJUST RETURN THRESHOLD:
   Edit app/api/train_model.py:
   return_threshold=0.01  # Lower from 0.02 to 0.01
   
3. ADD VALIDATION:
   Check that y has diverse labels before training
   If 95%+ are same class, increase sample size or lower threshold
   
4. RETRAIN MODEL:
   python app/api/train_model.py
""")

print("\n✅ MEDIUM-TERM IMPROVEMENTS:")
print("""
1. Add volatility-aware features
   - Scale features by current market volatility
   - Adjust thresholds based on macro risk

2. Implement online learning
   - Retrain model weekly with new data
   - Detect model degradation automatically

3. Add ensemble methods
   - Use multiple models, ensemble predictions
   - RandomForest + GradientBoost + LightGBM

4. Cross-validation
   - Time-series cross-validation
   - Verify model generalizes to new periods
""")

print("\n" + "="*80)
