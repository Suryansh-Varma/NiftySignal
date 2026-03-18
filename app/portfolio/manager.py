"""
Portfolio management and recommendation engine.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .models import Portfolio, Holding
from app.data.loaders import fetch_history_hybrid
from app.config import PortfolioConfig, RESULTS_DIR, get_fno_stocks, get_all_nse_stocks

logger = logging.getLogger(__name__)

# Directory for storing portfolios
PORTFOLIO_DIR = RESULTS_DIR / "portfolios"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)


class PortfolioManager:
    """
    Manages user portfolios and generates buy/sell recommendations.
    """
    
    def __init__(self):
        self.portfolio_dir = PORTFOLIO_DIR
    
    def create_portfolio(self, user_id: str, name: str) -> Portfolio:
        """Create a new portfolio for a user."""
        portfolio = Portfolio(user_id=user_id, name=name)
        portfolio.save(self.portfolio_dir)
        logger.info(f"Created portfolio '{name}' for user {user_id}")
        return portfolio
    
    def get_portfolio(self, user_id: str) -> Optional[Portfolio]:
        """Load user's portfolio."""
        return Portfolio.load(user_id, self.portfolio_dir)
    
    def add_stock(self, user_id: str, symbol: str, shares: float, 
                  avg_price: float, purchase_date: Optional[str] = None) -> Portfolio:
        """Add stock to user's portfolio."""
        portfolio = self.get_portfolio(user_id)
        if portfolio is None:
            portfolio = self.create_portfolio(user_id, f"Portfolio_{user_id}")
        
        holding = Holding(
            symbol=symbol,
            shares=shares,
            avg_buy_price=avg_price,
            purchase_date=purchase_date or datetime.now().strftime("%Y-%m-%d")
        )
        portfolio.add_holding(holding)
        portfolio.save(self.portfolio_dir)
        logger.info(f"Added {shares} shares of {symbol} to portfolio {user_id}")
        return portfolio
    
    def remove_stock(self, user_id: str, symbol: str, shares: Optional[float] = None) -> Portfolio:
        """Remove stock from user's portfolio."""
        portfolio = self.get_portfolio(user_id)
        if portfolio is None:
            raise ValueError(f"Portfolio not found for user {user_id}")
        
        portfolio.remove_holding(symbol, shares)
        portfolio.save(self.portfolio_dir)
        logger.info(f"Removed {shares or 'all'} shares of {symbol} from portfolio {user_id}")
        return portfolio
    
    def get_current_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch current prices for given symbols.
        
        Returns DataFrame with columns: symbol, price, change_pct
        """
        if not symbols:
            return pd.DataFrame(columns=["symbol", "price", "change_pct", "date"])
        
        # Fetch last 5 days of data to get current price
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        try:
            df = fetch_history_hybrid(symbols, start=start_date, end=end_date, use_nselib=True)
            
            if df.empty:
                logger.warning("No price data fetched")
                return pd.DataFrame(columns=["symbol", "price", "change_pct", "date"])
            
            # Get latest price per symbol
            latest = df.sort_values("date").groupby("symbol").tail(1)
            
            # Calculate daily change
            prev = df.sort_values("date").groupby("symbol").tail(2).groupby("symbol").head(1)
            prev = prev.set_index("symbol")["close"]
            
            result = pd.DataFrame({
                "symbol": latest["symbol"].values,
                "price": latest["close"].values,
                "date": latest["date"].values,
            })
            
            result["prev_close"] = result["symbol"].map(prev)
            result["change_pct"] = ((result["price"] - result["prev_close"]) / result["prev_close"] * 100)
            result = result.drop(columns=["prev_close"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching current prices: {e}")
            return pd.DataFrame(columns=["symbol", "price", "change_pct", "date"])
    
    def get_portfolio_summary(self, user_id: str) -> Dict:
        """
        Get complete portfolio summary with current values and P&L.
        
        Returns:
            Dictionary with portfolio metrics and holdings details
        """
        portfolio = self.get_portfolio(user_id)
        if portfolio is None:
            return {"error": "Portfolio not found"}
        
        if not portfolio.holdings:
            return {
                "user_id": user_id,
                "total_invested": 0,
                "current_value": 0,
                "total_pnl": 0,
                "total_pnl_pct": 0,
                "holdings": []
            }
        
        # Get current prices
        symbols = portfolio.symbols
        prices_df = self.get_current_prices(symbols)
        prices = dict(zip(prices_df["symbol"], prices_df["price"]))
        
        # Calculate holdings details
        holdings_detail = []
        total_invested = 0
        total_current_value = 0
        
        for holding in portfolio.holdings:
            current_price = prices.get(holding.symbol, holding.avg_buy_price)
            current_value = holding.shares * current_price
            invested = holding.total_invested
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            
            holdings_detail.append({
                "symbol": holding.symbol,
                "shares": holding.shares,
                "avg_buy_price": holding.avg_buy_price,
                "current_price": current_price,
                "invested": invested,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "purchase_date": holding.purchase_date,
            })
            
            total_invested += invested
            total_current_value += current_value
        
        total_pnl = total_current_value - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        # Add advanced analytics!
        analytics = self.get_portfolio_analytics(user_id)
        
        return {
            "user_id": user_id,
            "portfolio_name": portfolio.name,
            "total_invested": round(total_invested, 2),
            "current_value": round(total_current_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "cash_balance": portfolio.cash_balance,
            "holdings": holdings_detail,
            "analytics": analytics,
            "last_updated": portfolio.updated_at,
        }

    def get_portfolio_analytics(self, user_id: str) -> Dict:
        """
        Calculate Advanced Risk Metrics: Sharpe Ratio and Risk of Ruin.
        Uses 1 year (252 days) historical data.
        """
        portfolio = self.get_portfolio(user_id)
        if not portfolio or not portfolio.holdings:
            return {"sharpe_ratio": 0, "risk_of_ruin": 0, "volatility": 0}

        symbols = portfolio.symbols
        # Fetch 1 year of history
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        try:
            df = fetch_history_hybrid(symbols, start=start_date, end=end_date, use_nselib=True)
            if df.empty:
                return {"sharpe_ratio": 0, "risk_of_ruin": 0, "volatility": 0, "status": "insufficient_data"}
            
            # Pivot to get returns matrix
            df_pivot = df.pivot(index="date", columns="symbol", values="close")
            returns = df_pivot.pct_change().dropna()

            if returns.empty:
                return {"sharpe_ratio": 0, "risk_of_ruin": 0, "volatility": 0, "status": "insufficient_data"}

            # Calculate Weights
            total_val = sum(h.shares * df_pivot[h.symbol].iloc[-1] for h in portfolio.holdings)
            weights = np.array([(h.shares * df_pivot[h.symbol].iloc[-1]) / total_val for h in portfolio.holdings])
            
            # Align weights with columns order
            weight_dict = {h.symbol: w for h, w in zip(portfolio.holdings, weights)}
            sorted_weights = np.array([weight_dict[col] for col in returns.columns])

            # Portfolio daily returns
            port_daily_returns = (returns * sorted_weights).sum(axis=1)
            
            # 1. Annualized Sharpe Ratio (7% RF)
            rf_daily = 0.07 / 252
            mean_ret = port_daily_returns.mean()
            std_ret = port_daily_returns.std()
            
            sharpe = 0
            if std_ret > 0:
                sharpe = (mean_ret - rf_daily) / std_ret * np.sqrt(252)

            # 2. Risk of Ruin (Simplified Continuous Model)
            # Probability of hitting a 50% drawdown
            # RoR = exp(-2 * alpha * goal / sigma^2) where alpha is drift and sigma is volatility
            vol_ann = std_ret * np.sqrt(252)
            drift_ann = mean_ret * 252
            
            drawdown_target = 0.50 # 50% ruin point
            risk_of_ruin = 0
            if vol_ann > 0:
                # Based on Win/Loss walk: P = ( (1-Edge)/(1+Edge) ) ^ Capital
                # We use the drift-vol ratio for a more "holding-based" view
                risk_of_ruin = np.exp(-2 * drift_ann * drawdown_target / (vol_ann**2))
                risk_of_ruin = min(max(risk_of_ruin, 0), 1) # Clamp between 0 and 1

            return {
                "sharpe_ratio": round(float(sharpe), 2),
                "risk_of_ruin": round(float(risk_of_ruin * 100), 1),
                "volatility_ann": round(float(vol_ann * 100), 2),
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Analytics failure for {user_id}: {e}")
            return {"sharpe_ratio": 0, "risk_of_ruin": 0, "volatility": 0, "status": "error"}
    
    def generate_recommendations(self, user_id: str) -> Dict:
        """
        Generate buy/sell/hold recommendations for portfolio stocks.
        
        Uses simple momentum and trend analysis. Can be enhanced with ML models later.
        
        Returns:
            Dictionary with recommendations for each holding
        """
        portfolio = self.get_portfolio(user_id)
        if portfolio is None or not portfolio.holdings:
            return {"recommendations": []}
        
        symbols = portfolio.symbols
        
        # Fetch 3 months of data for trend analysis
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        try:
            df = fetch_history_hybrid(symbols, start=start_date, end=end_date, use_nselib=True)
        except Exception as e:
            logger.error(f"Error fetching data for recommendations: {e}")
            return {"recommendations": [], "error": str(e)}
        
        recommendations = []
        
        for holding in portfolio.holdings:
            symbol_data = df[df["symbol"] == holding.symbol].sort_values("date")
            
            if len(symbol_data) < 20:
                recommendations.append({
                    "symbol": holding.symbol,
                    "action": "HOLD",
                    "reason": "Insufficient data for analysis",
                    "confidence": "LOW"
                })
                continue
            
            # Calculate technical indicators
            current_price = symbol_data["close"].iloc[-1]
            ma_20 = symbol_data["close"].tail(20).mean()
            ma_50 = symbol_data["close"].tail(50).mean() if len(symbol_data) >= 50 else ma_20
            
            # Price vs moving averages
            price_vs_ma20 = (current_price - ma_20) / ma_20
            price_vs_ma50 = (current_price - ma_50) / ma_50
            
            # Recent momentum (5-day, 20-day returns)
            returns_5d = (current_price - symbol_data["close"].iloc[-5]) / symbol_data["close"].iloc[-5]
            returns_20d = (current_price - symbol_data["close"].iloc[-20]) / symbol_data["close"].iloc[-20]
            
            # P&L for this holding
            pnl_pct = (current_price - holding.avg_buy_price) / holding.avg_buy_price
            
            # Decision logic
            action = "HOLD"
            reason = "Neutral signals"
            confidence = "MEDIUM"
            
            # Strong sell signals
            if pnl_pct < -PortfolioConfig.STOP_LOSS_PCT:
                action = "SELL"
                reason = f"Stop loss triggered ({pnl_pct*100:.1f}% loss)"
                confidence = "HIGH"
            elif pnl_pct > PortfolioConfig.TAKE_PROFIT_PCT:
                action = "SELL"
                reason = f"Take profit target reached ({pnl_pct*100:.1f}% gain)"
                confidence = "HIGH"
            elif returns_5d < -0.05 and price_vs_ma20 < -0.05:
                action = "SELL"
                reason = "Downtrend: Price below MA20 with negative momentum"
                confidence = "MEDIUM"
            # Buy signals (for averaging down or adding)
            elif price_vs_ma20 > 0.05 and returns_20d > 0.10:
                action = "BUY"
                reason = "Strong uptrend: Price above MA20 with good momentum"
                confidence = "MEDIUM"
            elif pnl_pct < -0.10 and returns_5d > 0.03:
                action = "BUY"
                reason = "Recovery signal: Oversold with recent bounce"
                confidence = "LOW"
            
            recommendations.append({
                "symbol": holding.symbol,
                "action": action,
                "reason": reason,
                "confidence": confidence,
                "current_price": round(current_price, 2),
                "avg_buy_price": round(holding.avg_buy_price, 2),
                "pnl_pct": round(pnl_pct * 100, 2),
                "shares_held": holding.shares,
                "returns_5d": round(returns_5d * 100, 2),
                "returns_20d": round(returns_20d * 100, 2),
            })
        
        # Build high-growth candidate suggestions from a broader universe (default: F&O for liquidity)
        try:
            growth_candidates = self.find_high_growth_candidates(universe="fno",
                                                                 min_growth_pct=PortfolioConfig.MIN_CANDIDATE_GROWTH_PCT,
                                                                 top_n=PortfolioConfig.MAX_CANDIDATES)
        except Exception as e:
            logger.warning(f"High-growth candidate scan failed: {e}")
            growth_candidates = []

        # Rotation suggestions: propose reallocating from losing holdings to high-growth candidates
        rotation_suggestions = []
        try:
            losing_holdings = [h for h in portfolio.holdings
                               if (symbol_data := df[df["symbol"] == h.symbol]).shape[0] >= 20 and
                               (symbol_data.sort_values("date")["close"].iloc[-1] - h.avg_buy_price) / h.avg_buy_price < -0.10]
            top_candidates = growth_candidates[:3]
            for loser in losing_holdings:
                for cand in top_candidates:
                    rotation_suggestions.append({
                        "from_symbol": loser.symbol,
                        "to_symbol": cand["symbol"],
                        "reason": f"Rotate from underperformer into high-growth ({int(cand['growth_60d']*100)}% 60D)",
                        "suggested_action": "SELL_PARTIAL_AND_BUY",
                        "confidence": "MEDIUM"
                    })
        except Exception as e:
            logger.warning(f"Rotation suggestion build failed: {e}")

        return {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "recommendations": recommendations,
            "high_growth_candidates": growth_candidates,
            "rotation_suggestions": rotation_suggestions,
        }

    def find_high_growth_candidates(self, universe: str = "fno",
                                    min_growth_pct: float = 0.20,
                                    top_n: int = 10) -> List[Dict]:
        """
        Scan a selected universe and return top high-growth candidates.
        
        Criteria:
        - Positive momentum: 20D and 60D returns
        - Price above MA20
        - 60D growth >= min_growth_pct
        
        Returns a list of dicts with symbol, growth metrics, and simple score.
        """
        # Select universe
        if universe == "fno":
            symbols = get_fno_stocks()
        else:
            # Full equity universe can be heavy; limit to first 500 for performance
            symbols = get_all_nse_stocks()[:500]
        if not symbols:
            return []

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")

        df = fetch_history_hybrid(symbols, start=start_date, end=end_date, use_nselib=True)
        if df.empty:
            return []

        results = []
        for sym, sdf in df.groupby("symbol"):
            sdf = sdf.sort_values("date")
            closes = sdf["close"].values
            if len(closes) < 60:
                continue
            current = closes[-1]
            ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else current
            r20 = (current - closes[-20]) / closes[-20] if len(closes) >= 20 else 0.0
            r60 = (current - closes[-60]) / closes[-60]
            score = r60 + 0.5 * r20 + (0.05 if current > ma20 else -0.05)
            if r60 >= min_growth_pct and r20 > 0 and current > ma20:
                results.append({
                    "symbol": sym,
                    "growth_20d": round(r20 * 100, 2),
                    "growth_60d": round(r60 * 100, 2),
                    "above_ma20": True,
                    "score": round(score, 4)
                })

        # Sort by score and cap top_n
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
        return results
