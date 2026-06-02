from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
from typing import Tuple

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import (
    DATA_PROCESSED_DIR as DATA_DIR,
    MODELS_DIR,
    RESULTS_DIR,
    TradingConfig,
)
from app.features.technical import prepare_features
from app.signals.ml_signals import MLSignalGenerator
from app.backtest.strategy import SimpleBacktester

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import enhanced features for accuracy improvement
try:
    from enhanced_features import (
        calculate_enhanced_features,
        get_enhanced_feature_columns,
    )

    USE_ENHANCED_FEATURES = True
    logger.info("Enhanced features module loaded - using 38 features for training")
except ImportError:
    USE_ENHANCED_FEATURES = False
    logger.info("Enhanced features not available - using standard 8 features")

# Load the data from processed folder (canonical location)
try:
    data_path = DATA_DIR / "universe_data.csv"

    if not data_path.exists():
        error_msg = (
            f"Data file not found: {data_path}\n\n"
            f"Please run one of the following to generate data:\n"
            f"  1. python app/api/main.py (to fetch fresh data)\n"
            f"  2. python app/scripts/assemble_universe.py (to assemble from parquet files)"
        )
        raise FileNotFoundError(error_msg)

    df = pd.read_csv(data_path)
    logger.info(f"Loaded data from {data_path} ({len(df)} rows)")
except FileNotFoundError as e:
    logger.error(f"Data file not found: {e}")
    raise
except Exception as e:
    logger.error(f"Error loading data: {e}")
    raise
df["date"] = pd.to_datetime(df["date"])

# Check data sufficiency before feature preparation
total_rows = len(df)
unique_symbols = df["symbol"].nunique()
rows_per_symbol = total_rows / unique_symbols if unique_symbols > 0 else 0

logger.info(
    f"Data summary: {total_rows} total rows, {unique_symbols} symbols, ~{rows_per_symbol:.1f} rows per symbol"
)

# Estimate minimum rows needed: Enhanced features need 200+ days for MA_200 and better accuracy
min_rows_needed = (
    200 if USE_ENHANCED_FEATURES else max(50, 20, TradingConfig.FORWARD_DAYS) + 10
)
if USE_ENHANCED_FEATURES:
    logger.info(
        f"Using enhanced features - require {min_rows_needed} rows per symbol for better accuracy"
    )
if rows_per_symbol < min_rows_needed:
    error_msg = (
        f"Insufficient data for model training!\n"
        f"  - Current: ~{rows_per_symbol:.1f} rows per symbol\n"
        f"  - Required: At least {min_rows_needed} rows per symbol\n"
        f"  - Total rows: {total_rows}\n"
        f"  - Symbols: {unique_symbols}\n\n"
        f"Technical indicators require:\n"
        f"  - SMA_50: 50 periods\n"
        f"  - Volatility_20d: 20 periods\n"
        f"  - Forward returns: {TradingConfig.FORWARD_DAYS} days\n\n"
        f"Please fetch more historical data by running:\n"
        f"  python app/api/main.py"
    )
    logger.error(error_msg)
    raise ValueError(error_msg)

# Prepare features and labels
logger.info("Preparing features and labels...")
X, y, _ = prepare_features(
    df,
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=TradingConfig.RETURN_THRESHOLD,
)

# Store the feature columns used for training (important for predictions)
TRAINING_FEATURE_COLUMNS = list(X.columns)
logger.info(f"After feature preparation: {len(X)} samples, {len(X.columns)} features")
logger.info(f"Training feature columns: {TRAINING_FEATURE_COLUMNS}")
if len(X) == 0:
    error_msg = (
        f"No valid samples after feature preparation!\n"
        f"This usually means:\n"
        f"  1. Not enough historical data (need at least {min_rows_needed} rows per symbol)\n"
        f"  2. Too many NaN values in technical indicators\n"
        f"  3. Forward returns couldn't be calculated\n\n"
        f"Try fetching more data: python app/api/main.py"
    )
    logger.error(error_msg)
    raise ValueError(error_msg)

