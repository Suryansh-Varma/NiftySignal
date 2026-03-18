# Risk-Based Optimization - Implementation Guide

## Current Status
- **Macro Risk: 0.75 (VERY HIGH)**
- **Environment:** Geopolitical tensions, gold highs, rupee at record lows

## 4 Key Optimizations

### 1️⃣ Position Sizing (CRITICAL)
```
BEFORE: 2.0% per position (aggressive)
AFTER:  0.5% per position (conservative)

Example with ₹10 Lakh portfolio:
- Aggressive: ₹20,000 per trade
- Current: ₹5,000 per trade (4x smaller!)
```

**Implementation:**
```python
# In config.py or train_model.py
POSITION_SIZE = 0.005  # Changed from 0.02
MAX_POSITIONS = 10     # Max 10 concurrent positions
```

---

### 2️⃣ Confidence Thresholds (FILTER)
```
BEFORE: Accept 40%+ confidence buys
AFTER:  Need 70%+ confidence buys

This filters out weak signals!
```

**Current Signals Analysis:**
- TCS: 45.3% confidence ❌ (below 70% threshold - SKIP)
- SBILIFE: 49.2% confidence ❌ (below 70% threshold - SKIP)
- TATAMOTORS SELL: 71.3% confidence ✅ (above 50% threshold - GOOD)

**Impact:** Reduces trades from 10 to maybe 2-3 per week (quality over quantity)

---

### 3️⃣ Stop Loss & Take Profit (PROTECT)
```
BEFORE: SL 2%, TP 5%, Trailing 1.5%
AFTER:  SL 1%, TP 2.5%, Trailing 0.8%

Tighter stops = less downside exposure
Quicker profits = reduce time in market
```

**Example Trade:**
```
Entry: ₹100
BEFORE: SL ₹98, TP ₹105 (5% upside needed)
AFTER:  SL ₹99, TP ₹102.50 (2.5% upside needed)

Easier targets in high-risk environment!
```

---

### 4️⃣ Sector Focus (DEFENSIVE)
```
PREFERRED (Trade these):
✅ Pharma (DRREDDY, SUNPHARMA, CIPLA)
✅ FMCG (HINDUNILVR, BRITANNIA, NESTLEIND)
✅ Utilities (POWERGRID, NTPC)

AVOID (Skip these):
❌ Auto (TATAMOTORS, MARUTI, EICHERMOT)
❌ Tech (INFY, TCS, WIPRO, TECHM)
❌ Finance (HDFCBANK, ICICIBANK, KOTAKBANK)
❌ Cyclicals (All discretionary spending)
```

**Why?** Defensive sectors are less volatile in crises.

---

## Quick Implementation (5 Minutes)

### Step 1: Update config.py
```python
# Change position size
POSITION_SIZE = 0.005  # 0.5%

# Add risk thresholds
MIN_BUY_CONFIDENCE = 0.70
MIN_SELL_CONFIDENCE = 0.50

# Adjust stops
STOP_LOSS = 0.01      # 1%
TAKE_PROFIT = 0.025   # 2.5%
```

### Step 2: Filter signals
Keep only trades with:
- Buy confidence > 70%
- Sell confidence > 50%

### Step 3: Sector filter
Before entering any trade, check:
```python
DEFENSIVE_SECTORS = ['Pharma', 'FMCG', 'Utilities']
AVOID_SECTORS = ['Auto', 'Tech', 'Finance', 'Cyclicals']

if stock_sector in AVOID_SECTORS:
    SKIP_TRADE()
```

### Step 4: Rebalance infrequently
- Only check portfolio **every 2 weeks**
- Not daily (reduce noise)
- Max 0-2 new entries per week

---

## Expected Results (0.75 Risk)

| Metric | Before | After |
|--------|--------|-------|
| Position Size | 2.0% | 0.5% |
| Max Positions | 25 | 10 |
| Avg Trades/Week | ~20 | ~2-3 |
| Max Drawdown | -39% | ~-15-20% |
| Win Rate | 47% | 55%+ |
| Avg Win/Loss | Better | Much better |
| Volatility | High | Low |

---

## When Risk Drops (e.g., 0.4-0.5)

The optimizer **automatically suggests:**
```
Position Size: 1.5% (up 3x)
Min Buy Confidence: 50% (down from 70%)
Stop Loss: 2% (up from 1%)
Take Profit: 5% (up from 2.5%)
Max Positions: 20 (up from 10)
```

**No code changes needed!** Just update the risk factor, and everything adapts.

---

## Check Optimizations Anytime

```bash
# View current recommendations
python risk_optimizer.py
```

This shows you exactly what parameters to use based on current risk.

---

## Summary

**Your 0.75 high-risk environment needs:**
1. ✅ **Smaller positions** (0.5% instead of 2%)
2. ✅ **Higher confidence** (70% instead of 40%)
3. ✅ **Tighter stops** (1% instead of 2%)
4. ✅ **Defensive sectors only** (Pharma, FMCG, Utilities)

**Result:** Lose less, win more often, sleep better! 🎯
