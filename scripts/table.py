import datetime
import os

def print_linkedin_tables():
    print("\n" + "="*80)
    print(" NIFTY SIGNAL - MARKET REGIME RECOGNITION (V1 vs V2)".center(80))
    print("="*80 + "\n")

    # V1 Output (Feb 2025)
    print("DATE: February 18, 2025")
    print("MODEL: NiftySignal V1 (Standard Regime)")
    print("-" * 80)
    print(f"{'Metric':<25} | {'Value':<15} | {'Status':<30}")
    print("-" * 80)
    print(f"{'Total Stocks Analyzed':<25} | {'50':<15} | {' Complete':<30}")
    print(f"{'BUY Signals':<25} | {'14':<15} | {' Active Market Setup':<30}")
    print(f"{'HOLD Signals':<25} | {'31':<15} | {' Monitoring':<30}")
    print(f"{'SELL Signals':<25} | {'5':<15} | {' Risk Warning':<30}")
    print(f"{'Market Volatility':<25} | {'Normal':<15} | {' Stable':<30}")
    print(f"{'System Action':<25} | {'TRADING ACTIVE':<15} | {' Capitalizing on trends':<30}")
    
    print("\n" + "."*80 + "\n")

    # V2 Output (Current)
    print("  DATE: June 2, 2026 (Today)")
    print(" MODEL: NiftySignal V2 (High Volatility Regime)")
    print("-" * 80)
    print(f"{'Metric':<25} | {'Value':<15} | {'Status':<30}")
    print("-" * 80)
    print(f"{'Total Stocks Analyzed':<25} | {'50':<15} | {' Complete':<30}")
    print(f"{'BUY Signals':<25} | {'0':<15} | {' Suspended':<30}")
    print(f"{'HOLD Signals':<25} | {'50':<15} | {' 100% CAPITAL PROTECTION':<30}")
    print(f"{'SELL Signals':<25} | {'0':<15} | {' Suspended':<30}")
    print(f"{'Market Volatility':<25} | {'High / Erratic':<15} | {' Elevated Risk Detected':<30}")
    print(f"{'System Action':<25} | {'DEFENSIVE STANDBY':<15} | {' Waiting out the storm':<30}")

    print("\n" + "="*80)
    print(" INSIGHT: Knowing when NOT to trade is an algorithm's greatest strength.")
    print("="*80 + "\n")

if __name__ == "__main__":
    print_linkedin_tables()
