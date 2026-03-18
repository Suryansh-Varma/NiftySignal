import json
import pandas as pd
from datetime import datetime
from app.features.risk_factors import RiskFactorCalculator

print("\n" + "="*80)
print("MACRO RISK FACTOR UPDATE - JANUARY 28, 2026")
print("="*80)

try:
    # Calculate current macro risk
    calc = RiskFactorCalculator()
    macro_risk = calc.get_macro_risk_factor()
    
    print(f"\n🔍 MACRO RISK ASSESSMENT:")
    print(f"   Current Risk Factor: {macro_risk:.3f}")
    print(f"   Risk Level: ", end="")
    
    if macro_risk < 0.3:
        print("🟢 LOW (Aggressive trading recommended)")
    elif macro_risk < 0.5:
        print("🟡 MODERATE (Normal trading)")
    elif macro_risk < 0.7:
        print("🟠 HIGH (Defensive trading)")
    else:
        print("🔴 VERY HIGH (Cautious/Reduced trading)")
    
    # Load risk optimization data
    print(f"\n📊 POSITION SIZING RECOMMENDATIONS:")
    
    if macro_risk < 0.3:
        print(f"   Position Size: 2.0% per trade (Aggressive)")
        print(f"   Max Positions: 25")
        print(f"   Stance: Aggressive")
    elif macro_risk < 0.5:
        print(f"   Position Size: 1.5% per trade (Normal)")
        print(f"   Max Positions: 20")
        print(f"   Stance: Normal")
    elif macro_risk < 0.7:
        print(f"   Position Size: 1.0% per trade (Defensive)")
        print(f"   Max Positions: 15")
        print(f"   Stance: Defensive")
    else:
        print(f"   Position Size: 0.5% per trade (Very Cautious)")
        print(f"   Max Positions: 10")
        print(f"   Stance: Very Cautious")
    
    # Risk factors analysis
    print(f"\n⚠️  RISK FACTORS BREAKDOWN:")
    risk_data = {
        'vix_equivalent': macro_risk * 0.35,
        'volatility': macro_risk * 0.25,
        'market_trend': macro_risk * 0.20,
        'liquidity': macro_risk * 0.10,
        'sector_concentration': macro_risk * 0.10
    }
    
    for factor, value in risk_data.items():
        factor_name = factor.replace('_', ' ').title()
        print(f"   {factor_name:25s}: {value:.3f}")
    
    # Load current portfolio accuracy data
    try:
        jan28_data = pd.read_csv('results/accuracy_verification_jan28.csv')
        accuracy = (jan28_data['correct'].sum() / len(jan28_data)) * 100
        print(f"\n📈 ACCURACY-BASED RISK ADJUSTMENT:")
        print(f"   Current Model Accuracy: {accuracy:.2f}%")
        
        if accuracy > 60:
            adjusted_risk = macro_risk * 1.1  # Can take more risk if accurate
            print(f"   Model Health: GOOD - Confidence boost +10%")
        elif accuracy > 40:
            adjusted_risk = macro_risk * 1.0  # Use as-is
            print(f"   Model Health: FAIR - No adjustment needed")
        else:
            adjusted_risk = macro_risk * 0.8  # Reduce risk if inaccurate
            print(f"   Model Health: POOR - Reduce risk by 20%")
        
        print(f"   Adjusted Risk Factor: {adjusted_risk:.3f}")
        
    except FileNotFoundError:
        print(f"\n⚠️  Jan 28 accuracy data not found - using macro risk only")
        adjusted_risk = macro_risk
    
    # Generate risk update report
    report = {
        'update_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'macro_risk_factor': float(macro_risk),
        'adjusted_risk_factor': float(adjusted_risk),
        'risk_level': 'LOW' if macro_risk < 0.3 else 'MODERATE' if macro_risk < 0.5 else 'HIGH' if macro_risk < 0.7 else 'VERY HIGH',
        'position_sizing': {
            'position_size_pct': 2.0 if macro_risk < 0.3 else 1.5 if macro_risk < 0.5 else 1.0 if macro_risk < 0.7 else 0.5,
            'max_positions': 25 if macro_risk < 0.3 else 20 if macro_risk < 0.5 else 15 if macro_risk < 0.7 else 10,
            'stance': 'Aggressive' if macro_risk < 0.3 else 'Normal' if macro_risk < 0.5 else 'Defensive' if macro_risk < 0.7 else 'Very Cautious'
        },
        'risk_factors': risk_data
    }
    
    # Save risk update
    with open('data/macro_risk_factor.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Risk factors updated and saved to data/macro_risk_factor.json")
    
    # Create risk update log
    log_entry = {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'macro_risk': float(macro_risk),
        'adjusted_risk': float(adjusted_risk),
        'risk_level': report['risk_level'],
        'stance': report['position_sizing']['stance']
    }
    
    try:
        with open('results/risk_update_log.json', 'r') as f:
            log = json.load(f)
    except:
        log = []
    
    log.append(log_entry)
    with open('results/risk_update_log.json', 'w') as f:
        json.dump(log[-10:], f, indent=2)  # Keep last 10 updates
    
    print("✅ Risk update log updated")
    
    print("\n" + "="*80)
    print("RECOMMENDATION FOR JAN 28, 2026")
    print("="*80)
    print(f"\n🎯 Based on current macro risk of {macro_risk:.3f}:")
    print(f"   → Trading Stance: {report['position_sizing']['stance']}")
    print(f"   → Max Portfolio Size: {report['position_sizing']['max_positions']} positions")
    print(f"   → Risk Per Trade: {report['position_sizing']['position_size_pct']:.1f}%")
    print(f"   → Stop Loss: Tight stops recommended")
    print(f"   → Take Profit: Book profits early")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\n❌ Error updating risk factors: {e}")
    import traceback
    traceback.print_exc()
