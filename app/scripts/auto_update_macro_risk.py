"""
Auto Macro Risk Factor Updater
==============================
Fetches live market data from yfinance and automatically computes and writes
the macro_risk_factor.json file. Designed to be called from the scheduler
(daily after market close) or run standalone.

Data sources:
  - India VIX  : ^INDIAVIX  (market fear gauge)
  - Gold (USD)  : GC=F       (safe-haven demand)
  - Crude Oil   : CL=F       (input cost / inflation pressure)
  - USD/INR     : INR=X      (currency stability)
  - NIFTY 50    : ^NSEI      (market trend)

Usage:
    python -m app.scripts.auto_update_macro_risk
    python -m app.scripts.auto_update_macro_risk --dry-run
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np


logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).parent.parent.parent
MACRO_RISK_FILE = BASE_DIR / "data" / "macro_risk_factor.json"


# --------------------------------------------------------------------------- #
# Live data fetching
# --------------------------------------------------------------------------- #

def _fetch_ticker_close(symbol: str, period: str = "5d") -> Optional[float]:
    """
    Fetch the most-recent close price for a yfinance ticker symbol.
    Returns None on any error so callers can fall back gracefully.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            logger.warning(f"No data returned for {symbol}")
            return None
        return float(hist["Close"].dropna().iloc[-1])
    except Exception as e:
        logger.warning(f"Failed to fetch {symbol}: {e}")
        return None


def _fetch_30d_returns(symbol: str) -> Optional[float]:
    """
    Compute 30-day return for a ticker.
    Returns a float (e.g. 0.05 = +5%) or None on failure.
    """
    try:
        import yfinance as yf
        hist = yf.Ticker(symbol).history(period="35d")["Close"].dropna()
        if len(hist) < 5:
            return None
        return float((hist.iloc[-1] / hist.iloc[0]) - 1)
    except Exception as e:
        logger.warning(f"Failed 30d return for {symbol}: {e}")
        return None


# --------------------------------------------------------------------------- #
# Risk factor computation
# --------------------------------------------------------------------------- #

def _vix_risk(vix: Optional[float]) -> Tuple[float, str]:
    """
    Normalise India VIX to a 0-1 risk score.
      <12  → very low
      12-16 → low
      16-20 → moderate
      20-25 → high
      >25  → very high
    """
    if vix is None:
        return 0.5, "unavailable"
    if vix < 12:
        return 0.1, f"{vix:.1f} (Very Low)"
    if vix < 16:
        return 0.25, f"{vix:.1f} (Low)"
    if vix < 20:
        return 0.45, f"{vix:.1f} (Moderate)"
    if vix < 25:
        return 0.65, f"{vix:.1f} (High)"
    return 0.85, f"{vix:.1f} (Very High)"


def _gold_risk(gold_usd: Optional[float]) -> Tuple[float, str]:
    """
    Proxy for safe-haven demand. High gold = fear / risk-off.
    2026 reference band: $2800-$3200 is 'new normal'; above $4000 signals stress.
    """
    if gold_usd is None:
        return 0.5, "unavailable"
    if gold_usd < 2500:
        return 0.15, f"${gold_usd:.0f} (Low / historical)"
    if gold_usd < 3200:
        return 0.30, f"${gold_usd:.0f} (Normal/elevated)"
    if gold_usd < 4000:
        return 0.50, f"${gold_usd:.0f} (High demand)"
    if gold_usd < 5000:
        return 0.65, f"${gold_usd:.0f} (Very high demand)"
    return 0.85, f"${gold_usd:.0f} (Extreme)"


