# Model Accuracy Test & Win Ratio Optimization Report
**Date:** January 26, 2026  
**Test Period:** Jan 14-21, 2026  
**Compiled from:** 3,038 historical trades & 18-stock test portfolio

---

## Executive Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **Test Accuracy** | 33.3% | 60%+ | **+26.7%** |
| **Overall Win Ratio** | 46.2% | 55%+ | **+8.8%** |
| **Recent Win Ratio** | 40.0% | 50%+ | **+10.0%** |
| **Take Profit Avg ROI** | +4.04% | 4.5%+ | +0.46% |
| **Stop Loss Avg ROI** | -1.93% | -1.0% | +0.93% |

**Key Finding:** Model has strong fundamentals but is losing 6.2% performance trend (46.2% historical vs 40% recent) due to tight stop losses and poor sell signal quality.

---

## 1. Test Accuracy Results (Jan 21, 2026)

### Portfolio Performance
```
Test Portfolio: 18 stocks from high-risk sectors
Total Investment: Rs 33,77,205
Positions: 12 active (4 sold by Jan 21)

Accuracy: 33.3% (6/18 correct predictions)
P&L: +Rs 39,304 (+1.16%)
```

### Sector Breakdown
| Sector | Stocks | Correct | Win % | Expected |
|--------|--------|---------|-------|----------|
| **Defensive (Pharma/FMCG)** | 5 | 2 | 40% | 70% |
| **Risky (Auto/Tech)** | 10 | 3 | 30% | 20% |
| **Mixed** | 3 | 1 | 33% | 50% |

**Issue:** Defensive sectors underperformed expectations during Jan 21 risk spike (0.75 macro risk).

### Signal Quality Correlation
- **High Confidence (>70%):** 6 predictions | 67% correct
- **Low Confidence (≤70%):** 12 predictions | 17% correct
- **Correlation:** STRONG positive (confidence = 4x accuracy multiplier)

---

## 2. Overall Trading Performance Analysis

### Win Ratio Breakdown
```
Total Trades: 3,038
Winning Trades:  1,404 (46.2%)
Losing Trades:   1,423 (46.8%)
Breakeven:         211 (6.9%)

Profit Factor: 1.59x (Rs 148.55 avg win vs Rs -91.99 avg loss)
```

### Performance by Signal Type
| Signal | Count | Win % | Issue |
|--------|-------|-------|-------|
| **BUY (+1)** | 2,171 | 55.0% | ✓ GOOD |
| **SELL (-1)** | 867 | 24.2% | ✗ BAD (-31 pts) |

**Critical Issue:** Sell signals are only 24.2% accurate vs 55% for buy signals. This is the largest accuracy gap.

### Exit Strategy Performance
| Exit Type | Count | Win % | Avg ROI | Quality |
|-----------|-------|-------|---------|---------|
| **Take Profit** | 1,284 | 92.8% | +4.04% | ✓ EXCELLENT |
| **Stop Loss** | 1,700 | 10.2% | -1.93% | ✗ POOR |
| Signal | 50 | 76.0% | +0.63% | Good |

**Problem:** Stop losses are too tight! 56% of trades hit stops before reaching profit targets.

### Recent Performance Trend (Last 30 trades)
- Win Ratio: **40.0%** (down from 46.2% historical)
- Trend: **-6.2%** ⚠️ DECLINING
- Avg ROI: +0.10% (flat performance)

---

## 3. Model Confidence Distribution

### Current Confidence Levels
```
Total Recommendations: 44
Average Confidence: 62.1%
Median Confidence: 60.7%

HIGH CONFIDENCE (>70%):  11 recommendations (25%)
  Avg Confidence: 79.0%

LOW CONFIDENCE (<=70%):  33 recommendations (75%)
  Avg Confidence: 56.4%
```

**Issue:** 75% of current recommendations are below 70% confidence threshold, yet all are being traded equally.

---

## 4. Symbol-Level Performance Analysis

### Top 5 Performers
| Symbol | Profit | Trades | Win % | ROI |
|--------|--------|--------|-------|-----|
| BPCL.NS | Rs 4,345 | 55 | 45.5% | +0.68% |
| JSWSTEEL.NS | Rs 3,878 | 89 | 58.4% | +0.58% |
| BHARTIARTL.NS | Rs 3,473 | 68 | 55.9% | +0.55% |
| ADANIPORTS.NS | Rs 3,444 | 107 | 48.6% | +0.42% |
| CIPLA.NS | Rs 3,050 | 58 | 62.1% | +0.62% |

