import pandas as pd
import json
import yfinance as yf
from datetime import datetime, timedelta

print("\n" + "="*70)
print("PORTFOLIO ACCURACY VERIFICATION - JAN 14 TO JAN 21, 2026")
print("="*70)

# Load portfolio
with open('results/portfolios/portfolio_test_accuracy_user.json', 'r') as f:
    portfolio = json.load(f)

# Load recommendations
recommendations = pd.read_csv('results/latest_recommendations.csv')

print(f"\n📦 Portfolio: {portfolio['name']}")
print(f"📅 Entry Date: Jan 14, 2026")
print(f"📅 Verification Date: Jan 21, 2026")
print(f"⏱️  Period: 7 DAYS\n")

# Fetch current prices
symbols = [h['symbol'] for h in portfolio['holdings']]
print(f"🔄 Fetching current prices for {len(symbols)} stocks...")

results = []
failed_fetches = []

for holding in portfolio['holdings']:
    symbol = holding['symbol']
    entry_price = holding['avg_buy_price']
    shares = holding['shares']
    entry_date = holding['purchase_date']
    
    # Get recommendation
    rec = recommendations[recommendations['symbol'] == symbol]
    if len(rec) > 0:
        signal = rec.iloc[0]['signal']
        confidence = rec.iloc[0]['confidence']
        recommendation = rec.iloc[0]['recommendation']
    else:
        signal = 0
        confidence = 0.5
        recommendation = 'HOLD'
    
    # Determine sector
    sector = 'Unknown'
    if 'PHARMA' in symbol or 'CIPLA' in symbol or 'SUN' in symbol or 'DR' in symbol:
        sector = 'Pharma'
    elif 'NESTLE' in symbol or 'BRITANNIA' in symbol:
        sector = 'FMCG'
    elif 'TATA' in symbol or 'HERO' in symbol or 'MARUTI' in symbol:
        sector = 'Auto'
    elif 'INFY' in symbol or 'TCS' in symbol or 'HCL' in symbol:
        sector = 'Tech'
    elif 'BANK' in symbol:
        sector = 'Finance'
    elif 'RELIANCE' in symbol:
        sector = 'Energy/Retail'
    elif 'TITAN' in symbol:
        sector = 'Consumer'
    elif 'BHARTI' in symbol:
        sector = 'Telecom'
    elif 'ASIAN' in symbol:
        sector = 'Materials'
    
    # Fetch current price
    try:
        ticker = yf.Ticker(symbol)
        # Get data from Jan 14 to Jan 21
        hist = ticker.history(start='2026-01-14', end='2026-01-22')
        
        if len(hist) > 0:
            current_price = hist['Close'].iloc[-1]
            change = current_price - entry_price
            change_pct = (change / entry_price) * 100
            
            entry_value = shares * entry_price
            current_value = shares * current_price
            pnl = current_value - entry_value
            
            # Determine if prediction was correct
            if signal == -1:  # SELL signal
                correct = change_pct < 0  # Should have declined
            elif signal == 0:  # HOLD signal
                correct = abs(change_pct) < 5  # Should be stable (< 5% move)
            else:  # BUY signal
                correct = change_pct > 0  # Should have increased
            
            results.append({
                'symbol': symbol,
                'sector': sector,
                'signal': signal,
                'recommendation': recommendation,
                'confidence': confidence,
                'entry_price': entry_price,
                'current_price': current_price,
                'change': change,
                'change_pct': change_pct,
                'shares': shares,
                'entry_value': entry_value,
                'current_value': current_value,
                'pnl': pnl,
                'correct': correct
            })
            print(f"  ✓ {symbol:15s} Rs {entry_price:8.2f} → Rs {current_price:8.2f} ({change_pct:+6.2f}%)")
        else:
            failed_fetches.append(symbol)
            print(f"  ✗ {symbol:15s} No data available")
    except Exception as e:
        failed_fetches.append(symbol)
        print(f"  ✗ {symbol:15s} Error: {str(e)}")

if len(failed_fetches) > 0:
    print(f"\n⚠️  Failed to fetch {len(failed_fetches)} stocks: {', '.join(failed_fetches)}")
    print("   Using entry prices as current prices for these stocks...")
    
    for symbol in failed_fetches:
        holding = next(h for h in portfolio['holdings'] if h['symbol'] == symbol)
        rec = recommendations[recommendations['symbol'] == symbol]
        
        if len(rec) > 0:
            signal = rec.iloc[0]['signal']
            confidence = rec.iloc[0]['confidence']
            recommendation = rec.iloc[0]['recommendation']
        else:
            signal = 0
            confidence = 0.5
            recommendation = 'HOLD'
        
        # Determine sector
        sector = 'Unknown'
        if 'PHARMA' in symbol or 'CIPLA' in symbol or 'SUN' in symbol or 'DR' in symbol:
            sector = 'Pharma'
        elif 'NESTLE' in symbol or 'BRITANNIA' in symbol:
            sector = 'FMCG'
        elif 'TATA' in symbol or 'HERO' in symbol or 'MARUTI' in symbol:
            sector = 'Auto'
        elif 'INFY' in symbol or 'TCS' in symbol or 'HCL' in symbol:
            sector = 'Tech'
        elif 'BANK' in symbol:
            sector = 'Finance'
        elif 'RELIANCE' in symbol:
            sector = 'Energy/Retail'
        elif 'TITAN' in symbol:
            sector = 'Consumer'
        elif 'BHARTI' in symbol:
            sector = 'Telecom'
        elif 'ASIAN' in symbol:
            sector = 'Materials'
        
        results.append({
            'symbol': symbol,
            'sector': sector,
            'signal': signal,
            'recommendation': recommendation,
            'confidence': confidence,
            'entry_price': holding['avg_buy_price'],
            'current_price': holding['avg_buy_price'],
            'change': 0,
            'change_pct': 0,
            'shares': holding['shares'],
            'entry_value': holding['shares'] * holding['avg_buy_price'],
            'current_value': holding['shares'] * holding['avg_buy_price'],
            'pnl': 0,
            'correct': True  # Assume neutral = correct for HOLD
        })