# Initialize and train the model
model = MLSignalGenerator(
    model_type="gradient_boost",
    use_risk_adjustment=True,
    forward_days=TradingConfig.FORWARD_DAYS,
    return_threshold=TradingConfig.RETURN_THRESHOLD_STRICT,
    test_size=TradingConfig.TEST_SIZE,
    random_state=TradingConfig.RANDOM_STATE,
)

# Train and get metrics
try:
    train_metrics, test_metrics = model.fit(X, y)
    logger.info("Model training completed successfully")
except Exception as e:
    logger.error(f"Error during model training: {e}")
    raise

# Print model performance
print("\nTraining Performance:")
print(pd.DataFrame(train_metrics["classification_report"]).T)
print("\nTest Performance:")
print(pd.DataFrame(test_metrics["classification_report"]).T)

# Get feature importance
importance = pd.Series(model.feature_importance_).sort_values(ascending=False)
print("\nTop 10 Important Features:")
print(importance.head(10))

# Save the trained model
try:
    MODELS_DIR.mkdir(exist_ok=True)
    model_path = MODELS_DIR / "trading_model.pkl"
    model.save(model_path)
    logger.info(f"Model saved to {model_path}")
except Exception as e:
    logger.error(f"Error saving model: {e}")
    raise

# Generate signals for the entire dataset
signals = model.predict(X)

# Add signals back to the original data
df_signals = df.copy()
df_signals["signal"] = np.nan
df_signals.loc[X.index, "signal"] = signals

# Run backtest with optimized parameters
backtest = SimpleBacktester(
    initial_capital=TradingConfig.INITIAL_CAPITAL,
    position_size=TradingConfig.POSITION_SIZE,
    stop_loss=TradingConfig.STOP_LOSS,
    take_profit=TradingConfig.TAKE_PROFIT,
    trailing_stop=TradingConfig.TRAILING_STOP,
    min_confidence=TradingConfig.MIN_BUY_CONFIDENCE,
)

try:
    trades_df, equity_df, metrics = backtest.run(df_signals)
    logger.info("Backtest completed successfully")
except Exception as e:
    logger.error(f"Error during backtest: {e}")
    raise

# Print backtest results
print("\nBacktest Results:")
print(f"Total Trades: {metrics['total_trades']}")
print(f"Win Rate: {metrics['win_rate']:.2%}")
print(f"Average Profit: ${metrics['avg_profit']:,.2f}")
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")

# Save results
RESULTS_DIR.mkdir(exist_ok=True)

trades_df.to_csv(RESULTS_DIR / "trades.csv", index=False)
equity_df.to_csv(RESULTS_DIR / "equity.csv", index=False)

# For each company, get most recent data point and enough history for features
latest_data = []
X_latest = pd.DataFrame()
latest_symbols = []
latest_prices = []
latest_dates = []

for symbol in df["symbol"].unique():
    symbol_data = df[df["symbol"] == symbol].copy()
    if len(symbol_data) >= TradingConfig.MIN_DAYS_FOR_FEATURES:
        symbol_data = symbol_data.sort_values("date")
        try:
            # Use the same feature columns as training
            X_temp, _, _ = prepare_features(
                symbol_data,
                feature_columns=TRAINING_FEATURE_COLUMNS,  # Use same features as training
                forward_days=TradingConfig.FORWARD_DAYS,
                return_threshold=TradingConfig.RETURN_THRESHOLD,
            )
        except Exception as e:
            logger.warning(f"Error preparing features for {symbol}: {e}")
            continue

        if not X_temp.empty:
            # Ensure we only use the training feature columns
            missing_cols = set(TRAINING_FEATURE_COLUMNS) - set(X_temp.columns)
            if missing_cols:
                logger.warning(
                    f"Missing features for {symbol}: {missing_cols}, skipping"
                )
                continue

            # Get features for the latest date, ensuring correct column order
            latest_features = X_temp[TRAINING_FEATURE_COLUMNS].iloc[-1:]
            X_latest = pd.concat([X_latest, latest_features])
            latest_symbols.append(symbol)
            latest_prices.append(symbol_data.iloc[-1]["close"])
            latest_dates.append(symbol_data.iloc[-1]["date"])

