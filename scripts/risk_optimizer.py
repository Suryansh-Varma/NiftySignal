"""
Risk-Based Optimization Engine
Automatically adjusts trading parameters based on macro risk factor
"""

import json
from pathlib import Path
from app.features.risk_factors import RiskFactorCalculator

class RiskOptimizer:
    """Optimize trading parameters based on macro risk level."""
    
    def __init__(self):
        self.calc = RiskFactorCalculator()
        self.macro_risk = self.calc.get_macro_risk_factor()
    
    def get_position_sizing(self) -> dict:
        """
        Adjust position size based on risk.
        
        Risk 0.0-0.3 (Low):     2.0% per position (aggressive)
        Risk 0.3-0.5 (Moderate): 1.5% per position (normal)
        Risk 0.5-0.7 (High):     1.0% per position (defensive)
        Risk 0.7-1.0 (V.High):   0.5% per position (very cautious)
        """
        if self.macro_risk < 0.3:
            return {
                'position_size': 0.02,
                'max_positions': 25,
                'stance': 'Aggressive'
            }
        elif self.macro_risk < 0.5:
            return {
                'position_size': 0.015,
                'max_positions': 20,
                'stance': 'Normal'
            }
        elif self.macro_risk < 0.7:
            return {
                'position_size': 0.01,
                'max_positions': 15,
                'stance': 'Defensive'
            }
        else:
            return {
                'position_size': 0.005,
                'max_positions': 10,
                'stance': 'Very Cautious'
            }
    
    def get_confidence_thresholds(self) -> dict:
        """
        Adjust confidence thresholds based on risk.
        Only trade signals with confidence above threshold.
        """
        if self.macro_risk < 0.3:
            return {
                'buy_confidence_min': 0.40,  # Accept 40%+ confidence
                'sell_confidence_min': 0.35,
                'hold_threshold': 0.50
            }
        elif self.macro_risk < 0.5:
            return {
                'buy_confidence_min': 0.50,
                'sell_confidence_min': 0.40,
                'hold_threshold': 0.55
            }
        elif self.macro_risk < 0.7:
            return {
                'buy_confidence_min': 0.60,  # Need 60%+ confidence
                'sell_confidence_min': 0.45,
                'hold_threshold': 0.60
            }
        else:
            return {
                'buy_confidence_min': 0.70,  # Very conservative
                'sell_confidence_min': 0.50,
                'hold_threshold': 0.65
            }
    
    def get_stop_loss_take_profit(self) -> dict:
        """
        Adjust stop loss and take profit levels based on risk.
        Higher risk = tighter stops, lower targets
        """
        if self.macro_risk < 0.3:
            return {
                'stop_loss': 0.03,       # 3% stop loss
                'take_profit': 0.08,    # 8% target
                'trailing_stop': 0.02   # 2% trailing stop
            }
        elif self.macro_risk < 0.5:
            return {
                'stop_loss': 0.02,       # 2% stop loss
                'take_profit': 0.05,    # 5% target
                'trailing_stop': 0.015
            }
        elif self.macro_risk < 0.7:
            return {
                'stop_loss': 0.015,      # 1.5% stop loss
                'take_profit': 0.04,    # 4% target
                'trailing_stop': 0.01
            }
        else:
            return {
                'stop_loss': 0.01,       # 1% stop loss (tight)
                'take_profit': 0.025,   # 2.5% target (quick gains)
                'trailing_stop': 0.008
            }
    
    def get_sector_filter(self) -> dict:
        """
        Filter sectors based on risk environment.
        """
        if self.macro_risk < 0.3:
            return {
                'preferred': ['Tech', 'Finance', 'Auto', 'Pharma'],
                'avoid': [],
                'description': 'All sectors okay'
            }
        elif self.macro_risk < 0.5:
            return {
                'preferred': ['Finance', 'FMCG', 'Pharma', 'Utilities'],
                'avoid': ['Auto', 'Discretionary'],
                'description': 'Moderate risk - avoid cyclical'
            }
        elif self.macro_risk < 0.7:
            return {
                'preferred': ['FMCG', 'Pharma', 'Utilities', 'Defensive'],
                'avoid': ['Auto', 'Tech', 'Discretionary'],
                'description': 'High risk - focus on defensive'
            }
        else:
            return {
                'preferred': ['Pharma', 'FMCG', 'Utilities'],
                'avoid': ['Auto', 'Tech', 'Finance', 'Cyclicals'],
                'description': 'Very high risk - ultra defensive only'
            }
    
    def get_trade_frequency(self) -> dict:
        """
        Adjust how often to trade based on risk.
        """
        if self.macro_risk < 0.3:
            return {
                'trades_per_day': 'Unlimited',
                'rebalance_frequency': 'Daily',
                'new_entries': 'Aggressive'
            }
        elif self.macro_risk < 0.5:
            return {
                'trades_per_day': '5-10',
                'rebalance_frequency': 'Every 2-3 days',
                'new_entries': 'Normal'
            }
        elif self.macro_risk < 0.7:
            return {
                'trades_per_day': '2-5',
                'rebalance_frequency': 'Weekly',
                'new_entries': 'Selective'
            }
        else:
            return {
                'trades_per_day': '0-2',
                'rebalance_frequency': 'Every 2 weeks',
                'new_entries': 'Very selective, only best setups'
            }
    
    def generate_report(self):
        """Generate optimization report."""
        print("\n" + "="*70)
        print("RISK-BASED OPTIMIZATION REPORT")
        print("="*70)
        
        info = self.calc.get_macro_risk_info()
        print(f"\nMacro Risk Factor: {self.macro_risk:.2f}")
        print(f"Updated: {info.get('last_updated', 'N/A')}")
        print(f"Notes: {info.get('notes', 'N/A')}")
        
        # Position Sizing
        pos_sizing = self.get_position_sizing()
        print(f"\n📊 POSITION SIZING")
        print(f"   Stance: {pos_sizing['stance']}")
        print(f"   Position Size: {pos_sizing['position_size']*100:.1f}% per trade")
        print(f"   Max Positions: {pos_sizing['max_positions']}")
        
        # Confidence Thresholds
        conf = self.get_confidence_thresholds()
        print(f"\n🎯 CONFIDENCE THRESHOLDS")
        print(f"   Buy Confidence Min: {conf['buy_confidence_min']*100:.0f}%")
        print(f"   Sell Confidence Min: {conf['sell_confidence_min']*100:.0f}%")
        print(f"   Hold Range: {conf['hold_threshold']*100:.0f}%")
        
        # Stop Loss / Take Profit
        sl_tp = self.get_stop_loss_take_profit()
        print(f"\n🛑 STOP LOSS & TAKE PROFIT")
        print(f"   Stop Loss: {sl_tp['stop_loss']*100:.2f}%")
        print(f"   Take Profit: {sl_tp['take_profit']*100:.2f}%")
        print(f"   Trailing Stop: {sl_tp['trailing_stop']*100:.2f}%")
        
        # Sector Filter
        sectors = self.get_sector_filter()
        print(f"\n🏢 SECTOR FILTER")
        print(f"   Strategy: {sectors['description']}")
        print(f"   Preferred: {', '.join(sectors['preferred'])}")
        if sectors['avoid']:
            print(f"   Avoid: {', '.join(sectors['avoid'])}")
        
        # Trade Frequency
        freq = self.get_trade_frequency()
        print(f"\n📈 TRADE FREQUENCY")
        print(f"   Trades/Day: {freq['trades_per_day']}")
        print(f"   Rebalance: {freq['rebalance_frequency']}")
        print(f"   New Entries: {freq['new_entries']}")
        
        print("\n" + "="*70)
        print("IMPLEMENTATION TIPS")
        print("="*70)
        
        if self.macro_risk > 0.7:
            print("\n⚠️  VERY HIGH RISK ENVIRONMENT (0.75)")
            print("   • Reduce position sizes to 0.5% max")
            print("   • Only enter trades with 70%+ confidence")
            print("   • Use tight 1% stop losses")
            print("   • Take quick profits at 2.5%")
            print("   • Focus on defensive sectors (Pharma, FMCG)")
            print("   • Hold more cash (30-40% dry powder)")
            print("   • Avoid momentum trading")
            print("   • Consider hedging with puts/downside protection")
        
        print("\n" + "="*70)

def main():
    optimizer = RiskOptimizer()
    optimizer.generate_report()

if __name__ == "__main__":
    main()
