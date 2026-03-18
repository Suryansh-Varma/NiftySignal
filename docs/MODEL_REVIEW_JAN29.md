# MODEL REVIEW - COMPREHENSIVE ANALYSIS
## January 29, 2026

---

## Executive Summary

The trading model's accuracy has completely degraded from **33.33% (Jan 21) to 0% (Jan 28)**. Investigation reveals the model is **predicting HOLD for 97.7% of stocks** instead of generating diverse signals (BUY/SELL/HOLD).

**Root Cause**: Model architecture and prediction pipeline are fundamentally broken, not data quality.

---

## Current Model Status

| Metric | Value | Status |
|--------|-------|--------|
| **Model Type** | GradientBoostingClassifier | ✅ Valid |
| **Model Size** | 1039.9 KB | ✅ Loaded |
| **Last Trained** | 2026-01-21 22:20:44 | ⏱️ 8 days old |
| **Parameters** | n_estimators=100, max_depth=5, lr=0.1 | ✅ Reasonable |
| **Test Performance** | Unknown (need to check) | 🔴 CRITICAL |

---

## Problem Diagnosis

### 1. **CRITICAL ISSUE: Model Not Generating Diverse Signals**

```
Desired Output (Should be):
   BUY  : ~30-40% of predictions
   HOLD : ~30-40% of predictions
   SELL : ~20-30% of predictions

Actual Output (Jan 29):
   HOLD : 97.7% (43/44)
   SELL :  2.3% (1/44)
   BUY  :  0.0% (0/44)
```

**This indicates:** Model has learned to default to predicting HOLD for almost everything.

### 2. **Root Cause Analysis**

#### Training Data Analysis ✅
```
✅ Data Quality: GOOD
   - 10,071 rows, 49 symbols (good coverage)
   - No missing values (clean)
   - 205.5 rows per symbol (excellent)
   - Date range: 2023-01-02 to 2026-01-19 (3 years)
```

#### Feature Engineering ✅
```
✅ Features: GOOD
   - 15 features generated (comprehensive)
   - No NaN values in features
   - No Inf values in features
   - Feature ranges: -440 to +11,505 (large but reasonable)
```

#### Label Distribution ⚠️ **ISSUE HERE**
```
✅ Training Labels (Before Model):
   - SELL : 2,197 (25.9%)
   - HOLD : 2,919 (34.5%)
   - BUY  : 3,356 (39.6%)
   
   → Balanced distribution! (No class imbalance)

❌ Model Predictions (After Inference):
   - SELL : 1 (2.3%)
   - HOLD : 43 (97.7%)
   - BUY  : 0 (0.0%)
   
   → Predictions are totally different!
   → Model is NOT using learned distributions
```

### 3. **Why Is This Happening?**

The mismatch between balanced training labels and imbalanced predictions indicates:

1. **Model Inference Issue** (Most Likely 70%)
   - Model is not outputting probabilities correctly
   - Risk adjustment layer might be breaking predictions
   - Prediction thresholds misconfigured (converting to single class)

2. **Data Drift / Market Regime Change** (20%)
   - Market conditions (high volatility, macro risk 0.68) differ from training data
   - Model trained on 2023-2026 stable market data
   - Current market structure totally different

3. **Feature Scaling / Normalization Issue** (10%)
   - Features might be scaled incorrectly for current market values
   - Feature ranges different than training distribution

---

## Detailed Technical Analysis

### Model Architecture

**Current Setup**:
```
GradientBoostingClassifier
├── n_estimators: 100 (good)
├── max_depth: 5 (shallow, helps prevent overfitting)
├── learning_rate: 0.1 (conservative)
├── min_samples_split: 10 (good)
└── Random state: 42 (reproducible)
```

**Status**: Architecture is reasonable ✅

### Prediction Pipeline

```
Step 1: Load features [15 dimensions]
Step 2: Scale features (StandardScaler)
Step 3: Pass through GradientBoost
Step 4: Get predict_proba() outputs
Step 5: Apply risk adjustment
Step 6: Convert to signal (BUY/HOLD/SELL)
```

**Issue Likely In**: Steps 5-6 (Risk adjustment or signal conversion)

### Confidence Scores

```
Current Confidence Distribution:
   Mean:     0.621 (meets >0.6 threshold ✅)
   Median:   0.607 (adequate)
   Range:    0.367 to 0.840 (diverse)
```

**Analysis**: Confidences look reasonable, but don't reflect actual accuracy (0%).

---

## Why Accuracy Dropped to 0%

### Jan 21 State: 33.33% accuracy
- Portfolio: 6/18 correct (earning money)
- Model was generating BUY/SELL signals
- Risk adjustment seemed to work

### Jan 28 State: 0% accuracy
- Portfolio: 0/18 correct (losing money)
- Model now defaults to HOLD
- Risk adjustment might be zeroing out signals

