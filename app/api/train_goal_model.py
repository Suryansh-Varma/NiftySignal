"""
Train goal-based portfolio selection model.
Predicts which stocks will achieve target return (e.g., 15%) over specified horizon (e.g., 126 days).
Uses softmax allocation to distribute capital across high-confidence picks.
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

def prepare_goal_features(
    df: pd.DataFrame,
    horizon_days: int,
    target_return: float
) -> tuple:
    """
    Prepare features and labels for goal-based model.
    
    Args:
        df: DataFrame with price data
        horizon_days: Forward horizon (e.g., 126 days = ~6 months)
        target_return: Target return threshold (e.g., 0.15 for 15%)
        
    Returns:
        X: Feature matrix
        y: Binary labels (1 = achieves target, 0 = doesn't)
        df_labeled: Full dataframe with labels
    """
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
    
    # Select features (using adaptive set based on available data)
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
    
    logger.info(f"Prepared {len(X)} samples with {len(feature_columns)} features")
    logger.info(f"Positive samples (achieving {target_return*100}%): {y.sum()} ({y.mean()*100:.1f}%)")
    
    return X, y, df_ml, feature_columns


def generate_goal_recommendations(
    model: RandomForestClassifier,
    df: pd.DataFrame,
    feature_columns: list,
    capital: float,
    top_n: int = 15
) -> pd.DataFrame:
    """
    Generate portfolio allocation recommendations.
    
    Args:
        model: Trained classifier
        df: Latest data with features
        feature_columns: Features used in model
        capital: Total capital to allocate (INR)
        top_n: Number of top stocks to select
        
    Returns:
        DataFrame with recommendations and allocation amounts
    """
    # Get latest data point for each symbol
    latest = df.sort_values('date').groupby('symbol').tail(1).copy()
    
    # Get features
    X_latest = latest[feature_columns]
    
    # Predict probabilities
    probs = model.predict_proba(X_latest)
    
    # Extract probability of achieving goal (class 1)
    buy_prob = probs[:, 1]
    
    # Create recommendations dataframe
    recommendations = pd.DataFrame({
        'symbol': latest['symbol'].values,
        'date': latest['date'].values,
        'close': latest['close'].values,
        'buy_prob': buy_prob,
        'confidence': buy_prob * 100  # As percentage
    })
    
    # Sort by confidence and take top N
    recommendations = recommendations.sort_values('buy_prob', ascending=False).head(top_n)
    
    # Apply softmax to get allocation weights
    exp_probs = np.exp(recommendations['buy_prob'].values)
    softmax_weights = exp_probs / exp_probs.sum()
    
    recommendations['weight'] = softmax_weights
    recommendations['allocation_inr'] = (softmax_weights * capital).round(2)
    
    # Format for display
    recommendations['allocation_inr'] = recommendations['allocation_inr'].apply(lambda x: f"₹{x:,.2f}")
    recommendations = recommendations.reset_index(drop=True)
    
    return recommendations


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("GOAL-BASED PORTFOLIO TRAINING")
    logger.info(f"Target: {GoalConfig.TARGET_RETURN_PCT*100}% return in {GoalConfig.HORIZON_DAYS} days")
    logger.info(f"Capital: ₹{GoalConfig.CAPITAL_INR:,.0f}")
    logger.info("=" * 80)
    
    # Load data
    csv_path = DATA_DIR / "universe_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}\nRun: python app/api/main.py")
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    
    # Prepare features
    X, y, df_labeled, feature_columns = prepare_goal_features(
        df,
        horizon_days=GoalConfig.HORIZON_DAYS,
        target_return=GoalConfig.TARGET_RETURN_PCT
    )
    
    # Check if we have enough positive samples
    if y.sum() < 10:
        logger.warning(
            f"Very few positive samples ({y.sum()})! "
            f"Consider lowering target return or increasing data history."
        )
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=GoalConfig.TEST_SIZE,
        random_state=GoalConfig.RANDOM_STATE,
        stratify=y if y.sum() >= 10 else None
    )
    
    logger.info(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # Train model
    logger.info("Training RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=GoalConfig.RANDOM_STATE,
        class_weight='balanced',  # Important for imbalanced data
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    logger.info("Training completed")
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    logger.info(f"Train accuracy: {train_score:.2%}")
    logger.info(f"Test accuracy: {test_score:.2%}")
    
    # Classification report
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    
    print("\n" + "=" * 80)
    print("TEST SET PERFORMANCE")
    print("=" * 80)
    print(pd.DataFrame(report).T)
    
    # Feature importance
    importance = pd.Series(model.feature_importances_, index=feature_columns).sort_values(ascending=False)
    print("\nTop 10 Important Features:")
    print(importance.head(10))
    
    # Save model
    MODELS_DIR.mkdir(exist_ok=True)
    model_path = MODELS_DIR / "goal_model.pkl"
    
    # Save model with feature columns
    joblib.dump({
        'model': model,
        'feature_columns': feature_columns,
        'horizon_days': GoalConfig.HORIZON_DAYS,
        'target_return': GoalConfig.TARGET_RETURN_PCT
    }, model_path)
    
    logger.info(f"Model saved to {model_path}")
    
    # Generate recommendations
    logger.info("\nGenerating portfolio recommendations...")
    recommendations = generate_goal_recommendations(
        model,
        df_labeled,
        feature_columns,
        capital=GoalConfig.CAPITAL_INR,
        top_n=15
    )
    
    # Save recommendations
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / "latest_goal_recommendations.csv"
    recommendations.to_csv(output_path, index=False)
    logger.info(f"Recommendations saved to {output_path}")
    
    # Display recommendations
    print("\n" + "=" * 80)
    print(f"INVESTMENT RECOMMENDATIONS FOR ₹{GoalConfig.CAPITAL_INR:,.0f}")
    print(f"Target: {GoalConfig.TARGET_RETURN_PCT*100}% in ~{GoalConfig.HORIZON_DAYS} days ({GoalConfig.HORIZON_DAYS//21} months)")
    print("=" * 80)
    
    # Calculate expected timeframe
    today = datetime.now()
    target_date = today + timedelta(days=GoalConfig.HORIZON_DAYS * 7 // 5)  # Adjust for weekends
    
    print(f"\nInvest Today: {today.strftime('%Y-%m-%d')}")
    print(f"Expected Exit: {target_date.strftime('%Y-%m-%d')}")
    print(f"\nTop {len(recommendations)} Stock Picks:")
    print("-" * 80)
    
    for idx, row in recommendations.iterrows():
        print(f"{row['symbol']:15s} | Price: ₹{row['close']:>8,.2f} | "
              f"Confidence: {row['confidence']:>5.1f}% | "
              f"Allocation: {row['allocation_inr']}")
    
    print("\n" + "=" * 80)
    print(f"Total Allocation: ₹{GoalConfig.CAPITAL_INR:,.0f}")
    print("=" * 80)
