# Macroeconomic & Geopolitical Risk Factor

## Overview

The system now includes a **manually updated macroeconomic/geopolitical risk factor** that incorporates global market conditions into trading decisions. This factor considers:

- **Federal Reserve Interest Rates (FD Rate)**: Higher rates typically increase market risk
- **Gold Prices**: Rising gold often signals flight to safety (higher risk)
- **Geopolitical Events**: Wars, tensions, political instability
- **VIX (Market Volatility)**: The "fear index" - measures market uncertainty
- **Oil Prices**: Extreme volatility in energy markets
- **Currency Volatility**: Foreign exchange instability

## How It Works

### Integration into Risk System

The macro risk factor is integrated into the composite risk calculation with a **20% weight**:

```python
composite_risk = (
    0.30 * volatility_risk +      # Stock-specific volatility
    0.25 * drawdown_risk +         # Stock-specific drawdown
    0.15 * sharpe_risk +           # Stock-specific risk-adjusted return
    0.10 * var_risk +              # Stock-specific Value at Risk
    0.20 * macro_risk              # GLOBAL macro/geopolitical risk
)
```

This means that even if individual stocks look good, high global risk will reduce position sizes and adjust signals accordingly.

### Storage

The macro risk factor is stored in: `data/macro_risk_factor.json`

Example structure:
```json
{
  "risk_factor": 0.65,
  "last_updated": "2026-01-21T10:30:00",
  "notes": "Fed rate hike expected, geopolitical tensions in Middle East",
  "factors": {
    "fed_rate": 5.5,
    "gold_price": 2100,
    "geopolitical_score": 0.7,
    "vix": 22.5,
    "oil_price": 88.0,
    "currency_volatility": 0.6
  }
}
```

## Usage

### 1. View Current Risk Factor

```bash
python -m app.scripts.update_macro_risk --view
```

Output:
```
============================================================
CURRENT MACRO RISK FACTOR
============================================================
Risk Factor: 0.65
Last Updated: 2026-01-21T10:30:00
Notes: Fed rate hike expected, geopolitical tensions
Contributing Factors:
  - fed_rate: 5.5
  - gold_price: 2100
  - vix: 22.5
============================================================
```

### 2. Interactive Mode (Recommended)

```bash
python -m app.scripts.update_macro_risk --interactive
```

The script will guide you through assessing each factor:

```
============================================================
MACROECONOMIC & GEOPOLITICAL RISK ASSESSMENT
============================================================

1. Federal Reserve Interest Rate:
   Current rate: 5.5
   Risk level (0-1, higher rate = higher risk): 0.7

2. Gold Price (USD/oz):
   Current price: 2100
   Risk level (0-1, rising gold = higher risk): 0.6

3. Geopolitical Tensions:
   Rate geopolitical risk (0=peaceful, 1=extreme tension): 0.7

4. Market Volatility (VIX):
   Current VIX level: 22.5

5. Oil Price (USD/barrel):
   Current price: 88
   Risk level (0-1, extreme prices = higher risk): 0.5

6. Currency Volatility:
   Rate currency risk (0=stable, 1=extreme volatility): 0.6

------------------------------------------------------------
CALCULATED OVERALL RISK: 0.64
------------------------------------------------------------
```

### 3. Command-Line Mode

```bash
python -m app.scripts.update_macro_risk \
    --risk 0.65 \
    --notes "Fed hiking, geopolitical tensions" \
    --fed-rate 5.5 \
    --gold-price 2100 \
    --vix 22.5 \
    --oil-price 88
```

### 4. Quick Update

```bash
python -m app.scripts.update_macro_risk --risk 0.7 --notes "High uncertainty"
```

## Risk Factor Scale

| Value | Label | Interpretation |
|-------|-------|----------------|
| 0.0 - 0.2 | Very Low Risk | Bullish market conditions, low volatility, stable geopolitics |
| 0.2 - 0.4 | Low Risk | Generally favorable conditions with minor concerns |
| 0.4 - 0.6 | Moderate Risk | Neutral conditions, some uncertainty |
| 0.6 - 0.8 | High Risk | Elevated uncertainty, significant market concerns |
| 0.8 - 1.0 | Very High Risk | Extreme uncertainty, crisis conditions |

## Impact on Trading

### Buy Signals
- **Low macro risk (< 0.4)**: Full position sizes, high confidence
- **Moderate macro risk (0.4-0.6)**: Reduced position sizes
- **High macro risk (> 0.6)**: Conservative positions, may skip volatile stocks
- **Very high macro risk (> 0.8)**: Minimal new positions, focus on defensive stocks

