import pandas as pd
import json
from datetime import datetime
import sys

print("\n" + "="*80)
print("ACCURACY COMPARISON: JANUARY 28 vs JANUARY 21, 2026 (7-DAY ANALYSIS)")
print("="*80)

try:
    # Load Jan 21 data
    jan21_data = pd.read_csv('results/accuracy_verification_jan21.csv')
    print(f"\n✅ Loaded Jan 21 data: {len(jan21_data)} records")
    
except FileNotFoundError:
    print(f"\n❌ Jan 21 data not found at results/accuracy_verification_jan21.csv")
    jan21_data = None

# Load latest recommendations and portfolio
try:
    recommendations = pd.read_csv('results/latest_recommendations.csv')
    print(f"✅ Loaded current recommendations: {len(recommendations)} stocks")
except Exception as e:
    print(f"❌ Error loading recommendations: {e}")
    recommendations = None

try:
    with open('results/portfolios/portfolio_test_accuracy_user.json', 'r') as f:
        portfolio = json.load(f)
    print(f"✅ Loaded portfolio: {portfolio.get('name', 'Unknown')}")
except Exception as e:
    print(f"❌ Error loading portfolio: {e}")
    portfolio = None

# Collect Jan 28 data
print("\n" + "-"*80)
print("FETCHING CURRENT (JAN 28) DATA FOR COMPARISON")
print("-"*80)

