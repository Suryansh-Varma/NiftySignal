from pathlib import Path
from typing import List
import pandas as pd
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import DATA_PROCESSED_DIR as PROC, DATA_RAW_DIR as RAW

PROC.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

parquets = sorted(PROC.glob("*.parquet"))
print(f"Found {len(parquets)} parquet files in {PROC}")

if not parquets:
    raise SystemExit("No parquet files found in data/processed; nothing to assemble.")

frames = []
for p in parquets:
    try:
        df = pd.read_parquet(p)
        # Keep only expected columns if present
        expected = ["date","symbol","open","high","low","close","volume"]
        cols = [c for c in expected if c in df.columns]
        df = df[cols]
        frames.append(df)
    except Exception as e:
        print(f"Warning: failed to read {p}: {e}")

if not frames:
    raise SystemExit("No readable parquet frames found.")

full = pd.concat(frames, ignore_index=True)
# Ensure date column
full['date'] = pd.to_datetime(full['date'], errors='coerce')
# Drop rows without key price fields
full = full.dropna(subset=['date','open','high','low','close'])
# Deduplicate keeping last
full = full.sort_values(['symbol','date'])
full = full.drop_duplicates(subset=['symbol','date'], keep='last')

out_proc = PROC / 'universe_data.csv'
full.to_csv(out_proc, index=False)

print(f"Wrote {len(full)} rows to {out_proc}")

# Summary by symbol
latest = full.groupby('symbol')['date'].max().reset_index()
print('\nPer-symbol latest dates sample:')
print(latest.sort_values('date').head(5).to_string(index=False))
print(latest.sort_values('date').tail(5).to_string(index=False))

# Overall date range
print('\nOverall date range:', full['date'].min(), 'to', full['date'].max())

# Count symbols with latest < expected recent date (2025-11-04)
expected_date = pd.Timestamp('2025-11-04')
missing = latest[latest['date'] < expected_date]
print(f"\nSymbols with latest before {expected_date.date()}: {len(missing)}")
if not missing.empty:
    print(missing.sort_values('date').to_string(index=False))
