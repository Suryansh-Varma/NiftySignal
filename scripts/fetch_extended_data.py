"""
Fetch Extended Data
===================
Fetches 2 years of OHLCV data for all Nifty 50 stocks PLUS
NSE sectoral indices (BankNifty, NiftyIT, NiftyPharma, NiftyAuto, NiftyMetal).
Merges everything into data/processed/universe_data.csv and saves
sectoral index data separately for use as model features.

Usage:
    python scripts/fetch_extended_data.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows console encoding for progress bars
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import yfinance as yf

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.getLogger("yfinance").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_PROCESSED = Path("data/processed")
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

UNIVERSE_CSV   = DATA_PROCESSED / "universe_data.csv"
SECTOR_IDX_CSV = DATA_PROCESSED / "sectoral_indices.csv"

# ── NIFTY 50 stocks ───────────────────────────────────────────────────────────
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "BAJFINANCE.NS", "TATAMOTORS.NS", "WIPRO.NS", "ULTRACEMCO.NS", "TITAN.NS",
    "NESTLEIND.NS", "HCLTECH.NS", "POWERGRID.NS", "TECHM.NS", "NTPC.NS",
    "M&M.NS", "INDUSINDBK.NS", "ADANIENT.NS", "BAJAJFINSV.NS", "JSWSTEEL.NS",
    "TATASTEEL.NS", "GRASIM.NS", "ONGC.NS", "HINDALCO.NS", "COALINDIA.NS",
    "BPCL.NS", "DIVISLAB.NS", "CIPLA.NS", "DRREDDY.NS", "EICHERMOT.NS",
    "HEROMOTOCO.NS", "BRITANNIA.NS", "APOLLOHOSP.NS", "TATACONSUM.NS", "ADANIPORTS.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "BAJAJ-AUTO.NS", "SHRIRAMFIN.NS", "BEL.NS",
    "LTIM.NS",
]

# ── NSE Sectoral Indices (yfinance symbols) ───────────────────────────────────
SECTORAL_INDICES = {
    "nifty50":   "^NSEI",       # Nifty 50 (market benchmark)
    "banknifty": "^NSEBANK",    # Bank Nifty
    "niftyit":   "^CNXIT",      # Nifty IT
    "niftypharma": "NIFTYPHARMA.NS",  # Nifty Pharma
    "niftyauto": "^CNXAUTO",    # Nifty Auto
    "niftymetal": "^CNXMETAL",  # Nifty Metal
    "niftyfmcg": "^CNXFMCG",    # Nifty FMCG
    "niftyenergy": "^CNXENERGY", # Nifty Energy
    "niftyinfra": "^CNXINFRA",  # Nifty Infra
}


def _download_close(symbols, start, end, label="data"):
    """Download close prices using yfinance. Returns DataFrame with date index."""
    logger.info(f"Downloading {label} for {len(symbols)} symbols ({start} → {end})...")
    raw = yf.download(
        symbols if len(symbols) > 1 else symbols[0],
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if raw.empty:
        logger.error(f"No data returned for {label}")
        return pd.DataFrame()
    return raw


def fetch_stock_data(start: str, end: str) -> pd.DataFrame:
    """Download 2 years of OHLCV for all Nifty 50 stocks and return in long format."""
    raw = _download_close(NIFTY_50, start, end, label="Nifty 50 stocks")
    if raw.empty:
        return pd.DataFrame()

    rows = []
    for symbol in NIFTY_50:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                sym_data = raw.xs(symbol, axis=1, level=1)
            else:
                sym_data = raw
            for date, row in sym_data.iterrows():
                close = row.get("Close", None)
                if pd.isna(close):
                    continue
                rows.append({
                    "symbol": symbol,
                    "date": pd.Timestamp(date).normalize(),
                    "open":   float(row.get("Open",   close)),
                    "high":   float(row.get("High",   close)),
                    "low":    float(row.get("Low",    close)),
                    "close":  float(close),
                    "volume": float(row.get("Volume", 0)),
                })
        except Exception as e:
            logger.warning(f"Skipping {symbol}: {e}")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.drop_duplicates(subset=["symbol", "date"]).sort_values(["symbol", "date"])
    logger.info(f"Stock data: {len(df)} rows for {df['symbol'].nunique()} symbols")
    return df


def fetch_sectoral_indices(start: str, end: str) -> pd.DataFrame:
    """Download sectoral index close prices and return in wide format (date + one col per index)."""
    symbols = list(SECTORAL_INDICES.values())
    names   = list(SECTORAL_INDICES.keys())

    raw = yf.download(symbols, start=start, end=end, auto_adjust=True, progress=False, threads=True)
    if raw.empty:
        logger.error("Sectoral index download failed")
        return pd.DataFrame()

    result = pd.DataFrame(index=raw.index)

    for name, sym in SECTORAL_INDICES.items():
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                col = raw["Close"][sym] if sym in raw["Close"].columns else raw["Close"].iloc[:, 0]
            else:
                col = raw["Close"]
            result[f"idx_{name}_close"] = col.values
        except Exception as e:
            logger.warning(f"Index {name} ({sym}): {e}")

    result.index = pd.to_datetime(result.index).tz_localize(None)
    result = result.reset_index().rename(columns={"index": "date", "Date": "date"})
    result = result.dropna(how="all", subset=[c for c in result.columns if c != "date"])
    logger.info(f"Sectoral indices: {len(result)} rows, {result.shape[1]-1} indices")
    return result


def main():
    end   = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")  # 2 years

    print("\n" + "=" * 70)
    print("EXTENDED DATA FETCH — 2 YEARS + SECTORAL INDICES")
    print(f"Period: {start} → {end}")
    print("=" * 70)

    # ── 1. Stock OHLCV ────────────────────────────────────────────────────────
    print("\n[1] Fetching 2 years of stock data...")
    stock_df = fetch_stock_data(start, end)

    if stock_df.empty:
        print("ERROR: No stock data fetched. Aborting.")
        sys.exit(1)

    stock_df.to_csv(UNIVERSE_CSV, index=False)
    print(f"  Saved {len(stock_df)} rows → {UNIVERSE_CSV}")
    print(f"  Date range: {stock_df['date'].min().date()} → {stock_df['date'].max().date()}")
    print(f"  Avg rows/symbol: {len(stock_df) // stock_df['symbol'].nunique()}")

    # ── 2. Sectoral Indices ───────────────────────────────────────────────────
    print("\n[2] Fetching NSE sectoral indices...")
    idx_df = fetch_sectoral_indices(start, end)

    if not idx_df.empty:
        idx_df.to_csv(SECTOR_IDX_CSV, index=False)
        print(f"  Saved {len(idx_df)} rows → {SECTOR_IDX_CSV}")
        cols = [c for c in idx_df.columns if c != "date"]
        print(f"  Indices captured: {', '.join(cols)}")
    else:
        print("  WARNING: No sectoral index data fetched (will use Nifty 50 only)")

    print("\n" + "=" * 70)
    print("DATA FETCH COMPLETE")
    print(f"  Run next: python scripts/retrain_sector_models.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
