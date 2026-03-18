import sys
from pathlib import Path
import pandas as pd
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import DATA_RAW_DIR as RAW, DATA_PROCESSED_DIR as PROC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger('regularize_calendar')

try:
    import pandas_market_calendars as mcal
except Exception:
    mcal = None


def main():
    src = RAW / 'universe_data.csv'
    if not src.exists():
        log.error(f"Source CSV not found: {src}")
        raise SystemExit(1)
    df = pd.read_csv(src)
    if df.empty:
        log.error("Source CSV is empty")
        raise SystemExit(1)
    df['date'] = pd.to_datetime(df['date'])
    symbols = sorted(df['symbol'].unique())

    # Build trading calendar (XNSE) or fallback to business days
    start = df['date'].min().normalize()
    end = df['date'].max().normalize()
    if mcal is not None:
        cal = mcal.get_calendar('XNSE')
        schedule = cal.schedule(start_date=start, end_date=end)
        trading_days = pd.to_datetime(schedule.index).normalize()
        log.info(f"Using XNSE calendar with {len(trading_days)} trading days")
    else:
        trading_days = pd.bdate_range(start=start, end=end)
        log.warning("pandas-market-calendars not available, using business days as fallback")

    frames = []
    for sym in symbols:
        s = df[df['symbol'] == sym].copy()
        s = s.drop_duplicates(subset=['date']).set_index('date')
        # Reindex to trading days
        s = s.reindex(trading_days)
        s['symbol'] = sym
        s['missing'] = s['open'].isna() | s['close'].isna()
        frames.append(s.reset_index().rename(columns={'index': 'date'}))

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(['symbol','date'])

    # Write to processed folder as a new file
    PROC.mkdir(parents=True, exist_ok=True)
    dst = PROC / 'universe_data_regularized.csv'
    out.to_csv(dst, index=False)
    log.info(f"Wrote regularized CSV with continuous trading dates: {dst}")


if __name__ == '__main__':
    main()
