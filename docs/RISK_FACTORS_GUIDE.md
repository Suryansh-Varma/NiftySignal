# Risk-Adjusted ML Trading Signals

## Overview

The enhanced ML Signal Generator now incorporates **risk factors** to improve trading signal quality and reduce false positives, especially for buy signals in volatile markets.

## Risk Factor Formulas

### 1. **Volatility Risk**
```
Volatility_Risk = σ(daily_returns) × √252

Where:
- σ = standard deviation of daily returns
- 252 = trading days per year
- Normalized to 0-1 scale
```
**Purpose**: Identifies stocks with high price fluctuations. Reduces buy signal confidence in volatile markets.

---

### 2. **Drawdown Risk**
```
Max_Drawdown_Risk = |min(Cumulative_Return - Running_Max) / Running_Max|

Where:
- Running_Max = peak cumulative return up to current date
- Measures the worst peak-to-trough decline
```
**Purpose**: Captures downside risk. High drawdown suggests elevated risk.

---

### 3. **Sharpe Ratio Risk** (Inverse)
```
Sharpe_Ratio = (E[R] - Rf) / σ(R)

Risk_Factor = 1 / (1 + e^(Sharpe_Ratio))  [Sigmoid normalization]

Where:
- E[R] = expected daily return
- Rf = risk-free rate (6% annually ≈ 0.024% daily)
- σ(R) = return volatility
```
**Purpose**: Inverse Sharpe ratio captures risk-adjusted performance. Low Sharpe = high risk.

---

### 4. **Beta Risk** (Market Sensitivity)
```
Beta = Cov(Stock_Returns, Market_Returns) / Var(Market_Returns)

Normalized_Beta = min(max(Beta / 3.0, 0), 1)

Where:
- Beta > 1: More volatile than market (higher risk)
- Beta < 1: Less volatile than market (lower risk)
```
**Purpose**: Measures stock sensitivity to market movements.

---

### 5. **Value at Risk (VaR)**
```
VaR_95 = Percentile(returns, 5%)

Risk_Factor = |VaR| / 0.5  [assuming VaR ranges from -50% to 0%]

Where:
- 95% confidence: worst expected loss 95% of the time
```
**Purpose**: Measures potential downside in stressed markets.

---

### 6. **Composite Risk Factor** (Weighted)
```
Risk_Factor_Composite = (
    0.40 × Volatility_Risk +
    0.30 × Drawdown_Risk +
    0.20 × Sharpe_Risk +
    0.10 × VaR_Risk
)

Final Risk Score: 0-1 scale
- 0 = Minimal risk
- 1 = Maximum risk
```

---

## Signal Adjustment Rules

### Buy Signals (Original Signal = 1)
```python
if Risk_Factor > 0.7:
    # High risk environment
    Adjusted_Signal = 0 (HOLD)  if Risk_Factor < 0.85
    Adjusted_Signal = -1 (SELL) if Risk_Factor ≥ 0.85

Adjusted_Confidence = Original_Confidence × (1 - 0.5 × Risk_Factor)
```
**Impact**: Buy signals are downgraded or converted to sells when market risk is elevated.

### Sell Signals (Original Signal = -1)
```python
if Risk_Factor > 0.7:
    # Increase conviction to exit in risky environments
    Adjusted_Confidence = Original_Confidence + 0.2 × Risk_Factor
```
**Impact**: Sell signals gain confidence during high-risk periods (good for risk management).

### Hold Signals (Original Signal = 0)
- No adjustment applied

---

## Usage Example

```python
from app.features.technical import prepare_features
from app.signals.ml_signals import MLSignalGenerator
from app.features.risk_factors import RiskFactorCalculator
import pandas as pd

# Load your data
df = pd.read_csv('universe_data.csv')

# Prepare features WITH risk factors
X, y = prepare_features(
    df,
    include_risk_factors=True  # Enable risk factors
)

# Initialize model with risk adjustment
model = MLSignalGenerator(
    model_type="random_forest",
    use_risk_adjustment=True  # Enable risk adjustment
)

# Train the model
train_metrics, test_metrics = model.fit(X, y)

# Generate predictions with risk adjustment
X_new = pd.read_csv('new_data.csv')
X_new_features, _ = prepare_features(X_new, include_risk_factors=True)

# Extract risk factors
risk_calc = RiskFactorCalculator()
risk_factors = []
for symbol in X_new_features['symbol'].unique():
    risk = risk_calc.calculate_composite_risk_factor(X_new, symbol)
    risk_factors.extend(risk.values)

# Get risk-adjusted predictions
predictions, confidences = model.predict_with_risk(
    X_new_features[model.feature_columns],
    risk_factors=np.array(risk_factors)
)
```

---

## Benefits

| Aspect | Without Risk | With Risk |
|--------|-------------|----------|
| **Buy Signal Reliability** | ❌ Lower | ✅ Higher |
| **False Positives in Volatile Markets** | ❌ More | ✅ Fewer |
| **Confidence Calibration** | ❌ Overconfident | ✅ Realistic |
| **Risk Management** | ❌ Passive | ✅ Active |
| **Sell Signal Conviction** | ❌ Same | ✅ Increased |

---

## Key Takeaways

1. **Risk factors normalize** all signals based on current market risk
2. **Buy signals** are penalized in volatile/risky markets
3. **Sell signals** gain strength when risk is high
4. **Confidence scores** become more realistic
5. **Overall portfolio risk** is reduced through risk-aware decision making

---

## Tuning Parameters

You can adjust the risk weighting formula in `risk_factors.py`:

```python
# Current weights (line ~180):
composite_risk = (
    0.40 * volatility_risk +      # Increase if volatility sensitive
    0.30 * drawdown_risk +        # Increase if drawdown-averse
    0.20 * sharpe_risk +          # Increase if quality-focused
    0.10 * var_risk               # Increase if tail-risk concerned
)

# Example: Conservative (drawdown-focused)
composite_risk = (
    0.25 * volatility_risk +
    0.50 * drawdown_risk +        # Higher weight
    0.15 * sharpe_risk +
    0.10 * var_risk
)
```

Also adjust signal adjustment thresholds:

```python
# Current: Buy downgraded if risk > 0.7
if risk_factor > 0.7:  # Change threshold (e.g., 0.6 for more conservative)
    ...
```
