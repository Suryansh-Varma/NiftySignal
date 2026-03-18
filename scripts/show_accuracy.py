import pandas as pd
import json

print("\n" + "="*60)
print("CURRENT MODEL ACCURACY METRICS")
print("="*60)

# Load latest recommendations
df = pd.read_csv('results/latest_recommendations.csv')

print(f"\n📊 Total Stocks Analyzed: {len(df)}")

print(f"\n📈 Signal Distribution:")
signal_counts = df['recommendation'].value_counts()
for signal, count in signal_counts.items():
    pct = (count / len(df)) * 100
    print(f"   {signal}: {count} ({pct:.1f}%)")

print(f"\n🎯 Confidence Statistics:")
print(f"   Mean Confidence: {df['confidence'].mean():.1%}")
print(f"   Median Confidence: {df['confidence'].median():.1%}")
print(f"   Min Confidence: {df['confidence'].min():.1%}")
print(f"   Max Confidence: {df['confidence'].max():.1%}")

print(f"\n⭐ Top 10 Most Confident Predictions:")
top_confident = df.nlargest(10, 'confidence')[['symbol', 'recommendation', 'confidence', 'last_price']]
for idx, row in top_confident.iterrows():
    print(f"   {row['symbol']:15s} {row['recommendation']:4s} {row['confidence']:6.1%}  Rs {row['last_price']:8.2f}")

print(f"\n⚠️  Bottom 5 Least Confident Predictions:")
bottom_confident = df.nsmallest(5, 'confidence')[['symbol', 'recommendation', 'confidence', 'last_price']]
for idx, row in bottom_confident.iterrows():
    print(f"   {row['symbol']:15s} {row['recommendation']:4s} {row['confidence']:6.1%}  Rs {row['last_price']:8.2f}")

# Load test portfolio
try:
    with open('results/portfolios/portfolio_test_accuracy_user.json', 'r') as f:
        portfolio = json.load(f)
    
    print("\n" + "="*60)
    print("TEST PORTFOLIO ACCURACY SETUP")
    print("="*60)
    
    print(f"\n📦 Portfolio: {portfolio['user_id']} - {portfolio['name']}")
    print(f"   Total Stocks: {len(portfolio['holdings'])}")
    
    # Get recommendations for portfolio stocks
    recommendations = pd.read_csv('results/latest_recommendations.csv')
    
    # Signal distribution in portfolio
    signals = {}
    sectors = {}
    total_investment = 0
    
    holdings_with_signals = []
    for holding in portfolio['holdings']:
        symbol = holding['symbol']
        rec = recommendations[recommendations['symbol'] == symbol]
        if len(rec) > 0:
            signal = rec.iloc[0]['signal']
            confidence = rec.iloc[0]['confidence']
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
            
            investment = holding['shares'] * holding['avg_buy_price']
            
            holdings_with_signals.append({
                'symbol': symbol,
                'signal': signal,
                'confidence': confidence,
                'sector': sector,
                'shares': holding['shares'],
                'entry_price': holding['avg_buy_price'],
                'investment': investment
            })
            
            signals[signal] = signals.get(signal, 0) + 1
            sectors[sector] = sectors.get(sector, 0) + investment
            total_investment += investment
    
    print(f"\n📊 Portfolio Signal Distribution:")
    for signal, count in sorted(signals.items()):
        pct = (count / len(portfolio['holdings'])) * 100
        signal_name = 'HOLD' if signal == 0 else 'SELL' if signal == -1 else 'BUY'
        print(f"   {signal_name}: {count} ({pct:.1f}%)")
    
    print(f"\n🏢 Sector Allocation:")
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    for sector, amount in sorted_sectors:
        pct = (amount / total_investment) * 100
        print(f"   {sector:15s} Rs {amount:10,.0f} ({pct:5.1f}%)")
    
    print(f"\n   Total Investment: Rs {total_investment:,.0f}")
    
    print(f"\n⭐ Highest Confidence Holdings:")
    holdings_df = pd.DataFrame(holdings_with_signals)
    top_holdings = holdings_df.nlargest(5, 'confidence')
    for idx, row in top_holdings.iterrows():
        signal_name = 'HOLD' if row['signal'] == 0 else 'SELL' if row['signal'] == -1 else 'BUY'
        print(f"   {row['symbol']:15s} {signal_name:4s} {row['confidence']:6.1%}  {row['sector']}")
    
    print(f"\n🎯 Key Test Cases:")
    sell_signals = holdings_df[holdings_df['signal'] == -1]
    if len(sell_signals) > 0:
        for idx, row in sell_signals.iterrows():
            print(f"   ⚠️  {row['symbol']} - SELL signal at {row['confidence']:.1%} confidence")
            print(f"       Entry: Rs {row['entry_price']:.2f}, Shares: {int(row['shares'])}")
            print(f"       Investment: Rs {row['investment']:,.0f}")
            print(f"       Expected: Price should decline by week's end")
    else:
        print("   No SELL signals in portfolio")
    
    # Defensive vs Risky comparison
    defensive = holdings_df[holdings_df['sector'].isin(['Pharma', 'FMCG'])]
    risky = holdings_df[holdings_df['sector'].isin(['Auto', 'Tech', 'Finance'])]
    
    if len(defensive) > 0 and len(risky) > 0:
        print(f"\n🎯 Defensive vs Risky Test:")
        def_invest = defensive['investment'].sum()
        risky_invest = risky['investment'].sum()
        print(f"   Defensive (Pharma, FMCG): Rs {def_invest:,.0f} ({def_invest/total_investment*100:.1f}%)")
        print(f"   Risky (Auto, Tech, Finance): Rs {risky_invest:,.0f} ({risky_invest/total_investment*100:.1f}%)")
        print(f"   Expected: Defensive should outperform risky in 0.75 HIGH risk")
    
    print("\n" + "="*60)
    print("ACCURACY VALIDATION - READY FOR CHECK")
    print("="*60)
    print("\n📅 Portfolio Created: Jan 14, 2026")
    print("📅 Today's Date: Jan 21, 2026")
    print("⏱️  Time Elapsed: 7 DAYS\n")
    print("✅ NEXT STEP: Fetch current prices and calculate accuracy!")
    print("\n   1. Update all stock prices (Jan 21 closing)")
    print("   2. Calculate actual returns by sector")
    print("   3. Verify TATAMOTORS SELL signal accuracy")
    print("   4. Compare defensive vs risky performance")
    print("   5. Calculate hit rate: (correct predictions / total)")
    print("\n📝 Expected in 0.75 HIGH risk environment:")
    print("   - Defensive sectors (Pharma, FMCG) should outperform")
    print("   - Risky sectors (Auto, Tech, Finance) should lag")
    print("   - TATAMOTORS should decline from Rs 357.80")

except FileNotFoundError:
    print("\n⚠️  Test portfolio file not found")

print("\n" + "="*60)