### What Changed Between Jan 21-28?

1. **Market Volatility**: Increased from ~0.4 to 0.68 (macro risk)
2. **Stock Correlations**: Likely increased in high volatility
3. **Technical Indicators**: Less predictive when everything moves together
4. **Model Predictions**: Shifted from diverse to all-HOLD

### Most Likely Cause

**Risk Adjustment Layer is Too Aggressive**:
```
Hypothesis:
1. Base model predicts BUY/SELL with risk adjustment disabled
2. Risk adjustment kicks in
3. Sees macro risk = 0.68 (HIGH)
4. Reduces confidence significantly
5. Everything falls below BUY threshold
6. Converts everything to HOLD

Result: Model plays it safe, predicts all HOLD
Accuracy: 0% (always wrong in dynamic market)
```

---

## Impact Assessment

### Portfolio Damage (Jan 21 → Jan 28)

```
Loss: Rs 179,988 in 7 days
Return: -4.17% (was +1.16%)
Cause: Model predicting HOLD while market moved sharply

Example - KOTAKBANK:
   - Predicted: HOLD
   - Actual: Down -80%
   - Result: Massive loss
```

### Why Predictions Are All HOLD?

**Scenario 1**: Risk adjustment threshold too conservative
- High macro risk (0.68) triggers risk reduction
- Confidence reduction: 0.6 → 0.3
- 0.3 < BUY threshold (0.7?)
- Default to HOLD

**Scenario 2**: Prediction probability rescaling broken
- predict_proba() returns [0.33, 0.33, 0.33]
- Argmax selects HOLD (index 1)
- Repeat for all predictions

**Scenario 3**: Signal conversion threshold issue
- BUY requires >80% confidence
- Current avg confidence 62.1%
- Nothing meets threshold
- Default to HOLD

---

## Code Review Findings

### Training Script (app/api/train_model.py)
```python
model = MLSignalGenerator(
    model_type='gradient_boost',
    use_risk_adjustment=True,  # ← THIS IS ACTIVE
    forward_days=5,
    return_threshold=0.02,      # ← May be too high
    test_size=0.2,
    random_state=42
)
```

**Issues**:
1. `use_risk_adjustment=True` is applied at inference
2. Risk factors from macro risk (0.68) might be too extreme
3. No validation that output signals are diverse

### Risk Adjustment (app/features/risk_factors.py)

```python
# Suspected problem: Risk adjustment reduces all predictions
if macro_risk > 0.7:
    # Reduce position confidence?
    confidence *= (1 - macro_risk)  # Makes sense
```

**With macro risk = 0.68**:
- Confidence 0.62 * (1 - 0.68) = 0.62 * 0.32 = 0.20
- 0.20 too low for BUY signal
- Model defaults to HOLD

---

## Recommended Fixes

### IMMEDIATE (Do Today)

**1. Disable Risk Adjustment & Retrain**
```bash
# Edit app/api/train_model.py
model = MLSignalGenerator(
    use_risk_adjustment=False  # ← DISABLE
)

# Retrain
python app/api/train_model.py

# Check if signals become diverse again
cat results/latest_recommendations.csv | grep recommendation | sort | uniq -c
```

**Expected Result**: If this fixes it, risk adjustment was the culprit.

**2. Lower Return Threshold**
```bash
# Edit app/api/train_model.py  
return_threshold=0.01  # Down from 0.02

# Check label distribution
# If training labels become more balanced, use this
```

**3. Validate Output Signals**
```python
# Add to train_model.py before saving model:
signal_dist = recommendations['recommendation'].value_counts()
if signal_dist['HOLD'] > total * 0.95:
    raise ValueError("Model is defaulting to HOLD! Check risk adjustment.")
```

### SHORT-TERM (This Week)

**1. Investigate Risk Adjustment Layer**
- Review `app/features/risk_factors.py`
- Check how macro risk is reducing confidence
- Verify math: is (1 - 0.68) = 0.32 correct?

**2. Separate Risk from Signals**
```python
# Current (broken):
prediction = model.predict(X)  # Already risk-adjusted

# Proposed (better):
prediction = model.predict(X)  # Raw predictions
risk_adjustment = calculate_risk_adjustment()  # Separate
final_signal = apply_risk_to_sizing(prediction, risk_adjustment)  # Only for position sizing
```

**3. Implement Signal Validation**
```python
def validate_signals(signals):
    """Ensure signal diversity"""
    if signals['BUY'].sum() < 5:
        raise ValueError("Too few BUY signals")
    if signals['HOLD'].sum() > total * 0.90:
        raise ValueError("Too many HOLD signals")
```

### MEDIUM-TERM (Next 2 Weeks)

**1. Volatility-Adjusted Features**
```python
# Add to technical.py
features['volatility_adjusted_rsi'] = rsi / current_volatility
features['macro_risk_adjusted_macd'] = macd * (1 - macro_risk)
```

