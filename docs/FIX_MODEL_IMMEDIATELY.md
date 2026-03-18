# IMMEDIATE ACTION PLAN - FIX MODEL NOW
## January 29, 2026

---

## 🚨 CRITICAL ISSUE

**Model is predicting HOLD for 97.7% of stocks instead of diverse signals.**

**Root Cause**: Risk adjustment layer is reducing all predictions to HOLD.

**Impact**: Portfolio down -4.17% in 7 days, model accuracy 0%

**Time to Fix**: 30-60 minutes

---

## 🔧 FIX #1: DISABLE RISK ADJUSTMENT (5 minutes)

### Step 1: Edit train_model.py
File: `app/api/train_model.py` (Line ~120)

```python
# BEFORE:
model = MLSignalGenerator(
    model_type='gradient_boost', 
    use_risk_adjustment=True,  # ← PROBLEM
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=TradingConfig.RETURN_THRESHOLD_STRICT,
    test_size=TradingConfig.TEST_SIZE,
    random_state=TradingConfig.RANDOM_STATE
)

# AFTER:
model = MLSignalGenerator(
    model_type='gradient_boost', 
    use_risk_adjustment=False,  # ← DISABLED
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=TradingConfig.RETURN_THRESHOLD_STRICT,
    test_size=TradingConfig.TEST_SIZE,
    random_state=TradingConfig.RANDOM_STATE
)
```

### Step 2: Retrain the model
```bash
cd c:\Users\surya\OneDrive\Documents\github\NiftySIgnal
python app/api/train_model.py
```

### Step 3: Check if signals are now diverse
```bash
cat results/latest_recommendations.csv | grep recommendation | sort | uniq -c
```

Expected output:
```
     13 recommendation
     15 BUY
     16 HOLD
      8 SELL
     44 recommendation
```

(Not 43 HOLD, 1 SELL like now)

---

## 🔧 FIX #2: LOWER RETURN THRESHOLD (5 minutes)

If Fix #1 doesn't work:

### Step 1: Edit return threshold
File: `app/api/train_model.py` (Line ~120)

```python
# BEFORE:
return_threshold=TradingConfig.RETURN_THRESHOLD_STRICT  # Was 0.02 probably

# AFTER:
return_threshold=0.01  # Lower from 0.02 to 0.01
```

### Step 2: Retrain
```bash
python app/api/train_model.py
```

---

## 🧪 TEST #1: Verify Diverse Signals

After retraining, run:
```bash
python -c "
import pandas as pd
df = pd.read_csv('results/latest_recommendations.csv')
print(df['recommendation'].value_counts())
print('Total:', len(df))
"
```

✅ **PASS**: Each signal ~10-15 times each
❌ **FAIL**: Still 40+ HOLD signals → Fix #3

---

## 🔧 FIX #3: CHECK RISK ADJUSTMENT CODE (30 minutes)

If Fixes #1-2 don't work, risk adjustment is breaking inference.

### Step 1: Review risk adjustment
File: `app/features/risk_factors.py`

Look for function: `predict_with_risk()` or similar

### Step 2: Check for this pattern
```python
# PROBLEM PATTERN:
adjusted_probs = raw_probs * (1 - macro_risk)  # ← Multiplies by 0.32!

# This makes all probabilities very small
# [0.5, 0.3, 0.2] * 0.32 = [0.16, 0.096, 0.064]
# All equally small → Random/majority class picked
```

### Step 3: Fix the math
```python
# BETTER APPROACH:
adjusted_probs = raw_probs.copy()

# Only adjust confidence, not probability distribution
if macro_risk > 0.7:
    adjusted_probs = adjusted_probs * 0.8  # Reduce confidence to 80%
elif macro_risk > 0.5:
    adjusted_probs = adjusted_probs * 0.9  # Reduce confidence to 90%

# Keep highest probability signal, just with lower confidence
signal = np.argmax(adjusted_probs)  # Still gets BUY/SELL/HOLD
confidence = adjusted_probs[signal]  # Lower due to risk
```

### Step 4: Retrain and test
```bash
python app/api/train_model.py
cat results/latest_recommendations.csv | grep recommendation | sort | uniq -c
```

---

## 🧪 TEST #2: Backtest on Old Data

If signals are now diverse, test on historical data:

```bash
python backtest/strategy.py --start 2026-01-07 --end 2026-01-21
```

Expected: Accuracy should be 25-40% (not 0%)

---

## 🧪 TEST #3: Live Test on Jan 28 Data

Compare model predictions with actual Jan 28 outcomes:

