from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import talib as ta
from sklearn.preprocessing import LabelEncoder

# Import risk factor calculator
try:
    from app.features.risk_factors import RiskFactorCalculator
except ImportError:
    RiskFactorCalculator = None

# Import market context features (Nifty 50 index-relative)
try:
    from app.features.market_context import add_market_context_features, MARKET_CONTEXT_FEATURES
except ImportError:
    add_market_context_features = None
    MARKET_CONTEXT_FEATURES = []

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
        macd, macd_signal, macd_hist = ta.MACD(
            temp['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        # Normalize MACD by price to make it scale-invariant
        temp['macd'] = macd / temp['close']
        temp['macd_signal'] = macd_signal / temp['close']
        temp['macd_hist'] = macd_hist / temp['close']
        
        # Volatility indicators
        temp['bb_upper'], temp['bb_middle'], temp['bb_lower'] = ta.BBANDS(
            temp['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        # Normalize BB distance from middle
        temp['bb_dist'] = (temp['close'] - temp['bb_middle']) / temp['bb_middle']
        
        # Normalize ATR by price
        temp['atr'] = ta.ATR(temp['high'], temp['low'], temp['close'], timeperiod=14) / temp['close']
        
        # Volume indicators
        temp['obv'] = ta.OBV(temp['close'], temp['volume'])
        temp['adl'] = ta.AD(temp['high'], temp['low'], temp['close'], temp['volume'])
        
        # Price patterns
        temp['doji'] = ta.CDLDOJI(temp['open'], temp['high'], temp['low'], temp['close'])
        temp['engulfing'] = ta.CDLENGULFING(temp['open'], temp['high'], temp['low'], temp['close'])
        temp['hammer'] = ta.CDLHAMMER(temp['open'], temp['high'], temp['low'], temp['close'])
        
        # Trend indicators
        temp['adx'] = ta.ADX(temp['high'], temp['low'], temp['close'], timeperiod=14)
        
        # Additional Momentum Indicators
        temp['stoch_k'], temp['stoch_d'] = ta.STOCH(
            temp['high'], temp['low'], temp['close'], 
            fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0
        )
        temp['willr'] = ta.WILLR(temp['high'], temp['low'], temp['close'], timeperiod=14)
        temp['roc'] = ta.ROC(temp['close'], timeperiod=10)
        temp['cci'] = ta.CCI(temp['high'], temp['low'], temp['close'], timeperiod=14)
        
        # Custom features
        # Returns
        temp['returns_1d'] = temp['close'].pct_change()
        temp['returns_5d'] = temp['close'].pct_change(5)
        temp['returns_20d'] = temp['close'].pct_change(20)
        
        # Lags of returns (Autocorrection features)
        temp['returns_1d_lag1'] = temp['returns_1d'].shift(1)
        temp['returns_1d_lag2'] = temp['returns_1d'].shift(2)
        
        # Volatility
        temp['volatility_20d'] = temp['returns_1d'].rolling(20).std()
        temp['volatility_lag5'] = temp['volatility_20d'].shift(5)
        
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
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Prepare feature matrix X and target vector y for ML model.
    Also returns the labelled DataFrame (with 'symbol' column) for sector routing.
    Returns: (X, y, df_ml)
    """
    # Add technical indicators
    df_features = add_technical_features(df)
    
    # Add symbol encoding to learn ticker-specific patterns
    le = LabelEncoder()
    df_features['symbol_encoded'] = le.fit_transform(df_features['symbol'])
    
    # Add volatility-normalized returns
    df_features['returns_vol_adj'] = df_features['returns_1d'] / df_features['volatility_20d'].replace(0, np.nan)
    
    # Add Nifty 50 market context features (index-relative alpha, regime, beta)
    if add_market_context_features is not None:
        try:
            df_features = add_market_context_features(df_features)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).warning(f"Market context features skipped: {_e}")

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
                'symbol_encoded',
                'rsi_14', 'macd', 'macd_signal', 'macd_hist', 'stoch_k', 'stoch_d', 'willr', 'roc', 'cci',
                'bb_dist', 'atr', 'adx', 'returns_vol_adj',
                'returns_1d', 'returns_5d', 'returns_20d',
                'returns_1d_lag1', 'returns_1d_lag2',
                'volatility_20d', 'volatility_lag5',
                'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50',
            ]
            # Append Nifty 50 market context features if present in the dataframe
            for _col in MARKET_CONTEXT_FEATURES:
                if _col in df_labeled.columns and _col not in feature_columns:
                    feature_columns.append(_col)
        elif min_rows_per_symbol >= 20:
            # Reduced feature set for smaller datasets
            feature_columns = [
                'rsi_14', 'macd', 'macd_signal', 'macd_hist',
                'bb_dist', 'atr',
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
    
    # Use only columns that are actually present
    available_features = [c for c in feature_columns if c in df_labeled.columns]

    # Prepare X and y, dropping any rows with NaN in selected features
    df_ml = df_labeled.dropna(subset=available_features + ['signal'])
    
    if len(df_ml) == 0:
        raise ValueError(
            f"No valid samples after feature preparation. "
            f"Need at least {max(20, forward_days + 5)} rows per symbol. "
            f"Current: {min_rows_per_symbol} rows per symbol."
        )
    
    X = df_ml[available_features]
    y = df_ml['signal']
    
    # Return X, y, and the labelled DataFrame (contains 'symbol' for sector routing)
    return X, y, df_ml