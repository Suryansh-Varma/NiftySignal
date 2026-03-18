import pandas as pd
import numpy as np
import talib
from app.features.risk_factors import RiskFactorCalculator
from app.config import TradingConfig
import json

print("\n" + "="*70)
print("ENHANCED FEATURE ENGINEERING - MODEL IMPROVEMENT")
print("="*70)

def calculate_enhanced_features(df, symbol):
    """
    Add advanced technical indicators and features to improve model accuracy.
    
    New Features:
    1. Volume indicators (OBV, Volume ROC)
    2. Momentum indicators (Stochastic, CCI, MFI)
    3. Volatility indicators (Bollinger Bands, ATR)
    4. Moving average systems (50-day, 200-day crossovers)
    5. Price patterns (higher highs, lower lows)
    6. Sector relative strength
    """
    
    df = df.copy()
    
    # Existing features
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    volume = df['Volume'].values
    
    print(f"\n🔧 Calculating enhanced features for {symbol}...")
    
    # 1. VOLUME INDICATORS
    try:
        # On-Balance Volume
        df['OBV'] = talib.OBV(close, volume)
        df['OBV_MA'] = df['OBV'].rolling(window=20).mean()
        df['OBV_signal'] = np.where(df['OBV'] > df['OBV_MA'], 1, -1)
        
        # Volume Rate of Change
        df['volume_roc'] = talib.ROC(volume, timeperiod=10)
        
        # Volume Moving Average Ratio
        df['volume_ma20'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_ma20']
        
        print("   ✓ Volume indicators added")
    except Exception as e:
        print(f"   ✗ Volume indicators failed: {e}")
    
    # 2. MOMENTUM INDICATORS
    try:
        # Stochastic Oscillator
        slowk, slowd = talib.STOCH(high, low, close,
                                    fastk_period=14,
                                    slowk_period=3,
                                    slowd_period=3)
        df['STOCH_K'] = slowk
        df['STOCH_D'] = slowd
        df['STOCH_signal'] = np.where(slowk > slowd, 1, -1)
        
        # Commodity Channel Index
        df['CCI'] = talib.CCI(high, low, close, timeperiod=20)
        df['CCI_signal'] = np.where(df['CCI'] > 0, 1, -1)
        
        # Money Flow Index
        df['MFI'] = talib.MFI(high, low, close, volume, timeperiod=14)
        df['MFI_signal'] = np.where(df['MFI'] > 50, 1, -1)
        
        # Rate of Change
        df['ROC'] = talib.ROC(close, timeperiod=10)
        
        print("   ✓ Momentum indicators added")
    except Exception as e:
        print(f"   ✗ Momentum indicators failed: {e}")
    
    # 3. VOLATILITY INDICATORS
    try:
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(close,
                                             timeperiod=20,
                                             nbdevup=2,
                                             nbdevdn=2)
        df['BB_upper'] = upper
        df['BB_middle'] = middle
        df['BB_lower'] = lower
        df['BB_width'] = (upper - lower) / middle
        df['BB_position'] = (close - lower) / (upper - lower)
        
        # Average True Range
        df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
        df['ATR_percent'] = df['ATR'] / close * 100
        
        # Normalized ATR (volatility score)
        df['volatility_score'] = df['ATR_percent'].rolling(window=20).apply(
            lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0.5
        )
        
        print("   ✓ Volatility indicators added")
    except Exception as e:
        print(f"   ✗ Volatility indicators failed: {e}")
    
    # 4. MOVING AVERAGE SYSTEMS
    try:
        # Multiple timeframe MAs
        df['SMA_20'] = talib.SMA(close, timeperiod=20)
        df['SMA_50'] = talib.SMA(close, timeperiod=50)
        df['SMA_200'] = talib.SMA(close, timeperiod=200)
        
        df['EMA_12'] = talib.EMA(close, timeperiod=12)
        df['EMA_26'] = talib.EMA(close, timeperiod=26)
        
        # Price position relative to MAs
        df['price_vs_sma20'] = (close - df['SMA_20']) / df['SMA_20'] * 100
        df['price_vs_sma50'] = (close - df['SMA_50']) / df['SMA_50'] * 100
        df['price_vs_sma200'] = (close - df['SMA_200']) / df['SMA_200'] * 100
        
        # MA crossovers
        df['sma20_vs_sma50'] = np.where(df['SMA_20'] > df['SMA_50'], 1, -1)
        df['sma50_vs_sma200'] = np.where(df['SMA_50'] > df['SMA_200'], 1, -1)
        df['golden_cross'] = np.where((df['SMA_50'] > df['SMA_200']) & 
                                       (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1)), 1, 0)
        df['death_cross'] = np.where((df['SMA_50'] < df['SMA_200']) & 
                                      (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1)), 1, 0)
        
        print("   ✓ Moving average systems added")
    except Exception as e:
        print(f"   ✗ Moving average systems failed: {e}")
    
    # 5. PRICE PATTERNS
    try:
        # Higher highs / Lower lows
        df['higher_high'] = (df['High'] > df['High'].shift(1)).astype(int)
        df['lower_low'] = (df['Low'] < df['Low'].shift(1)).astype(int)
        
        # Consecutive up/down days
        df['up_days'] = (df['Close'] > df['Close'].shift(1)).astype(int)
        df['consecutive_up'] = df['up_days'].rolling(window=5).sum()
        df['consecutive_down'] = (1 - df['up_days']).rolling(window=5).sum()
        
        # Price momentum (distance from recent low/high)
        df['distance_from_20d_high'] = (df['High'].rolling(window=20).max() - close) / close * 100
        df['distance_from_20d_low'] = (close - df['Low'].rolling(window=20).min()) / close * 100
        
        print("   ✓ Price patterns added")
    except Exception as e:
        print(f"   ✗ Price patterns failed: {e}")
    
    # 6. TREND STRENGTH
    try:
        # ADX (Average Directional Index)
        df['ADX'] = talib.ADX(high, low, close, timeperiod=14)
        df['trend_strength'] = np.where(df['ADX'] > 25, 'strong',
                                         np.where(df['ADX'] > 15, 'moderate', 'weak'))
        
        # Aroon Indicator
        aroon_down, aroon_up = talib.AROON(high, low, timeperiod=14)
        df['AROON_UP'] = aroon_up
        df['AROON_DOWN'] = aroon_down
        df['AROON_signal'] = np.where(aroon_up > aroon_down, 1, -1)
        
        print("   ✓ Trend strength indicators added")
    except Exception as e:
        print(f"   ✗ Trend strength indicators failed: {e}")
    
    # 7. RISK FACTORS (Enhanced)
    try:
        risk_calc = RiskFactorCalculator()
        
        # Get macro risk factor
        macro_risk_info = risk_calc.get_macro_risk_info()
        macro_risk = macro_risk_info['risk_factor']
        
        # Calculate technical risk
        returns = df['Close'].pct_change()
        df['volatility_20d'] = returns.rolling(window=20).std() * np.sqrt(252)
        df['sharpe_20d'] = (returns.rolling(window=20).mean() * 252) / (returns.rolling(window=20).std() * np.sqrt(252))
        
        # Drawdown
        rolling_max = df['Close'].rolling(window=20).max()
        df['drawdown_20d'] = (df['Close'] - rolling_max) / rolling_max
        
        # Composite risk
        df['risk_factor_composite'] = (
            df['volatility_20d'].fillna(0) * 0.3 +
            abs(df['drawdown_20d'].fillna(0)) * 0.3 +
            (1 - df['sharpe_20d'].fillna(0.5).clip(-1, 1)) * 0.2 +
            macro_risk * 0.2
        )
        
        df['risk_factor_macro'] = macro_risk
        
        print(f"   ✓ Risk factors added (macro risk: {macro_risk})")
    except Exception as e:
        print(f"   ✗ Risk factors failed: {e}")
    
    return df