def _oil_risk(oil_usd: Optional[float]) -> Tuple[float, str]:
    """
    Extreme-high OR extreme-low oil prices both signal risk for India
    (import cost / demand collapse).
    Center band: $60-$90 is comfortable for India.
    """
    if oil_usd is None:
        return 0.5, "unavailable"
    if oil_usd < 50:
        return 0.60, f"${oil_usd:.0f} (Demand collapse risk)"
    if oil_usd < 70:
        return 0.25, f"${oil_usd:.0f} (Low)"
    if oil_usd < 90:
        return 0.35, f"${oil_usd:.0f} (Comfortable)"
    if oil_usd < 110:
        return 0.60, f"${oil_usd:.0f} (Elevated)"
    return 0.80, f"${oil_usd:.0f} (High)"


def _usdinr_risk(usdinr: Optional[float]) -> Tuple[float, str]:
    """
    USD/INR rate pressure. Rapid depreciation of INR signals capital flight / risk.
    2026 reference band: 85-88 is current normal; above 90 is stress.
    """
    if usdinr is None:
        return 0.5, "unavailable"
    if usdinr < 83:
        return 0.10, f"\u20b9{usdinr:.2f} (Strong INR)"
    if usdinr < 86:
        return 0.25, f"\u20b9{usdinr:.2f} (Normal)"
    if usdinr < 89:
        return 0.45, f"\u20b9{usdinr:.2f} (Mild pressure)"
    if usdinr < 92:
        return 0.65, f"\u20b9{usdinr:.2f} (Stress)"
    return 0.85, f"\u20b9{usdinr:.2f} (Extreme depreciation)"


def _nifty_trend_risk(return_30d: Optional[float]) -> Tuple[float, str]:
    """
    30-day NIFTY return as a trend signal. Falling market = higher risk.
    """
    if return_30d is None:
        return 0.5, "unavailable"
    pct = return_30d * 100
    if pct > 5:
        return 0.10, f"+{pct:.1f}% (Strong uptrend)"
    if pct > 1:
        return 0.25, f"+{pct:.1f}% (Uptrend)"
    if pct > -2:
        return 0.45, f"{pct:.1f}% (Sideways)"
    if pct > -5:
        return 0.65, f"{pct:.1f}% (Downtrend)"
    return 0.85, f"{pct:.1f}% (Sharp selloff)"


# --------------------------------------------------------------------------- #
# Risk level labels
# --------------------------------------------------------------------------- #

def _risk_label(risk: float) -> str:
    if risk < 0.20:
        return "VERY_LOW"
    if risk < 0.35:
        return "LOW"
    if risk < 0.50:
        return "MODERATE"
    if risk < 0.70:
        return "HIGH"
    return "VERY_HIGH"


def _position_sizing(risk: float) -> Dict:
    """
    Translate composite risk into position-sizing guidance.
    """
    if risk < 0.20:
        return {"position_size_pct": 3.0, "max_positions": 20, "stance": "Aggressive"}
    if risk < 0.35:
        return {"position_size_pct": 2.5, "max_positions": 18, "stance": "Growth"}
    if risk < 0.50:
        return {"position_size_pct": 2.0, "max_positions": 15, "stance": "Balanced"}
    if risk < 0.70:
        return {"position_size_pct": 1.0, "max_positions": 10, "stance": "Defensive"}
    return {"position_size_pct": 0.5, "max_positions": 5, "stance": "Capital Preservation"}


# --------------------------------------------------------------------------- #
# Main update function
# --------------------------------------------------------------------------- #

