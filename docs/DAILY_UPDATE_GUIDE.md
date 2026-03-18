# Daily Data Update & Intraday Guide

## 🔄 Daily Data Updates - NOT AUTOMATED YET

Your system currently requires **manual data refresh**. Here's how to automate it:

---

## Option 1: Linux Cron Job (Recommended for VPS)

### Setup Daily 6:00 PM IST Update
```bash
# Open crontab
crontab -e

# Add this line (runs at 6 PM IST daily after market closes)
0 18 * * * cd /path/to/NiftySIgnal && /path/to/python app/api/main.py >> logs/daily_update.log 2>&1

# Or call the API endpoint
0 18 * * * curl -X POST http://localhost:8000/api/refresh_universe >> logs/refresh.log 2>&1
```

### After data update, retrain model weekly:
```bash
# Every Sunday at 8 PM
0 20 * * 0 cd /path/to/NiftySIgnal && /path/to/python retrain_model_recent.py >> logs/retrain.log 2>&1
```

---

## Option 2: Windows Task Scheduler

### Create Batch Script
Create `daily_update.bat`:
```batch
@echo off
cd C:\Users\surya\OneDrive\Documents\github\NiftySIgnal
python app\api\main.py >> logs\daily_update.log 2>&1
python retrain_model_recent.py >> logs\retrain.log 2>&1
```

### Schedule in Windows:
1. Open **Task Scheduler**
2. Create Basic Task → Name: "NiftySignal Daily Update"
3. Trigger: Daily at 6:00 PM
4. Action: Start a program → `daily_update.bat`
5. Save

---

## Option 3: Python Background Scheduler (Best for Development)

### Create `app/scheduler.py`:
```python
"""
Background scheduler for daily data updates
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_daily_data():
    """Run daily data fetch"""
    logger.info("Starting daily data fetch...")
    try:
        script = Path(__file__).parent / "api" / "main.py"
        subprocess.run([sys.executable, str(script)], check=True)
        logger.info("Daily data fetch completed successfully")
    except Exception as e:
        logger.error(f"Daily data fetch failed: {e}")

def retrain_model_weekly():
    """Retrain model weekly"""
    logger.info("Starting weekly model retraining...")
    try:
        script = Path(__file__).parent.parent / "retrain_model_recent.py"
        subprocess.run([sys.executable, str(script)], check=True)
        logger.info("Weekly retraining completed successfully")
    except Exception as e:
        logger.error(f"Weekly retraining failed: {e}")

# Create scheduler
scheduler = BackgroundScheduler()

# Schedule daily data fetch at 6 PM IST (after market closes)
scheduler.add_job(fetch_daily_data, 'cron', hour=18, minute=0)

# Schedule weekly retraining on Sunday at 8 PM
scheduler.add_job(retrain_model_weekly, 'cron', day_of_week='sun', hour=20, minute=0)

# Start scheduler
def start_scheduler():
    scheduler.start()
    logger.info("Scheduler started. Jobs:")
    logger.info("  - Daily data fetch: Every day at 6:00 PM")
    logger.info("  - Weekly retraining: Sundays at 8:00 PM")

if __name__ == "__main__":
    start_scheduler()
    # Keep script running
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
```

### Install APScheduler:
```bash
pip install apscheduler
```

### Add to `requirements.txt`:
```
apscheduler>=3.10.0
```

### Run scheduler in background:
```bash
python app/scheduler.py &
```

---

## 📈 Intraday Data - SIMULATED (Not Real)

### Current State: **Mock Data Only**

Your WebSocket server ([ws-server/index.js](ws-server/index.js)) currently generates **FAKE intraday data** every 5 seconds:

```javascript
// This is MOCK data - not real market prices!
setInterval(() => {
  const symbols = ['AAPL', 'MSFT', 'TSLA']  // ❌ Not NIFTY stocks
  symbols.forEach((symbol) => {
    const value = 170 + Math.random() * 20  // ❌ Random fake prices
    const payload = {
      symbol,
      point: { t: timeStr, v: value },
      ts: new Date().getTime(),
    }
    io.to(`symbol:${symbol}`).emit('intraday', payload)
  })
}, 5000)
```

