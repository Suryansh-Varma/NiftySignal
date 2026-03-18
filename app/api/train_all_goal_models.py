"""
Train multiple goal-based portfolio models with different risk/return profiles.
Creates Conservative, Moderate, and Aggressive strategies.
"""
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import (
    DATA_PROCESSED_DIR as DATA_DIR,
    MODELS_DIR,
    RESULTS_DIR,
    GoalConfig
)
from app.features.technical import add_technical_features
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Strategy configurations
STRATEGIES = {
    'conservative': {
        'target_return': 0.05,  # 5%
        'horizon_days': 126,     # 6 months
        'description': 'Lower risk, steady growth',
        'capital': GoalConfig.CAPITAL_INR
    },
    'moderate': {
        'target_return': 0.10,  # 10%
        'horizon_days': 126,     # 6 months
        'description': 'Balanced risk-reward',
        'capital': GoalConfig.CAPITAL_INR
    },
    'aggressive': {
        'target_return': 0.15,  # 15%
        'horizon_days': 63,      # 3 months
        'description': 'Higher risk, faster returns',
        'capital': GoalConfig.CAPITAL_INR
    }
}


def prepare_goal_features(
    df: pd.DataFrame,
    horizon_days: int,
    target_return: float
) -> tuple:
    """Prepare features and labels for goal-based model."""
    # Filter out missing data rows if column exists
    if 'missing' in df.columns:
        df = df[df['missing'] == False].copy()
    
    # Add technical features
    df_features = add_technical_features(df)
    
    # Calculate forward returns for each symbol
    symbols = df_features['symbol'].unique()
    dfs = []
    
    for sym in symbols:
        temp = df_features[df_features['symbol'] == sym].copy()
        temp = temp.sort_values('date')
        
        # Calculate forward return over horizon
        temp['forward_return'] = temp['close'].shift(-horizon_days) / temp['close'] - 1
        
        # Binary label: 1 if achieves target, 0 otherwise
        temp['achieves_goal'] = (temp['forward_return'] >= target_return).astype(int)
        
        dfs.append(temp)
    
    df_labeled = pd.concat(dfs, ignore_index=True)
    
    # Select features
    min_rows = df_labeled.groupby('symbol').size().min()
    
    if min_rows >= 50:
        feature_columns = [
            'rsi_14', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower', 'atr',
            'adx', 'returns_1d', 'returns_5d', 'returns_20d',
            'volatility_20d', 'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50'
        ]
    elif min_rows >= 20:
        feature_columns = [
            'rsi_14', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower', 'atr',
            'adx', 'returns_1d', 'returns_5d',
            'price_to_sma_10', 'price_to_sma_20'
        ]
    else:
        feature_columns = [
            'rsi_14', 'macd', 'macd_signal',
            'returns_1d', 'returns_5d',
            'price_to_sma_10'
        ]
    
    # Drop NaN rows
    df_ml = df_labeled.dropna(subset=feature_columns + ['achieves_goal'])
    
    if len(df_ml) == 0:
        raise ValueError(f"No valid samples after feature preparation for {horizon_days}-day horizon")
    
    X = df_ml[feature_columns]
    y = df_ml['achieves_goal']
    
    return X, y, df_ml, feature_columns


def generate_goal_recommendations(
    model: RandomForestClassifier,
    df: pd.DataFrame,
    feature_columns: list,
    capital: float,
    top_n: int = 15
) -> pd.DataFrame:
    """Generate portfolio allocation recommendations."""
    # Get latest data point for each symbol
    latest = df.sort_values('date').groupby('symbol').tail(1).copy()
    
    # Get features
    X_latest = latest[feature_columns]
    
    # Predict probabilities
    probs = model.predict_proba(X_latest)
    
    # Extract probability of achieving goal (class 1)
    buy_prob = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
    
    # Create recommendations dataframe
    recommendations = pd.DataFrame({
        'symbol': latest['symbol'].values,
        'date': latest['date'].values,
        'close': latest['close'].values,
        'buy_prob': buy_prob,
        'confidence': buy_prob * 100
    })
    
    # Sort by confidence and take top N
    recommendations = recommendations.sort_values('buy_prob', ascending=False).head(top_n)
    
    # Apply softmax to get allocation weights
    exp_probs = np.exp(recommendations['buy_prob'].values - recommendations['buy_prob'].max())  # Numerical stability
    softmax_weights = exp_probs / exp_probs.sum()
    
    recommendations['weight'] = softmax_weights
    recommendations['allocation_inr'] = (softmax_weights * capital).round(2)
    
    recommendations = recommendations.reset_index(drop=True)
    
    return recommendations


