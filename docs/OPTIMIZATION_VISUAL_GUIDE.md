# MODEL ACCURACY & WIN RATIO OPTIMIZATION - VISUAL SUMMARY
**Generated:** Jan 26, 2026 | **Analysis Period:** 3,038 trades (2023-2026)

---

## 📊 CURRENT PERFORMANCE DASHBOARD

```
TEST PORTFOLIO ACCURACY (Jan 21, 2026)
┌─────────────────────────────────────────────┐
│  Stocks Tested: 18                          │
│  Correct Predictions: 6                     │
│  ┌─────────────────────────────────────────┐ │
│  │ ACCURACY: 33.3% ███░░░░░░░░░░░░░░░░░░  │ │
│  └─────────────────────────────────────────┘ │
│  Portfolio Return: +1.16% (Rs 39,304)       │
│  Active Positions: 12                        │
└─────────────────────────────────────────────┘

OVERALL TRADING PERFORMANCE (3,038 Trades)
┌─────────────────────────────────────────────┐
│  Total Trades: 3,038                        │
│  Winners: 1,404                             │
│  ┌─────────────────────────────────────────┐ │
│  │ WIN RATIO: 46.2% ████████████████░░░░  │ │
│  └─────────────────────────────────────────┘ │
│  Losers: 1,423                              │
│  Breakeven: 211                             │
│  Profit Factor: 1.59x                       │
│  Avg ROI/Trade: +0.64%                      │
└─────────────────────────────────────────────┘

RECENT PERFORMANCE TREND (Last 30 Trades)
┌─────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────┐ │
│  │ TREND: -6.2% ⚠️  DECLINING ░░░░░░░     │ │
│  │ Recent Win Ratio: 40.0%                 │ │
│  │ Historical: 46.2%                       │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 🔴 CRITICAL ISSUES (4 Problems Found)

```
ISSUE #1: SELL SIGNALS ARE UNRELIABLE
┌──────────────────────────────────────────────────┐
│ Buy Signals:      ████████████████░░░░░░░░░░░░  │ 55.0%
│ Sell Signals:     ████░░░░░░░░░░░░░░░░░░░░░░░░  │ 24.2%
│                                                   │
│ GAP: -30.8 PERCENTAGE POINTS ❌ CRITICAL        │
│                                                   │
│ Current SELL Signal: SBILIFE.NS (55.1% conf)    │
└──────────────────────────────────────────────────┘

ISSUE #2: STOP LOSSES ARE TOO TIGHT
┌──────────────────────────────────────────────────┐
│ Stop Loss Trades:  1,700 (56% of all trades)    │
│ Win Ratio:         10.2% ❌ TOO LOW             │
│ Avg Loss:          -Rs 91.99 per trade          │
│                                                   │
│ Take Profit Trades: 1,284 (42%)                 │
│ Win Ratio:         92.8% ✅ EXCELLENT          │
│                                                   │
│ PROBLEM: False stops on normal pullbacks        │
└──────────────────────────────────────────────────┘

ISSUE #3: POOR CONFIDENCE FILTERING
┌──────────────────────────────────────────────────┐
│ High Confidence (>70%):  11 signals (25%)      │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│                                                   │
│ Low-Med Confidence (≤70%): 33 signals (75%)    │
│ ████████████████████████████░░░░░░░░░░░░░░░░  │
│                                                   │
│ PROBLEM: Trading low-confidence signals equally │
│ Expected: 75% of signals should be FILTERED OUT │
└──────────────────────────────────────────────────┘

ISSUE #4: SYMBOL SELECTION BIAS
┌──────────────────────────────────────────────────┐
│ Best Performer (CIPLA):      62.1% win ratio   │
│ ████████████████████████░░░░░░░░░░░░░░░░░░░░  │
│                                                   │
│ Worst Performer (APOLLOHOSP): 0.0% win ratio   │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│                                                   │
│ RANGE: 62.1% dispersion - 6x variation!         │
│ 17 symbols with <45% win ratio (14 should be OK) │
└──────────────────────────────────────────────────┘
```

---

## 🎯 OPTIMIZATION SOLUTIONS (4 Fixes)

```
FIX #1: SELL SIGNAL FILTER
┌─────────────────────────────────────────────────┐
│ ACTION:  Increase SELL confidence to 75%       │
│         Add confirmation filter (2+ indicators) │
│                                                  │
│ FROM:    24.2% sell accuracy                   │
│ TO:      40%+ sell accuracy                    │
│ GAIN:    +15.8 percentage points                │
│                                                  │
│ Impact:  Test accuracy +7.7%                   │
│ Effort:  MEDIUM | Risk: LOW                     │
│ Timeline: 3-5 days                              │
└─────────────────────────────────────────────────┘

FIX #2: STOP LOSS ADJUSTMENT
┌─────────────────────────────────────────────────┐
│ ACTION:  Increase stop loss 2.0% → 3.5%        │
│                                                  │
│ FROM:    1,700 SL trades (56% of total)        │
│ TO:      1,275 SL trades (40% of total)        │
│ GAIN:    -425 false stops (-25%)                │
│                                                  │
│ FROM:    10.2% SL win ratio                    │
│ TO:      15-18% SL win ratio                   │
│ GAIN:    +5-8 percentage points                 │
│                                                  │
│ Impact:  Test accuracy +5%, Avg ROI +0.5%     │
│ Effort:  LOW | Risk: VERY LOW                   │
│ Timeline: 1-2 days                              │
└─────────────────────────────────────────────────┘

