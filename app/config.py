"""
Configuration file for NiftySignal project.
Contains shared constants, paths, and configuration values.
"""
from pathlib import Path
from typing import List

# Project root directory (go up one level from app/ to project root)
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw_csv"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Model and results directories
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure directories exist
for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, MODELS_DIR, RESULTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Trading configuration constants
class TradingConfig:
    """Trading strategy configuration constants."""
    # Capital and position sizing
    INITIAL_CAPITAL = 1_000_000.0  # 1M initial capital
    POSITION_SIZE = 0.005  # 0.5% per position (optimized for 0.75 risk)
    MAX_POSITIONS = 10  # Max 10 concurrent positions
    STOP_LOSS = 0.01  # 1% stop loss (tighter in high risk)
    TAKE_PROFIT = 0.025  # 2.5% take profit (quicker exits)
    TRAILING_STOP = 0.008  # 0.8% trailing stop
    
    # Confidence thresholds (risk-aware)
    MIN_BUY_CONFIDENCE = 0.55  # lowered from 0.70 to increase signal capture
    MIN_SELL_CONFIDENCE = 0.45  # lowered from 0.50
    HOLD_THRESHOLD = 0.50  # Neutral zone
    
    # Feature engineering
    MIN_DAYS_FOR_FEATURES = 60  # Minimum days needed for technical indicators
    FORWARD_DAYS = 5  # 5-day forward returns
    RETURN_THRESHOLD = 0.015  # lowered from 0.025 to capture more opportunities
    RETURN_THRESHOLD_STRICT = 0.01  # 1% threshold for model training
    
    # Model configuration
    TEST_SIZE = 0.2  # 20% test split
    RANDOM_STATE = 42  # For reproducibility
    
    # Sector strategy (0.75 risk = defensive only)
    DEFENSIVE_SECTORS = ['Pharma', 'FMCG', 'Utilities', 'Healthcare']
    AVOID_SECTORS = ['Auto', 'Tech', 'Finance', 'Cyclicals', 'Discretionary']
    SECTOR_FILTER_ENABLED = True

# Investment goal configuration (for target return in specific horizon)
class GoalConfig:
    """Configuration for goal-based selection (e.g., 15% in ~6 months)."""
    CAPITAL_INR = 1_200_000  # 12 lakh
    TARGET_RETURN_PCT = 0.15  # 15% target
    HORIZON_DAYS = 126  # approx 6 months of trading days
    # Model/testing specifics (defaults sensible for longer horizon)
    TEST_SIZE = 0.2
    RANDOM_STATE = 42

# NIFTY 50 universe
NIFTY_50_UNIVERSE: List[str] = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS",
    "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS",
    "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

# Portfolio tracking configuration
class PortfolioConfig:
    """Configuration for portfolio tracking and recommendations."""
    # Data fetching strategy
    FETCH_ON_DEMAND = True  # Only fetch data for stocks in user portfolios
    CACHE_EXPIRY_DAYS = 1  # How often to refresh stock data
    
    # Recommendation thresholds
    STRONG_BUY_THRESHOLD = 0.10  # 10% expected gain
    BUY_THRESHOLD = 0.05  # 5% expected gain
    HOLD_THRESHOLD = 0.02  # 2% expected gain
    SELL_THRESHOLD = -0.05  # -5% expected loss
    
    # Portfolio limits
    MAX_STOCKS_PER_PORTFOLIO = 100
    MIN_INVESTMENT_PER_STOCK = 1000  # Rs 1,000 minimum
    
    # Risk management
    STOP_LOSS_PCT = 0.07  # 7% stop loss
    TAKE_PROFIT_PCT = 0.15  # 15% take profit
    MAX_PORTFOLIO_DRAWDOWN = 0.20  # 20% max drawdown
    
    # High-growth candidate scanning
    MIN_CANDIDATE_GROWTH_PCT = 0.20  # 20% growth over ~60 days
    MAX_CANDIDATES = 10  # top N high-growth suggestions

# Helper function to get all NSE stocks (lazy loading)
def get_all_nse_stocks() -> List[str]:
    """
    Get complete list of all NSE-listed stocks (~3000+ companies).
    
    This function lazy-loads the data from nselib to avoid startup delays.
    Results are cached in the data loader module.
    
    Returns:
        List of all NSE stock symbols with .NS suffix
        
    Usage:
        from app.config import get_all_nse_stocks
        all_stocks = get_all_nse_stocks()
    """
    from app.data.loaders import get_all_nse_equities
    return get_all_nse_equities()

def get_fno_stocks() -> List[str]:
    """
    Get list of NSE F&O stocks (~200 liquid stocks).
    
    Returns:
        List of F&O stock symbols with .NS suffix
    """
    from app.data.loaders import get_nse_fno_equities
    return get_nse_fno_equities()

# Data validation thresholds
class DataValidationConfig:
    """Data quality validation thresholds."""
    MAX_PRICE_CHANGE_PCT = 0.50  # 50% max daily price change (sanity check - increased from 20%)
    MIN_VOLUME = 0  # Minimum volume (0 means no filter)
    MAX_MISSING_DAYS = 7  # Warn if data is more than 7 days old
    MIN_DATA_POINTS_PER_SYMBOL = 60  # Minimum data points required per symbol