def train_strategy(strategy_name: str, config: dict, df: pd.DataFrame):
    """Train a single strategy model."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TRAINING {strategy_name.upper()} STRATEGY")
    logger.info(f"Target: {config['target_return']*100}% return in {config['horizon_days']} days")
    logger.info(f"Description: {config['description']}")
    logger.info("=" * 80)
    
    # Prepare features
    X, y, df_labeled, feature_columns = prepare_goal_features(
        df,
        horizon_days=config['horizon_days'],
        target_return=config['target_return']
    )
    
    logger.info(f"Prepared {len(X)} samples with {len(feature_columns)} features")
    logger.info(f"Positive samples (achieving {config['target_return']*100}%): {y.sum()} ({y.mean()*100:.1f}%)")
    
    if y.sum() < 5:
        logger.warning(f"⚠️  Very few positive samples ({y.sum()})! Results may be unreliable.")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.sum() >= 10 else None
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    logger.info(f"Train accuracy: {train_score:.2%}, Test accuracy: {test_score:.2%}")
    
    # Save model
    MODELS_DIR.mkdir(exist_ok=True)
    model_path = MODELS_DIR / f"goal_model_{strategy_name}.pkl"
    
    joblib.dump({
        'model': model,
        'feature_columns': feature_columns,
        'horizon_days': config['horizon_days'],
        'target_return': config['target_return'],
        'strategy_name': strategy_name,
        'description': config['description']
    }, model_path)
    
    logger.info(f"Model saved to {model_path}")
    
    # Generate recommendations
    recommendations = generate_goal_recommendations(
        model,
        df_labeled,
        feature_columns,
        capital=config['capital'],
        top_n=15
    )
    
    # Save recommendations
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / f"latest_goal_recommendations_{strategy_name}.csv"
    recommendations.to_csv(output_path, index=False)
    logger.info(f"Recommendations saved to {output_path}")
    
    # Display recommendations
    today = datetime.now()
    target_date = today + timedelta(days=config['horizon_days'] * 7 // 5)
    
    print(f"\n{'='*80}")
    print(f"{strategy_name.upper()} STRATEGY - ₹{config['capital']:,.0f}")
    print(f"Target: {config['target_return']*100}% in {config['horizon_days']} days (~{config['horizon_days']//21} months)")
    print(f"Invest: {today.strftime('%Y-%m-%d')} → Exit: {target_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}")
    print(f"\nTop {min(10, len(recommendations))} Stock Picks:")
    print(f"{'-'*80}")
    
    for idx, row in recommendations.head(10).iterrows():
        print(f"{row['symbol']:15s} | ₹{row['close']:>8,.2f} | "
              f"Confidence: {row['confidence']:>5.1f}% | "
              f"Weight: {row['weight']*100:>5.1f}% | "
              f"₹{row['allocation_inr']:>10,.2f}")
    
    return recommendations


if __name__ == "__main__":
    # Load data
    csv_path = DATA_DIR / "universe_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}\nRun: python app/api/main.py")
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    
    # Train all strategies
    results = {}
    for strategy_name, config in STRATEGIES.items():
        try:
            recommendations = train_strategy(strategy_name, config, df.copy())
            results[strategy_name] = recommendations
        except Exception as e:
            logger.error(f"Failed to train {strategy_name} strategy: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE - ALL STRATEGIES")
    print("=" * 80)
    print(f"\n✓ {len(results)} strategies trained successfully")
    print(f"✓ Models saved to: {MODELS_DIR}")
    print(f"✓ Recommendations saved to: {RESULTS_DIR}")
    print("\nNext steps:")
    print("  1. Start API server: python app/api_server/main.py")
    print("  2. View in browser: http://localhost:8000")