if portfolio:
    symbols = [h['symbol'] for h in portfolio['holdings']]
    print(f"\n🔄 Fetching current prices for {len(symbols)} stocks (as of Jan 28)...")
    
    results = []
    success_count = 0
    
    for holding in portfolio['holdings']:
        symbol = holding['symbol']
        entry_price = holding['avg_buy_price']
        shares = holding['shares']
        entry_date = holding['purchase_date']
        
        # Get recommendation
        rec = recommendations[recommendations['symbol'] == symbol] if recommendations is not None else None
        if rec is not None and len(rec) > 0:
            signal = rec.iloc[0]['signal']
            confidence = rec.iloc[0]['confidence']
            recommendation = rec.iloc[0]['recommendation']
            current_price = rec.iloc[0]['last_price']
        else:
            signal = 0
            confidence = 0.5
            recommendation = 'HOLD'
            current_price = entry_price
        
        # Calculate returns
        entry_value = entry_price * shares
        current_value = current_price * shares
        pnl = current_value - entry_value
        change_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0
        
        # Determine signal accuracy
        if pnl > 0 and recommendation in ['BUY', 'STRONG BUY']:
            correct = True
        elif pnl <= 0 and recommendation in ['SELL', 'STRONG SELL']:
            correct = True
        else:
            correct = False
        
        results.append({
            'symbol': symbol,
            'sector': 'Unknown',
            'signal': signal,
            'recommendation': recommendation,
            'confidence': confidence,
            'entry_price': entry_price,
            'current_price': current_price,
            'change': pnl,
            'change_pct': change_pct,
            'shares': shares,
            'entry_value': entry_value,
            'current_value': current_value,
            'pnl': pnl,
            'correct': correct
        })
        success_count += 1
    
    jan28_data = pd.DataFrame(results)
    
    # Save Jan 28 data
    jan28_data.to_csv('results/accuracy_verification_jan28.csv', index=False)
    print(f"✅ Saved Jan 28 data: {len(jan28_data)} records")
    
    # COMPARISON ANALYSIS
    print("\n" + "="*80)
    print("COMPARISON ANALYSIS: JAN 21 vs JAN 28 (7-DAY PERIOD)")
    print("="*80)
    
    if jan21_data is not None:
        jan21_accuracy = (jan21_data['correct'].sum() / len(jan21_data)) * 100 if len(jan21_data) > 0 else 0
    else:
        jan21_accuracy = 0
        
    jan28_accuracy = (jan28_data['correct'].sum() / len(jan28_data)) * 100 if len(jan28_data) > 0 else 0
    
    print(f"\n📊 ACCURACY METRICS:")
    if jan21_data is not None:
        print(f"   Jan 21 Accuracy: {jan21_accuracy:.2f}% ({int(jan21_data['correct'].sum())}/{len(jan21_data)} correct)")
    else:
        print(f"   Jan 21 Accuracy: Data not available")
    print(f"   Jan 28 Accuracy: {jan28_accuracy:.2f}% ({int(jan28_data['correct'].sum())}/{len(jan28_data)} correct)")
    
    if jan21_data is not None:
        accuracy_change = jan28_accuracy - jan21_accuracy
        trend = "📈 IMPROVED" if accuracy_change > 0 else "📉 DECLINED" if accuracy_change < 0 else "➡️  NO CHANGE"
        print(f"   Change: {accuracy_change:+.2f}% {trend}")
    
    # Portfolio performance
    print(f"\n💰 PORTFOLIO PERFORMANCE:")
    jan28_total_gain = jan28_data['pnl'].sum()
    jan28_total_gain_pct = (jan28_total_gain / jan28_data['entry_value'].sum()) * 100 if jan28_data['entry_value'].sum() > 0 else 0
    
    print(f"   Total P&L (Jan 28): Rs {jan28_total_gain:,.2f}")
    print(f"   Return %: {jan28_total_gain_pct:+.2f}%")
    print(f"   Winning Trades: {(jan28_data['pnl'] > 0).sum()} / {len(jan28_data)}")
    
    if jan21_data is not None:
        jan21_total_gain = jan21_data['pnl'].sum()
        jan21_total_gain_pct = (jan21_total_gain / jan21_data['entry_value'].sum()) * 100 if jan21_data['entry_value'].sum() > 0 else 0
        print(f"   Total P&L (Jan 21): Rs {jan21_total_gain:,.2f}")
        print(f"   Return % (Jan 21): {jan21_total_gain_pct:+.2f}%")
        print(f"   Weekly Improvement: Rs {jan28_total_gain - jan21_total_gain:,.2f}")
    
    # Recommendation distribution
    print(f"\n📈 RECOMMENDATION DISTRIBUTION (JAN 28):")
    rec_dist = jan28_data['recommendation'].value_counts()
    for rec, count in rec_dist.items():
        pct = (count / len(jan28_data)) * 100
        print(f"   {rec}: {count} ({pct:.1f}%)")
    
    # Top gainers and losers
    print(f"\n🏆 TOP 5 GAINERS (JAN 28):")
    top_gainers = jan28_data.nlargest(5, 'change_pct')[['symbol', 'change_pct', 'recommendation', 'confidence']]
    for idx, row in top_gainers.iterrows():
        print(f"   {row['symbol']:15s} {row['change_pct']:+7.2f}% {row['recommendation']:12s} Conf: {row['confidence']:.1%}")
    
    print(f"\n💔 TOP 5 LOSERS (JAN 28):")
    top_losers = jan28_data.nsmallest(5, 'change_pct')[['symbol', 'change_pct', 'recommendation', 'confidence']]
    for idx, row in top_losers.iterrows():
        print(f"   {row['symbol']:15s} {row['change_pct']:+7.2f}% {row['recommendation']:12s} Conf: {row['confidence']:.1%}")
    
    # Confidence analysis
    print(f"\n🎯 CONFIDENCE METRICS (JAN 28):")
    avg_confidence = jan28_data['confidence'].mean()
    print(f"   Average Confidence: {avg_confidence:.1%}")
    print(f"   Median Confidence: {jan28_data['confidence'].median():.1%}")
    print(f"   Min Confidence: {jan28_data['confidence'].min():.1%}")
    print(f"   Max Confidence: {jan28_data['confidence'].max():.1%}")
    
    # High confidence accuracy
    high_conf = jan28_data[jan28_data['confidence'] >= 0.7]
    if len(high_conf) > 0:
        high_conf_accuracy = (high_conf['correct'].sum() / len(high_conf)) * 100
        print(f"   High Confidence (>=70%) Accuracy: {high_conf_accuracy:.2f}% ({int(high_conf['correct'].sum())}/{len(high_conf)})")
    
    # Risk assessment
    print(f"\n⚠️  RISK ASSESSMENT (JAN 28):")
    losing_positions = (jan28_data['pnl'] < 0).sum()
    losing_pct = (losing_positions / len(jan28_data)) * 100
    max_loss = jan28_data['change_pct'].min()
    avg_loss = jan28_data[jan28_data['pnl'] < 0]['change_pct'].mean() if losing_positions > 0 else 0
    
    print(f"   Losing Positions: {losing_positions} ({losing_pct:.1f}%)")
    print(f"   Max Loss: {max_loss:.2f}%")
    print(f"   Average Loss: {avg_loss:.2f}%")
    print(f"   Drawdown Risk: {'🔴 HIGH' if max_loss < -10 else '🟡 MODERATE' if max_loss < -5 else '🟢 LOW'}")
    
    print("\n" + "="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    if jan21_data is not None:
        if jan28_accuracy > jan21_accuracy:
            print(f"\n✅ ACCURACY IMPROVED: {jan21_accuracy:.2f}% → {jan28_accuracy:.2f}% (+{jan28_accuracy-jan21_accuracy:.2f}%)")
        elif jan28_accuracy < jan21_accuracy:
            print(f"\n⚠️  ACCURACY DECLINED: {jan21_accuracy:.2f}% → {jan28_accuracy:.2f}% ({jan28_accuracy-jan21_accuracy:.2f}%)")
        else:
            print(f"\n➡️  ACCURACY STABLE: {jan28_accuracy:.2f}%")
    
    print(f"\n💡 KEY INSIGHTS:")
    if avg_confidence > 0.6:
        print(f"   ✅ Model confidence is good ({avg_confidence:.1%})")
    else:
        print(f"   ⚠️  Model confidence needs improvement ({avg_confidence:.1%})")
    
    if losing_pct > 50:
        print(f"   ⚠️  Over 50% losing positions ({losing_pct:.1f}%) - consider tighter stops")
    else:
        print(f"   ✅ Less than 50% losing positions ({losing_pct:.1f}%) - good signal quality")
    
    if jan28_total_gain_pct > 0:
        print(f"   ✅ Overall portfolio positive ({jan28_total_gain_pct:+.2f}%)")
    else:
        print(f"   ⚠️  Overall portfolio negative ({jan28_total_gain_pct:+.2f}%) - review signals")
    
    print("\n" + "="*80)

else:
    print("\n❌ Could not load portfolio data for analysis")
    sys.exit(1)