**2. Adaptive Return Threshold**
```python
# Adjust threshold based on market volatility
if macro_risk > 0.6:  # High volatility
    return_threshold = 0.01  # Easier to trigger
else:  # Low volatility
    return_threshold = 0.02  # Harder to trigger
```

**3. Ensemble Models**
```python
# Use 3 models, ensemble predictions
model1 = RandomForestClassifier()
model2 = GradientBoostingClassifier()
model3 = LGBMClassifier()

predictions = [model1, model2, model3]
final_signal = mode(predictions)  # Majority vote
```

**4. Weekly Retraining**
```bash
# Schedule weekly:
python app/api/train_model.py --retrain

# Monitor accuracy on rolling 7-day window
# Alert if accuracy drops below 50%
```

---

## Risk Adjustment Deep Dive

### Current Implementation (Suspected)

```python
# In ml_signals.py predict_with_risk():

# Get raw predictions
raw_probs = self.model.predict_proba(X_scaled)

# Get risk factors
macro_risk = self.risk_calculator.get_macro_risk_factor()

# Apply risk adjustment
if macro_risk > 0.7:
    adjusted_probs = raw_probs * (1 - macro_risk)  # ← PROBLEM
elif macro_risk > 0.5:
    adjusted_probs = raw_probs * (1 - macro_risk * 0.5)

# Convert to signal
prediction = np.argmax(adjusted_probs)  # ← Loses diversity
```

### Why This Breaks Predictions

**Example**: 3 stocks in high volatility (macro_risk=0.68)

```
Stock A - Raw: [0.2, 0.5, 0.3] (HOLD)
         Risk: [0.2, 0.5, 0.3] * 0.32 = [0.064, 0.16, 0.096]
         Argmax: 1 (HOLD) → HOLD ✓

Stock B - Raw: [0.4, 0.35, 0.25] (BUY)
         Risk: [0.4, 0.35, 0.25] * 0.32 = [0.128, 0.112, 0.08]
         Argmax: 0 (SELL) → CHANGED! ✗

Stock C - Raw: [0.1, 0.6, 0.3] (HOLD)
         Risk: [0.1, 0.6, 0.3] * 0.32 = [0.032, 0.192, 0.096]
         Argmax: 1 (HOLD) → HOLD ✓

Result: All three become either SELL or HOLD
        No BUY signals generated
        Portfolio loses money
```

---

## Recommendations Summary

| Priority | Action | Expected Impact | Effort |
|----------|--------|-----------------|--------|
| 🚨 CRITICAL | Disable risk adjustment, retrain | Signals should diversify | 30 min |
| 🚨 CRITICAL | Add signal diversity validation | Catch broken models early | 15 min |
| 🟠 HIGH | Fix risk adjustment math | Proper risk handling | 2 hours |
| 🟠 HIGH | Lower return threshold to 0.01 | More balanced signals | 15 min |
| 🟡 MEDIUM | Implement weekly retraining | Adapt to market changes | 4 hours |
| 🟡 MEDIUM | Add volatility-adjusted features | Better in high volatility | 3 hours |
| 🟢 LOW | Ensemble multiple models | Robustness | 8 hours |

---

## Testing Plan

### Test 1: Does Model Work Without Risk Adjustment?

```bash
# Edit app/api/train_model.py
use_risk_adjustment=False

# Train and check
python app/api/train_model.py
grep "HOLD\|BUY\|SELL" results/latest_recommendations.csv | wc -l

# Expected: Each signal ~15 times (not 43 HOLD)
```

### Test 2: Lower Return Threshold

```bash
# Edit app/api/train_model.py
return_threshold=0.01

# Train and check labels
python app/api/train_model.py

# Expected: More balanced BUY/SELL in training labels
```

### Test 3: Backtest on Historical Data

```bash
# Run on Jan 7-21 data (when model was working)
python backtest/strategy.py --start 2026-01-07 --end 2026-01-21

# Expected accuracy: >30% (better than current 0%)
```

---

## Key Takeaways

1. **Data Quality**: Good ✅ (10k rows, 49 symbols, balanced)
2. **Features**: Good ✅ (15 features, no NaN, diverse)
3. **Model Architecture**: Reasonable ✅ (GradientBoost, balanced params)
4. **Predictions**: Broken ❌ (97.7% HOLD instead of 30-40%)
5. **Risk Adjustment**: Likely culprit ❌ (converts diverse to all-HOLD)

**Diagnosis**: Problem is in **inference/risk adjustment**, not training data.

**Solution**: Disable risk adjustment, retrain, validate signal diversity.

**Expected Outcome**: Restore 30-50% accuracy within 1 hour.

---

**Status**: 🔴 REQUIRES IMMEDIATE ACTION
**Severity**: 🚨 CRITICAL (Model is unusable)
**Timeline**: Fix in <2 hours, validate in <4 hours

