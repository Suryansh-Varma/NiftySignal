"""
Evaluate goal-based strategies and recommend the best approach.
Computes expected portfolio return based on recommendation weights and probabilities.
"""
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

STRATEGIES = {
    'conservative': {
        'csv': RESULTS_DIR / 'latest_goal_recommendations_conservative.csv',
        'target_return': 0.05,
        'horizon_days': 126,
        'description': 'Lower risk, steady growth'
    },
    'moderate': {
        'csv': RESULTS_DIR / 'latest_goal_recommendations_moderate.csv',
        'target_return': 0.10,
        'horizon_days': 126,
        'description': 'Balanced risk-reward'
    },
    'aggressive': {
        'csv': RESULTS_DIR / 'latest_goal_recommendations_aggressive.csv',
        'target_return': 0.15,
        'horizon_days': 63,
        'description': 'Higher risk, faster returns'
    }
}

def evaluate_strategy(name: str, cfg: dict) -> dict:
    csv_path = cfg['csv']
    if not csv_path.exists():
        return {
            'strategy': name,
            'available': False,
            'reason': f"Recommendations CSV not found: {csv_path}"
        }
    df = pd.read_csv(csv_path)
    if df.empty:
        return {
            'strategy': name,
            'available': False,
            'reason': "No recommendations available"
        }
    # Ensure required columns
    for col in ['weight', 'buy_prob', 'confidence']:
        if col not in df.columns:
            return {
                'strategy': name,
                'available': False,
                'reason': f"Missing column '{col}' in {csv_path.name}"
            }
    # Weighted confidence and expected return
    weights = df['weight'].astype(float)
    probs = df['buy_prob'].astype(float)
    weighted_confidence = float((weights * probs).sum())  # in [0,1]
    expected_return_pct = weighted_confidence * cfg['target_return']  # portfolio expectation
    latest_date = pd.to_datetime(df['date']).max()

    return {
        'strategy': name,
        'available': True,
        'target_return_pct': cfg['target_return'],
        'horizon_days': cfg['horizon_days'],
        'weighted_confidence_pct': round(weighted_confidence * 100, 2),
        'expected_return_pct': round(expected_return_pct * 100, 2),
        'latest_recommendation_date': latest_date.strftime('%Y-%m-%d') if pd.notnull(latest_date) else None,
        'description': cfg['description']
    }

def recommend_best(strategies: dict) -> dict:
    evaluations = []
    for name, cfg in strategies.items():
        evaluations.append(evaluate_strategy(name, cfg))

    # Filter out unavailable
    available = [e for e in evaluations if e.get('available')]
    if not available:
        return {
            'recommended': None,
            'evaluations': evaluations,
            'reason': 'No available strategies with recommendations.'
        }
    # Choose max expected_return_pct
    best = max(available, key=lambda e: e.get('expected_return_pct', 0.0))
    return {
        'recommended': best['strategy'],
        'evaluations': evaluations,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    rec = recommend_best(STRATEGIES)
    out_path = RESULTS_DIR / 'goal_strategy_evaluation.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rec, f, indent=2)
    print(f"Wrote evaluation to {out_path}")

if __name__ == '__main__':
    main()
