"""
Market Context Features
========================
Adds two types of macro features to every stock row:

1. Nifty 50 index features  (market regime, beta, alpha vs broad market)
2. Sectoral index features   (stock vs its own sector index: BankNifty, NiftyIT, etc.)

The sectoral index features are the most powerful — they let the model
distinguish between a banking stock falling WITH the sector (sector risk)
vs falling AGAINST the sector (company-specific risk).
"""

from pathlib import Path
from typing import Dict, Optional
import logging

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── Symbols ───────────────────────────────────────────────────────────────────
NIFTY_SYMBOL = "^NSEI"

# NSE sectoral index yfinance symbols
SECTORAL_INDEX_SYMBOLS: Dict[str, str] = {
    "nifty50": "^NSEI",
    "banknifty": "^NSEBANK",
    "niftyit": "^CNXIT",
    "niftypharma": "NIFTYPHARMA.NS",
    "niftyauto": "^CNXAUTO",
    "niftymetal": "^CNXMETAL",
    "niftyfmcg": "^CNXFMCG",
    "niftyenergy": "^CNXENERGY",
    "niftyinfra": "^CNXINFRA",
}

# The sector index each stock belongs to (for relative-to-sector features)
STOCK_SECTOR_INDEX: Dict[str, str] = {
    # Banking — use BankNifty
    "HDFCBANK.NS": "banknifty",
    "ICICIBANK.NS": "banknifty",
    "KOTAKBANK.NS": "banknifty",
    "AXISBANK.NS": "banknifty",
    "SBIN.NS": "banknifty",
    "INDUSINDBK.NS": "banknifty",
    # Finance — use BankNifty as closest proxy
    "HDFCLIFE.NS": "banknifty",
    "SBILIFE.NS": "banknifty",
    "BAJFINANCE.NS": "banknifty",
    "BAJAJFINSV.NS": "banknifty",
    "SHRIRAMFIN.NS": "banknifty",
    # Technology — NiftyIT
    "TCS.NS": "niftyit",
    "INFY.NS": "niftyit",
    "HCLTECH.NS": "niftyit",
    "WIPRO.NS": "niftyit",
    "TECHM.NS": "niftyit",
    "LTIM.NS": "niftyit",
    # FMCG
    "HINDUNILVR.NS": "niftyfmcg",
    "ITC.NS": "niftyfmcg",
    "NESTLEIND.NS": "niftyfmcg",
    "BRITANNIA.NS": "niftyfmcg",
    "TATACONSUM.NS": "niftyfmcg",
    # Auto
    "MARUTI.NS": "niftyauto",
    "BAJAJ-AUTO.NS": "niftyauto",
    "HEROMOTOCO.NS": "niftyauto",
    "TATAMOTORS.NS": "niftyauto",
    "EICHERMOT.NS": "niftyauto",
    "M&M.NS": "niftyauto",
    # Pharma
    "SUNPHARMA.NS": "niftypharma",
    "DRREDDY.NS": "niftypharma",
    "CIPLA.NS": "niftypharma",
    "DIVISLAB.NS": "niftypharma",
    "APOLLOHOSP.NS": "niftypharma",
    # Energy
    "RELIANCE.NS": "niftyenergy",
    "ONGC.NS": "niftyenergy",
    "BPCL.NS": "niftyenergy",
    "COALINDIA.NS": "niftyenergy",
    # Metals
    "TATASTEEL.NS": "niftymetal",
    "JSWSTEEL.NS": "niftymetal",
    "HINDALCO.NS": "niftymetal",
    # Infrastructure / Materials
    "LT.NS": "niftyinfra",
    "ADANIENT.NS": "niftyinfra",
    "ADANIPORTS.NS": "niftyinfra",
    "BEL.NS": "niftyinfra",
    "GRASIM.NS": "nifty50",
    "ULTRACEMCO.NS": "nifty50",
    # Utilities / Telecom — use broad market
    "NTPC.NS": "nifty50",
    "POWERGRID.NS": "nifty50",
    "BHARTIARTL.NS": "nifty50",
    # Discretionary
    "TITAN.NS": "nifty50",
    "ASIANPAINT.NS": "nifty50",
}

