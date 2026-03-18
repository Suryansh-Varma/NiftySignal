"""
Refresh ALL NSE stocks data (2000+ companies).
This takes 30-60 minutes due to Yahoo Finance rate limits.

Run in background: python refresh_all_nse_data.py
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
import sys

# Suppress yfinance debug logs
logging.getLogger('yfinance').setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_refresh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_all_nse_symbols():
    """Get all NSE equity symbols."""
    try:
        from app.config import get_all_nse_stocks
        symbols = get_all_nse_stocks()
        logger.info(f"Loaded {len(symbols)} symbols from config")
        return symbols
    except:
        # Fallback to nselib
        try:
            from nselib import capital_market
            eq_list = capital_market.equity_list()
            symbols = [f"{s}.NS" for s in eq_list['SYMBOL'].tolist()]
            logger.info(f"Loaded {len(symbols)} symbols from nselib")
            return symbols
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []

def fetch_batch(symbols, start, end, batch_size=50):
    """Fetch data in batches to avoid rate limits."""
    all_data = []
    total_batches = (len(symbols) + batch_size - 1) // batch_size
    
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Batch {batch_num}/{total_batches}: Fetching {len(batch)} symbols...")
        
        try:
            data = yf.download(batch, start=start, end=end, progress=False, threads=True)
            
            if data.empty:
                logger.warning(f"Batch {batch_num}: No data returned")
                continue
            
            # Convert to long format
            for symbol in batch:
                try:
                    if isinstance(data.columns, pd.MultiIndex):
                        sym_data = data.xs(symbol, axis=1, level=1)
                    else:
                        sym_data = data
                    
                    for date, row in sym_data.iterrows():
                        close_val = row.get('Close', row.get('close'))
                        if pd.notna(close_val):
                            all_data.append({
                                'symbol': symbol,
                                'date': date.strftime('%Y-%m-%d'),
                                'open': row.get('Open', row.get('open')),
                                'high': row.get('High', row.get('high')),
                                'low': row.get('Low', row.get('low')),
                                'close': close_val,
                                'volume': row.get('Volume', row.get('volume'))
                            })
                except Exception as e:
                    pass  # Skip failed symbols silently
            
            logger.info(f"Batch {batch_num}: Collected {len(all_data)} total records")
            
        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
        
        # Rate limit delay between batches
        if i + batch_size < len(symbols):
            time.sleep(1)
    
    return pd.DataFrame(all_data)

def main():
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("REFRESHING ALL NSE STOCKS (~2000+ companies)")
    logger.info("This will take 30-60 minutes...")
    logger.info("=" * 70)
    
    # Get all symbols
    symbols = get_all_nse_symbols()
    if not symbols:
        logger.error("No symbols found!")
        return
    
    logger.info(f"Total symbols to fetch: {len(symbols)}")
    
    # Date range
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
    
    logger.info(f"Date range: {start} to {end}")
    
    # Fetch in batches
    start_time = time.time()
    df = fetch_batch(symbols, start, end, batch_size=50)
    elapsed = time.time() - start_time
    
    if df.empty:
        logger.error("No data collected!")
        return
    
    logger.info(f"Fetched {len(df)} records for {df['symbol'].nunique()} symbols in {elapsed/60:.1f} minutes")
    
    # Save
    output_path = Path(__file__).parent / "data" / "processed" / "universe_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved to {output_path}")
    
    # Check date distribution
    latest_per_symbol = df.groupby('symbol')['date'].max()
    logger.info(f"\nLatest date distribution:")
    for date, count in latest_per_symbol.value_counts().sort_index(ascending=False).head(5).items():
        logger.info(f"  {date}: {count} stocks")
    
    # Update recommendations
    logger.info("\nUpdating recommendations with latest prices...")
    rec_path = Path(__file__).parent / "results" / "latest_recommendations.csv"
    
    if rec_path.exists():
        recs = pd.read_csv(rec_path)
        latest_prices = df.groupby('symbol').apply(lambda x: x.loc[x['date'].idxmax()]).reset_index(drop=True)
        
        updated = 0
        for idx, row in recs.iterrows():
            symbol = row['symbol']
            if symbol in latest_prices['symbol'].values:
                latest = latest_prices[latest_prices['symbol'] == symbol].iloc[0]
                recs.at[idx, 'last_price'] = latest['close']
                recs.at[idx, 'last_date'] = latest['date']
                updated += 1
        
        recs.to_csv(rec_path, index=False)
        logger.info(f"Updated {updated} recommendations")
    
    logger.info("\n" + "=" * 70)
    logger.info("COMPLETE!")
    logger.info(f"Total time: {elapsed/60:.1f} minutes")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
