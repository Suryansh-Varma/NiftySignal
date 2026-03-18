"""
Portfolio Goal Optimizer
-------------------------
Analyzes ALL companies and provides personalized recommendations:
1. BUY: Best stocks NOT in your portfolio (opportunities to add)
2. HOLD/SELL: Recommendations for stocks you already own

Usage:
    python portfolio_goal_optimizer.py --capital 100000 --target 40
    python portfolio_goal_optimizer.py --portfolio "RELIANCE,TCS,INFY" --capital 100000
    python portfolio_goal_optimizer.py --portfolio-file my_portfolio.json
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
NSE_ANNUAL_RETURN = 0.12  # ~12% typical NSE Nifty annual return
RISK_FREE_RATE = 0.07  # ~7% FD rate in India
TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_PER_MONTH = 21


def load_recommendations():
    """Load ML recommendations with buy probabilities - ALL companies."""
    csv_path = Path('results/latest_recommendations.csv')
    if not csv_path.exists():
        raise FileNotFoundError("Run generate_recommendations first!")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} companies for analysis")
    return df


def load_historical_data():
    """Load historical price data for volatility calculation."""
    csv_path = Path('data/processed/universe_data.csv')
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path)


def load_portfolio(portfolio_str=None, portfolio_file=None):
    """
    Load user's current portfolio holdings.
    
    Args:
        portfolio_str: Comma-separated symbols (e.g., "RELIANCE,TCS,INFY")
        portfolio_file: Path to JSON file with portfolio
                       Format: {"holdings": [{"symbol": "RELIANCE", "shares": 10, "avg_price": 2500}, ...]}
    
    Returns:
        dict: {symbol: {"shares": n, "avg_price": p}, ...}
    """
    if portfolio_file and Path(portfolio_file).exists():
        with open(portfolio_file, 'r') as f:
            data = json.load(f)
            portfolio = {}
            for h in data.get('holdings', []):
                symbol = h['symbol'].upper().replace('.NS', '') + '.NS'
                portfolio[symbol] = {
                    'shares': h.get('shares', 0),
                    'avg_price': h.get('avg_price', 0)
                }
            return portfolio
    
    if portfolio_str:
        symbols = [s.strip().upper().replace('.NS', '') + '.NS' for s in portfolio_str.split(',')]
        return {s: {'shares': 0, 'avg_price': 0} for s in symbols}
    
    return {}


def calculate_stock_metrics(hist_df, symbol, lookback_days=60):
    """Calculate historical volatility and returns for a stock."""
    default_metrics = {'volatility': 0.25, 'avg_return': 0.001, 'sharpe': 0.5}
    
    if hist_df is None or len(hist_df) == 0:
        return default_metrics
    
    try:
        stock_data = hist_df[hist_df['symbol'] == symbol].tail(lookback_days)
        if len(stock_data) < 20:
            return default_metrics
        
        returns = stock_data['close'].pct_change().dropna()
        if len(returns) < 10:
            return default_metrics
        
        volatility = returns.std() * np.sqrt(252)  # Annualized
        avg_return = returns.mean() * 252  # Annualized
        sharpe = (avg_return - RISK_FREE_RATE) / volatility if volatility > 0 else 0
        
        return {
            'volatility': volatility,
            'avg_return': avg_return,
            'sharpe': sharpe
        }
    except Exception:
        return default_metrics


def analyze_all_companies(recs_df, hist_df, portfolio):
    """
    Analyze ALL companies and categorize recommendations based on portfolio.
    Optimized for speed - only calculates detailed metrics for portfolio stocks and top candidates.
    
    Returns:
        buy_opportunities: Best stocks NOT in portfolio (sorted by score)
        portfolio_actions: HOLD/SELL recommendations for stocks IN portfolio
    """
    portfolio_symbols = set(portfolio.keys())
    
    # Pre-compute historical metrics only for portfolio stocks (small subset)
    portfolio_metrics = {}
    for symbol in portfolio_symbols:
        portfolio_metrics[symbol] = calculate_stock_metrics(hist_df, symbol)
    
    all_metrics = []
    for _, row in recs_df.iterrows():
        symbol = row['symbol']
        in_portfolio = symbol in portfolio_symbols
        
        # Use pre-computed metrics for portfolio stocks, defaults for others
        if in_portfolio:
            stock_metrics = portfolio_metrics.get(symbol, {'volatility': 0.25, 'avg_return': 0.001, 'sharpe': 0.5})
        else:
            # Use simplified scoring for non-portfolio stocks (faster)
            stock_metrics = {'volatility': 0.25, 'avg_return': 0.001, 'sharpe': 0.5}
        
        # Calculate composite score for ranking
        score = (
            row['buy_prob'] * 0.4 +
            row['confidence'] * 0.3 +
            max(0, stock_metrics['sharpe']) * 0.15 +
            (1 - min(1, stock_metrics['volatility'])) * 0.15
        )
        
        all_metrics.append({
            'symbol': symbol,
            'price': row['close'],
            'signal': row['signal'],
            'buy_prob': row['buy_prob'],
            'sell_prob': row['sell_prob'],
            'confidence': row['confidence'],
            'score': score,
            'in_portfolio': in_portfolio,
            **stock_metrics
        })
    
    metrics_df = pd.DataFrame(all_metrics)
    
    # Split into portfolio and non-portfolio stocks
    portfolio_stocks = metrics_df[metrics_df['in_portfolio']].copy()
    non_portfolio_stocks = metrics_df[~metrics_df['in_portfolio']].copy()
    
    # BUY opportunities: Best non-portfolio stocks with BUY signal
    buy_candidates = non_portfolio_stocks[non_portfolio_stocks['signal'] == 'BUY']
    buy_opportunities = buy_candidates.nlargest(50, 'score')  # Top 50 buy opportunities
    
    # Portfolio actions: What to do with stocks you own
    portfolio_actions = portfolio_stocks.copy()
    for symbol in portfolio_symbols:
        if symbol in portfolio:
            idx = portfolio_actions[portfolio_actions['symbol'] == symbol].index
            if len(idx) > 0:
                portfolio_actions.loc[idx, 'owned_shares'] = portfolio[symbol].get('shares', 0)
                portfolio_actions.loc[idx, 'avg_cost'] = portfolio[symbol].get('avg_price', 0)
    
    return buy_opportunities, portfolio_actions, metrics_df


def estimate_timeline(target_return_pct, expected_monthly_return, confidence_factor=0.7):
    """
    Estimate months needed to achieve target return.
    """
    adjusted_return = expected_monthly_return * confidence_factor
    
    if adjusted_return <= 0:
        return float('inf'), "Not achievable"
    
    months = np.log(1 + target_return_pct) / np.log(1 + adjusted_return)
    months_with_buffer = months * 1.3
    
    return months_with_buffer, f"{int(months_with_buffer)} months ({int(months_with_buffer/12*10)/10} years)"


def create_buy_allocation(buy_opportunities, capital, risk_level='moderate'):
    """
    Create allocation for BUY opportunities (stocks NOT in portfolio).
    """
    if len(buy_opportunities) == 0:
        return None
    
    if risk_level == 'conservative':
        num_stocks = min(15, len(buy_opportunities))
        max_per_stock = 0.10
    elif risk_level == 'moderate':
        num_stocks = min(10, len(buy_opportunities))
        max_per_stock = 0.15
    else:  # aggressive
        num_stocks = min(7, len(buy_opportunities))
        max_per_stock = 0.25
    
    selected = buy_opportunities.head(num_stocks).copy()
    
    base_weight = 1.0 / num_stocks
    selected['weight'] = np.minimum(base_weight, max_per_stock)
    selected['weight'] = selected['weight'] / selected['weight'].sum()
    
    selected['allocation'] = (selected['weight'] * capital).round(0)
    selected['shares'] = (selected['allocation'] / selected['price']).astype(int)
    selected['actual_allocation'] = selected['shares'] * selected['price']
    
    return selected


def print_portfolio_analysis(portfolio_actions, buy_opportunities, capital, num_buy_to_show=20):
    """Print comprehensive portfolio analysis."""
    
    print("\n" + "="*70)
    print("  📊 COMPLETE PORTFOLIO ANALYSIS - ALL COMPANIES ANALYZED")
    print("="*70)
    
    # SECTION 1: Your Portfolio Holdings (HOLD/SELL recommendations)
    if len(portfolio_actions) > 0:
        print("\n" + "-"*70)
        print("  🔒 YOUR PORTFOLIO HOLDINGS - HOLD/SELL RECOMMENDATIONS")
        print("-"*70)
        print(f"  {'Symbol':<18} {'Price':>10} {'Signal':>8} {'Action':>10} {'Buy%':>8} {'Sell%':>8} {'Score':>8}")
        print(f"  {'-'*68}")
        
        # Sort portfolio by signal priority (SELL first, then HOLD, then BUY)
        signal_order = {'SELL': 0, 'HOLD': 1, 'BUY': 2}
        portfolio_sorted = portfolio_actions.sort_values(
            by=['signal', 'sell_prob'], 
            key=lambda x: x.map(signal_order) if x.name == 'signal' else x,
            ascending=[True, False]
        )
        
        sell_stocks = portfolio_sorted[portfolio_sorted['signal'] == 'SELL']
        hold_stocks = portfolio_sorted[portfolio_sorted['signal'] == 'HOLD']
        buy_in_portfolio = portfolio_sorted[portfolio_sorted['signal'] == 'BUY']
        
        if len(sell_stocks) > 0:
            print(f"\n  ❌ SELL ({len(sell_stocks)} stocks):")
            for _, stock in sell_stocks.iterrows():
                symbol_clean = stock['symbol'].replace('.NS', '')
                action = "⚠️ SELL"
                print(f"  {symbol_clean:<18} ₹{stock['price']:>9,.2f} {'SELL':>8} {action:>10} "
                      f"{stock['buy_prob']*100:>7.1f}% {stock['sell_prob']*100:>7.1f}% {stock['score']:>7.2f}")
        
        if len(hold_stocks) > 0:
            print(f"\n  ✋ HOLD ({len(hold_stocks)} stocks):")
            for _, stock in hold_stocks.iterrows():
                symbol_clean = stock['symbol'].replace('.NS', '')
                action = "HOLD"
                print(f"  {symbol_clean:<18} ₹{stock['price']:>9,.2f} {'HOLD':>8} {action:>10} "
                      f"{stock['buy_prob']*100:>7.1f}% {stock['sell_prob']*100:>7.1f}% {stock['score']:>7.2f}")
        
        if len(buy_in_portfolio) > 0:
            print(f"\n  ✅ ADD MORE ({len(buy_in_portfolio)} stocks - already owned but good to buy more):")
            for _, stock in buy_in_portfolio.iterrows():
                symbol_clean = stock['symbol'].replace('.NS', '')
                action = "ADD MORE"
                print(f"  {symbol_clean:<18} ₹{stock['price']:>9,.2f} {'BUY':>8} {action:>10} "
                      f"{stock['buy_prob']*100:>7.1f}% {stock['sell_prob']*100:>7.1f}% {stock['score']:>7.2f}")
    else:
        print("\n  ℹ️  No portfolio provided. Use --portfolio to specify your holdings.")
        print("      Example: --portfolio \"RELIANCE,TCS,INFY,HDFC\"")
    
    # SECTION 2: BUY Opportunities (stocks NOT in portfolio)
    print("\n" + "-"*70)
    print(f"  💰 TOP {num_buy_to_show} BUY OPPORTUNITIES - STOCKS NOT IN YOUR PORTFOLIO")
    print("-"*70)
    print(f"  {'Rank':<5} {'Symbol':<18} {'Price':>10} {'Buy%':>8} {'Conf':>8} {'Score':>8} {'Vol':>8}")
    print(f"  {'-'*68}")
    
    for i, (_, stock) in enumerate(buy_opportunities.head(num_buy_to_show).iterrows(), 1):
        symbol_clean = stock['symbol'].replace('.NS', '')
        print(f"  {i:<5} {symbol_clean:<18} ₹{stock['price']:>9,.2f} "
              f"{stock['buy_prob']*100:>7.1f}% {stock['confidence']*100:>7.1f}% "
              f"{stock['score']:>7.2f} {stock['volatility']*100:>7.1f}%")
    
    total_buy_available = len(buy_opportunities)
    if total_buy_available > num_buy_to_show:
        print(f"\n  ... and {total_buy_available - num_buy_to_show} more BUY opportunities available")
    
    return len(portfolio_actions), len(buy_opportunities)


def run_optimizer(capital, target_return_pct, portfolio=None, num_buy_to_show=20):
    """Run the portfolio optimizer with ALL companies analysis."""
    print("\n" + "="*70)
    print("  🎯 PORTFOLIO GOAL OPTIMIZER - COMPLETE ANALYSIS")
    print("="*70)
    print(f"  Investment Capital: ₹{capital:,}")
    print(f"  Target Return: {target_return_pct*100:.0f}%")
    print(f"  Target Amount: ₹{capital * (1 + target_return_pct):,.0f}")
    
    # Load data
    logger.info("Loading recommendations for ALL companies...")
    recs_df = load_recommendations()
    hist_df = load_historical_data()
    
    total_companies = len(recs_df)
    buy_count = len(recs_df[recs_df['signal'] == 'BUY'])
    hold_count = len(recs_df[recs_df['signal'] == 'HOLD'])
    sell_count = len(recs_df[recs_df['signal'] == 'SELL'])
    
    print(f"\n  📈 MARKET OVERVIEW ({total_companies} companies analyzed):")
    print(f"     BUY signals:  {buy_count} stocks ({buy_count/total_companies*100:.1f}%)")
    print(f"     HOLD signals: {hold_count} stocks ({hold_count/total_companies*100:.1f}%)")
    print(f"     SELL signals: {sell_count} stocks ({sell_count/total_companies*100:.1f}%)")
    
    if portfolio is None:
        portfolio = {}
    
    print(f"\n  📁 YOUR PORTFOLIO: {len(portfolio)} stocks")
    
    # Analyze ALL companies
    logger.info("Analyzing all companies...")
    buy_opportunities, portfolio_actions, all_metrics = analyze_all_companies(
        recs_df, hist_df, portfolio
    )
    
    # Print comprehensive analysis
    print_portfolio_analysis(portfolio_actions, buy_opportunities, capital, num_buy_to_show)
    
    # If user has capital, show suggested allocation
    if capital > 0 and len(buy_opportunities) > 0:
        print("\n" + "-"*70)
        print("  💼 SUGGESTED BUY ALLOCATION (for new investments)")
        print("-"*70)
        
        for risk_level in ['conservative', 'moderate', 'aggressive']:
            allocation = create_buy_allocation(buy_opportunities, capital, risk_level)
            if allocation is not None:
                print(f"\n  {risk_level.upper()} ({len(allocation)} stocks, max {['10%','15%','25%'][['conservative','moderate','aggressive'].index(risk_level)]} per stock):")
                print(f"  {'Symbol':<18} {'Price':>10} {'Shares':>8} {'Amount':>12}")
                for _, stock in allocation.iterrows():
                    symbol_clean = stock['symbol'].replace('.NS', '')
                    print(f"  {symbol_clean:<18} ₹{stock['price']:>9,.2f} {stock['shares']:>8} ₹{stock['actual_allocation']:>11,.0f}")
                print(f"  {'Total:':<18} {'':<10} {'':<8} ₹{allocation['actual_allocation'].sum():>11,.0f}")
    
    # Summary statistics
    print("\n" + "="*70)
    print("  📊 SUMMARY")
    print("="*70)
    print(f"  Total companies analyzed: {total_companies}")
    print(f"  Your portfolio stocks: {len(portfolio_actions)}")
    print(f"  BUY opportunities (not in portfolio): {len(buy_opportunities)}")
    
    if len(portfolio_actions) > 0:
        sell_in_portfolio = len(portfolio_actions[portfolio_actions['signal'] == 'SELL'])
        hold_in_portfolio = len(portfolio_actions[portfolio_actions['signal'] == 'HOLD'])
        buy_in_portfolio = len(portfolio_actions[portfolio_actions['signal'] == 'BUY'])
        print(f"\n  Your portfolio breakdown:")
        print(f"     SELL recommended: {sell_in_portfolio} stocks")
        print(f"     HOLD recommended: {hold_in_portfolio} stocks")
        print(f"     BUY MORE recommended: {buy_in_portfolio} stocks")
    
    # Risk warnings
    print("\n" + "="*70)
    print("  ⚠️ IMPORTANT NOTES")
    print("="*70)
    print("  • BUY: Best opportunities NOT in your portfolio")
    print("  • HOLD/SELL: Actions for stocks you already OWN")
    print("  • ML predictions are probabilistic, not guarantees")
    print("  • This is NOT financial advice - consult a SEBI advisor")
    
    # Save results
    results = {
        'capital': capital,
        'target_return_pct': target_return_pct,
        'generated_at': datetime.now().isoformat(),
        'total_companies_analyzed': total_companies,
        'portfolio_holdings': len(portfolio_actions),
        'buy_opportunities_count': len(buy_opportunities),
        'buy_opportunities': buy_opportunities.head(50).to_dict('records'),
        'portfolio_actions': portfolio_actions.to_dict('records') if len(portfolio_actions) > 0 else []
    }
    
    output_path = Path('results/goal_portfolio_plan.json')
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  📁 Results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Portfolio Goal Optimizer - Analyze ALL companies")
    parser.add_argument('--capital', type=float, default=100000, 
                        help='Investment capital in INR (default: 100000)')
    parser.add_argument('--target', type=float, default=40,
                        help='Target return percentage (default: 40)')
    parser.add_argument('--portfolio', type=str, default=None,
                        help='Comma-separated list of your portfolio stocks (e.g., "RELIANCE,TCS,INFY,HDFC")')
    parser.add_argument('--portfolio-file', type=str, default=None,
                        help='Path to JSON file with portfolio holdings')
    parser.add_argument('--num-buy', type=int, default=20,
                        help='Number of BUY recommendations to show (default: 20)')
    
    args = parser.parse_args()
    
    # Load portfolio
    portfolio = load_portfolio(args.portfolio, args.portfolio_file)
    
    run_optimizer(
        capital=args.capital,
        target_return_pct=args.target / 100,
        portfolio=portfolio,
        num_buy_to_show=args.num_buy
    )
