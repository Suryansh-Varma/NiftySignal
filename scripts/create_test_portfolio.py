"""
Create a Test Portfolio for Prediction Accuracy Validation

This portfolio includes diverse stocks across:
- Different sectors (Pharma, FMCG, Tech, Finance, Auto)
- Different signals (HOLD, SELL, and some high-confidence)
- Defensive + Risky stocks (to test in 0.75 risk environment)
"""

from app.portfolio.manager import PortfolioManager
from datetime import datetime

def create_test_portfolio():
    """Create a diversified test portfolio."""
    
    manager = PortfolioManager()
    user_id = "test_accuracy_user"
    
    # Create or get portfolio
    portfolio = manager.get_portfolio(user_id)
    if portfolio is None:
        portfolio = manager.create_portfolio(user_id, "Accuracy Test Portfolio")
    
    print("\n" + "="*70)
    print("CREATING TEST PORTFOLIO FOR ACCURACY VALIDATION")
    print("="*70)
    
    # Portfolio composition based on latest recommendations
    test_stocks = [
        # DEFENSIVE SECTORS (Should perform well in 0.75 risk)
        {
            'symbol': 'CIPLA.NS',
            'shares': 100,
            'price': 1516.60,
            'sector': 'Pharma',
            'confidence': 0.706,
            'signal': 'HOLD',
            'rationale': 'Defensive sector, high confidence HOLD'
        },
        {
            'symbol': 'SUNPHARMA.NS',
            'shares': 80,
            'price': 1831.60,
            'sector': 'Pharma',
            'confidence': 0.577,
            'signal': 'HOLD',
            'rationale': 'Defensive pharma, moderate confidence'
        },
        {
            'symbol': 'DRREDDY.NS',
            'shares': 60,
            'price': 1275.20,
            'sector': 'Pharma',
            'confidence': 0.443,
            'signal': 'HOLD',
            'rationale': 'Pharma with lower confidence'
        },
        {
            'symbol': 'NESTLEIND.NS',
            'shares': 50,
            'price': 1242.40,
            'sector': 'FMCG',
            'confidence': 0.791,
            'signal': 'HOLD',
            'rationale': 'Defensive FMCG, high confidence'
        },
        {
            'symbol': 'BRITANNIA.NS',
            'shares': 40,
            'price': 5500.00,  # Approximate
            'sector': 'FMCG',
            'confidence': 0.65,  # Estimated
            'signal': 'HOLD',
            'rationale': 'Defensive FMCG staple'
        },
        
        # RISKY SECTORS (Should underperform in 0.75 risk - test defensive strategy)
        {
            'symbol': 'TATAMOTORS.NS',
            'shares': 200,
            'price': 357.80,
            'sector': 'Auto',
            'confidence': 0.632,
            'signal': 'SELL',
            'rationale': 'SELL signal - test if model correctly predicts downside'
        },
        {
            'symbol': 'HEROMOTOCO.NS',
            'shares': 30,
            'price': 6174.50,
            'sector': 'Auto',
            'confidence': 0.877,
            'signal': 'HOLD',
            'rationale': 'High confidence HOLD in risky auto sector'
        },
        {
            'symbol': 'MARUTI.NS',
            'shares': 50,
            'price': 11000.00,  # Approximate
            'sector': 'Auto',
            'confidence': 0.55,  # Estimated
            'signal': 'HOLD',
            'rationale': 'Auto sector in high-risk environment'
        },
        
        # TECH SECTOR (Should be cautious in high-risk)
        {
            'symbol': 'INFY.NS',
            'shares': 150,
            'price': 1578.70,
            'sector': 'Tech',
            'confidence': 0.828,
            'signal': 'HOLD',
            'rationale': 'High confidence tech hold'
        },
        {
            'symbol': 'TCS.NS',
            'shares': 80,
            'price': 3100.00,  # Approximate
            'sector': 'Tech',
            'confidence': 0.70,  # Estimated
            'signal': 'HOLD',
            'rationale': 'Blue chip tech'
        },
        {
            'symbol': 'HCLTECH.NS',
            'shares': 120,
            'price': 1610.40,
            'sector': 'Tech',
            'confidence': 0.606,
            'signal': 'HOLD',
            'rationale': 'Moderate tech hold'
        },
        
        # FINANCE SECTOR (Should be cautious)
        {
            'symbol': 'HDFCBANK.NS',
            'shares': 100,
            'price': 1007.85,
            'sector': 'Finance',
            'confidence': 0.573,
            'signal': 'HOLD',
            'rationale': 'Banking leader'
        },
        {
            'symbol': 'ICICIBANK.NS',
            'shares': 120,
            'price': 1391.50,
            'sector': 'Finance',
            'confidence': 0.512,
            'signal': 'HOLD',
            'rationale': 'Private bank'
        },
        {
            'symbol': 'KOTAKBANK.NS',
            'shares': 80,
            'price': 2110.20,
            'sector': 'Finance',
            'confidence': 0.600,
            'signal': 'HOLD',
            'rationale': 'Premium banking'
        },
        
        # OTHER SECTORS (Mixed)
        {
            'symbol': 'RELIANCE.NS',
            'shares': 100,
            'price': 1549.10,
            'sector': 'Energy/Retail',
            'confidence': 0.647,
            'signal': 'HOLD',
            'rationale': 'Diversified conglomerate'
        },
        {
            'symbol': 'TITAN.NS',
            'shares': 60,
            'price': 3874.30,
            'sector': 'Consumer',
            'confidence': 0.494,
            'signal': 'HOLD',
            'rationale': 'Consumer discretionary'
        },
        {
            'symbol': 'BHARTIARTL.NS',
            'shares': 100,
            'price': 2103.80,
            'sector': 'Telecom',
            'confidence': 0.744,
            'signal': 'HOLD',
            'rationale': 'Utility-like telecom'
        },
        {
            'symbol': 'ASIANPAINT.NS',
            'shares': 70,
            'price': 2874.40,
            'sector': 'Materials',
            'confidence': 0.840,
            'signal': 'HOLD',
            'rationale': 'High confidence materials'
        }
    ]
    
    # Add stocks to portfolio
    total_investment = 0
    print("\nAdding stocks to portfolio:")
    print("-" * 70)
    
    for stock in test_stocks:
        investment = stock['shares'] * stock['price']
        total_investment += investment
        
        try:
            manager.add_stock(
                user_id=user_id,
                symbol=stock['symbol'],
                shares=stock['shares'],
                avg_price=stock['price'],
                purchase_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            print(f"✓ {stock['symbol']:<20} | {stock['sector']:<15} | "
                  f"{stock['shares']:>4} shares @ Rs{stock['price']:>8,.2f} | "
                  f"{stock['signal']:<4} ({stock['confidence']:.1%})")
        except Exception as e:
            print(f"✗ {stock['symbol']:<20} | Error: {e}")
    
    print("-" * 70)
    print(f"Total Investment: Rs {total_investment:,.2f}")
    print(f"Total Stocks: {len(test_stocks)}")
    
    # Portfolio breakdown
    print("\n" + "="*70)
    print("PORTFOLIO COMPOSITION")
    print("="*70)
    
    sectors = {}
    signals = {'HOLD': 0, 'SELL': 0, 'BUY': 0}
    
    for stock in test_stocks:
        sector = stock['sector']
        sectors[sector] = sectors.get(sector, 0) + stock['shares'] * stock['price']
        signals[stock['signal']] = signals.get(stock['signal'], 0) + 1
    
    print("\nBy Sector:")
    for sector, amount in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
        pct = (amount / total_investment) * 100
        print(f"  {sector:<20} Rs {amount:>12,.2f} ({pct:>5.1f}%)")
    
    print("\nBy Signal:")
    for signal, count in signals.items():
        print(f"  {signal:<10} {count} stocks")
    
    print("\n" + "="*70)
    print("TEST STRATEGY")
    print("="*70)
    
    print("\n📊 EXPECTED BEHAVIOR (Risk = 0.75 HIGH)")
    print("\n✅ Should OUTPERFORM:")
    print("  • Pharma stocks (CIPLA, SUNPHARMA, DRREDDY)")
    print("  • FMCG stocks (NESTLEIND, BRITANNIA)")
    print("  • These are defensive in high-risk environment")
    
    print("\n⚠️ Should UNDERPERFORM:")
    print("  • Auto stocks (TATAMOTORS, HEROMOTOCO, MARUTI)")
    print("  • Tech stocks (INFY, TCS, HCLTECH)")
    print("  • Finance stocks (HDFCBANK, ICICIBANK, KOTAKBANK)")
    print("  • These are risky in high-risk environment")
    
    print("\n🎯 KEY TEST:")
    print("  • TATAMOTORS SELL (63.2%) - Should decline")
    print("  • If defensive outperform risky → Model is CORRECT")
    print("  • If risky outperform defensive → Market risk lower than 0.75")
    
    print("\n" + "="*70)
    print("TRACKING INSTRUCTIONS")
    print("="*70)
    
    print("\n1. Save this portfolio composition")
    print("2. Check prices again in 1 week (Jan 28, 2026)")
    print("3. Calculate actual returns by sector")
    print("4. Compare with model predictions")
    print("5. Validate if risk-based strategy worked")
    
    print("\n" + "="*70)
    print("✅ TEST PORTFOLIO CREATED")
    print("="*70)
    print(f"\nPortfolio ID: {user_id}")
    print(f"Total Value: Rs {total_investment:,.2f}")
    print(f"Stocks: {len(test_stocks)}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    return portfolio, test_stocks, total_investment


if __name__ == "__main__":
    portfolio, stocks, investment = create_test_portfolio()
