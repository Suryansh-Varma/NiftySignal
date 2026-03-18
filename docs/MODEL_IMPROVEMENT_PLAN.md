# Model Accuracy Improvement Plan

## Current Performance Analysis

### Issues Identified:
1. **Low Accuracy:** 33.3% (6/18 correct predictions)
2. **Risk Factor Mismatch:** Defensive sectors declined (-3.83%) while risky sectors gained (+4.80%) in 0.75 HIGH risk environment
3. **No Confidence Correlation:** High confidence (>70%) and low confidence (≤70%) both showed 33.3% accuracy
4. **Sector Misjudgment:** Pharma declined -10.48% when expected to be defensive
5. **Data Issues:** KOTAKBANK -80% (corporate action), TATAMOTORS delisted

---

## Improvement Strategies

### 1. Feature Engineering Enhancements
**Current Features:** 8 features (risk factors, MACD, RSI, returns)
**Proposed Additions:**
- Volume indicators (OBV, Volume Rate of Change)
- Momentum indicators (Stochastic, CCI)
- Volatility bands (Bollinger Bands)
- Moving average crossovers (50-day, 200-day)
- Sector relative strength
- Market breadth indicators
- Price patterns (higher highs, lower lows)

### 2. Risk Factor Calibration
**Current Issue:** 0.75 HIGH risk didn't predict sector performance correctly
**Improvements:**
- Add sector-specific risk weights
- Incorporate forward-looking indicators (earnings calendar, corporate actions)
- Add market sentiment (put/call ratio, VIX term structure)
- Include currency-specific risks for Indian market (INR, crude oil dependency)

### 3. Model Architecture Improvements
**Current:** Single Gradient Boost model
**Proposed:**
- Ensemble of models (GradientBoost + RandomForest + XGBoost)
- Sector-specific models (different models for Pharma, Auto, Tech, etc.)
- Time-based model selection (bull market model vs bear market model)
- Confidence calibration using Platt scaling

### 4. Training Data Improvements
**Current Issues:**
- 76.7 rows per symbol (limited history)
- May not capture recent market regime changes
**Improvements:**
- Expand to 200+ days of history per symbol
- Add more symbols to training universe (currently 27 stocks)
- Use sector rotation patterns
- Include market regime classification (trending vs ranging)

### 5. Signal Generation Logic
**Current:** Binary HOLD/SELL with confidence threshold
**Improvements:**
- Multi-class: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
- Dynamic confidence thresholds based on market conditions
- Add "uncertainty" signals when model confidence is low
- Implement signal filters (trend alignment, volume confirmation)

### 6. Backtesting Enhancements
**Current Issues:**
- 49.37% win rate
- May not account for transaction costs, slippage
**Improvements:**
- Walk-forward optimization
- Out-of-sample testing with hold-out data
- Monte Carlo simulation for robustness
- Include realistic transaction costs (0.1-0.2%)

### 7. Risk Management Updates
**Current:** Fixed position size (0.5%), stop loss (1%), take profit (2.5%)
**Improvements:**
- Dynamic position sizing based on:
  - Model confidence
  - Stock volatility
  - Sector allocation
  - Portfolio correlation
- Trailing stop loss adjustment
- Partial profit taking at milestones

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
✅ **1.1 Add More Technical Features**
- Volume indicators
- Bollinger Bands
- Moving average crossovers
- Expected Impact: +5-10% accuracy

✅ **1.2 Expand Training Data**
- Increase from 76 to 200+ days per symbol
- Add more stocks to universe
- Expected Impact: +10-15% accuracy

✅ **1.3 Sector-Specific Risk Factors**
- Calculate sector beta vs Nifty
- Add sector momentum score
- Expected Impact: +5% accuracy

### Phase 2: Model Improvements (3-5 days)
⏳ **2.1 Ensemble Models**
- Train RandomForest + XGBoost alongside GradientBoost
- Voting/stacking ensemble
- Expected Impact: +10-15% accuracy

⏳ **2.2 Hyperparameter Tuning**
- Grid search for optimal parameters
- Cross-validation
- Expected Impact: +5-10% accuracy

⏳ **2.3 Confidence Calibration**
- Implement Platt scaling
- Recalibrate thresholds
- Expected Impact: Better confidence correlation

### Phase 3: Advanced Features (1 week)
⏳ **3.1 Market Regime Detection**
- Bull/bear/sideways classification
- Different models for different regimes
- Expected Impact: +10% accuracy

⏳ **3.2 Sentiment Analysis**
- News sentiment scores
- Social media sentiment
- Expected Impact: +5-10% accuracy

⏳ **3.3 Sector Rotation Model**
- Predict which sectors will outperform
- Adjust allocations accordingly
- Expected Impact: +15% portfolio return

---

## Expected Outcomes

### After Phase 1 (Quick Wins):
- **Accuracy:** 33% → **50-55%**
- **Portfolio Return:** +1.16% → **+3-5%** (per week)
- **Confidence Correlation:** Improved from none to moderate

### After Phase 2 (Model Improvements):
- **Accuracy:** 50-55% → **65-70%**
- **Portfolio Return:** +3-5% → **+6-8%** (per week)
- **Win Rate:** 49% → **55-60%**

### After Phase 3 (Advanced Features):
- **Accuracy:** 65-70% → **75-80%**
- **Portfolio Return:** +6-8% → **+10-15%** (per week)
- **Sharpe Ratio:** Improve risk-adjusted returns

---

## Next Steps

1. **Immediate:** Implement Phase 1 improvements (add features + expand data)
2. **This Week:** Train new model and test on portfolio
3. **Next Week:** Implement Phase 2 (ensemble + tuning)
4. **Monitor:** Track accuracy over next 2-3 weeks

---

## Success Metrics

### Minimum Acceptable:
- Accuracy > 60%
- Positive weekly returns > 80% of weeks
- Sharpe Ratio > 1.5

### Target Performance:
- Accuracy > 70%
- Weekly return > 5%
- Sharpe Ratio > 2.0
- Max drawdown < 10%

### Stretch Goals:
- Accuracy > 80%
- Monthly return > 15%
- Sharpe Ratio > 3.0
- Consecutive losing weeks < 2
