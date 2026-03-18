"""
Risk Factor Calculation and Prediction Module

Computes various risk metrics to normalize and adjust trading signals.
"""

from typing import Tuple, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import json
from pathlib import Path
from datetime import datetime


class RiskFactorCalculator:
    """
    Calculates multiple risk factors for stocks to adjust trading signals.
    """
    
    def __init__(self, lookback_period: int = 30, macro_risk_file: Optional[str] = None):
        """
        Args:
            lookback_period: Number of days to look back for risk calculations
            macro_risk_file: Path to JSON file storing macro/geopolitical risk factor
        """
        self.lookback_period = lookback_period
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.macro_risk_file = Path(macro_risk_file) if macro_risk_file else Path("data/macro_risk_factor.json")
        # No in-memory cache — always read from disk so live auto-updates are
        # immediately picked up by the running process.
    
    def calculate_volatility_risk(self, returns: pd.Series) -> float:
        """
        Calculate volatility-based risk (annualized).
        Higher volatility = Higher risk
        
        Formula: std(returns) * sqrt(252)
        """
        if len(returns) < 2:
            return 0.5  # Default mid-range risk
        
        daily_volatility = returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252)
        
        return min(annualized_volatility, 1.0)  # Cap at 1.0
    
    def calculate_drawdown_risk(self, returns: pd.Series) -> float:
        """
        Calculate maximum drawdown risk.
        Higher drawdown = Higher risk
        
        Formula: max(cumulative_return) - cumulative_return / max(cumulative_return)
        """
        if len(returns) < 2:
            return 0.5
        
        cumulative_return = (1 + returns).cumprod()
        running_max = cumulative_return.expanding().max()
        drawdown = (cumulative_return - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        return min(max_drawdown, 1.0)  # Cap at 1.0
    
    def calculate_sharpe_ratio_risk(self, returns: pd.Series, risk_free_rate: float = 0.06) -> float:
        """
        Calculate inverse Sharpe ratio (lower Sharpe = higher risk).
        Formula: (E[R] - Rf) / std(R)
        
        Risk is normalized as: 1 - (sharpe_ratio / max_possible_sharpe)
        """
        if len(returns) < 2:
            return 0.5
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        std_returns = returns.std()
        
        if std_returns == 0:
            return 0.5
        
        sharpe_ratio = excess_returns.mean() / std_returns
        # Normalize: Low sharpe (negative) = high risk (1.0), High sharpe (>2) = low risk (0.0)
        # Use np.clip to avoid overflow in np.exp
        risk_factor = 1.0 / (1.0 + np.exp(np.clip(sharpe_ratio, -100, 100)))  # Sigmoid normalization
        
        return risk_factor
    
    def calculate_beta_risk(self, stock_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        Calculate beta (market sensitivity).
        Beta > 1 = More volatile than market (Higher risk)
        Beta < 1 = Less volatile than market (Lower risk)
        
        Formula: Cov(Stock, Market) / Var(Market)
        """
        if len(stock_returns) < 2 or len(market_returns) < 2:
            return 0.5  # Default beta = 1.0 means market risk
        
        # Align lengths
        min_len = min(len(stock_returns), len(market_returns))
        stock_ret = stock_returns.iloc[-min_len:].values
        market_ret = market_returns.iloc[-min_len:].values
        
        if np.var(market_ret) == 0:
            return 0.5
        
        beta = np.cov(stock_ret, market_ret)[0, 1] / np.var(market_ret)
        
        # Normalize beta to 0-1 scale (assuming beta ranges from 0 to 3)
        normalized_beta = min(max(beta / 3.0, 0.0), 1.0)
        
        return normalized_beta
    
    def calculate_value_at_risk(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) at given confidence level.
        Higher VaR = Higher risk
        
        Formula: percentile(returns, 1 - confidence_level)
        """
        if len(returns) < 10:
            return 0.5
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        # Normalize to 0-1 scale (assuming VaR ranges from -50% to 0%)
        normalized_var = min(max(abs(var) / 0.5, 0.0), 1.0)
        
        return normalized_var
    
    def get_macro_risk_factor(self) -> float:
        """
        Get the current macroeconomic/geopolitical risk factor.

        Always reads from disk so that the auto-updater (which rewrites the
        JSON daily) is immediately reflected in all predictions — no restart
        required.

        Key precedence in JSON:
          1. adjusted_risk_factor  (set by auto_update_macro_risk)
          2. macro_risk_factor     (set by update_macro_risk script)
          3. risk_factor           (legacy field)
          4. 0.5                   (fallback / neutral)

        Returns:
            float: Risk factor between 0 (low risk) and 1 (high risk)
        """
        try:
            if self.macro_risk_file.exists():
                with open(self.macro_risk_file, 'r') as f:
                    data = json.load(f)
                # Prefer the richer adjusted value; fall back gracefully
                value = (
                    data.get('adjusted_risk_factor')
                    or data.get('macro_risk_factor')
                    or data.get('risk_factor')
                    or 0.5
                )
                return float(value)
        except Exception as e:
            print(f"Warning: Could not load macro risk factor: {e}")

        # Default to neutral risk
        return 0.5
    
    def update_macro_risk_factor(
        self,
        risk_factor: float,
        notes: str = "",
        factors: Optional[Dict[str, any]] = None
    ) -> None:
        """
        Update the macroeconomic/geopolitical risk factor.
        
        Args:
            risk_factor: Risk level between 0 (low risk) and 1 (high risk)
            notes: Description of current macro conditions
            factors: Dictionary of contributing factors, e.g.:
                {
                    'fed_rate': 5.5,
                    'gold_price': 2100,
                    'geopolitical_score': 0.7,
                    'vix': 18.5,
                    'oil_price': 85.0
                }
        """
        if not 0 <= risk_factor <= 1:
            raise ValueError("Risk factor must be between 0 and 1")
        
        data = {
            'risk_factor': risk_factor,
            'last_updated': datetime.now().isoformat(),
            'notes': notes,
            'factors': factors or {}
        }
        
        # Create directory if it doesn't exist
        self.macro_risk_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(self.macro_risk_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Macro risk factor updated to {risk_factor:.2f}")
    
    def get_macro_risk_info(self) -> Dict:
        """
        Get detailed information about the current macro risk factor.
        
        Returns:
            Dictionary with risk factor, last update time, notes, and contributing factors
        """
        try:
            if self.macro_risk_file.exists():
                with open(self.macro_risk_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load macro risk info: {e}")
        
        return {
            'risk_factor': 0.5,
            'last_updated': None,
            'notes': 'No data available',
            'factors': {}
        }
    
    def calculate_composite_risk_factor(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """
        Compute composite risk factor combining all risk metrics.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
        
        Returns:
            Pandas Series of risk factors (0-1 scale), same length as df
        """
        symbol_data = df[df['symbol'] == symbol].copy().sort_values('date')
        
        if len(symbol_data) < self.lookback_period:
            return pd.Series(0.5, index=symbol_data.index)  # Default risk
        
        risk_factors = []
        
        for i in range(len(symbol_data)):
            window_start = max(0, i - self.lookback_period)
            window_data = symbol_data.iloc[window_start:i+1]
            
            if len(window_data) < 2:
                risk_factors.append(0.5)
                continue
            
            returns = window_data['close'].pct_change().dropna()
            
            # Calculate individual risk metrics
            volatility_risk = self.calculate_volatility_risk(returns)
            drawdown_risk = self.calculate_drawdown_risk(returns)
            sharpe_risk = self.calculate_sharpe_ratio_risk(returns)
            var_risk = self.calculate_value_at_risk(returns)
            macro_risk = self.get_macro_risk_factor()
            
            # Composite risk (weighted average)
            # Weights: volatility=30%, drawdown=25%, sharpe=15%, VaR=10%, macro=20%
            composite_risk = (
                0.30 * volatility_risk +
                0.25 * drawdown_risk +
                0.15 * sharpe_risk +
                0.10 * var_risk +
                0.20 * macro_risk
            )
            
            risk_factors.append(composite_risk)
        
        return pd.Series(risk_factors, index=symbol_data.index)
    
    def add_risk_factors_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add risk factor columns to dataframe for all symbols.
        
        Returns DataFrame with new columns:
        - risk_factor_volatility
        - risk_factor_drawdown
        - risk_factor_sharpe
        - risk_factor_var
        - risk_factor_macro
        - risk_factor_composite (normalized 0-1)
        """
        df = df.copy()
        
        risk_factor_composite = []
        
        # Get macro risk once (same for all symbols)
        macro_risk = self.get_macro_risk_factor()
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].copy().sort_values('date')
            composite_risk = self.calculate_composite_risk_factor(df, symbol)
            risk_factor_composite.extend(composite_risk.values)
        
        df['risk_factor_composite'] = risk_factor_composite
        df['risk_factor_macro'] = macro_risk  # Add macro risk as separate column
        
        return df


def adjust_signal_by_risk(
    signal: int,
    confidence: float,
    risk_factor: float
) -> Tuple[int, float]:
    """
    Adjust trading signal based on risk factor.
    
    Args:
        signal: Original signal (-1: sell, 0: hold, 1: buy)
        confidence: Original confidence (0-1)
        risk_factor: Risk factor (0-1, where 1 = high risk)
    
    Returns:
        Adjusted signal and adjusted confidence
    """
    # High risk reduces confidence
    risk_adjusted_confidence = confidence * (1 - 0.5 * risk_factor)
    
    # For buy signals: only buy if risk is not extreme
    # Changed threshold from 0.7 to 0.85 (more permissive)
    if signal == 1 and risk_factor > 0.85:
        # Downgrade BUY to HOLD or SELL only if very extreme risk
        adjusted_signal = 0 if risk_factor < 0.95 else -1
    # For sell signals: increase confidence if risk is high
    elif signal == -1 and risk_factor > 0.75:
        risk_adjusted_confidence = min(1.0, confidence + 0.15 * risk_factor)
        adjusted_signal = signal
    else:
        adjusted_signal = signal
    
    return adjusted_signal, risk_adjusted_confidence


def normalize_predictions_with_risk(
    predictions: np.ndarray,
    probabilities: np.ndarray,
    risk_factors: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Normalize predictions using risk factors.
    
    Args:
        predictions: Model predictions (-1, 0, 1)
        probabilities: Model confidence scores
        risk_factors: Risk factor array (0-1)
    
    Returns:
        Adjusted predictions and adjusted confidences
    """
    adjusted_predictions = predictions.copy()
    adjusted_confidences = np.zeros_like(probabilities)
    
    for i in range(len(predictions)):
        max_prob_idx = np.argmax(probabilities[i])
        confidence = probabilities[i][max_prob_idx]
        
        signal, adj_confidence = adjust_signal_by_risk(
            predictions[i],
            confidence,
            risk_factors[i]
        )
        
        adjusted_predictions[i] = signal
        adjusted_confidences[i] = adj_confidence
    
    return adjusted_predictions, adjusted_confidences
