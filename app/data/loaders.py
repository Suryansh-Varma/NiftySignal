# app/data/loaders.py
from __future__ import annotations
import os
import logging
from pathlib import Path
from io import BytesIO
from typing import List, Optional
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
try:
    # Primary: nselib for NSE official data
    from nselib import capital_market
except Exception:
    capital_market = None

try:
    # Optional: NSE India oriented free provider (fallback)
    from nsepy import get_history as nse_get_history
except Exception:
    nse_get_history = None

from app.config import DATA_RAW_DIR as DATA_RAW, DATA_PROCESSED_DIR as DATA_PROC, DataValidationConfig, NIFTY_50_UNIVERSE

# Set up logging
logger = logging.getLogger(__name__)

# Cache for full NSE equity list
_NSE_EQUITY_LIST_CACHE = None
_NSE_EQUITY_LIST_CACHE_TIME = None
_CACHE_EXPIRY_HOURS = 24  # Refresh equity list daily

for p in (DATA_RAW, DATA_PROC):
    p.mkdir(parents=True, exist_ok=True)


def get_all_nse_equities() -> List[str]:
    """
    Get complete list of all NSE-listed equities (~3000+ companies).
    
    Uses nselib to fetch from NSE official source. Results are cached for 24 hours.
    Falls back to NIFTY_50 universe when nselib isn't available or fails.
    
    Returns:
        List of symbols with .NS suffix (e.g., ["RELIANCE.NS", "TCS.NS", ...])
    """
    global _NSE_EQUITY_LIST_CACHE, _NSE_EQUITY_LIST_CACHE_TIME
    
    # Check cache
    if _NSE_EQUITY_LIST_CACHE is not None and _NSE_EQUITY_LIST_CACHE_TIME is not None:
        hours_elapsed = (datetime.now() - _NSE_EQUITY_LIST_CACHE_TIME).total_seconds() / 3600
        if hours_elapsed < _CACHE_EXPIRY_HOURS:
            logger.info(f"Returning cached NSE equity list ({len(_NSE_EQUITY_LIST_CACHE)} symbols)")
            return _NSE_EQUITY_LIST_CACHE
    
    if capital_market is None:
        logger.warning("nselib capital_market not available; attempting NSE archives fallback")
        # Try archives-based full equity list
        fallback_syms = _fetch_equity_list_via_archives()
        if fallback_syms:
            _NSE_EQUITY_LIST_CACHE = fallback_syms
            _NSE_EQUITY_LIST_CACHE_TIME = datetime.now()
            logger.info(f"Fetched {len(fallback_syms)} symbols via NSE archives")
            return fallback_syms
        # Try recent bhav copies to assemble active universe
        bhav_syms = _fetch_equity_list_via_recent_bhav(days=14)
        if bhav_syms:
            _NSE_EQUITY_LIST_CACHE = bhav_syms
            _NSE_EQUITY_LIST_CACHE_TIME = datetime.now()
            logger.info(f"Fetched {len(bhav_syms)} symbols via recent bhav copies")
            return bhav_syms
        logger.warning("Fallback equity list failed; returning NIFTY_50 universe")
        return NIFTY_50_UNIVERSE
    
    try:
        logger.info("Fetching full NSE equity list from nselib...")
        # Get all equity list from NSE
        equity_df = capital_market.equity_list()
        
        # Extract symbols column robustly and add .NS suffix for yfinance compatibility
        sym_col = None
        for candidate in ["SYMBOL", "Symbol", "symbol"]:
            if candidate in equity_df.columns:
                sym_col = candidate
                break
        if sym_col is None:
            logger.warning("nselib equity_list returned unexpected columns; falling back to NIFTY_50 universe")
            return NIFTY_50_UNIVERSE
        symbols = equity_df[sym_col].astype(str).unique().tolist()
        symbols_with_ns = [f"{sym}.NS" for sym in symbols]
        
        # Cache the result
        _NSE_EQUITY_LIST_CACHE = symbols_with_ns
        _NSE_EQUITY_LIST_CACHE_TIME = datetime.now()
        
        logger.info(f"Successfully fetched {len(symbols_with_ns)} NSE equities")
        return symbols_with_ns
        
    except Exception as e:
        logger.error(f"Failed to fetch NSE equity list via nselib: {e}")
        logger.info("Attempting NSE archives fallback for full equity list")
        fallback_syms = _fetch_equity_list_via_archives()
        if fallback_syms:
            _NSE_EQUITY_LIST_CACHE = fallback_syms
            _NSE_EQUITY_LIST_CACHE_TIME = datetime.now()
            logger.info(f"Fetched {len(fallback_syms)} symbols via NSE archives")
            return fallback_syms
        # Try recent bhav copies
        bhav_syms = _fetch_equity_list_via_recent_bhav(days=14)
        if bhav_syms:
            _NSE_EQUITY_LIST_CACHE = bhav_syms
            _NSE_EQUITY_LIST_CACHE_TIME = datetime.now()
            logger.info(f"Fetched {len(bhav_syms)} symbols via recent bhav copies")
            return bhav_syms
        logger.info("Fallback failed; returning NIFTY_50 universe")
        return NIFTY_50_UNIVERSE