def compute_and_update(dry_run: bool = False) -> Dict:
    """
    Fetch live data, compute the macro risk factor, and write the JSON file.

    Args:
        dry_run: If True, compute but do not write to disk.

    Returns:
        The computed risk data dict.
    """
    logger.info("Auto Macro Risk Updater: fetching live market data...")

    # ---- Fetch live prices ------------------------------------------------ #
    vix_raw        = _fetch_ticker_close("^INDIAVIX")
    gold_raw       = _fetch_ticker_close("GC=F")
    oil_raw        = _fetch_ticker_close("CL=F")
    usdinr_raw     = _fetch_ticker_close("INR=X")
    nifty_ret_30d  = _fetch_30d_returns("^NSEI")

    logger.info(
        f"  India VIX={vix_raw}  Gold=${gold_raw}  Oil=${oil_raw}  "
        f"USD/INR={usdinr_raw}  NIFTY 30d={nifty_ret_30d}"
    )

    # ---- Individual risk scores ------------------------------------------- #
    vix_risk,    vix_label    = _vix_risk(vix_raw)
    gold_risk,   gold_label   = _gold_risk(gold_raw)
    oil_risk,    oil_label    = _oil_risk(oil_raw)
    fx_risk,     fx_label     = _usdinr_risk(usdinr_raw)
    trend_risk,  trend_label  = _nifty_trend_risk(nifty_ret_30d)

    # ---- Composite weighted average --------------------------------------- #
    # Weights: VIX=35%, Gold=20%, Oil=15%, FX=15%, Market Trend=15%
    composite = (
        0.35 * vix_risk  +
        0.20 * gold_risk +
        0.15 * oil_risk  +
        0.15 * fx_risk   +
        0.15 * trend_risk
    )
    composite = round(min(max(composite, 0.0), 1.0), 4)

    # Slight upward adjustment in very high-risk environments
    adjusted = round(min(composite * 1.10, 1.0), 4) if composite > 0.65 else composite

    risk_level = _risk_label(adjusted)
    pos_sizing = _position_sizing(adjusted)

    # ---- Build output dict ------------------------------------------------ #
    data = {
        "update_date":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "update_source":        "auto",
        "macro_risk_factor":    composite,
        "adjusted_risk_factor": adjusted,
        "risk_level":           risk_level,
        "position_sizing":      pos_sizing,
        "risk_factors": {
            "vix_equivalent":      round(vix_risk, 4),
            "gold_demand":         round(gold_risk, 4),
            "oil_price":           round(oil_risk, 4),
            "currency":            round(fx_risk, 4),
            "market_trend":        round(trend_risk, 4),
        },
        "raw_market_data": {
            "india_vix":           vix_raw,
            "gold_usd":            gold_raw,
            "crude_oil_usd":       oil_raw,
            "usd_inr":             usdinr_raw,
            "nifty_30d_return":    round(nifty_ret_30d * 100, 2) if nifty_ret_30d else None,
        },
        "factor_descriptions": {
            "india_vix":     vix_label,
            "gold":          gold_label,
            "crude_oil":     oil_label,
            "usd_inr":       fx_label,
            "nifty_trend":   trend_label,
        }
    }

    if dry_run:
        logger.info(f"[DRY RUN] Computed risk factor: {adjusted:.4f} ({risk_level})")
        logger.info(f"[DRY RUN] Would write to: {MACRO_RISK_FILE}")
    else:
        MACRO_RISK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MACRO_RISK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(
            f"macro_risk_factor.json updated: {adjusted:.4f} ({risk_level}) "
            f"[VIX={vix_raw}, Gold={gold_raw}, Oil={oil_raw}, "
            f"USDINR={usdinr_raw}, NIFTY30d={nifty_ret_30d}]"
        )

    return data


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Auto-update macro risk factor from live market data")
    parser.add_argument("--dry-run", action="store_true", help="Compute but do not write to disk")
    args = parser.parse_args()

    result = compute_and_update(dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("MACRO RISK FACTOR — AUTO UPDATE RESULT")
    print("=" * 60)
    print(f"  Composite Risk      : {result['macro_risk_factor']:.4f}")
    print(f"  Adjusted Risk       : {result['adjusted_risk_factor']:.4f}")
    print(f"  Risk Level          : {result['risk_level']}")
    print(f"  Max Positions       : {result['position_sizing']['max_positions']}")
    print(f"  Stance              : {result['position_sizing']['stance']}")
    print("\n  Raw Market Data:")
    for k, v in result.get("raw_market_data", {}).items():
        print(f"    {k:25s}: {v}")
    print("\n  Factor Descriptions:")
    for k, v in result.get("factor_descriptions", {}).items():
        print(f"    {k:25s}: {v}")
    print("=" * 60)