```python
import pandas as pd

jan28 = pd.read_csv('results/accuracy_verification_jan28.csv')
print("\nSignal Accuracy Analysis:")
print(f"Total: {len(jan28)}")
print(f"Correct: {jan28['correct'].sum()}")
print(f"Accuracy: {jan28['correct'].mean():.1%}")

print("\nBy Signal Type:")
for rec in jan28['recommendation'].unique():
    subset = jan28[jan28['recommendation'] == rec]
    acc = subset['correct'].mean()
    print(f"  {rec}: {acc:.1%} ({subset['correct'].sum()}/{len(subset)})")
```

Expected: Accuracy > 0% (any improvement is progress)

---

## 📋 CHECKLIST

- [ ] **Step 1**: Disable risk adjustment in train_model.py
- [ ] **Step 2**: Run `python app/api/train_model.py`
- [ ] **Step 3**: Check signal distribution (should be diverse)
- [ ] **Step 4**: Run backtest on Jan 7-21 data
- [ ] **Step 5**: Verify accuracy improved (target: 25-40%)
- [ ] **Step 6**: If not improved, lower return_threshold to 0.01
- [ ] **Step 7**: Repeat steps 2-5
- [ ] **Step 8**: If still not working, investigate risk adjustment code

---

## ⏱️ TIMELINE

| Step | Time | Status |
|------|------|--------|
| 1. Disable risk adjustment | 5 min | TODO |
| 2. Retrain model | 2-3 min | TODO |
| 3. Check signal diversity | 1 min | TODO |
| 4. If needed: Lower threshold | 5 min | TODO |
| 5. Retrain again | 2-3 min | TODO |
| 6. Backtest | 5 min | TODO |
| **TOTAL** | **~30 min** | **TODO** |

---

## 🎯 SUCCESS CRITERIA

### ✅ Fix is successful if:
- [ ] Signal diversity: BUY 25-40%, HOLD 30-40%, SELL 20-30%
- [ ] Backtest accuracy: 25-40% (improvement from 0%)
- [ ] Jan 28 accuracy: > 10% (was 0%)
- [ ] Model generating different signals for different stocks

### ❌ Fix failed if:
- [ ] Still getting 90%+ HOLD signals
- [ ] Accuracy still 0%
- [ ] All stocks getting same signal

---

## 📞 IF YOU NEED HELP

**Problem**: Still getting all HOLD signals
**Solution**: 
1. Check `use_risk_adjustment=False` was applied
2. Check model file was saved (check timestamp)
3. Clear cache: `rm models/trading_model.pkl`
4. Retrain fresh

**Problem**: Accuracy still 0%
**Solution**:
1. Lower threshold further: `return_threshold=0.005`
2. Review risk adjustment code
3. Check training labels are diverse (25% SELL, 35% HOLD, 40% BUY)

**Problem**: Backtest accuracy worse than portfolio
**Solution**:
1. Portfolio tested on live market data
2. Backtest might be using different data
3. Both should show improvement after fix

---

## 🔍 VERIFICATION SCRIPT

Run this after each fix to track progress:

```bash
python -c "
import pandas as pd
import numpy as np

print('\n' + '='*60)
print('MODEL VERIFICATION')
print('='*60)

# Check latest recommendations
rec = pd.read_csv('results/latest_recommendations.csv')
print(f'\n📊 Signal Distribution:')
for sig in ['BUY', 'HOLD', 'SELL']:
    count = (rec['recommendation'] == sig).sum()
    pct = count / len(rec) * 100
    print(f'  {sig:6s}: {count:2d} ({pct:5.1f}%)')

# Check test data
try:
    test = pd.read_csv('results/accuracy_verification_jan28.csv')
    acc = test['correct'].mean()
    print(f'\n🎯 Jan 28 Accuracy: {acc:.1%} ({test[\"correct\"].sum()}/{len(test)})')
    
    if acc > 0.33:
        print('   ✅ IMPROVEMENT DETECTED!')
    elif acc > 0:
        print('   ✅ SLIGHT IMPROVEMENT')
    else:
        print('   ❌ STILL 0% - NEEDS MORE WORK')
except:
    print('\n⏳ Test data not available')

print('\n' + '='*60)
"
```

Run this command after each fix to see if it's working:
```bash
python -c "import pandas as pd; rec = pd.read_csv('results/latest_recommendations.csv'); print(rec['recommendation'].value_counts().to_dict())"
```

---

## 🚀 AFTER FIX IS SUCCESSFUL

1. **Monitor next 7 days**: Track Jan 29-Feb 4 accuracy
2. **Weekly retraining**: Run `python app/api/train_model.py` every Monday
3. **Implement safeguards**:
   - Check signal diversity before deploying
   - Alert if accuracy drops below 50%
   - Auto-rollback if model degrades

4. **Improve model**:
   - Add volatility-adjusted features
   - Implement ensemble methods
   - Daily model monitoring

---

**Status**: Ready to execute fixes
**Owner**: You
**Deadline**: Today (Jan 29)
**Escalation**: If issue not fixed in 1 hour, investigate risk adjustment code