def _fetch_equity_list_via_archives() -> List[str]:
    """
    Fetch full equity list from NSE archives CSV (EQUITY_L.csv).
    Returns list of symbols with .NS suffix, or empty list on failure.
    """
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            logger.warning(f"EQUITY_L.csv fetch failed with status {resp.status_code}")
            return []
        df = pd.read_csv(BytesIO(resp.content))
        # Robustly find symbol column
        sym_col = None
        for candidate in ["SYMBOL", "Symbol", "Security Symbol", "SECURITY SYMBOL", "SecurityCode"]:
            if candidate in df.columns:
                sym_col = candidate
                break
        if sym_col is None:
            # Try first column if it looks like strings
            sym_col = df.columns[0]
        symbols = (
            df[sym_col].astype(str).str.strip()
            .str.upper()
            .dropna()
            .unique()
            .tolist()
        )
        symbols_with_ns = [f"{s}.NS" for s in symbols if s and s != "nan"]
        # Deduplicate and sort
        symbols_with_ns = sorted(set(symbols_with_ns))
        return symbols_with_ns
    except Exception as e:
        logger.warning(f"EQUITY_L.csv fallback failed: {e}")
        return []

def _fetch_equity_list_via_recent_bhav(days: int = 14) -> List[str]:
    """
    Assemble equity list by aggregating symbols from recent bhav copy files.
    Fetches sec_bhavdata_full_YYYYMMDD.csv from NSE archives for the past N days.
    Returns list of symbols with .NS suffix, or empty list on failure.
    """
    base = datetime.now()
    collected: List[str] = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for i in range(days):
        day = base - timedelta(days=i)
        use_date = day.strftime("%d%m%Y")
        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{use_date}.csv"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            df = pd.read_csv(BytesIO(resp.content))
            # Normalize columns
            df.columns = [c.strip().upper().replace(" ", "") for c in df.columns]
            if "SYMBOL" in df.columns:
                syms = df["SYMBOL"].astype(str).str.strip().str.upper().tolist()
                collected.extend(syms)
        except Exception:
            continue
    syms = sorted(set(s for s in collected if s and s != "nan"))
    return [f"{s}.NS" for s in syms]


def get_nse_fno_equities() -> List[str]:
    """
    Get list of NSE F&O (Futures & Options) stocks (typically ~200 stocks).
    
    These are the most liquid stocks suitable for active trading.
    
    Returns:
        List of F&O symbols with .NS suffix. Falls back to NIFTY_50 universe if unavailable.
    """
    if capital_market is None:
        logger.warning("nselib capital_market not available; returning NIFTY_50 universe as fallback for F&O list")
        return NIFTY_50_UNIVERSE
    
    try:
        logger.info("Fetching NSE F&O equity list...")
        fno_df = capital_market.fno_equity_list()
        sym_col = None
        for candidate in ["SYMBOL", "Symbol", "symbol"]:
            if candidate in fno_df.columns:
                sym_col = candidate
                break
        if sym_col is None:
            logger.warning("nselib fno_equity_list returned unexpected columns; falling back to NIFTY_50 universe")
            return NIFTY_50_UNIVERSE
        symbols = fno_df[sym_col].astype(str).unique().tolist()
        symbols_with_ns = [f"{sym}.NS" for sym in symbols]
        logger.info(f"Successfully fetched {len(symbols_with_ns)} F&O equities")
        return symbols_with_ns
    except Exception as e:
        logger.error(f"Failed to fetch F&O equity list via nselib: {e}")
        logger.info("Falling back to NIFTY_50 universe")
        return NIFTY_50_UNIVERSE

