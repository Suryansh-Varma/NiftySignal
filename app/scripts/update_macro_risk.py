"""
Script to update the macroeconomic/geopolitical risk factor.

This script allows you to manually update the global risk factor based on:
- Federal Reserve interest rates (FD rate)
- Gold prices
- Geopolitical events
- VIX (market volatility index)
- Oil prices
- Currency volatility
- Global economic indicators

Usage:
    python -m app.scripts.update_macro_risk --risk 0.6 --notes "Fed rate hike expected"
    
Or run interactively:
    python -m app.scripts.update_macro_risk
"""

import argparse
from datetime import datetime
from app.features.risk_factors import RiskFactorCalculator


def get_risk_assessment() -> tuple:
    """Interactive risk assessment questionnaire."""
    print("\n" + "="*60)
    print("MACROECONOMIC & GEOPOLITICAL RISK ASSESSMENT")
    print("="*60)
    
    factors = {}
    weights = []
    
    # Federal Reserve Rate
    print("\n1. Federal Reserve Interest Rate:")
    print("   Current rate: ", end="")
    fed_rate = input()
    if fed_rate:
        factors['fed_rate'] = float(fed_rate)
        print("   Risk level (0-1, higher rate = higher risk): ", end="")
        fed_risk = float(input())
        weights.append(fed_risk * 0.20)
    
    # Gold Price
    print("\n2. Gold Price (USD/oz):")
    print("   Current price: ", end="")
    gold_price = input()
    if gold_price:
        factors['gold_price'] = float(gold_price)
        print("   Risk level (0-1, rising gold = higher risk): ", end="")
        gold_risk = float(input())
        weights.append(gold_risk * 0.15)
    
    # Geopolitical Score
    print("\n3. Geopolitical Tensions:")
    print("   Rate geopolitical risk (0=peaceful, 1=extreme tension): ", end="")
    geo_risk = input()
    if geo_risk:
        factors['geopolitical_score'] = float(geo_risk)
        weights.append(float(geo_risk) * 0.25)
    
    # VIX
    print("\n4. Market Volatility (VIX):")
    print("   Current VIX level: ", end="")
    vix = input()
    if vix:
        factors['vix'] = float(vix)
        # VIX > 20 is high volatility
        vix_risk = min(float(vix) / 40, 1.0)
        weights.append(vix_risk * 0.15)
    
    # Oil Price
    print("\n5. Oil Price (USD/barrel):")
    print("   Current price: ", end="")
    oil_price = input()
    if oil_price:
        factors['oil_price'] = float(oil_price)
        print("   Risk level (0-1, extreme prices = higher risk): ", end="")
        oil_risk = float(input())
        weights.append(oil_risk * 0.10)
    
    # Currency Volatility
    print("\n6. Currency Volatility:")
    print("   Rate currency risk (0=stable, 1=extreme volatility): ", end="")
    currency_risk = input()
    if currency_risk:
        factors['currency_volatility'] = float(currency_risk)
        weights.append(float(currency_risk) * 0.15)
    
    # Calculate overall risk
    if weights:
        overall_risk = sum(weights)
    else:
        overall_risk = 0.5
    
    # Cap at 1.0
    overall_risk = min(overall_risk, 1.0)
    
    print("\n" + "-"*60)
    print(f"CALCULATED OVERALL RISK: {overall_risk:.2f}")
    print("-"*60)
    
    # Get notes
    print("\nAdditional notes (press Enter to skip): ", end="")
    notes = input()
    
    return overall_risk, notes, factors


def main():
    parser = argparse.ArgumentParser(
        description="Update macroeconomic/geopolitical risk factor"
    )
    parser.add_argument(
        "--risk",
        type=float,
        help="Risk factor value (0-1, where 0=low risk, 1=high risk)"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Notes about current conditions"
    )
    parser.add_argument(
        "--fed-rate",
        type=float,
        help="Current Federal Reserve rate (%)"
    )
    parser.add_argument(
        "--gold-price",
        type=float,
        help="Current gold price (USD/oz)"
    )
    parser.add_argument(
        "--vix",
        type=float,
        help="Current VIX level"
    )
    parser.add_argument(
        "--oil-price",
        type=float,
        help="Current oil price (USD/barrel)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--view",
        action="store_true",
        help="View current risk factor information"
    )
    
    args = parser.parse_args()
    
    calculator = RiskFactorCalculator()
    
    # View current risk
    if args.view:
        info = calculator.get_macro_risk_info()
        print("\n" + "="*60)
        print("CURRENT MACRO RISK FACTOR")
        print("="*60)
        print(f"Risk Factor: {info['risk_factor']:.2f}")
        print(f"Last Updated: {info.get('last_updated', 'Never')}")
        print(f"Notes: {info.get('notes', 'N/A')}")
        print("\nContributing Factors:")
        for key, value in info.get('factors', {}).items():
            print(f"  - {key}: {value}")
        print("="*60)
        return
    
    # Interactive mode
    if args.interactive or args.risk is None:
        risk_factor, notes, factors = get_risk_assessment()
    else:
        risk_factor = args.risk
        notes = args.notes
        factors = {}
        if args.fed_rate is not None:
            factors['fed_rate'] = args.fed_rate
        if args.gold_price is not None:
            factors['gold_price'] = args.gold_price
        if args.vix is not None:
            factors['vix'] = args.vix
        if args.oil_price is not None:
            factors['oil_price'] = args.oil_price
    
    # Confirm
    print("\n" + "="*60)
    print("CONFIRM UPDATE")
    print("="*60)
    print(f"Risk Factor: {risk_factor:.2f}")
    print(f"Notes: {notes}")
    print(f"Factors: {factors}")
    print("\nProceed? (y/n): ", end="")
    
    confirm = input().lower()
    if confirm == 'y':
        calculator.update_macro_risk_factor(
            risk_factor=risk_factor,
            notes=notes,
            factors=factors
        )
        print("\n✓ Macro risk factor updated successfully!")
        print(f"  Risk level: {risk_factor:.2f} ({get_risk_label(risk_factor)})")
        print(f"  File: {calculator.macro_risk_file}")
    else:
        print("\n✗ Update cancelled.")


def get_risk_label(risk: float) -> str:
    """Get descriptive label for risk level."""
    if risk < 0.2:
        return "Very Low Risk"
    elif risk < 0.4:
        return "Low Risk"
    elif risk < 0.6:
        return "Moderate Risk"
    elif risk < 0.8:
        return "High Risk"
    else:
        return "Very High Risk"


if __name__ == "__main__":
    main()
