from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import talib as ta

# Import risk factor calculator
try:
    from app.features.risk_factors import RiskFactorCalculator
except ImportError:
    RiskFactorCalculator = None

def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to price data.
    Expects a DataFrame with columns: [date, symbol, open, high, low, close, volume]
    Returns the same DataFrame with additional technical indicator columns.
    """
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Filter out rows marked as missing (if column exists)
    if 'missing' in df.columns:
        valid_mask = df['missing'] == False
        df = df[valid_mask].copy()
    
    # Calculate for each symbol separately
    symbols = df['symbol'].unique()
    dfs = []
    
    for sym in symbols:
        temp = df[df['symbol'] == sym].copy()
        # Sort by date
        temp = temp.sort_values('date')
        
        # Price-based indicators
        # Moving averages
        temp['sma_10'] = ta.SMA(temp['close'], timeperiod=10)
        temp['sma_20'] = ta.SMA(temp['close'], timeperiod=20)
        temp['sma_50'] = ta.SMA(temp['close'], timeperiod=50)
        
        # Momentum indicators
        temp['rsi_14'] = ta.RSI(temp['close'], timeperiod=14)
        temp['macd'], temp['macd_signal'], temp['macd_hist'] = ta.MACD(
            temp['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Volatility indicators
        temp['bb_upper'], temp['bb_middle'], temp['bb_lower'] = ta.BBANDS(
            temp['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        temp['atr'] = ta.ATR(temp['high'], temp['low'], temp['close'], timeperiod=14)
        
        # Volume indicators
        temp['obv'] = ta.OBV(temp['close'], temp['volume'])
        temp['adl'] = ta.AD(temp['high'], temp['low'], temp['close'], temp['volume'])
        
        # Price patterns
        temp['doji'] = ta.CDLDOJI(temp['open'], temp['high'], temp['low'], temp['close'])
        temp['engulfing'] = ta.CDLENGULFING(temp['open'], temp['high'], temp['low'], temp['close'])
        temp['hammer'] = ta.CDLHAMMER(temp['open'], temp['high'], temp['low'], temp['close'])
        
        # Trend indicators
        temp['adx'] = ta.ADX(temp['high'], temp['low'], temp['close'], timeperiod=14)
        
        # Custom features
        # Returns
        temp['returns_1d'] = temp['close'].pct_change()
        temp['returns_5d'] = temp['close'].pct_change(5)
        temp['returns_20d'] = temp['close'].pct_change(20)
        
        # Volatility
        temp['volatility_20d'] = temp['returns_1d'].rolling(20).std()
        
        # Price relative to moving averages
        temp['price_to_sma_10'] = temp['close'] / temp['sma_10'] - 1
        temp['price_to_sma_20'] = temp['close'] / temp['sma_20'] - 1
        temp['price_to_sma_50'] = temp['close'] / temp['sma_50'] - 1
        
        dfs.append(temp)
    
    # Combine all symbols back
    result = pd.concat(dfs, ignore_index=True)
    
    # Forward fill NaN values from indicators
    feature_columns = [c for c in result.columns if c not in ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
    result[feature_columns] = result.groupby('symbol')[feature_columns].transform(lambda x: x.ffill())
    
    return result

def generate_labels(df: pd.DataFrame, forward_days: int = 5, return_threshold: float = 0.01) -> pd.DataFrame:
    """
    Generate trading signal labels based on forward returns.
    1 = Buy (forward return > threshold)
    0 = Hold (-threshold <= forward return <= threshold)
    -1 = Sell (forward return < -threshold)
    """
    df = df.copy()
    
    # Calculate forward returns for each symbol
    symbols = df['symbol'].unique()
    dfs = []
    
    for sym in symbols:
        temp = df[df['symbol'] == sym].copy()
        temp = temp.sort_values('date')
        
        # Calculate forward returns
        temp['forward_returns'] = temp['close'].shift(-forward_days) / temp['close'] - 1
        
        # Generate labels
        temp['signal'] = 0  # Hold
        temp.loc[temp['forward_returns'] > return_threshold, 'signal'] = 1  # Buy
        temp.loc[temp['forward_returns'] < -return_threshold, 'signal'] = -1  # Sell
        
        dfs.append(temp)
    
    result = pd.concat(dfs, ignore_index=True)
    return result

def prepare_features(
    df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None,
    forward_days: int = 5,
    return_threshold: float = 0.015,  # Reduced to 1.5% to capture more opportunities
    include_risk_factors: bool = True
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare feature matrix X and target vector y for ML model.
    
    Args:
        df: DataFrame with price data
        feature_columns: List of feature columns to use (None = use default)
        forward_days: Days to look ahead for forward returns
        return_threshold: Return threshold for signal generation
        include_risk_factors: Whether to include risk factor features
        
    Returns:
        Tuple of (X, y) where X is feature matrix and y is target labels
    """
    # Add technical indicators
    df_features = add_technical_features(df)
    
    # Add risk factors if available
    if include_risk_factors and RiskFactorCalculator is not None:
        risk_calc = RiskFactorCalculator(lookback_period=30)
        df_features = risk_calc.add_risk_factors_to_dataframe(df_features)
    
    # Generate labels
    df_labeled = generate_labels(df_features, forward_days, return_threshold)
    
    # Check data size to determine feature set
    min_rows_per_symbol = df_labeled.groupby('symbol').size().min() if 'symbol' in df_labeled.columns else len(df_labeled)
    
    # Default feature columns if none provided
    if feature_columns is None:
        # Use full feature set if enough data, otherwise use reduced set
        if min_rows_per_symbol >= 50:
            feature_columns = [
                'rsi_14', 'macd', 'macd_signal', 'macd_hist',
                'bb_upper', 'bb_middle', 'bb_lower', 'atr',
                'adx', 'returns_1d', 'returns_5d', 'returns_20d',
                'volatility_20d', 'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50'
            ]
        elif min_rows_per_symbol >= 20:
            # Reduced feature set for smaller datasets (no SMA_50, no returns_20d, no volatility_20d)
            feature_columns = [
                'rsi_14', 'macd', 'macd_signal', 'macd_hist',
                'bb_upper', 'bb_middle', 'bb_lower', 'atr',
                'adx', 'returns_1d', 'returns_5d',
                'price_to_sma_10', 'price_to_sma_20'
            ]
        else:
            # Minimal feature set for very small datasets
            feature_columns = [
                'rsi_14', 'macd', 'macd_signal',
                'returns_1d', 'returns_5d',
                'price_to_sma_10'
            ]
        
        # Always add risk factors if available (critical for risk-aware trading)
        if include_risk_factors and RiskFactorCalculator is not None:
            if 'risk_factor_composite' in df_labeled.columns:
                feature_columns.append('risk_factor_composite')
            if 'risk_factor_macro' in df_labeled.columns:
                feature_columns.append('risk_factor_macro')
    
    # Prepare X and y, dropping any rows with NaN
    df_ml = df_labeled.dropna(subset=feature_columns + ['signal'])
    
    if len(df_ml) == 0:
        raise ValueError(
            f"No valid samples after feature preparation. "
            f"Need at least {max(20, forward_days + 5)} rows per symbol. "
            f"Current: {min_rows_per_symbol} rows per symbol."
        )
    
    X = df_ml[feature_columns]
    y = df_ml['signal']
    
    return X, y