def _validate_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate price data for quality issues.
    
    Args:
        df: DataFrame with price columns
        
    Returns:
        DataFrame with validated data
    """
    original_len = len(df)
    
    # Check for negative prices
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if col in df.columns:
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                logger.warning(f"Found {negative_count} negative {col} values, removing")
                df = df[df[col] >= 0]
    
    # Check for high-low consistency (high >= low)
    if "high" in df.columns and "low" in df.columns:
        invalid = df[df["high"] < df["low"]]
        if len(invalid) > 0:
            logger.warning(f"Found {len(invalid)} rows where high < low, removing")
            df = df[df["high"] >= df["low"]]
    
    # Check for extreme price changes (potential data errors)
    if "close" in df.columns and len(df) > 1:
        df_sorted = df.sort_values("date")
        pct_change = df_sorted["close"].pct_change().abs()
        extreme_changes = pct_change > DataValidationConfig.MAX_PRICE_CHANGE_PCT
        if extreme_changes.sum() > 0:
            logger.warning(f"Found {extreme_changes.sum()} extreme price changes (>{(DataValidationConfig.MAX_PRICE_CHANGE_PCT*100):.0f}%), removing")
            extreme_indices = df_sorted[extreme_changes].index
            df = df[~df.index.isin(extreme_indices)]
    
    removed = original_len - len(df)
    if removed > 0:
        logger.info(f"Data validation removed {removed} rows ({removed/original_len*100:.2f}%)")
    
    return df


def _to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert yfinance multiindex DataFrame to long format.
    
    Args:
        df: DataFrame with MultiIndex columns like ('Close','RELIANCE.NS')
        
    Returns:
        Long format DataFrame with columns [date, symbol, open, high, low, close, volume]
    """
    # yfinance multiindex -> long tidy
    # Expected columns like ('Close','RELIANCE.NS'), etc.
    df = df.copy()
    if not isinstance(df.columns, pd.MultiIndex):
        col_tuples = []
        for c in df.columns:
            if isinstance(c, tuple):
                col_tuples.append(c)
            else:
                col_tuples.append((c,))
        df.columns = pd.MultiIndex.from_tuples(col_tuples)
    else:
        df.columns = df.columns
    # Select only needed fields in canonical order
    keep_lv0 = ["Open","High","Low","Close","Volume"]
    df = df[keep_lv0]
    # Stack ticker level to rows
    df = df.stack(level=1, future_stack=True).reset_index()
    df.columns = ["date","symbol","open","high","low","close","volume"]
    # Sort and clean
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values(["symbol","date"]).dropna(subset=["open","high","low","close"])
    
    # Remove any future dates by comparing against the current date
    df = df[df["date"] <= pd.Timestamp.now().normalize()]
    
    # Ensure numeric
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open","high","low","close"])
    
    # Validate data quality
    df = _validate_price_data(df)
    
    return df

