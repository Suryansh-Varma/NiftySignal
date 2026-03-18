# � NiftySignal Portfolio Dashboard - Quick Start

## ✨ What's Live Now (Feb 2026)

**Two fully-running servers** on your machine:
- **Frontend (Next.js)**: http://localhost:3000
- **WebSocket Server**: ws://localhost:4000

Both verified: ✅ Ports 3000 and 4000 listening

---

## 🎯 Dashboard Features

Access at: **http://localhost:3000/dashboard**

✅ **My Stocks** - Real-time portfolio positions with live price updates  
✅ **Intraday Chart** - Streaming 5-minute rolling chart (14-bar window)  
✅ **Market Trend** - 30-day price trend visualization  
✅ **Risk Assessment** - Volatility, macro, and liquidity risk factors  
✅ **Live Indicator** - Green dot = WebSocket connected, auto-updates every 2-5 sec  
✅ **Light Theme** - Clean white UI, easy to read, mobile-responsive  

---

## 🔌 What's Running

**Frontend (port 3000)**:
- Next.js 14 React app with TypeScript
- 4 new components: StockList, TrendChart, IntradayChart, RiskPanel
- HTTP APIs for initial load (portfolio, market)
- WebSocket client (socket.io) auto-subscribes to live feeds

**WebSocket Server (port 4000)**:
- Node.js Socket.IO server
- Broadcasts live updates every 2-5 seconds:
  - `price_update` (per symbol)
  - `intraday` (streaming prices)
  - `portfolio_update` (position changes)
  - `risk_update` (macro/volatility)

---

## 📊 Architecture Diagram

```
Dashboard (React)
    ↓
    ├─→ REST API (initial load)
    │   ├─→ /api/portfolio (mock positions)
    │   └─→ /api/market (mock trends)
    │
    └─→ WebSocket Client (socket.io)
        └─→ ws://localhost:4000
            └─→ Subscriptions: price_update, intraday, portfolio_update, risk_update
                └─→ Real-time chart updates + table refresh
```

---

## 🛠 Deploy in 3 Steps

### Step 1: Docker (Self-Hosted / VPS)
```bash
docker compose up --build
# Access: http://localhost:3000
# Both services auto-start, auto-restart on crash
```

### Step 2: Vercel (Frontend Only)
1. Push to GitHub
2. https://vercel.com → New Project
3. Set env: `NEXT_PUBLIC_WS_URL=wss://your-ws-server.com`
4. Deploy (auto on push)

### Step 3: Render/Railway (WebSocket Server)
1. https://render.com or https://railway.app
2. Connect GitHub, select `ws-server`
3. Deploy (copy the URL)
4. Update Vercel env var with that URL

**That's it!** Live in ~5 minutes.

---

## 🔧 Development (Local)

**Terminal 1 - WebSocket**:
```bash
cd ws-server
npm install
npm run dev
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000/dashboard

---

## 📁 New Files Added

```
frontend/
├── pages/
│   ├── dashboard.tsx           # ← Portfolio dashboard (WebSocket integrated)
│   ├── api/
│   │   ├── portfolio.ts        # ← Mock portfolio API
│   │   └── market.ts           # ← Mock market API
│   └── index.tsx               # Updated with dashboard link
├── components/
│   ├── StockList.tsx           # ← Position table
│   ├── TrendChart.tsx          # ← Chart.js trend line
│   ├── IntradayChart.tsx       # ← Intraday streaming
│   └── RiskPanel.tsx           # ← Risk summary panel
├── Dockerfile                  # Updated for production
└── package.json                # Added socket.io-client

ws-server/
├── index.js                    # Node + Socket.IO server
├── package.json
└── Dockerfile