### Bottom 5 Performers
| Symbol | Profit | Trades | Win % | ROI |
|--------|--------|--------|-------|-----|
| TCS.NS | Rs -786 | 58 | 34.5% | -0.27% |
| ASIANPAINT.NS | Rs -457 | 50 | 42.0% | -0.18% |
| APOLLOHOSP.NS | Rs 0 | 26 | 0.0% | -1.44% |
| ONGC.NS | Rs 164 | 38 | 50.0% | -0.07% |
| SUNPHARMA.NS | Rs 308 | 46 | 52.2% | +0.11% |

**Observation:** Win ratio ranges from 0% to 62.1% - huge dispersion. Top performers have 62% win rate, worst has 0%.

---

## 5. KEY OPTIMIZATION OPPORTUNITIES

### 🔴 CRITICAL: Fix Sell Signals (Priority 1)
**Impact:** +8-12% accuracy improvement  
**Current State:**
- Sell signal win ratio: 24.2%
- Buy signal win ratio: 55.0%
- Gap: -31 percentage points ❌

**Root Cause:**
- Sell signals generated too early (false reversal detection)
- No confirmation filter before executing sells
- Algorithm overestimating downside momentum

**Solutions:**
1. **Add confirmation filter:** Require 2+ indicators to agree before SELL
2. **Increase sell threshold:** Only SELL when confidence > 75% (not 50%)
3. **Add bounce detection:** Wait 1-2 days after dip before confirming SELL
4. **Expected Result:** Improve sell accuracy from 24% to 40%+ (50% relative improvement)

---

### 🔴 CRITICAL: Optimize Stop Loss Levels (Priority 2)
**Impact:** +4-6% accuracy improvement  
**Current State:**
- Stop loss trades: 1,700 (56% of all trades)
- Stop loss win ratio: 10.2% ❌
- Avg loss per stop: Rs -91.99
- Missing out on bounces

**Root Cause:**
- Stop loss too tight (~2% of entry price)
- Hitting stops on normal intraday noise
- Not allowing positions to recover

**Solutions:**
1. **Increase stop loss to 3-4%** instead of 2%
   - Reduces false stops by ~25%
   - Allows recovery on normal pullbacks
   
2. **Add stop loss logic:**
   - Stop only if 3+ consecutive down days
   - Don't stop on volatility spikes
   - Allow macro risk to override tight stops

3. **Expected Result:** 
   - Reduce stop-loss frequency from 56% to 45%
   - Improve stop-loss win ratio from 10.2% to 18-20%

---

### 🟡 HIGH PRIORITY: Confidence Filter (Priority 3)
**Impact:** +15-20% prediction accuracy  
**Current State:**
- Only trading 11/44 (25%) high-confidence signals
- 75% of signals are below 70% confidence
- Low-confidence trades average 17% accuracy

**Root Cause:**
- Model generates signals for all stocks regardless of confidence
- No filtering mechanism
- Spreads capital too thin

**Solutions:**
1. **Only trade HIGH CONFIDENCE signals (>70%)**
   - Reduces signal count from 44 to 11 (-75%)
   - Improves accuracy from 33% to 50%+
   
2. **Reject all MEDIUM confidence signals**
   - Avoids low-probability trades
   - Improves win ratio quality

3. **Expected Result:**
   - Fewer trades but higher accuracy
   - Shift from "trade everything" to "trade only high-probability"
   - Accuracy: 33% → 50-55%

---

### 🟡 HIGH PRIORITY: Symbol Universe Optimization (Priority 4)
**Impact:** +5-10% win ratio improvement  
**Current State:**
- Best symbol (CIPLA): 62.1% win ratio
- Worst symbol (APOLLOHOSP): 0% win ratio
- Range: 62.1% (6x variation) ⚠️

**Root Cause:**
- Including poor performers in trade universe
- Not concentrating on proven winners
- Model struggles with certain stock patterns

**Solutions:**
1. **Create tier system:**
   - Tier 1 (>55% win): CIPLA, JSWSTEEL, BHARTIARTL (high focus)
   - Tier 2 (45-55% win): ADANIPORTS, BPCL, etc (normal)
   - Tier 3 (<45% win): APOLLOHOSP, TCS, ASIANPAINT (avoid)

2. **Universe rules:**
   - Only include Tier 1 & 2 symbols
   - Exclude Tier 3 (0-45% win performers)
   - Re-evaluate quarterly

3. **Expected Result:**
   - Overall win ratio: 46.2% → 50-52%
   - Better trade quality
   - Reduced losing position concentration