def get_enhanced_feature_columns():
    """Return list of all enhanced feature columns"""
    return [
        # Existing features
        'MACD', 'MACD_signal', 'RSI', 'returns_1d', 'returns_5d', 
        'risk_factor_composite', 'risk_factor_macro',
        
        # Volume features
        'OBV_signal', 'volume_roc', 'volume_ratio',
        
        # Momentum features
        'STOCH_signal', 'CCI_signal', 'MFI_signal', 'ROC',
        
        # Volatility features
        'BB_width', 'BB_position', 'ATR_percent', 'volatility_score',
        
        # Moving average features
        'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200',
        'sma20_vs_sma50', 'sma50_vs_sma200', 'golden_cross', 'death_cross',
        
        # Price pattern features
        'higher_high', 'lower_low', 'consecutive_up', 'consecutive_down',
        'distance_from_20d_high', 'distance_from_20d_low',
        
        # Trend features
        'ADX', 'AROON_signal',
        
        # Risk features
        'volatility_20d', 'sharpe_20d', 'drawdown_20d'
    ]

# Test on sample data
if __name__ == "__main__":
    print("\n📊 Testing enhanced features on sample data...")
    
    # Load sample stock data
    try:
        df = pd.read_csv('data/processed/universe_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Test on INFY
        sample = df[df['Symbol'] == 'INFY.NS'].sort_values('Date').tail(250).copy()
        
        if len(sample) > 0:
            enhanced = calculate_enhanced_features(sample, 'INFY.NS')
            
            print("\n📈 Enhanced Feature Summary:")
            print(f"   Original features: {len(sample.columns)}")
            print(f"   Enhanced features: {len(enhanced.columns)}")
            print(f"   New features added: {len(enhanced.columns) - len(sample.columns)}")
            
            feature_cols = get_enhanced_feature_columns()
            available_features = [col for col in feature_cols if col in enhanced.columns]
            
            print(f"\n✅ Available features for training: {len(available_features)}")
            print(f"   Original: 8 features")
            print(f"   Enhanced: {len(available_features)} features")
            print(f"   Improvement: +{len(available_features) - 8} features ({(len(available_features) - 8) / 8 * 100:.0f}% increase)")
            
            # Show sample of new features
            print("\n📊 Sample of enhanced features (last row):")
            last_row = enhanced.iloc[-1]
            for col in available_features[:10]:
                if col in enhanced.columns:
                    print(f"   {col:30s} {last_row[col]:.4f}")
            
            print("\n💾 Feature columns saved to enhanced_features.json")
            with open('enhanced_features.json', 'w') as f:
                json.dump({
                    'feature_columns': available_features,
                    'feature_count': len(available_features),
                    'original_count': 8,
                    'improvement': len(available_features) - 8
                }, f, indent=2)
        else:
            print("   ✗ No data found for INFY.NS")
    
    except FileNotFoundError:
        print("   ✗ Data file not found. Run data loaders first.")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*70)
    print("✅ Enhanced feature engineering ready!")
    print("   Next: Update train_model.py to use calculate_enhanced_features()")
    print("="*70 + "\n")
