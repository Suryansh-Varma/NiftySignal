# Macro Risk Factor - Quick Reference

## Quick Commands

### View Current Risk
```bash
python -m app.scripts.update_macro_risk --view
```

### Update Interactively (Recommended)
```bash
python -m app.scripts.update_macro_risk --interactive
```

### Quick Update
```bash
python -m app.scripts.update_macro_risk --risk 0.65 --notes "Your notes here"
```

### Full Update with Factors
```bash
python -m app.scripts.update_macro_risk \
    --risk 0.65 \
    --notes "Fed hiking, tensions rising" \
    --fed-rate 5.5 \
    --gold-price 2100 \
    --vix 22.5 \
    --oil-price 88
```

## Risk Scale

| Value | Label | Action |
|-------|-------|--------|
| 0.0-0.2 | Very Low | Aggressive trading |
| 0.2-0.4 | Low | Normal trading |
| 0.4-0.6 | Moderate | Balanced approach |
| 0.6-0.8 | High | Defensive trading |
| 0.8-1.0 | Very High | Crisis mode |

## Key Factors to Monitor

### 1. Federal Reserve Rate
- **Low (<3%)**: Risk 0.2-0.3
- **Moderate (3-5%)**: Risk 0.4-0.5
- **High (>5%)**: Risk 0.6-0.8

### 2. Gold Price (USD/oz)
- **Normal ($1,800-1,950)**: Risk 0.3-0.4
- **Elevated ($2,000-2,200)**: Risk 0.5-0.7
- **Flight to safety (>$2,200)**: Risk 0.7-0.9

### 3. VIX (Volatility Index)
- **Low (<15)**: Risk 0.2-0.3
- **Normal (15-20)**: Risk 0.4-0.5
- **Elevated (20-30)**: Risk 0.6-0.7
- **High (>30)**: Risk 0.8-0.9

### 4. Geopolitical Score
- **Peaceful**: 0.1-0.2
- **Minor tensions**: 0.3-0.4
- **Regional conflicts**: 0.5-0.7
- **Major wars/crises**: 0.8-0.9

### 5. Oil Price (USD/barrel)
- **Stable ($70-85)**: Risk 0.3-0.4
- **Volatile ($60-70 or $85-100)**: Risk 0.5-0.6
- **Extreme (<$60 or >$100)**: Risk 0.7-0.8

## Update Frequency

- **Normal times**: Weekly (every Monday)
- **Volatile markets**: Daily
- **Major events**: Immediately

## Events That Require Updates

### Immediate Update
- Fed rate decisions
- War/conflict escalation
- Market crashes (>5% drop)
- Banking crises

### Within 24 Hours
- Major economic data (jobs, inflation)
- Central bank policy changes
- Geopolitical developments
- Currency crises

### Weekly Review
- Gold/oil price trends
- VIX movements
- General market sentiment

## AI Prompt Template

```
Analyze the current macro risk environment for trading:

Current Data:
- Fed Rate: [value]%
- Gold: $[value]/oz
- VIX: [value]
- Oil: $[value]/barrel

Recent Events:
- [event 1]
- [event 2]

Provide:
1. Overall risk score (0-1)
2. Key drivers
3. Outlook for next week
```

## Python Usage

```python
from app.features.risk_factors import RiskFactorCalculator

calc = RiskFactorCalculator()

# Get current risk
risk = calc.get_macro_risk_factor()

# View details
info = calc.get_macro_risk_info()
print(info)

# Update
calc.update_macro_risk_factor(
    risk_factor=0.65,
    notes="Your assessment",
    factors={'fed_rate': 5.5, 'vix': 22.5}
)
```

## Integration

The macro risk factor is automatically included in:
- Composite risk calculations (20% weight)
- Trading signal adjustments
- Position sizing
- Portfolio recommendations

## File Location

Risk data stored in: `data/macro_risk_factor.json`

## Troubleshooting

**Problem**: File not found  
**Solution**: Run `python -m app.scripts.update_macro_risk --risk 0.5 --notes "Initialize"`

**Problem**: Invalid risk value  
**Solution**: Ensure value is between 0.0 and 1.0

**Problem**: Stale data  
**Solution**: Check `last_updated` field and update if old

## See Also

- [README_MACRO_RISK.md](README_MACRO_RISK.md) - Complete guide
- [demo_macro_risk.py](demo_macro_risk.py) - Examples
- [RISK_FACTORS_GUIDE.md](RISK_FACTORS_GUIDE.md) - Technical factors