def fetch_history_yf(
    symbols: List[str],
    start: str = "2021-01-01",
    end: Optional[str] = None,
    period: Optional[str] = None,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Download daily OHLCV for multiple tickers from yfinance and cache per symbol to Parquet.
    
    Args:
        symbols: List of ticker symbols (e.g., ["RELIANCE.NS", "TCS.NS"])
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD), defaults to today
        period: YFinance period (e.g. "1d", "5d", "1mo", "1y", "max"). If set, start/end are ignored.
        force_refresh: If True, ignore cache and re-download
    """
    if not symbols:
        raise ValueError("No symbols provided")
    
    msg = f"Fetching data for {len(symbols)} symbols"
    if period:
        msg += f" with period={period}"
    else:
        msg += f" from {start} to {end or 'today'}"
    logger.info(msg)
    
    cache_paths = {s: DATA_RAW / f"{s.replace('.','_')}.parquet" for s in symbols}
    cached = []
    missing = []

    if not force_refresh:
        for s, path in cache_paths.items():
            if path.exists():
                try:
                    df = pd.read_parquet(path)
                    cached.append(df)
                    continue
                except Exception:
                    pass
            missing.append(s)
    else:
        missing = symbols

    if missing:
        # Download data
        df = yf.download(
            tickers=missing,
            start=None if period else start,
            end=None if period else end,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
        
        # If yfinance returned nothing, avoid downstream attribute errors
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            long_df = pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
        else:
            # Normalize columns to have (field, ticker) as MultiIndex.
            # yfinance can return either (ticker, field) or (field, ticker) depending on options.
            if not isinstance(df.columns, pd.MultiIndex):
                # Single ticker -> create MultiIndex with (field, ticker) and then ensure (field,ticker)
                df = pd.concat({missing[0]: df}, axis=1).swaplevel(axis=1)
            else:
                # If level 0 contains tickers (requested symbols), swap levels so fields are level 0
                try:
                    lvl0 = list(df.columns.get_level_values(0))
                except Exception:
                    lvl0 = []
                tickers_set = set(missing)
                if any(v in tickers_set for v in lvl0):
                    df = df.swaplevel(0, 1, axis=1)

            # Ensure we have a MultiIndex and a deterministic column order
            if not isinstance(df.columns, pd.MultiIndex):
                col_tuples = []
                for c in df.columns:
                    if isinstance(c, tuple):
                        col_tuples.append(c)
                    else:
                        col_tuples.append((c,))
                df.columns = pd.MultiIndex.from_tuples(col_tuples)
            df = df.sort_index(axis=1)

            # Convert to long format and filter out future dates
            long_df = _to_long(df)
        # Write per-symbol parquet
        for sym in missing:
            out = long_df[long_df["symbol"] == sym]
            if not out.empty:
                out.to_parquet(cache_paths[sym], index=False)
                cached.append(out)

    if not cached:
        return pd.DataFrame(columns=["date","symbol","open","high","low","close","volume"])

    if not cached:
        logger.warning("No data cached or fetched")
        return pd.DataFrame(columns=["date","symbol","open","high","low","close","volume"])
    
    full = pd.concat(cached, ignore_index=True).sort_values(["symbol","date"])
    # De-duplicate and enforce unique (symbol,date)
    full = full.drop_duplicates(subset=["symbol","date"], keep="last")
    
    # Additional validation: check for missing dates per symbol
    if len(full) > 0:
        symbol_counts = full.groupby("symbol").size()
        low_count_symbols = symbol_counts[symbol_counts < DataValidationConfig.MIN_DATA_POINTS_PER_SYMBOL]
        if len(low_count_symbols) > 0:
            logger.warning(f"Found {len(low_count_symbols)} symbols with < {DataValidationConfig.MIN_DATA_POINTS_PER_SYMBOL} data points")
    
    logger.info(f"Returning {len(full)} rows for {full['symbol'].nunique()} symbols")
    return full


def fetch_history_nsepy(
    symbols: List[str],
    start: str = "2021-01-01",
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch daily OHLCV from NSE official site via nsepy for Indian equities.

    Args:
        symbols: e.g., ["RELIANCE.NS"]. Suffix ".NS" will be stripped for NSEpy.
        start: YYYY-MM-DD
        end: YYYY-MM-DD (defaults to today)

    Returns:
        DataFrame [date, symbol, open, high, low, close, volume]

    Notes:
        - nsepy can break when NSE changes site; use try/except per symbol.
        - Respects NSE holidays; returns only available trading days.
    """
    if nse_get_history is None:
        raise RuntimeError("nsepy is not installed. Please install with `pip install nsepy`." )

    if not symbols:
        raise ValueError("No symbols provided")

    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end, "%Y-%m-%d").date() if end else datetime.now().date()

    frames = []
    for sym in symbols:
        nse_sym = sym.replace(".NS", "")
        try:
            df = nse_get_history(symbol=nse_sym, start=start_dt, end=end_dt)
            if df is None or df.empty:
                logger.warning(f"No NSE data for {sym}")
                continue
            # Normalize columns to our schema
            out = pd.DataFrame({
                "date": pd.to_datetime(df.index),
                "symbol": sym,
                "open": pd.to_numeric(df["Open"], errors="coerce"),
                "high": pd.to_numeric(df["High"], errors="coerce"),
                "low": pd.to_numeric(df["Low"], errors="coerce"),
                "close": pd.to_numeric(df["Close"], errors="coerce"),
                "volume": pd.to_numeric(df.get("Volume", pd.Series(index=df.index, dtype=float)), errors="coerce"),
            })
            out = out.dropna(subset=["open","high","low","close"]).sort_values(["symbol","date"])
            # Validate data
            out = _validate_price_data(out)
            frames.append(out)
        except Exception as e:
            logger.warning(f"NSEpy fetch failed for {sym}: {e}")
            continue

    if not frames:
        return pd.DataFrame(columns=["date","symbol","open","high","low","close","volume"])

    full = pd.concat(frames, ignore_index=True)
    # De-duplicate
    full = full.drop_duplicates(subset=["symbol","date"], keep="last")
    logger.info(f"Returning {len(full)} rows via NSEpy for {full['symbol'].nunique()} symbols")
    return full


