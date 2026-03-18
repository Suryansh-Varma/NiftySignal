import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

class SimpleBacktester:
    def __init__(
        self,
        initial_capital: float = 1000000.0,
        position_size: float = 0.005,  # 0.5% per position (optimized)
        stop_loss: Optional[float] = 0.01,  # 1% stop loss (tighter)
        take_profit: Optional[float] = 0.025,  # 2.5% take profit (quicker)
        trailing_stop: Optional[float] = 0.008,  # 0.8% trailing stop
        min_confidence: float = 0.70,  # Min 70% confidence (selective)
    ) -> None:
        """
        Simple backtester for evaluating trading strategies.
        Optimized for 0.75 high-risk environment.
        
        Args:
            initial_capital: Starting capital
            position_size: Size of each position as fraction of capital (0.5%)
            stop_loss: Stop loss percentage (1%)
            take_profit: Take profit percentage (2.5%)
            trailing_stop: Trailing stop percentage (0.8%)
            min_confidence: Minimum confidence threshold (70%)
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        self.min_confidence = min_confidence
        
        self.positions: Dict[str, dict] = {}  # Current positions {symbol: position_info}
        self.trades: List[dict] = []  # Completed trades
        self.capital = initial_capital
        self.equity = []  # Track equity curve
    
    def _open_position(self, row: pd.Series, signal: int) -> None:
        """
        Open a new position.
        
        Args:
            row: DataFrame row with price data
            signal: Trading signal (1 for buy, -1 for sell)
        """
        symbol = row['symbol']
        if symbol in self.positions:
            return  # Already have a position
        
        position_capital = self.capital * self.position_size
        shares = position_capital // row['close']  # Integer number of shares
        cost = shares * row['close']
        
        self.positions[symbol] = {
            'entry_date': row['date'],
            'entry_price': row['close'],
            'shares': shares,
            'cost': cost,
            'signal': signal,
            'stop_price': row['close'] * (1 - self.stop_loss) if self.stop_loss else None,
            'target_price': row['close'] * (1 + self.take_profit) if self.take_profit else None
        }
        
        self.capital -= cost
    
    def _close_position(self, row: pd.Series, symbol: str, reason: str) -> None:
        """
        Close an existing position.
        
        Args:
            row: DataFrame row with price data
            symbol: Stock symbol
            reason: Reason for closing (e.g., 'stop_loss', 'take_profit', 'signal')
        """
        position = self.positions[symbol]
        proceeds = position['shares'] * row['close']
        profit = proceeds - position['cost']
        roi = profit / position['cost']
        
        self.trades.append({
            'symbol': symbol,
            'entry_date': position['entry_date'],
            'exit_date': row['date'],
            'entry_price': position['entry_price'],
            'exit_price': row['close'],
            'shares': position['shares'],
            'profit': profit,
            'roi': roi,
            'signal': position['signal'],
            'exit_reason': reason
        })
        
        self.capital += proceeds
        del self.positions[symbol]
    
    def run(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
        """
        Run backtest on price data with signals.
        
        Args:
            df: DataFrame with columns [date, symbol, open, high, low, close, signal]
                where signal is -1 (sell), 0 (hold), or 1 (buy)
        
        Returns:
            Tuple of (trades_df, equity_df, metrics_dict)
            - trades_df: DataFrame with individual trade records
            - equity_df: DataFrame with equity curve over time
            - metrics_dict: Dictionary with performance metrics
        """
        # Sort by date to process chronologically
        df = df.sort_values(['date', 'symbol'])
        
        # Track equity at each timestep
        dates = df['date'].unique()
        equity_data = []
        
        for date in dates:
            day_data = df[df['date'] == date]
            
            # First check stops/targets on open positions
            for symbol in list(self.positions.keys()):
                if symbol not in day_data['symbol'].values:
                    continue
                    
                row = day_data[day_data['symbol'] == symbol].iloc[0]
                pos = self.positions[symbol]
                
                # Check stop loss
                if pos['stop_price'] and row['low'] <= pos['stop_price']:
                    self._close_position(row, symbol, 'stop_loss')
                
                # Check take profit
                elif pos['target_price'] and row['high'] >= pos['target_price']:
                    self._close_position(row, symbol, 'take_profit')
                
                # Check exit signals
                elif (pos['signal'] == 1 and row['signal'] == -1) or \
                     (pos['signal'] == -1 and row['signal'] == 1):
                    self._close_position(row, symbol, 'signal')
            
            # Then look for new entry signals
            for _, row in day_data.iterrows():
                if row['signal'] in [-1, 1]:  # Valid entry signal
                    self._open_position(row, row['signal'])
            
            # Calculate current equity
            positions_value = sum(
                pos['shares'] * day_data[day_data['symbol'] == sym]['close'].iloc[0]
                for sym, pos in self.positions.items()
                if sym in day_data['symbol'].values
            )
            current_equity = self.capital + positions_value
            
            equity_data.append({
                'date': date,
                'equity': current_equity,
                'returns': (current_equity / self.initial_capital) - 1,
                'positions': len(self.positions)
            })
        
        # Close any remaining positions using last known prices
        for symbol in list(self.positions.keys()):
            symbol_data = df[df['symbol'] == symbol].sort_values('date')
            if symbol_data.empty:
                # If no data for symbol, skip closing (shouldn't happen but safety check)
                continue
            last_price = symbol_data.iloc[-1]
            self._close_position(last_price, symbol, 'end_of_data')
        
        # Convert results to DataFrames
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(equity_data)
        
        # Calculate metrics
        metrics = {
            'total_trades': len(trades_df),
            'winning_trades': len(trades_df[trades_df['profit'] > 0]),
            'losing_trades': len(trades_df[trades_df['profit'] <= 0]),
            'win_rate': len(trades_df[trades_df['profit'] > 0]) / len(trades_df) if len(trades_df) > 0 else 0,
            'avg_profit': trades_df['profit'].mean() if len(trades_df) > 0 else 0,
            'avg_roi': trades_df['roi'].mean() if len(trades_df) > 0 else 0,
            'final_equity': equity_df['equity'].iloc[-1] if len(equity_df) > 0 else self.initial_capital,
            'total_return': (equity_df['equity'].iloc[-1] / self.initial_capital - 1) if len(equity_df) > 0 else 0,
            'max_drawdown': (equity_df['equity'].max() - equity_df['equity'].min()) / equity_df['equity'].max() if len(equity_df) > 0 else 0,
        }
        
        return trades_df, equity_df, metrics