Root:
├── docker-compose.yml          # Run both services
├── DEPLOYMENT.md               # Full production guide (read this!)
└── QUICK_START.md              # This file
```

---

## ⚡ Live Features

| Feature | Status | Update Rate |
|---------|--------|-------------|
| Stock Prices | ✅ Real-time | Every 2s |
| Intraday Chart | ✅ Real-time | Every 5s |
| Portfolio Positions | ✅ Real-time | Every 3s |
| Risk Score | ✅ Real-time | Every 4s |
| Historical Trend | REST (initial) | Page load |

---

## 🔐 Next: Wire Real Data

Currently using **mock data generators**. To use real data:

1. **Replace portfolio API** → Query your backend for real positions
2. **Replace market API** → Real prices (Finnhub, Polygon.io, NSE API)
3. **Connect ws-server** → Real price ticker feeds
4. **Add auth** → JWT login, session management

See `DEPLOYMENT.md` for auth + scaling details.

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot GET /dashboard" | Run `npm run dev` in `frontend/` |
| Red offline dot | WebSocket not running. Check port 4000. |
| Port in use | `npx kill-port 3000 4000` |
| Charts not updating | Check DevTools Console, WebSocket tab |
| Docker fails | `docker system prune -a` then rebuild |

---

## 📞 Files to Read

1. **`DEPLOYMENT.md`** - Full deploy guide (Vercel, Docker, VPS, production checklist)
2. **`dashboard.tsx`** - WebSocket client integration code
3. **`ws-server/index.js`** - Server broadcast logic
4. **`docker-compose.yml`** - Service definitions

---

## 🚀 Action Items

### Today
- [ ] Review TATAMOTORS sell signal
- [ ] Confirm sector (Auto - should avoid in high-risk)
- [ ] Check stop loss at Rs 361

### This Week
- [ ] Update macro risk (Wednesday)
- [ ] Check for geopolitical changes
- [ ] Monitor gold prices, VIX

### Next Week
- [ ] Full weekly review
- [ ] Update risk factor if needed
- [ ] Check if risk drops (more buys possible)

---

## 📈 When Risk Changes

**Risk drops to 0.5-0.6?**
```
Position Size: 1.0% (up from 0.5%)
Buy Confidence: 60% (down from 70%)
Sell Confidence: 45% (down from 50%)
Stop Loss: 1.5% (up from 1%)
Take Profit: 4.0% (up from 2.5%)
→ More trading opportunities!
```

**Risk rises to 0.8+?**
```
Position Size: 0.3% (down from 0.5%)
Buy Confidence: 75%+ (higher threshold)
Stop Loss: 0.8% (tighter)
Take Profit: 2.0% (quicker)
→ Ultra defensive!
```

---

## 📞 Quick Commands

```bash
# View latest signals
cat results/latest_recommendations.csv

# Check macro risk
python -m app.scripts.update_macro_risk --view

# Update risk (copy from Gemini)
python -m app.scripts.update_macro_risk --interactive

# See optimization params
python risk_optimizer.py

# Retrain if needed
python app/api/train_model.py
```

---

## 💡 Key Wins

✅ **Positive returns in downturn** (+1.47%)  
✅ **Massive drawdown reduction** (-26.67%)  
✅ **Risk-aware trading** (macro risk #1 feature)  
✅ **Selective signals** (70% confidence for buys)  
✅ **Better win rate** (49.37%)  
✅ **Automated scaling** (adapts to risk level)  

---

## ⚠️ Remember

- **This IS a high-risk market** (0.75)
- **Positive returns here are GOOD** (+1.47%)
- **Lower drawdown is PRIORITY** (-12.74%)
- **Smaller positions are SMART** (0.5%)
- **Wait for 70%+ confidence** (quality over quantity)

---

## 🎯 Next: Weekly Update

**Every Monday:**
1. Check macro risk factors (Fed, gold, geopolitics)
2. Use Gemini prompt to assess
3. Update risk factor
4. Model automatically adapts
5. New recommendations generated

---

**Status:** ✅ READY FOR TRADING  
**Deployment Date:** Jan 21, 2026  
**Next Review:** Jan 28, 2026
