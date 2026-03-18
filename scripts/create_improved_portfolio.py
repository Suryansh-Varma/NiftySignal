"""
Create improved test portfolio to validate model accuracy improvements.
Uses new predictions from retrained model with 3 years data.
"""

import pandas as pd
import json
from datetime import datetime

print("\n" + "="*70)
print("CREATING IMPROVED TEST PORTFOLIO - MODEL V2")
print("="*70)

# Load new recommendations
recommendations = pd.read_csv('results/latest_recommendations.csv')

print(f"\n📊 Available Recommendations: {len(recommendations)}")
print(f"   Signals: {recommendations['recommendation'].value_counts().to_dict()}")
print(f"   Mean Confidence: {recommendations['confidence'].mean():.1%}")

# Select diverse portfolio
# Prioritize high confidence, mix of sectors
portfolio_stocks = []

# Add SELL signal if available
sell_signals = recommendations[recommendations['signal'] == -1].nlargest(2, 'confidence')
for _, row in sell_signals.iterrows():
    portfolio_stocks.append(row)

# Add high confidence HOLD signals (top performers expected)
high_conf_holds = recommendations[recommendations['signal'] == 0].nlargest(15, 'confidence')
for _, row in high_conf_holds.iterrows():
    portfolio_stocks.append(row)

# Add medium confidence to test range
med_conf_holds = recommendations[
    (recommendations['signal'] == 0) & 
    (recommendations['confidence'] >= 0.50) & 
    (recommendations['confidence'] < 0.70)
].sample(n=min(3, len(recommendations[(recommendations['signal'] == 0) & (recommendations['confidence'] >= 0.50) & (recommendations['confidence'] < 0.70)])))
for _, row in med_conf_holds.iterrows():
    portfolio_stocks.append(row)

print(f"\n📦 Selected {len(portfolio_stocks)} stocks for portfolio")

# Create portfolio with position sizing
total_capital = 5000000  # Rs 50 lakh
position_size = total_capital / len(portfolio_stocks)

holdings = []
total_investment = 0

print(f"\n💰 Allocating Rs {position_size:,.0f} per stock...")

for stock in portfolio_stocks:
    symbol = stock['symbol']
    price = stock['last_price']
    signal = stock['signal']
    confidence = stock['confidence']
    
    # Calculate shares (round down)
    shares = int(position_size / price)
    investment = shares * price
    
    # Determine sector
    sector = 'Unknown'
    if 'PHARMA' in symbol or 'CIPLA' in symbol or 'SUN' in symbol or 'DR' in symbol:
        sector = 'Pharma'
    elif 'NESTLE' in symbol or 'BRITANNIA' in symbol or 'HUL' in symbol:
        sector = 'FMCG'
    elif 'TATA' in symbol or 'HERO' in symbol or 'MARUTI' in symbol or 'EICHER' in symbol:
        sector = 'Auto'
    elif 'INFY' in symbol or 'TCS' in symbol or 'HCL' in symbol or 'TECH' in symbol:
        sector = 'Tech'
    elif 'BANK' in symbol or 'ICICI' in symbol or 'HDFC' in symbol or 'AXIS' in symbol or 'KOTAK' in symbol:
        sector = 'Finance'
    elif 'RELIANCE' in symbol:
        sector = 'Energy/Retail'
    elif 'TITAN' in symbol:
        sector = 'Consumer'
    elif 'BHARTI' in symbol:
        sector = 'Telecom'
    elif 'ASIAN' in symbol or 'ULTRACEM' in symbol or 'JSW' in symbol:
        sector = 'Materials'
    elif 'ADANI' in symbol:
        sector = 'Infrastructure'
    elif 'LIFE' in symbol or 'SBI' in symbol:
        sector = 'Financial Services'
    
    holdings.append({
        'symbol': symbol,
        'shares': shares,
        'avg_buy_price': float(price),
        'purchase_date': '2026-01-21',
        'signal': int(signal),
        'confidence': float(confidence),
        'sector': sector,
        'investment': investment,
        'notes': ''
    })
    
    total_investment += investment
    
    signal_name = 'SELL' if signal == -1 else 'HOLD' if signal == 0 else 'BUY'
    print(f"  ✓ {symbol:15s} {shares:4d} shares @ Rs {price:8.2f} = Rs {investment:10,.0f} [{signal_name} {confidence:.1%}] {sector}")

# Create portfolio JSON
portfolio = {
    'user_id': 'improved_model_v2',
    'name': 'Improved Model Test Portfolio (Phase 1)',
    'holdings': holdings,
    'cash_balance': total_capital - total_investment,
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat()
}

# Save portfolio
import os
os.makedirs('results/portfolios', exist_ok=True)

with open('results/portfolios/portfolio_improved_model_v2.json', 'w') as f:
    json.dump(portfolio, f, indent=2)

print(f"\n" + "="*70)
print("PORTFOLIO CREATED SUCCESSFULLY")
print("="*70)

print(f"\n💰 Portfolio Summary:")
print(f"   Total Capital: Rs {total_capital:,.0f}")
print(f"   Invested: Rs {total_investment:,.0f}")
print(f"   Cash Balance: Rs {total_capital - total_investment:,.0f}")
print(f"   Stocks: {len(holdings)}")

# Sector breakdown
sector_allocation = {}
for h in holdings:
    sector = h['sector']
    sector_allocation[sector] = sector_allocation.get(sector, 0) + h['investment']

print(f"\n🏢 Sector Allocation:")
sorted_sectors = sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True)
for sector, amount in sorted_sectors:
    pct = (amount / total_investment) * 100
    print(f"   {sector:20s} Rs {amount:10,.0f} ({pct:5.1f}%)")

# Signal breakdown
signal_counts = {}
for h in holdings:
    sig = h['signal']
    signal_counts[sig] = signal_counts.get(sig, 0) + 1

print(f"\n📊 Signal Distribution:")
for sig, count in sorted(signal_counts.items()):
    sig_name = 'SELL' if sig == -1 else 'HOLD' if sig == 0 else 'BUY'
    pct = (count / len(holdings)) * 100
    print(f"   {sig_name}: {count} ({pct:.1f}%)")

# Confidence stats
confidences = [h['confidence'] for h in holdings]
print(f"\n🎯 Confidence Statistics:")
print(f"   Mean: {sum(confidences)/len(confidences):.1%}")
print(f"   Min: {min(confidences):.1%}")
print(f"   Max: {max(confidences):.1%}")

print(f"\n🎯 Test Objectives:")
print(f"   1. Validate +393% return improvement (1.47% → 7.25%)")
print(f"   2. Test new risk factor integration")
print(f"   3. Verify high confidence predictions")
print(f"   4. Compare vs previous 33.3% accuracy")
print(f"   Target: >50% accuracy, positive returns")

print(f"\n📅 Tracking Period:")
print(f"   Start: Jan 21, 2026 (TODAY)")
print(f"   End: Jan 28, 2026 (7 days)")
print(f"   Verify: python verify_accuracy_v2.py")

print(f"\n💾 Saved to: results/portfolios/portfolio_improved_model_v2.json")
print("="*70 + "\n")
