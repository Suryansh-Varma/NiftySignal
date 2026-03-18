
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.metrics import accuracy_score, classification_report

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.config import DATA_PROCESSED_DIR, TradingConfig
from app.features.technical import prepare_features

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def tune_models():
    print("\n" + "="*70)
    print("HYPERPARAMETER TUNING FOR NIFTY SIGNAL MODELS")
    print("="*70)

    # 1. Load Data
    print("\n[1] Loading market data...")
    data_path = DATA_PROCESSED_DIR / "universe_data.csv"
    if not data_path.exists():
        print(f"ERROR: Data file not found at {data_path}")
        return

    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])

    # Filter for Nifty 50 stocks only to speed up tuning
    from app.config import NIFTY_50_UNIVERSE
    df = df[df['symbol'].isin(NIFTY_50_UNIVERSE)].copy()

    # Use recent data for more relevance to current market regime
    cutoff_date = df['date'].max() - timedelta(days=365) # Last 1 year
    df_recent = df[df['date'] >= cutoff_date].copy()
    
    print(f"Using data from {df_recent['date'].min().date()} to {df_recent['date'].max().date()}")
    print(f"Total rows: {len(df_recent)}")

    # 2. Prepare Features
    print("\n[2] Preparing features...")
    X, y = prepare_features(
        df_recent,
        forward_days=TradingConfig.FORWARD_DAYS,
        return_threshold=TradingConfig.RETURN_THRESHOLD_STRICT
    )
    
    # Scale features manually as we are using scikit-learn directly
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"Features ready: {X.shape[1]} features, {X.shape[0]} samples")
    print("Label distribution:")
    print(y.value_counts())

    # 3. Define Parameter Grids
    param_grids = {
        'RandomForest': {
            'model': RandomForestClassifier(random_state=42),
            'params': {
                'n_estimators': [100, 200, 300, 500],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'bootstrap': [True, False],
                'class_weight': [None, 'balanced']
            }
        },
        'GradientBoosting': {
            'model': GradientBoostingClassifier(random_state=42),
            'params': {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'max_depth': [3, 5, 7, 9],
                'min_samples_split': [2, 5, 10],
                'subsample': [0.7, 0.8, 0.9, 1.0]
            }
        },
        'ExtraTrees': {
            'model': ExtraTreesClassifier(random_state=42),
            'params': {
                'n_estimators': [100, 200, 300, 500],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'class_weight': [None, 'balanced']
            }
        }
    }

    # 4. Perform Search
    best_models = {}
    tscv = TimeSeriesSplit(n_splits=5)

    for name, config in param_grids.items():
        print(f"\n[3] Tuning {name}...")
        search = RandomizedSearchCV(
            config['model'],
            config['params'],
            n_iter=5,
            cv=tscv,
            scoring='accuracy',
            n_jobs=1,
            random_state=42,
            verbose=1
        )
        search.fit(X_scaled, y)
        
        print(f"Best Score: {search.best_score_:.4f}")
        print(f"Best Params: {search.best_params_}")
        best_models[name] = {
            'score': search.best_score_,
            'params': search.best_params_,
            'best_estimator': search.best_estimator_
        }

    # 5. Report Results
    print("\n" + "="*70)
    print("TUNING RESULTS SUMMARY")
    print("="*70)
    
    for name, result in best_models.items():
        print(f"{name:16s}: {result['score']:.4f} accuracy")
        
    best_overall_name = max(best_models, key=lambda x: best_models[x]['score'])
    print(f"\nWINNER: {best_overall_name} with {best_models[best_overall_name]['score']:.4f} accuracy")
    
    print("\nNext step: Update MLSignalGenerator with these parameters and implement Ensemble.")

if __name__ == "__main__":
    tune_models()