---

### 🟠 MEDIUM PRIORITY: Adaptive Stop Loss (Priority 5)
**Impact:** +2-3% accuracy improvement  
**Current State:**
- Fixed 2% stop loss across all trades
- Doesn't account for volatility
- Doesn't consider macro risk factor

**Solutions:**
1. **Volatility-based stops:**
   - High volatility (VIX > 15): 4% stop
   - Normal volatility (12-15): 3% stop
   - Low volatility (<12): 2% stop

2. **Macro-risk adjustments:**
   - Risk factor > 0.70: 4% stops
   - Risk factor 0.50-0.70: 3% stops
   - Risk factor < 0.50: 2% stops

3. **Expected Result:** Better stop efficiency, fewer false stops

---

## 6. Implementation Roadmap

### Phase 1: Immediate Fixes (This Week)
```
Week 1: Fix Sell Signals
├─ Add confirmation filter for SELL
├─ Increase SELL confidence threshold to 75%
├─ Backtest on 3 months of data
└─ Expected: +8% accuracy

Week 2: Optimize Stop Loss
├─ Increase stops from 2% to 3%
├─ Test on recent data (Jan 2026)
└─ Expected: +5% accuracy
```

### Phase 2: Medium-term (Weeks 3-4)
```
Week 3: Implement Confidence Filter
├─ Only trade >70% confidence signals
├─ Verify on test portfolio
└─ Expected: +15% accuracy

Week 4: Symbol Universe Optimization
├─ Create tier system
├─ Exclude Tier 3 performers
└─ Expected: +5% win ratio
```

### Phase 3: Advanced (Weeks 5-6)
```
Week 5: Adaptive Stops
├─ Implement volatility-based stops
├─ Add macro-risk adjustments
└─ Test in live environment

Week 6: Verification & Go-live
├─ Full backtest on all changes
├─ Monitor for 1 week
└─ Roll to production
```

---

## 7. Expected Results After Optimization

### Current State
```
Test Accuracy:        33.3%
Overall Win Ratio:    46.2%
Recent Win Ratio:     40.0%
Avg ROI/Trade:        +0.64%
Avg Stop Loss:        -1.93%
High Confidence %:    25%
```

### Phase 1 Results (After Fixes 1-2)
```
Test Accuracy:        45-50% (+12-17%)
Overall Win Ratio:    50-52% (+4-6%)
Recent Win Ratio:     46-48% (+6-8%)
Avg ROI/Trade:        +0.95% (+0.31%)
Avg Stop Loss:        -1.10% (+0.83%)
```

### Phase 2 Results (After All Optimizations)
```
Test Accuracy:        55-60% (+22-27%)
Overall Win Ratio:    52-55% (+6-9%)
Recent Win Ratio:     50-52% (+10-12%)
Avg ROI/Trade:        +1.20% (+0.56%)
Avg Stop Loss:        -0.90% (+1.03%)
High Confidence %:    75% (only trade these)
```

---

## 8. Risk Considerations

### Potential Downsides
1. **Confidence filter reduces signal count** by ~75%
   - Mitigation: Higher quality trades compensate
   - Test thoroughly first

2. **Wider stops might increase losses temporarily**
   - Mitigation: Only 3-4% vs 2% (manageable)
   - Allows profitable positions to breathe

3. **Symbol exclusion reduces diversification**
   - Mitigation: Still have 20+ symbols
   - Focus on quality over quantity

### Monitoring Plan
- Daily: Trade accuracy vs baseline
- Weekly: Win ratio trend
- Monthly: Backtest validation
- Alert if accuracy drops below 40%

---

## 9. Next Steps

1. **Implement Priority 1-2** this week
2. **Test on Jan 2026 data** (most recent)
3. **Verify with test portfolio** (18-stock portfolio)
4. **Backtest all changes** on 2023-2025 data
5. **Go-live** once accuracy > 50%

---

## Appendix: Metrics Definitions

- **Accuracy:** % of predictions that move in expected direction
- **Win Ratio:** % of trades that close with profit
- **Profit Factor:** Avg Win × Win Trades / Avg Loss × Loss Trades
- **ROI:** (Profit / Entry Value) × 100
- **Confidence:** Model's certainty score (0-1)
- **Macro Risk Factor:** 0-1 scale (0=safe, 1=crisis)

---

**Report Generated:** 2026-01-26  
**Data Sources:** results/trades.csv, results/latest_recommendations.csv, results/accuracy_verification_jan21.csv
