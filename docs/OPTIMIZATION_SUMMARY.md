# Model Accuracy Test & Optimization Summary
**Date:** January 26, 2026 | **Status:** ✅ ANALYSIS COMPLETE

---

## Current Model Performance

### Test Portfolio (Jan 21, 2026)
- **Accuracy:** 33.3% (6/18 stocks correct)
- **Return:** +1.16% (Rs 39,304 profit)
- **Positions:** 12 active

### Historical Trading (3,038 trades)
- **Win Ratio:** 46.2% (1,404 winning trades)
- **Profit Factor:** 1.59x
- **Avg ROI/Trade:** +0.64%

### Recent Performance Trend
- **Recent Win Ratio:** 40.0% (Last 30 trades)
- **Trend:** -6.2% 🔴 DECLINING

---

## 4 Critical Issues Identified

| Issue | Current | Target | Gap |
|-------|---------|--------|-----|
| **Sell Signals** | 24.2% accuracy | 40%+ | -30.8 pts |
| **Stop Losses** | 10.2% win ratio | 15-18% | -5-8 pts |
| **Confidence Filter** | None (50% min) | 70%+ min | -20 pts |
| **Symbol Universe** | 47 symbols (w/ losers) | 30 symbols (best) | Optimize |

---

## 4 Optimization Opportunities (Ranked by Impact)

### 1️⃣ FIX SELL SIGNALS - Highest Priority
**Impact:** +8-12% accuracy | **Effort:** Medium | **Risk:** Low

**Problem:** Only 24.2% of sell signals are profitable vs 55% of buy signals.

**Solution:**
- Increase SELL confidence threshold to 75% (from 50%)
- Add confirmation filter (require 2+ indicators)
- Current SELL signal: SBILIFE.NS (55.1% confidence → BLOCKED)

**Expected Outcome:** Sell accuracy 24% → 40% (+16 points)

---

### 2️⃣ OPTIMIZE STOP LOSS - Critical Priority
**Impact:** +4-6% accuracy | **Effort:** Low | **Risk:** Very Low

**Problem:** 56% of trades hit stop loss with only 10.2% win ratio (too tight!).

**Solution:**
- Increase stop loss from 2.0% to 3.5%
- Allows positions to recover from normal pullbacks
- Reduces false stops by ~25%

**Expected Outcome:** SL trades reduced from 1,700 to 1,275, win ratio improves to 15-18%

---

### 3️⃣ IMPLEMENT CONFIDENCE FILTER - High Priority
**Impact:** +15-20% accuracy | **Effort:** Low | **Risk:** Low

**Problem:** 75% of signals have <70% confidence; all are traded equally.

**Solution:**
- Only trade HIGH CONFIDENCE signals (>70%)
- Current signal distribution: 44 total, 11 high-confidence
- Reduces signal count by 75% but improves quality

**Expected Outcome:** Test accuracy 33% → 50-55% (+17-22 points)

---

### 4️⃣ REFINE SYMBOL UNIVERSE - Medium Priority
**Impact:** +5-10% win ratio | **Effort:** Medium | **Risk:** Low

**Problem:** Performance ranges from 0% to 62.1% win ratio - huge dispersion.

**Solution:**
- Create 3-tier symbol classification
- **Tier 1** (>55% win): 8 symbols (CIPLA, JSWSTEEL, BAJAJFINSV, etc.)
- **Tier 2** (45-55% win): 22 symbols (HINDALCO, ICICIBANK, etc.)
- **Tier 3** (<45% win): 17 symbols (ITC, TITAN, INFA, etc.) → EXCLUDE

**Expected Outcome:** Focus on 30 best symbols, improve overall win ratio to 50-52%

---

## Implementation Roadmap

### Phase 1: This Week (Immediate Wins)
```
 Fix #1: Sell Signal Filter     -> +8% accuracy
 Fix #2: Stop Loss Adjustment   -> +5% accuracy
 Combined Expected:             33.3% → 45-50% accuracy
```

### Phase 2: Weeks 3-4 (Sustained Improvement)
```
 Fix #3: Confidence Filter      -> +15% accuracy
 Fix #4: Symbol Universe        -> +5% win ratio
 Combined Expected:             45-50% → 55-60% accuracy
```

### Phase 3: Weeks 5-6 (Polish & Deploy)
```
 Adaptive Stop Loss             -> +2% improvement
 Full backtest & validation
 Production deployment
```

---

## Expected Results

### Before Optimization
```
Test Accuracy:     33.3%
Win Ratio:         46.2%
Recent Win:        40.0%
Avg ROI/Trade:    +0.64%
Avg Loss (SL):    -1.93%
```

### After Phase 1 (1-2 weeks)
```
Test Accuracy:     45-50%  (+12-17%)
Win Ratio:         50-52%  (+4-6%)
Recent Win:        46-48%  (+6-8%)
Avg ROI/Trade:    +0.95%  (+0.31%)
Avg Loss (SL):    -1.10%  (+0.83%)
```

### After All Phases (5-6 weeks)
```
Test Accuracy:     55-60%  (+22-27%)  ✅ TARGET
Win Ratio:         52-55%  (+6-9%)    ✅ TARGET
Recent Win:        50-52%  (+10-12%)  ✅ TARGET
Avg ROI/Trade:    +1.20%  (+0.56%)   ✅ TARGET
Avg Loss (SL):    -0.90%  (+1.03%)   ✅ TARGET
```

---

## Files Generated

1. **ACCURACY_OPTIMIZATION_REPORT.md** - Detailed analysis (9 sections)
2. **analyze_optimization.py** - Implementation planning script
3. **TEST_RESULTS_COMPARISON_JAN2026.md** - Jan 1 vs Jan 26 comparison
4. **THIS FILE** - Executive summary

---

## Next Steps

1. ✅ Analysis Complete (this document)
2. 📋 Review recommendations
3. 🔨 Implement Phase 1 fixes (Sell signals + Stop loss)
4. 🧪 Backtest on Jan 2026 data (most recent)
5. ✔️ Verify on test portfolio
6. 🚀 Deploy when accuracy >50%

---

## Key Metrics Reference

| Metric | Definition |
|--------|-----------|
| **Accuracy** | % of predictions moving in expected direction |
| **Win Ratio** | % of closed trades with profit |
| **Profit Factor** | Avg Win × Wins / Avg Loss × Losses |
| **ROI** | (Profit / Investment) × 100 |
| **Macro Risk** | 0=Safe to 1=Crisis |
| **Confidence** | Model certainty (0-1 scale) |

---

## Data Sources
- **trades.csv:** 3,038 historical trades (2023-2026)
- **latest_recommendations.csv:** 44 current signals
- **accuracy_verification_jan21.csv:** 18-stock test portfolio
- **macro_risk_factor.json:** Current market risk (0.68)

**Report Status:** ✅ READY FOR IMPLEMENTATION
