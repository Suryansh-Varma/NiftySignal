# Gemini Prompt for Macro Risk Factor Update

## Copy-Paste Prompt for Gemini

```
You are a macroeconomic and geopolitical risk analyst for equity trading. Analyze the current market environment and provide a comprehensive risk assessment for the Indian stock market (NSE/NIFTY).

Today's date: January 21, 2026

Please analyze and provide specific values for:

1. **Federal Reserve Interest Rate**
   - Current rate: [find latest]
   - Rate trajectory: [hiking/cutting/holding]
   - Risk score (0-1): [calculate]

2. **Reserve Bank of India (RBI) Rate**
   - Current repo rate: [find latest]
   - Policy stance: [hawkish/dovish/neutral]
   - Risk score (0-1): [calculate]

3. **Gold Price**
   - Current price (USD/oz): [find latest]
   - 1-month trend: [up/down/stable by X%]
   - Risk score (0-1): [calculate based on flight-to-safety signals]

4. **VIX (India VIX or US VIX)**
   - Current level: [find latest]
   - Status: [low<15, normal 15-20, elevated 20-30, high>30]
   - Risk score (0-1): [calculate]

5. **Oil Price (Brent Crude)**
   - Current price (USD/barrel): [find latest]
   - Impact on Indian economy: [positive/negative/neutral]
   - Risk score (0-1): [calculate]

6. **Geopolitical Tensions**
   - Major ongoing conflicts: [list]
   - Trade disputes: [list if any]
   - Regional tensions affecting India: [list]
   - Overall geopolitical risk score (0-1): [calculate]

7. **Currency Volatility (USD/INR)**
   - Current rate: [find latest]
   - 1-month volatility: [stable/moderate/high]
   - Risk score (0-1): [calculate]

8. **Additional Risk Factors**
   - Global recession risk: [score 0-1]
   - Banking sector stability: [score 0-1]
   - Inflation trajectory: [score 0-1]

Based on these factors, provide:

**OVERALL RISK ASSESSMENT**
- **Composite Risk Score (0-1)**: [weighted average, be specific]
- **Risk Level**: [Very Low/Low/Moderate/High/Very High]
- **Key Drivers**: [top 3 factors affecting risk]
- **Outlook for next 7 days**: [improving/stable/deteriorating]
- **Recommended Trading Stance**: [aggressive/balanced/defensive/very defensive]

**UPDATE COMMAND**
Provide the exact command I should run to update my system:
```bash
python -m app.scripts.update_macro_risk \
    --risk [X.XX] \
    --notes "[concise summary of conditions]" \
    --fed-rate [X.X] \
    --gold-price [XXXX] \
    --vix [XX.X] \
    --oil-price [XX.X]
```

**NOTES FOR SYSTEM**
Write a concise 1-2 sentence summary of the current macro environment suitable for system logs.

Please provide real-time data by searching current market information. Be specific with numbers and don't use placeholders.
```

---

## Alternative: Shorter Quick Prompt

If you want faster updates, use this shorter version:

```
Quick macro risk update for Indian equity trading (Jan 21, 2026):

Give me:
1. Current Fed rate, RBI rate, Gold price, VIX, Oil price, USD/INR
2. Overall risk score (0-1 scale) for trading
3. Key risk drivers (max 3)
4. One-line summary

Provide the exact command to run:
python -m app.scripts.update_macro_risk --risk X.XX --notes "..."

Search for real-time data, be specific with numbers.
```

---

## Alternative: Comprehensive Analysis Prompt

For detailed weekly analysis:

```
Comprehensive Macroeconomic Risk Analysis for NSE/NIFTY Trading
Date: January 21, 2026

As a risk analyst, provide a detailed assessment including:

**MACRO INDICATORS**
1. Interest Rates
   - US Fed Funds Rate: [current + next meeting outlook]
   - RBI Repo Rate: [current + policy stance]
   - Impact: [score 0-1]

2. Commodities
   - Gold (USD/oz): [price + trend + flight-to-safety indicator]
   - Oil/Brent (USD/bbl): [price + impact on India]
   - Combined commodity risk: [score 0-1]

3. Market Volatility
   - India VIX: [current level]
   - US VIX: [current level]
   - Volatility risk: [score 0-1]

4. Currency
   - USD/INR: [rate + trend + stability]
   - Currency risk: [score 0-1]

**GEOPOLITICAL FACTORS**
- Active conflicts: [list with impact on India]
- Trade tensions: [US-China, India-specific]
- Regional stability: [South Asia, Middle East]
- Geopolitical risk: [score 0-1]

**ECONOMIC INDICATORS**
- Global growth outlook: [IMF/World Bank latest]
- India GDP trajectory: [latest forecast]
- Inflation trends: [US, India]
- Banking sector: [any stress indicators]
- Economic risk: [score 0-1]

**RISK SYNTHESIS**
Calculate weighted average risk (0-1):
- Interest rates: 20% weight
- Commodities: 15% weight
- Volatility: 20% weight
- Geopolitical: 25% weight
- Economic: 15% weight
- Currency: 5% weight

**FINAL OUTPUT**
1. Overall Risk Score: [X.XX]
2. Risk Category: [Very Low/Low/Moderate/High/Very High]
3. Top 3 Risk Drivers
4. 7-day Outlook
5. Trading Recommendation
6. Update Command:
```bash
python -m app.scripts.update_macro_risk --risk X.XX --notes "..." \
    --fed-rate X.X --gold-price XXXX --vix XX.X --oil-price XX.X
```

Search current market data and news. Provide specific numbers, not estimates.
```

---

## How to Use

1. **Copy** one of the prompts above (choose based on detail level needed)
2. **Paste** into Google Gemini
3. **Wait** for analysis (usually 10-30 seconds)
4. **Copy** the generated command from Gemini's response
5. **Run** in your terminal
6. **Verify** with: `python -m app.scripts.update_macro_risk --view`

## Tips for Best Results

- **Use the first prompt** for weekly updates (comprehensive)
- **Use the short prompt** for daily quick checks
- **Use the comprehensive prompt** for major events/monthly reviews
- Always verify Gemini's data with recent news if possible
- Update immediately after Fed meetings, major geopolitical events
- Set a reminder for weekly updates (every Monday morning)

## Expected Response Time

- **Gemini Analysis**: 15-30 seconds
- **Copy command**: 5 seconds  
- **Run update**: 2 seconds
- **Total time**: ~30-40 seconds (vs. 5-10 minutes manual analysis)

## Sample Gemini Response

You should expect output like:

```
OVERALL RISK ASSESSMENT
Composite Risk Score: 0.67
Risk Level: High
Key Drivers: Fed hawkishness, Middle East tensions, elevated VIX
Outlook: Stable but elevated risk
Recommended Stance: Defensive

UPDATE COMMAND:
python -m app.scripts.update_macro_risk \
    --risk 0.67 \
    --notes "Fed hawkish, geopolitical tensions elevated, VIX at 24" \
    --fed-rate 5.5 \
    --gold-price 2105 \
    --vix 24.2 \
    --oil-price 87.5
```

Then just copy and run that command!

---

## Automation Idea (Future)

You could create a script that:
1. Calls Gemini API automatically
2. Parses the response
3. Updates the risk factor
4. Runs daily via cron/scheduler

But for now, the copy-paste method takes <1 minute! 🚀
