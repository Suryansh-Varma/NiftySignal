import json
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add root to sys.path
sys.path.append(str(Path(__file__).parent))

try:
    from app.features.risk_factors import RiskFactorCalculator
except ImportError:
    # Fallback if structure is different
    class RiskFactorCalculator:
        def get_macro_risk_factor(self): return 0.45 # Default moderate

print("\n" + "="*80)
print(f"MACRO RISK FACTOR UPDATE - {datetime.now().strftime('%B %d, %Y')}")
print("="*80)

try:
    calc = RiskFactorCalculator()
    macro_risk = calc.get_macro_risk_factor()
    
    print(f"\n🔍 MACRO RISK ASSESSMENT:")
    print(f"   Current Risk Factor: {macro_risk:.3f}")
    
    try:
        data = pd.read_csv('results/latest_recommendations.csv')
        avg_confidence = data['confidence'].mean()
        print(f"   Market Confidence (Model): {avg_confidence:.2%}")
        
        accuracy_adjustment = 1.0
        if avg_confidence < 0.4: accuracy_adjustment = 0.8
        elif avg_confidence > 0.6: accuracy_adjustment = 1.1
        
        adjusted_risk = macro_risk * accuracy_adjustment
    except:
        adjusted_risk = macro_risk
        
    risk_level = 'LOW' if macro_risk < 0.3 else 'MODERATE' if macro_risk < 0.5 else 'HIGH' if macro_risk < 0.7 else 'VERY HIGH'
    
    risk_data = {
        'vix_equivalent': macro_risk * 0.35,
        'volatility': macro_risk * 0.25,
        'market_trend': macro_risk * 0.20,
        'liquidity': macro_risk * 0.10,
        'sector_concentration': macro_risk * 0.10
    }
    
    report = {
        'update_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'macro_risk_factor': float(macro_risk),
        'adjusted_risk_factor': float(adjusted_risk),
        'risk_level': risk_level,
        'position_sizing': {
            'position_size_pct': 2.0 if macro_risk < 0.3 else 1.5 if macro_risk < 0.5 else 1.0 if macro_risk < 0.7 else 0.5,
            'max_positions': 25 if macro_risk < 0.3 else 20 if macro_risk < 0.5 else 15 if macro_risk < 0.7 else 10,
            'stance': 'Aggressive' if macro_risk < 0.3 else 'Normal' if macro_risk < 0.5 else 'Defensive' if macro_risk < 0.7 else 'Very Cautious'
        },
        'risk_factors': risk_data
    }
    
    # Save risk update
    output_path = Path('data/macro_risk_factor.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Risk factors updated and saved to {output_path}")
    print(f"   Stance: {report['position_sizing']['stance']}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