def fetch_history_nselib(
    symbols: List[str],
    start: str = "2021-01-01",
    end: Optional[str] = None,
    include_delivery: bool = False,
) -> pd.DataFrame:
    """
    Fetch daily OHLCV from NSE using nselib (official NSE data source).
    
    Args:
        symbols: List of symbols with .NS suffix (e.g., ["RELIANCE.NS", "TCS.NS"])
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD), defaults to today
        include_delivery: If True, includes delivery percentage data
        
    Returns:
        Long format DataFrame with columns [date, symbol, open, high, low, close, volume]
        If include_delivery=True, adds 'deliverable_qty' and 'delivery_pct' columns
        
    Notes:
        - More reliable than yfinance for NSE stocks
        - Directly from NSE official API
        - Includes delivery data (unique to NSE)
        - Uses period format for better performance
    """
    if capital_market is None:
        raise RuntimeError("nselib is not installed. Please install with `pip install nselib>=2.4.0`")
    
    if not symbols:
        raise ValueError("No symbols provided")
    
    # Convert date format from YYYY-MM-DD to DD-MM-YYYY for nselib
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.now()
    
    from_date = start_dt.strftime("%d-%m-%Y")
    to_date = end_dt.strftime("%d-%m-%Y")
    
    frames = []
    failed_symbols = []
    
    logger.info(f"Fetching data from nselib for {len(symbols)} symbols from {from_date} to {to_date}")
    
    for sym in symbols:
        # Strip .NS suffix for nselib
        nse_sym = sym.replace(".NS", "")
        
        try:
            # Use price_volume_and_deliverable_position_data if we want delivery data
            if include_delivery:
                df = capital_market.price_volume_and_deliverable_position_data(
                    symbol=nse_sym,
                    from_date=from_date,
                    to_date=to_date
                )
            else:
                df = capital_market.price_volume_data(
                    symbol=nse_sym,
                    from_date=from_date,
                    to_date=to_date
                )
            
            if df is None or df.empty:
                logger.warning(f"No nselib data for {sym}")
                failed_symbols.append(sym)
                continue
            
            # Normalize column names to our schema
            df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y', errors='coerce')
            
            out = pd.DataFrame({
                "date": df['Date'],
                "symbol": sym,  # Keep .NS suffix for consistency
                "open": pd.to_numeric(df.get('OpenPrice', df.get('Open')), errors="coerce"),
                "high": pd.to_numeric(df.get('HighPrice', df.get('High')), errors="coerce"),
                "low": pd.to_numeric(df.get('LowPrice', df.get('Low')), errors="coerce"),
                "close": pd.to_numeric(df.get('ClosePrice', df.get('Close')), errors="coerce"),
                "volume": pd.to_numeric(df.get('TotalTradedQuantity', df.get('Volume')), errors="coerce"),
            })
            
            # Add delivery data if requested
            if include_delivery and 'DeliverableQty' in df.columns:
                out['deliverable_qty'] = pd.to_numeric(df['DeliverableQty'], errors="coerce")
                out['delivery_pct'] = pd.to_numeric(df['%DlyQttoTradedQty'], errors="coerce")
            
            out = out.dropna(subset=["open", "high", "low", "close"]).sort_values("date")
            
            # Validate data
            out = _validate_price_data(out)
            
            if not out.empty:
                frames.append(out)
                
        except Exception as e:
            logger.warning(f"nselib fetch failed for {sym}: {e}")
            failed_symbols.append(sym)
            continue
    
    if failed_symbols:
        logger.info(f"Failed to fetch {len(failed_symbols)} symbols via nselib: {failed_symbols[:10]}")
    
    if not frames:
        return pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
    
    full = pd.concat(frames, ignore_index=True)
    full = full.drop_duplicates(subset=["symbol", "date"], keep="last")
    logger.info(f"Successfully fetched {len(full)} rows via nselib for {full['symbol'].nunique()} symbols")
    
    return full