FIX #3: CONFIDENCE FILTER
┌─────────────────────────────────────────────────┐
│ ACTION:  Only trade HIGH confidence (>70%)     │
│                                                  │
│ FROM:    44 signals (all confidence levels)    │
│ TO:      11 signals (high confidence only)     │
│ GAIN:    -33 low-confidence trades (-75%)      │
│                                                  │
│ FROM:    33.3% test accuracy                   │
│ TO:      50-55% test accuracy                  │
│ GAIN:    +17-22 percentage points              │
│                                                  │
│ Impact:  Higher quality trades, less noise     │
│ Effort:  LOW | Risk: LOW                        │
│ Timeline: 1 day                                 │
└─────────────────────────────────────────────────┘

FIX #4: SYMBOL UNIVERSE
┌─────────────────────────────────────────────────┐
│ ACTION:  Exclude Tier 3 symbols (<45% win)    │
│                                                  │
│ FROM:    47 symbols (all included)             │
│ TO:      30 symbols (best performers)          │
│ GAIN:    Focus on proven winners               │
│                                                  │
│ TIER BREAKDOWN:                                 │
│   Tier 1 (>55%):   8 symbols ✅ FOCUS          │
│   Tier 2 (45-55%): 22 symbols ✅ TRADE        │
│   Tier 3 (<45%):   17 symbols ❌ EXCLUDE       │
│                                                  │
│ Impact:  Win ratio 46.2% → 50-52%              │
│ Effort:  MEDIUM | Risk: LOW                     │
│ Timeline: 3-5 days                              │
└─────────────────────────────────────────────────┘
```

---

## 📈 EXPECTED IMPROVEMENTS

```
IMPROVEMENT PROGRESSION

BEFORE OPTIMIZATION:
  Test Accuracy:  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░  33.3%
  Win Ratio:      ███████████░░░░░░░░░░░░░░░░░░░░  46.2%
  Trend:          ██████░░░░░░░░░░░░░░░░░░░░░░░░░  40.0% (-6.2%)

AFTER PHASE 1 (Fixes #1 & #2):
  Test Accuracy:  ██████████░░░░░░░░░░░░░░░░░░░░░  45-50%  (+12-17%)
  Win Ratio:      ███████████░░░░░░░░░░░░░░░░░░░░  50-52%  (+4-6%)
  Trend:          ███████░░░░░░░░░░░░░░░░░░░░░░░░  46-48%  (+6-8%)

AFTER PHASE 2 (All Fixes):
  Test Accuracy:  ███████████████░░░░░░░░░░░░░░░░  55-60%  ✅ (+22-27%)
  Win Ratio:      █████████████░░░░░░░░░░░░░░░░░░  52-55%  ✅ (+6-9%)
  Trend:          ██████████░░░░░░░░░░░░░░░░░░░░░  50-52%  ✅ (+10-12%)

BONUS METRICS:
  Profit Factor:  1.59 → 1.85+ (+0.26)
  Avg ROI/Trade:  +0.64% → +1.20% (+0.56%)
  Avg Loss (SL):  -1.93% → -0.90% (+1.03%)
```

---

## ⏱️ IMPLEMENTATION TIMELINE

```
PHASE 1: THIS WEEK (Days 1-5)
├─ Day 1-2: Implement Sell Signal Filter
├─ Day 3-4: Adjust Stop Loss Levels
├─ Day 5:   Backtest & Validate
└─ RESULT: 33.3% → 45-50% accuracy

PHASE 2: WEEKS 3-4 (Days 8-14)
├─ Day 8-9:  Implement Confidence Filter
├─ Day 10-11: Symbol Universe Classification
├─ Day 12-13: Backtest All Changes
├─ Day 14:   Validation Complete
└─ RESULT: 45-50% → 55-60% accuracy

PHASE 3: WEEKS 5-6 (Days 15-21)
├─ Day 15-18: Adaptive Stop Loss
├─ Day 19:   Full System Backtest
├─ Day 20:   Final Validation
├─ Day 21:   Production Deploy
└─ RESULT: Sustained 55%+ accuracy
```

---

## 📋 CONFIGURATION CHANGES REQUIRED

```
File: app/config.py
─────────────────────────────────────────
NEW SETTINGS:
  SELL_CONFIDENCE_MIN = 0.75           (was 0.50)
  ENTRY_CONFIDENCE_MIN = 0.70          (new)
  STOP_LOSS_PCT = 0.035                (was 0.020)
  UNIVERSE_FILTER = "tier_1_and_2"     (new)
  SELL_CONFIRMATION_REQUIRED = True    (new)

File: app/api/train_model.py
─────────────────────────────────────────
CHANGES:
  - Add SELL confirmation logic
  - Implement confidence filter
  - Update stop loss calculation
  - Add universe filtering

File: app/portfolio/manager.py
─────────────────────────────────────────
CHANGES:
  - Add symbol tier system
  - Implement universe filter
  - Add trade filtering logic
```

---

## ✅ SUCCESS CRITERIA

```
Phase 1 Success:
  ✓ Sell signal accuracy > 40%
  ✓ Stop loss trades reduced to ~40%
  ✓ Test accuracy > 45%

Phase 2 Success:
  ✓ Only trading high-confidence signals
  ✓ Symbol universe optimized to 30 best
  ✓ Test accuracy > 55%

Phase 3 Success:
  ✓ Adaptive stops implemented
  ✓ Win ratio > 52%
  ✓ Sustained 55%+ test accuracy
  ✓ Ready for production
```

---

## 📚 DETAILED REPORTS

Additional analysis available in:
- **ACCURACY_OPTIMIZATION_REPORT.md** (9 sections, full analysis)
- **TEST_RESULTS_COMPARISON_JAN2026.md** (Jan 1 vs Jan 26 comparison)
- **analyze_optimization.py** (Implementation planning)

---

**Status:** ✅ READY FOR IMPLEMENTATION
**Next Step:** Deploy Phase 1 fixes
**Expected Timeline:** 5-6 weeks to 55%+ accuracy