if not X_latest.empty:
    try:
        latest_signals = model.predict(X_latest)
        latest_proba = model.predict_proba(X_latest)
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise

    # Create recommendations DataFrame
    recommendations = pd.DataFrame(
        {
            "symbol": latest_symbols,
            "last_price": latest_prices,
            "last_date": latest_dates,
            "signal": latest_signals,
            "confidence": np.max(latest_proba, axis=1),
        }
    )

    # Filter by confidence thresholds (risk-aware)
    # Buy signals need 70% confidence, Sell needs 50%
    buy_mask = (recommendations["signal"] == 1) & (
        recommendations["confidence"] >= TradingConfig.MIN_BUY_CONFIDENCE
    )
    sell_mask = (recommendations["signal"] == -1) & (
        recommendations["confidence"] >= TradingConfig.MIN_SELL_CONFIDENCE
    )
    hold_mask = recommendations["signal"] == 0

    recommendations = recommendations[buy_mask | sell_mask | hold_mask].copy()

    # Add signal text
    signal_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
    recommendations["recommendation"] = recommendations["signal"].map(signal_map)

    # Coerce numeric columns and use nullable float dtypes
    recommendations["last_price"] = pd.to_numeric(
        recommendations["last_price"], errors="coerce"
    ).astype("Float64")
    recommendations["confidence"] = pd.to_numeric(
        recommendations["confidence"], errors="coerce"
    ).astype("Float64")

    # Fill or mark missing values: leave prices as NA (so frontend can show '-') and set missing confidence to 0.0
    recommendations["confidence"] = recommendations["confidence"].fillna(0.0)

    # Round for readability
    recommendations["last_price"] = recommendations["last_price"].round(2)
    recommendations["confidence"] = recommendations["confidence"].round(3)

    # Sort by confidence for most confident predictions first
    recommendations = recommendations.sort_values("confidence", ascending=False)

    # Safe printing helpers
    def fmt_price(v):
        try:
            if pd.isna(v):
                return "-"
            # Use 'Rs' instead of rupee symbol for Windows compatibility
            return f"Rs{float(v):,.2f}"
        except Exception:
            return "-"

    def fmt_conf(v):
        try:
            if pd.isna(v):
                return "-"
            return f"{float(v) * 100:.1f}%"
        except Exception:
            return "-"

    print("\nTrading Recommendations by Company:")
    print("=" * 80)

    # Print buy signals
    buy_signals = recommendations[recommendations["signal"] == 1]
    if not buy_signals.empty:
        print("\nBUY Recommendations:")
        print("-" * 40)
        for _, row in buy_signals.iterrows():
            print(
                f"{row['symbol']:<12} Price: {fmt_price(row['last_price'])}  Confidence: {fmt_conf(row['confidence'])}"
            )

    # Print sell signals
    sell_signals = recommendations[recommendations["signal"] == -1]
    if not sell_signals.empty:
        print("\nSELL Recommendations:")
        print("-" * 40)
        for _, row in sell_signals.iterrows():
            print(
                f"{row['symbol']:<12} Price: {fmt_price(row['last_price'])}  Confidence: {fmt_conf(row['confidence'])}"
            )

    # Save recommendations (write cleaned CSV)
    try:
        recommendations_path = RESULTS_DIR / "latest_recommendations.csv"
        recommendations.to_csv(recommendations_path, index=False, float_format="%.3f")
        logger.info(f"Recommendations saved to {recommendations_path}")
        print("\nDetailed recommendations saved to results/latest_recommendations.csv")
    except Exception as e:
        logger.error(f"Error saving recommendations: {e}")
        raise
else:
    print("\nWarning: Could not generate predictions due to insufficient recent data")
