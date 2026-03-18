import sys
from pathlib import Path
from typing import List
import pandas as pd
from datetime import datetime, timedelta
import logging
import subprocess

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import DATA_PROCESSED_DIR as PROC, DATA_RAW_DIR as RAW
from app.data.loaders import fetch_history_yf

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CSV = PROC / 'universe_data.csv'

expected_date = pd.Timestamp('2025-11-04')
start = expected_date.strftime('%Y-%m-%d')
# end should be next day to ensure inclusive fetch
end = (expected_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

if not CSV.exists():
    logger.info(f"{CSV} not found, attempting to assemble from existing parquets first.")
    script_path = Path(__file__).parent / 'assemble_universe.py'
    subprocess.check_call([sys.executable, str(script_path)])

# Read assembled CSV
if not CSV.exists():
    logger.error(f"Still no {CSV}; aborting.")
    raise SystemExit(1)

df = pd.read_csv(CSV, parse_dates=['date'])
latest = df.groupby('symbol')['date'].max().reset_index()
missing: List[str] = latest[latest['date'] < expected_date]['symbol'].tolist()
logger.info(f"Symbols missing {expected_date.date()}: {len(missing)}")
if missing:
    logger.info(f"Fetching {len(missing)} symbols for {start}..{end}")
    fetched = fetch_history_yf(missing, start=start, end=end, force_refresh=True)
    logger.info(f"Fetched {len(fetched)} rows")
    # Re-run assemble to update CSV
    script_path = Path(__file__).parent / 'assemble_universe.py'
    subprocess.check_call([sys.executable, str(script_path)])
    logger.info("Re-assembled universe CSV from parquet caches.")
else:
    logger.info("No symbols missing; nothing to refetch.")

# Final verification
df2 = pd.read_csv(CSV, parse_dates=['date'])
latest2 = df2.groupby('symbol')['date'].max().reset_index()
count_up_to = (latest2['date'] >= expected_date).sum()
logger.info(f"Symbols with data on or after {expected_date.date()}: {count_up_to} / {len(latest2)}")
print(latest2.sort_values('date').tail(10).to_string(index=False))
