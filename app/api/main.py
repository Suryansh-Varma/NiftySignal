import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
import pandas as pd
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import DATA_RAW_DIR, get_all_nse_stocks, DataValidationConfig
import os
from app.data.loaders import fetch_history_yf, fetch_history_nsepy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silence verbose third-party debug noise during bulk fetch runs
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("peewee").setLevel(logging.WARNING)
logging.getLogger("nselib").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Get all NSE stocks (~2,671 listed companies)
logger.info("Loading NSE universe (all 2671+ listed stocks)...")
UNIVERSE = get_all_nse_stocks()
logger.info(f"Universe size: {len(UNIVERSE)} stocks")

# Get current date to fetch latest available data (includes today if market is open)
current_date = datetime.now().strftime("%Y-%m-%d")

try:
    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get current date to fetch latest available data (includes today if market is open)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # First try to fetch historical data
    # Default to NSELIB for official NSE data, fall back to yfinance
    provider = os.getenv("DATA_PROVIDER", "NSELIB").upper()  # NSELIB or YF or NSEPY
    logger.info(f"Provider={provider}: Fetching data for {len(UNIVERSE)} symbols from 2023-01-01 to {current_date}")
    
    if provider == "NSELIB":
        try:
            from app.data.loaders import fetch_history_nselib
            logger.info("Attempting to fetch data using nselib (official NSE data)...")
            df = fetch_history_nselib(UNIVERSE, start="2023-01-01", end=current_date, include_delivery=False)
            if df.empty:
                logger.warning("nselib returned empty; falling back to yfinance")
                df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
        except KeyboardInterrupt:
            logger.warning("nselib fetch interrupted; falling back to yfinance")
            df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
        except Exception as e:
            logger.warning(f"nselib unavailable or failed: {e}; falling back to yfinance")
            df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
    elif provider == "NSEPY":
        try:
            df = fetch_history_nsepy(UNIVERSE, start="2023-01-01", end=current_date)
        except KeyboardInterrupt:
            logger.warning("NSEpy fetch interrupted; falling back to yfinance")
            df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
        except Exception as e:
            logger.warning(f"NSEpy unavailable or failed: {e}; falling back to yfinance")
            df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
        # If NSEpy returns empty, fall back to yfinance
        if df.empty:
            logger.warning("NSEpy returned empty; falling back to yfinance")
            df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
    else:
        df = fetch_history_yf(UNIVERSE, start="2023-01-01", end=current_date, force_refresh=True)
    
    if df.empty:
        raise ValueError("No data fetched from yfinance")
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Only keep data up to the current date
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    df = df[df['date'] <= today]
    
    # Verify we have recent data
    if df.empty:
        raise ValueError("No data remaining after filtering future dates")
    
    latest_date = df['date'].max()
    if latest_date < today - timedelta(days=DataValidationConfig.MAX_MISSING_DAYS):
        logger.warning(f"Latest data is more than {DataValidationConfig.MAX_MISSING_DAYS} days old. Latest date: {latest_date}")
    
    logger.info(f"Filtered data to keep only historical dates up to {today}")
    
    # Sort by date and save to processed folder
    df = df.sort_values(['symbol', 'date'])
    DATA_PROCESSED_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_PROCESSED_DIR / "universe_data.csv"
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved data to {output_path}")
        logger.info(f"Data date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"Total records: {len(df)}")
    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {e}")
        raise
    
except ValueError as e:
    logger.error(f"Data validation error: {e}")
    raise
except Exception as e:
    logger.error(f"Error fetching data: {e}", exc_info=True)
    raise