# Sector mapping for MLSignalGenerator sector routing
NIFTY_SECTOR_MAP: Dict[str, str] = {
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "KOTAKBANK.NS": "Banking",
    "AXISBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "INDUSINDBK.NS": "Banking",
    "HDFCLIFE.NS": "Finance",
    "SBILIFE.NS": "Finance",
    "BAJFINANCE.NS": "Finance",
    "BAJAJFINSV.NS": "Finance",
    "SHRIRAMFIN.NS": "Finance",
    "TCS.NS": "Technology",
    "INFY.NS": "Technology",
    "HCLTECH.NS": "Technology",
    "WIPRO.NS": "Technology",
    "TECHM.NS": "Technology",
    "LTIM.NS": "Technology",
    "HINDUNILVR.NS": "FMCG",
    "ITC.NS": "FMCG",
    "NESTLEIND.NS": "FMCG",
    "BRITANNIA.NS": "FMCG",
    "TATACONSUM.NS": "FMCG",
    "MARUTI.NS": "Auto",
    "BAJAJ-AUTO.NS": "Auto",
    "HEROMOTOCO.NS": "Auto",
    "TATAMOTORS.NS": "Auto",
    "EICHERMOT.NS": "Auto",
    "M&M.NS": "Auto",
    "SUNPHARMA.NS": "Pharma",
    "DRREDDY.NS": "Pharma",
    "CIPLA.NS": "Pharma",
    "DIVISLAB.NS": "Pharma",
    "APOLLOHOSP.NS": "Healthcare",
    "RELIANCE.NS": "Energy",
    "ONGC.NS": "Energy",
    "BPCL.NS": "Energy",
    "NTPC.NS": "Utilities",
    "POWERGRID.NS": "Utilities",
    "COALINDIA.NS": "Utilities",
    "TATASTEEL.NS": "Metals",
    "JSWSTEEL.NS": "Metals",
    "HINDALCO.NS": "Metals",
    "GRASIM.NS": "Materials",
    "ULTRACEMCO.NS": "Materials",
    "BHARTIARTL.NS": "Telecom",
    "LT.NS": "Infrastructure",
    "ADANIENT.NS": "Infrastructure",
    "ADANIPORTS.NS": "Infrastructure",
    "BEL.NS": "Infrastructure",
    "TITAN.NS": "Consumer Discretionary",
    "ASIANPAINT.NS": "Consumer Discretionary",
}

# Path to pre-fetched sectoral index CSV
_SECTOR_IDX_PATH = (
    Path(__file__).parent.parent.parent / "data" / "processed" / "sectoral_indices.csv"
)

# In-memory cache
_sectoral_index_cache: Optional[pd.DataFrame] = None


def _load_sectoral_index_data() -> pd.DataFrame:
    """Load sectoral index data from CSV (cached after first call)."""
    global _sectoral_index_cache
    if _sectoral_index_cache is not None:
        return _sectoral_index_cache
    if _SECTOR_IDX_PATH.exists():
        try:
            df = pd.read_csv(_SECTOR_IDX_PATH, parse_dates=["date"])
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            df = df.set_index("date").sort_index()
            _sectoral_index_cache = df
            logger.info(
                f"Loaded sectoral index data: {df.shape[1]} indices, {len(df)} rows"
            )
            return df
        except Exception as e:
            logger.warning(f"Failed to load sectoral_indices.csv: {e}")
    return pd.DataFrame()