### Sell Signals
- High macro risk **increases** sell signal confidence
- System becomes more defensive in uncertain conditions

## When to Update

### Regular Updates
- **Weekly**: During normal market conditions
- **Daily**: During volatile periods or major events

### Event-Driven Updates
1. **Federal Reserve Announcements**
   - Rate decisions
   - Policy changes
   - Economic projections

2. **Geopolitical Events**
   - Wars or conflicts
   - Trade disputes
   - Political instability
   - Sanctions

3. **Economic Indicators**
   - GDP reports
   - Unemployment data
   - Inflation reports

4. **Market Events**
   - Sharp VIX spikes
   - Currency crises
   - Commodity shocks
   - Banking system stress

## AI-Assisted Updates

You can use AI to help assess the current macro environment:

### Prompt Template

```
Analyze the current macroeconomic and geopolitical risk environment 
for equity trading. Consider:

1. Federal Reserve rate (current: 5.5%)
2. Gold prices (current: $2,100/oz)
3. VIX level (current: 22.5)
4. Oil prices (current: $88/barrel)
5. Geopolitical tensions
6. Currency market stability

Provide a risk score from 0 (low risk) to 1 (high risk) and explain 
the key factors driving the assessment.
```

### Using the Assessment

1. Get AI analysis of current conditions
2. Extract risk scores for each factor
3. Run the update script in interactive mode
4. Input the AI-provided values

## Example Scenarios

### Scenario 1: Bull Market
```
Risk Factor: 0.25 (Low Risk)
Notes: Strong economy, low volatility, stable geopolitics
Factors:
  - fed_rate: 3.5
  - vix: 12
  - geopolitical_score: 0.2
```
**Effect**: System trades aggressively, takes larger positions

### Scenario 2: Uncertain Times
```
Risk Factor: 0.65 (High Risk)
Notes: Fed hiking cycle, Middle East tensions, rising gold
Factors:
  - fed_rate: 5.5
  - gold_price: 2150
  - vix: 25
  - geopolitical_score: 0.7
```
**Effect**: System trades defensively, smaller positions, higher sell threshold

### Scenario 3: Crisis
```
Risk Factor: 0.85 (Very High Risk)
Notes: Banking crisis, extreme volatility, flight to safety
Factors:
  - vix: 40
  - gold_price: 2300
  - geopolitical_score: 0.9
```
**Effect**: System mostly in cash, very selective buying, aggressive selling

## Integration with Code

### In Python Code

```python
from app.features.risk_factors import RiskFactorCalculator

# Initialize calculator
calc = RiskFactorCalculator()

# Get current macro risk
macro_risk = calc.get_macro_risk_factor()
print(f"Current macro risk: {macro_risk:.2f}")

# Get detailed info
info = calc.get_macro_risk_info()
print(f"Last updated: {info['last_updated']}")
print(f"Notes: {info['notes']}")

# Update macro risk
calc.update_macro_risk_factor(
    risk_factor=0.65,
    notes="Fed rate hike, geopolitical tensions",
    factors={
        'fed_rate': 5.5,
        'gold_price': 2100,
        'vix': 22.5
    }
)
```

### In DataFrames

The macro risk factor is automatically added to DataFrames:

```python
# After adding risk factors
df = calc.add_risk_factors_to_dataframe(df)

# Now df has these columns:
# - risk_factor_composite (includes macro risk)
# - risk_factor_macro (the macro component separately)
```

## Best Practices

1. **Update Regularly**: Keep the factor current (at least weekly)
2. **Document Changes**: Always include notes explaining the assessment
3. **Track Factors**: Log the specific values (FD rate, VIX, etc.)
4. **Review Impact**: Monitor how macro risk affects portfolio performance
5. **Use AI Wisely**: Leverage AI for analysis but validate with market data
6. **Stay Informed**: Follow financial news, Fed announcements, geopolitical events

## Troubleshooting

### File Not Found
If `data/macro_risk_factor.json` doesn't exist, the system defaults to 0.5 (moderate risk). Run the update script to create it.

### Invalid Risk Value
Risk factor must be between 0 and 1. Values outside this range will raise an error.

### Stale Data
Check `last_updated` field. If data is old, update it before running strategies.

## Further Reading

- [RISK_ADJUSTMENT_SUMMARY.md](RISK_ADJUSTMENT_SUMMARY.md) - Overall risk system
- [RISK_FACTORS_GUIDE.md](RISK_FACTORS_GUIDE.md) - Technical risk factors
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