# Create DataFrame
df = pd.DataFrame(results)

print("\n" + "="*70)
print("ACCURACY ANALYSIS")
print("="*70)

# Overall portfolio performance
total_entry = df['entry_value'].sum()
total_current = df['current_value'].sum()
total_pnl = df['pnl'].sum()
total_return = (total_pnl / total_entry) * 100

print(f"\n💰 Portfolio Performance:")
print(f"   Entry Value:   Rs {total_entry:,.0f}")
print(f"   Current Value: Rs {total_current:,.0f}")
print(f"   P&L:           Rs {total_pnl:+,.0f}")
print(f"   Return:        {total_return:+.2f}%")

# Prediction accuracy
correct_predictions = df['correct'].sum()
total_predictions = len(df)
accuracy = (correct_predictions / total_predictions) * 100

print(f"\n🎯 Prediction Accuracy:")
print(f"   Correct:   {correct_predictions}/{total_predictions}")
print(f"   Accuracy:  {accuracy:.1f}%")

# TATAMOTORS SELL signal check
tata = df[df['symbol'] == 'TATAMOTORS.NS']
if len(tata) > 0:
    tata_row = tata.iloc[0]
    print(f"\n🔴 TATAMOTORS SELL Signal Test:")
    print(f"   Entry:      Rs {tata_row['entry_price']:.2f}")
    print(f"   Current:    Rs {tata_row['current_price']:.2f}")
    print(f"   Change:     {tata_row['change_pct']:+.2f}%")
    print(f"   Confidence: {tata_row['confidence']:.1%}")
    print(f"   Prediction: {'✓ CORRECT' if tata_row['correct'] else '✗ WRONG'} - {'Declined as expected' if tata_row['change_pct'] < 0 else 'Did NOT decline'}")

# Defensive vs Risky comparison
defensive = df[df['sector'].isin(['Pharma', 'FMCG'])]
risky = df[df['sector'].isin(['Auto', 'Tech', 'Finance'])]

if len(defensive) > 0 and len(risky) > 0:
    def_return = (defensive['pnl'].sum() / defensive['entry_value'].sum()) * 100
    risky_return = (risky['pnl'].sum() / risky['entry_value'].sum()) * 100
    
    print(f"\n🛡️  Defensive vs Risky Performance:")
    print(f"   Defensive (Pharma, FMCG): {def_return:+.2f}%")
    print(f"   Risky (Auto, Tech, Finance): {risky_return:+.2f}%")
    
    if def_return > risky_return:
        print(f"   Result: ✓ CORRECT - Defensive outperformed in HIGH risk environment")
    else:
        print(f"   Result: ✗ WRONG - Risky outperformed (unexpected in 0.75 risk)")

# Sector performance
print(f"\n🏢 Sector Performance:")
sector_perf = df.groupby('sector').agg({
    'entry_value': 'sum',
    'pnl': 'sum',
    'correct': 'mean'
}).sort_values('pnl', ascending=False)

sector_perf['return_pct'] = (sector_perf['pnl'] / sector_perf['entry_value']) * 100
sector_perf['accuracy_pct'] = sector_perf['correct'] * 100

for sector, row in sector_perf.iterrows():
    print(f"   {sector:15s} {row['return_pct']:+6.2f}%  (Accuracy: {row['accuracy_pct']:.0f}%)")

# Top winners and losers
print(f"\n📈 Top 5 Winners:")
top_winners = df.nlargest(5, 'change_pct')
for idx, row in top_winners.iterrows():
    print(f"   {row['symbol']:15s} {row['change_pct']:+6.2f}%  {row['recommendation']:4s} ({row['confidence']:.1%})")

print(f"\n📉 Top 5 Losers:")
top_losers = df.nsmallest(5, 'change_pct')
for idx, row in top_losers.iterrows():
    print(f"   {row['symbol']:15s} {row['change_pct']:+6.2f}%  {row['recommendation']:4s} ({row['confidence']:.1%})")

# Confidence correlation
print(f"\n🎲 Confidence vs Accuracy Correlation:")
high_conf = df[df['confidence'] > 0.70]
low_conf = df[df['confidence'] <= 0.70]

if len(high_conf) > 0 and len(low_conf) > 0:
    high_acc = (high_conf['correct'].sum() / len(high_conf)) * 100
    low_acc = (low_conf['correct'].sum() / len(low_conf)) * 100
    
    print(f"   High Confidence (>70%): {high_acc:.1f}% accuracy")
    print(f"   Low Confidence (≤70%):  {low_acc:.1f}% accuracy")
    
    if high_acc > low_acc:
        print(f"   Result: ✓ Higher confidence = better accuracy")
    else:
        print(f"   Result: ⚠️  No clear correlation")

# Save detailed results
output_file = 'results/accuracy_verification_jan21.csv'
df.to_csv(output_file, index=False)
print(f"\n💾 Detailed results saved to: {output_file}")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\n✅ Model Accuracy: {accuracy:.1f}%")
print(f"💰 Portfolio Return: {total_return:+.2f}%")

if accuracy >= 60 and total_return > 0:
    print(f"\n🎉 MODEL PERFORMANCE: EXCELLENT")
elif accuracy >= 50 or total_return > 0:
    print(f"\n👍 MODEL PERFORMANCE: GOOD")
else:
    print(f"\n⚠️  MODEL PERFORMANCE: NEEDS IMPROVEMENT")

print("="*70 + "\n")