def fetch_history_hybrid(
    symbols: List[str],
    start: str = "2021-01-01",
    end: Optional[str] = None,
    force_refresh: bool = False,
    use_nselib: bool = True,
) -> pd.DataFrame:
    """
    Hybrid data fetching: tries nselib first, falls back to yfinance for failed symbols.
    
    This is the recommended method for NSE stocks as it combines:
    - nselib's reliability and direct NSE access
    - yfinance's fallback for any missing data
    
    Args:
        symbols: List of ticker symbols (e.g., ["RELIANCE.NS", "TCS.NS"])
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD), defaults to today
        force_refresh: If True, ignore cache and re-download
        use_nselib: If True, try nselib first (recommended for NSE stocks)
        
    Returns:
        Long format DataFrame with columns [date, symbol, open, high, low, close, volume]
    """
    if not symbols:
        raise ValueError("No symbols provided")
    
    logger.info(f"Hybrid fetch for {len(symbols)} symbols (nselib_enabled={use_nselib and capital_market is not None})")
    
    all_data = []
    remaining_symbols = symbols.copy()
    
    # Try nselib first if available and enabled
    if use_nselib and capital_market is not None:
        try:
            nselib_data = fetch_history_nselib(symbols, start, end, include_delivery=False)
            if not nselib_data.empty:
                all_data.append(nselib_data)
                # Remove successfully fetched symbols from remaining list
                fetched_symbols = nselib_data['symbol'].unique()
                remaining_symbols = [s for s in remaining_symbols if s not in fetched_symbols]
                logger.info(f"nselib fetched {len(fetched_symbols)} symbols, {len(remaining_symbols)} remaining")
        except Exception as e:
            logger.warning(f"nselib fetch failed, will use yfinance for all symbols: {e}")
    
    # Fetch remaining symbols with yfinance
    if remaining_symbols:
        logger.info(f"Fetching {len(remaining_symbols)} symbols via yfinance...")
        yf_data = fetch_history_yf(
            symbols=remaining_symbols,
            start=start,
            end=end,
            force_refresh=force_refresh
        )
        if not yf_data.empty:
            all_data.append(yf_data)
    
    # Combine all data
    if not all_data:
        return pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
    
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.drop_duplicates(subset=["symbol", "date"], keep="last")
    combined = combined.sort_values(["symbol", "date"])
    
    logger.info(f"Hybrid fetch complete: {len(combined)} rows for {combined['symbol'].nunique()} symbols")
    return combined