def fetch_nifty_data(start_date: str, end_date: Optional[str] = None) -> pd.Series:
    """Fetch Nifty 50 close prices from yfinance."""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    try:
        raw = yf.download(
            NIFTY_SYMBOL,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            return pd.Series(dtype=float)
        close = (
            raw["Close"].iloc[:, 0]
            if isinstance(raw.columns, pd.MultiIndex)
            else raw["Close"]
        )
        close.index = pd.to_datetime(close.index).tz_localize(None)
        close.name = "nifty_close"
        return close
    except Exception as e:
        logger.error(f"Nifty fetch failed: {e}")
        return pd.Series(dtype=float)


def _build_index_features(
    index_close: pd.Series, prefix: str, lookback: int = 20
) -> pd.DataFrame:
    """Build a return/volatility/regime feature DataFrame from an index close series."""
    r = index_close.pct_change()
    sma = index_close.rolling(lookback).mean()
    regime = pd.Series(0, index=index_close.index)
    regime[index_close > sma * 1.01] = 1
    regime[index_close < sma * 0.99] = -1

    out = pd.DataFrame(
        {
            f"{prefix}_ret1d": r,
            f"{prefix}_ret5d": index_close.pct_change(5),
            f"{prefix}_ret20d": index_close.pct_change(20),
            f"{prefix}_vol": r.rolling(lookback).std(),
            f"{prefix}_regime": regime,
        },
        index=index_close.index,
    )
    return out


def add_market_context_features(
    df: pd.DataFrame,
    nifty_series: Optional[pd.Series] = None,
    lookback_days: int = 20,
) -> pd.DataFrame:
    """
    Add broad market + sectoral index features to the stock DataFrame.

    Features per stock:
        Nifty 50     : nifty_return_1d/5d/20d, nifty_volatility, market_regime,
                       stock_vs_nifty_1d/5d/20d, rolling_beta
        Sector index : sector_ret1d/5d/20d, sector_vol, sector_regime,
                       stock_vs_sector_1d/5d/20d, sector_beta
    """
    df = df.copy()
    min_date = pd.to_datetime(df["date"]).min()
    fetch_start = (min_date - timedelta(days=60)).strftime("%Y-%m-%d")

    def _rolling_beta(
        stock_ret: pd.Series, bench_ret: pd.Series, window: int = lookback_days
    ) -> pd.Series:
        cov = stock_ret.rolling(window).cov(bench_ret)
        var = bench_ret.rolling(window).var()
        return (cov / var.replace(0, np.nan)).fillna(1.0)

    # ── 1. Nifty 50 ───────────────────────────────────────────────────────────
    if nifty_series is None or (
        isinstance(nifty_series, pd.Series) and nifty_series.empty
    ):
        nifty_series = fetch_nifty_data(fetch_start)

    _zero_nifty_cols = [
        "nifty_return_1d",
        "nifty_return_5d",
        "nifty_return_20d",
        "nifty_volatility",
        "market_regime",
        "stock_vs_nifty_1d",
        "stock_vs_nifty_5d",
        "stock_vs_nifty_20d",
        "rolling_beta",
    ]
    if nifty_series.empty:
        for c in _zero_nifty_cols:
            df[c] = 0.0
    else:
        nifty_feat = _build_index_features(nifty_series, "nifty", lookback_days)
        nifty_feat = nifty_feat.rename(
            columns={
                "nifty_ret1d": "nifty_return_1d",
                "nifty_ret5d": "nifty_return_5d",
                "nifty_ret20d": "nifty_return_20d",
                "nifty_vol": "nifty_volatility",
                "nifty_regime": "market_regime",
            }
        )

    # ── 2. Sectoral indices (pre-fetched CSV) ─────────────────────────────────
    idx_data = _load_sectoral_index_data()

    # Sector-relative feature column names
    _zero_sector_cols = [
        "sector_ret1d",
        "sector_ret5d",
        "sector_ret20d",
        "sector_vol",
        "sector_regime",
        "stock_vs_sector_1d",
        "stock_vs_sector_5d",
        "stock_vs_sector_20d",
        "sector_beta",
    ]

    # ── 3. Per-symbol processing ───────────────────────────────────────────────
    symbols = df["symbol"].unique()
    dfs = []

    for sym in symbols:
        temp = df[df["symbol"] == sym].copy().sort_values("date").set_index("date")
        temp.index = pd.to_datetime(temp.index).tz_localize(None)

        # --- Nifty features ---
        if not nifty_series.empty:
            temp = temp.join(nifty_feat, how="left")
            r1 = temp.get("returns_1d", pd.Series(0, index=temp.index))
            r5 = temp.get("returns_5d", pd.Series(0, index=temp.index))
            r20 = temp.get("returns_20d", pd.Series(0, index=temp.index))
            temp["stock_vs_nifty_1d"] = r1 - temp["nifty_return_1d"]
            temp["stock_vs_nifty_5d"] = r5 - temp["nifty_return_5d"]
            temp["stock_vs_nifty_20d"] = r20 - temp["nifty_return_20d"]

            temp["rolling_beta"] = _rolling_beta(r1, temp["nifty_return_1d"])
        else:
            for c in _zero_nifty_cols:
                temp[c] = 0.0

        # --- Sector index features ---
        sec_idx_name = STOCK_SECTOR_INDEX.get(sym, "nifty50")
        col = f"idx_{sec_idx_name}_close"

        if not idx_data.empty and col in idx_data.columns:
            sec_close = idx_data[col].dropna()
            sec_feat = _build_index_features(sec_close, "sector", lookback_days)
            temp = temp.join(sec_feat, how="left")

            r1 = temp.get("returns_1d", pd.Series(0, index=temp.index))
            r5 = temp.get("returns_5d", pd.Series(0, index=temp.index))
            r20 = temp.get("returns_20d", pd.Series(0, index=temp.index))
            temp["stock_vs_sector_1d"] = r1 - temp["sector_ret1d"]
            temp["stock_vs_sector_5d"] = r5 - temp["sector_ret5d"]
            temp["stock_vs_sector_20d"] = r20 - temp["sector_ret20d"]
            temp["sector_beta"] = _rolling_beta(r1, temp["sector_ret1d"])
        else:
            for c in _zero_sector_cols:
                temp[c] = 0.0

        temp = temp.reset_index()
        dfs.append(temp)

    result = pd.concat(dfs, ignore_index=True)

    # Fill any remaining NaNs
    all_ctx = _zero_nifty_cols + _zero_sector_cols
    for c in all_ctx:
        if c in result.columns:
            result[c] = result[c].fillna(0.0)

    return result


def get_symbol_sector(symbol: str) -> str:
    """Return ML routing sector for a given symbol ('Other' if unknown)."""
    return NIFTY_SECTOR_MAP.get(symbol, "Other")


# Feature list used by prepare_features
MARKET_CONTEXT_FEATURES = [
    # Nifty 50 broad market
    "nifty_return_1d",
    "nifty_return_5d",
    "nifty_return_20d",
    "nifty_volatility",
    "market_regime",
    "stock_vs_nifty_1d",
    "stock_vs_nifty_5d",
    "stock_vs_nifty_20d",
    "rolling_beta",
    # Sector index features
    "sector_ret1d",
    "sector_ret5d",
    "sector_ret20d",
    "sector_vol",
    "sector_regime",
    "stock_vs_sector_1d",
    "stock_vs_sector_5d",
    "stock_vs_sector_20d",
    "sector_beta",
]
