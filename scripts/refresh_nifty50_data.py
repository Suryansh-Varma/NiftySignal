"""
Quick script to refresh NIFTY 50 data and update recommendations.
Run: python refresh_nifty50_data.py
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Suppress yfinance debug logs
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# NIFTY 50 stocks
NIFTY_50 = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "ITC.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "KOTAKBANK.NS",
    "LT.NS",
    "AXISBANK.NS",
    "ASIANPAINT.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
    "BAJFINANCE.NS",
    "TATAMOTORS.NS",
    "WIPRO.NS",
    "ULTRACEMCO.NS",
    "TITAN.NS",
    "NESTLEIND.NS",
    "HCLTECH.NS",
    "POWERGRID.NS",
    "TECHM.NS",
    "NTPC.NS",
    "M&M.NS",
    "INDUSINDBK.NS",
    "ADANIENT.NS",
    "BAJAJFINSV.NS",
    "JSWSTEEL.NS",
    "TATASTEEL.NS",
    "GRASIM.NS",
    "ONGC.NS",
    "HINDALCO.NS",
    "COALINDIA.NS",
    "BPCL.NS",
    "DIVISLAB.NS",
    "CIPLA.NS",
    "DRREDDY.NS",
    "EICHERMOT.NS",
    "HEROMOTOCO.NS",
    "BRITANNIA.NS",
    "APOLLOHOSP.NS",
    "TATACONSUM.NS",
    "ADANIPORTS.NS",
    "SBILIFE.NS",
    "HDFCLIFE.NS",
    "BAJAJ-AUTO.NS",
    "SHRIRAMFIN.NS",
    "BEL.NS",
]


def main():
    logger.info("=" * 60)
    logger.info("Refreshing NIFTY 50 data")
    logger.info("=" * 60)

    # Fetch fresh data
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")

    logger.info(f"Fetching data from {start} to {end}...")
    raw_data = yf.download(NIFTY_50, start=start, end=end, progress=True, threads=True)

    if not isinstance(raw_data, pd.DataFrame) or raw_data.empty:
        logger.error("No data fetched!")
        return

    data: pd.DataFrame = raw_data

    latest_date = pd.to_datetime(str(data.index.max()), errors="coerce")
    if pd.isna(latest_date):
        logger.error("Could not determine latest data date")
        return
    logger.info(f"Latest data date: {latest_date.strftime('%Y-%m-%d')}")

    # Convert to long format
    rows = []
    for symbol in NIFTY_50:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                available_symbols = data.columns.get_level_values(1)
                if symbol not in available_symbols:
                    continue
                sym_data = data.xs(symbol, axis=1, level=1)
            else:
                sym_data = data

            if not isinstance(sym_data, pd.DataFrame):
                continue

            for date, row in sym_data.iterrows():
                if pd.notna(row.get("Close", row.get("close"))):
                    close_val = row.get("Close", row.get("close"))
                    row_date = pd.to_datetime(str(date), errors="coerce")
                    if pd.isna(row_date):
                        continue
                    rows.append(
                        {
                            "symbol": symbol,
                            "date": row_date.strftime("%Y-%m-%d"),
                            "open": row.get("Open", row.get("open")),
                            "high": row.get("High", row.get("high")),
                            "low": row.get("Low", row.get("low")),
                            "close": close_val,
                            "volume": row.get("Volume", row.get("volume")),
                        }
                    )
        except Exception as e:
            logger.warning(f"Error processing {symbol}: {e}")

    df = pd.DataFrame(rows)
    logger.info(f"Processed {len(df)} records for {df['symbol'].nunique()} symbols")

    # Save to universe_data.csv
    output_path = Path(__file__).parent / "data" / "processed" / "universe_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved to {output_path}")

    # Check date distribution
    latest_per_symbol = df.groupby("symbol")["date"].max()
    logger.info(f"\nDate distribution:")
    for date, count in latest_per_symbol.value_counts().head(5).items():
        logger.info(f"  {date}: {count} stocks")

    # Update recommendations CSV with latest prices
    logger.info("\nUpdating recommendations...")
    rec_path = Path(__file__).parent / "results" / "latest_recommendations.csv"

    if rec_path.exists():
        recs = pd.read_csv(rec_path)

        # Update with latest prices
        latest_prices = (
            df.groupby("symbol")
            .apply(lambda x: x.loc[x["date"].idxmax()])
            .reset_index(drop=True)
        )

        for idx, row in recs.iterrows():
            symbol = row["symbol"]
            if symbol in latest_prices["symbol"].values:
                latest = latest_prices[latest_prices["symbol"] == symbol].iloc[0]
                recs.at[idx, "last_price"] = latest["close"]
                recs.at[idx, "last_date"] = latest["date"]

        recs.to_csv(rec_path, index=False)
        logger.info(f"Updated {rec_path}")

        # Verify
        logger.info("\nUpdated recommendations sample:")
        print(
            recs[["symbol", "last_price", "last_date", "recommendation"]]
            .head(10)
            .to_string()
        )

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