### ⚠️ To Get REAL Intraday Data:

You need to integrate with a real-time data provider. Here are options:

#### Option 1: Yahoo Finance (Free, 15-min delay)
```javascript
import yahooFinance from 'yahoo-finance2'

async function fetchIntradayData(symbol) {
  const data = await yahooFinance.chart(symbol, {
    period1: new Date(Date.now() - 24*60*60*1000),
    interval: '5m'  // 5-minute bars
  })
  return data
}
```

#### Option 2: Alpha Vantage (Free tier: 5 calls/min)
```javascript
const ALPHA_VANTAGE_KEY = 'YOUR_API_KEY'

async function fetchIntradayAlpha(symbol) {
  const url = `https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=${symbol}&interval=5min&apikey=${ALPHA_VANTAGE_KEY}`
  const response = await fetch(url)
  return response.json()
}
```

#### Option 3: NSE Official (Free but complex)
NSE doesn't provide official free real-time APIs. You'd need to:
- Use web scraping (unreliable, may break)
- Subscribe to NSE data feed (paid)
- Use broker APIs (Zerodha Kite, Upstox, etc.)

---

## 🚀 Recommended Deployment Workflow

### Daily Operations:
1. **6:00 PM IST**: Auto-fetch latest market data
2. **6:15 PM IST**: Regenerate recommendations CSV
3. **Backend**: Auto-loads new recommendations (no restart needed if using file watch)

### Weekly Operations:
1. **Sunday 8:00 PM**: Retrain model with latest 6-month data
2. **Check accuracy**: Compare with last week's performance
3. **Deploy new model** if accuracy > 65%

### Real-time During Market Hours (9:15 AM - 3:30 PM IST):
- Currently: **Simulated data only**
- Production: Integrate real-time provider (see options above)

---

## 📋 Quick Setup Checklist

- [ ] Install APScheduler: `pip install apscheduler`
- [ ] Create `app/scheduler.py` (copy code above)
- [ ] Test manually: `python app/scheduler.py`
- [ ] Set up cron job OR Windows Task Scheduler
- [ ] Create logs directory: `mkdir logs`
- [ ] Monitor first week: Check `logs/daily_update.log`
- [ ] (Optional) Set up real-time data provider for intraday
- [ ] Update `ws-server/index.js` to use real data instead of mock

---

## 🔍 How to Verify It's Working

### Check Daily Updates:
```bash
# Check last data update time
ls -lht data/processed/universe_data.csv

# Check logs
tail -f logs/daily_update.log
```

### Check Model Accuracy:
```bash
# After weekly retrain
python verify_accuracy.py
```

### Test Backend:
```bash
curl http://localhost:8000/api/recommendations | jq '.[] | select(.recommendation == "BUY")'
```

---

## ⚡ Current Status Summary

| Feature | Status | Action Needed |
|---------|--------|---------------|
| Historical Data Fetch | ✅ Working | Add automation |
| Daily Updates | ❌ Manual | Set up cron/scheduler |
| Weekly Retraining | ❌ Manual | Add to scheduler |
| Intraday Data | ⚠️ Mock Only | Integrate real provider |
| Backend API | ✅ Working | None |
| Model Serving | ✅ Working | Monitor accuracy |

---

## 💡 Pro Tips

1. **Start conservatively**: Run daily updates manually for 1 week to verify stability
2. **Monitor accuracy**: Set up alerts if model accuracy drops below 60%
3. **Data quality**: Check for missing dates before retraining
4. **Real-time costs**: Free providers have rate limits (Alpha Vantage: 5/min, Yahoo: delayed)
5. **Consider paid data** if you need true real-time (NSE, broker APIs)

---

## 📞 Next Steps

1. Choose automation method (I recommend **Option 3: Python Scheduler**)
2. Test manually first
3. Set up monitoring
4. Deploy to production
5. (Later) Integrate real-time data provider for intraday charts

Let me know which option you'd like to implement!
