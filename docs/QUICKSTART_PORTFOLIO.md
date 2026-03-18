# Quick Start - Portfolio System

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install from setup.py
pip install -e .
```

## Try the Demo

```bash
python demo_portfolio.py
```

This will:
1. Fetch all NSE stocks (~3000)
2. Create a sample portfolio
3. Show real-time P&L
4. Generate buy/sell recommendations

## Basic Usage

### 1. Import the Manager

```python
from app.portfolio import PortfolioManager

manager = PortfolioManager()
```

### 2. Add Your Holdings

```python
# Add stocks you own
manager.add_stock(
    user_id="your_user_id",
    symbol="RELIANCE.NS",
    shares=50,
    avg_price=2450.00
)

manager.add_stock(
    user_id="your_user_id",
    symbol="TCS.NS",
    shares=30,
    avg_price=3200.00
)
```

### 3. View Portfolio Summary

```python
summary = manager.get_portfolio_summary("your_user_id")

print(f"Total Invested: ₹{summary['total_invested']:,.2f}")
print(f"Current Value:  ₹{summary['current_value']:,.2f}")
print(f"Total P&L:      ₹{summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.2f}%)")

# View each holding
for holding in summary['holdings']:
    print(f"{holding['symbol']}: ₹{holding['pnl']:,.2f} ({holding['pnl_pct']:.2f}%)")
```

### 4. Get Recommendations

```python
recs = manager.generate_recommendations("your_user_id")

for rec in recs['recommendations']:
    print(f"{rec['symbol']}: {rec['action']}")
    print(f"  Reason: {rec['reason']}")
    print(f"  Confidence: {rec['confidence']}")
```

## Get All NSE Stocks

```python
from app.config import get_all_nse_stocks, get_fno_stocks

# All 3000+ NSE stocks
all_stocks = get_all_nse_stocks()
print(f"Total stocks: {len(all_stocks)}")

# F&O stocks only (~200 liquid stocks)
fno_stocks = get_fno_stocks()
print(f"F&O stocks: {len(fno_stocks)}")
```

## Fetch Stock Data

```python
from app.data.loaders import fetch_history_hybrid

# Hybrid: tries nselib first, falls back to yfinance
data = fetch_history_hybrid(
    symbols=["RELIANCE.NS", "TCS.NS", "INFY.NS"],
    start="2024-01-01",
    use_nselib=True
)

print(data.head())
```

## Configuration

Edit `app/config.py`:

```python
class PortfolioConfig:
    STOP_LOSS_PCT = 0.07        # 7% stop loss trigger
    TAKE_PROFIT_PCT = 0.15      # 15% take profit target
    MAX_STOCKS_PER_PORTFOLIO = 100
```

## API Integration (Coming Soon)

```python
# FastAPI endpoints
POST   /api/portfolio/create
GET    /api/portfolio/{user_id}
POST   /api/portfolio/{user_id}/add-stock
GET    /api/recommendations/{user_id}
```

## Troubleshooting

**Problem**: "nselib is not installed"  
**Solution**: `pip install nselib python-dateutil`

**Problem**: Slow data fetching  
**Solution**: First fetch takes time, subsequent fetches use cache

**Problem**: No current prices  
**Solution**: Market may be closed, system will use last available price

## Next Steps

1. Run `demo_portfolio.py` to see it in action
2. Create your portfolio with actual holdings
3. Check recommendations daily
4. Build frontend integration
5. Add API endpoints for web/mobile apps

For more details, see [PORTFOLIO_SYSTEM_README.md](PORTFOLIO_SYSTEM_README.md)
