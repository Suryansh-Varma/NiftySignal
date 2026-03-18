# NiftySignal - Full Stack Setup Guide

**Date**: February 19, 2026  
**Status**: Development Ready  
**Components**: Frontend (Next.js) + WebSocket Server + Python Backend + Supabase  

---

## 🎯 Architecture Overview

```
Frontend (Next.js)
├── Public Pages (/, /login, /signup)
├── Protected Pages (auth required)
│   ├── /dashboard - Portfolio & recommendations
│   ├── /portfolio - User holdings management
│   ├── /company/[symbol] - Company details with charts
│   └── /goal-strategies - Goal-based investing
│
├── Services
│   ├── Supabase Auth (login/signup)
│   ├── REST API calls to Python Backend
│   └── WebSocket for live data (ws-server)
│
WebSocket Server (Node.js)
├── Live price updates
├── Intraday streaming
├── Portfolio updates
└── Risk alerts

Python Backend (FastAPI)
├── /api/recommendations - Trading signals
├── /api/goal_recommendations/{strategy} - Goal-based picks
├── /api/universe - NIFTY 50 list
├── /api/health - Status check
└── /api/refresh_universe - Data refresh

Database (Supabase PostgreSQL)
├── Users (Supabase Auth)
├── Portfolios
├── Positions (stocks in portfolio)
├── NIFTY Universe (company list)
└── Recommendations (cached)
```

---

## 🚀 Setup Instructions

### Step 1: Supabase Setup (5 minutes)

1. Go to https://supabase.com and create an account
2. Create a new project (free tier available)
3. In Supabase dashboard, go to **SQL Editor**
4. Copy the SQL from `supabase_schema.sql` and run it to create tables
5. Go to **Settings** > **API** and copy:
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL`
   - Anon Key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Step 2: Frontend Setup (10 minutes)

```bash
cd frontend

# Create .env.local with your Supabase keys
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:4000
NODE_ENV=development
EOF

# Install new dependencies
npm install

# Run frontend
npm run dev
# Visit: http://localhost:3000
```

**New pages available**:
- `http://localhost:3000` - Public home page
- `http://localhost:3000/login` - Login (Supabase Auth)
- `http://localhost:3000/signup` - Sign up
- `http://localhost:3000/dashboard` - Portfolio dashboard (protected)
- `http://localhost:3000/portfolio` - Add/manage stocks (protected)
- `http://localhost:3000/company/RELIANCE.NS` - Company detail page

### Step 3: Python Backend Setup (5 minutes)

```bash
# Make sure Python backend is running
cd app/api_server

# If not already installed:
pip install fastapi uvicorn pandas

# Start backend on port 8000
python -m uvicorn main:app --reload --port 8000
```

**Backend URLs**:
- Health check: `http://localhost:8000/api/health`
- Recommendations: `http://localhost:8000/api/recommendations`
- Goal strategies: `http://localhost:8000/api/goal_strategies`
- NIFTY universe: `http://localhost:8000/api/universe`

### Step 4: WebSocket Server (Optional - for live updates)

```bash
cd ws-server
npm install
npm run dev
# Listens on ws://localhost:4000
```

---

## 🔐 Authentication Flow

### Sign Up
1. User visits `/signup`
2. Enters email, password, full name
3. Supabase creates account
4. Confirmation email sent (check spam)
5. Confirm email, redirected to login
6. Sign in with credentials

### Sign In
1. User visits `/login`
2. Enters email + password
3. Supabase validates credentials
4. JWT token created & stored in browser
5. Redirected to `/dashboard`

### Protected Routes
All routes under `/dashboard`, `/portfolio`, `/company` require authentication. If not logged in, redirects to `/login`.

---

## 📊 Data Flow

### 1. View Company Details
```
User clicks on RELIANCE.NS
    ↓
Validates symbol (must be NIFTY 50)
    ↓
Fetches: GET /api/recommendations?symbol=RELIANCE.NS
    ↓
Displays:
  - Company name (Reliance Industries)
  - Current price
  - Buy/Sell/Hold recommendation
  - Confidence %
  - Intraday chart
  - 30-day trend chart
  - Risk score
```

### 2. Add Stock to Portfolio
```
User clicks "Add Stock" on company page
    ↓
Form appears (quantity, buy price, buy date)
    ↓
Validates NIFTY 50 symbol
    ↓
Stores in localStorage (or Supabase in production)
    ↓
Portfolio grid updates
    ↓
Shows total value: quantity × buy_price
```

### 3. Get Trading Recommendations
```
Authenticated user views /dashboard
    ↓
Fetches: GET /api/recommendations (list of all stocks with signals)
    ↓
Displays recommendation cards:
  - Symbol & company name
  - Recommendation (BUY/SELL/HOLD)
  - Confidence %
  - Expected return %
  - Risk score
  ↓
User can click symbol to view company details
```

---

## 🛠️ API Endpoints Summary

### Backend (Python) - Running on http://localhost:8000

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/recommendations` | GET | All trading recommendations |
| `/api/recommendations?symbol=RELIANCE.NS` | GET | Recommendation for specific symbol |
| `/api/goal_strategies` | GET | Available goal strategies (5%, 10%, 15%) |
| `/api/goal_recommendations/{strategy}` | GET | Picks for strategy (conservative/moderate/aggressive) |
| `/api/universe` | GET | NIFTY 50 symbol list |
| `/api/refresh_universe` | POST | Refresh data (admin only) |

### Frontend APIs (Next.js) - Running on http://localhost:3000

| Route | Purpose |
|-------|---------|
| `/` | Public home page (marketing) |
| `/login` | Supabase auth login |
| `/signup` | Supabase auth signup |
| `/dashboard` | User portfolio dashboard (protected) |
| `/portfolio` | Add/manage stocks (protected) |
| `/company/[symbol]` | Company details + charts |
| `/goal-strategies` | Goal-based investing (protected) |

### WebSocket Server (Node.js) - Running on ws://localhost:4000

| Event | Direction | Payload |
|-------|-----------|---------|
| `subscribe` | Client → Server | `symbol` (subscribe to symbol updates) |
| `subscribe_portfolio` | Client → Server | Subscribe to portfolio changes |
| `subscribe_risk` | Client → Server | Subscribe to risk updates |
| `price_update` | Server → Client | `{ symbol, price, changePct, ts }` |
| `intraday` | Server → Client | `{ symbol, point: {t, v}, ts }` |
| `portfolio_update` | Server → Client | `{ positions: [...], ts }` |
| `risk_update` | Server → Client | `{ riskScore, factors: [...], ts }` |

---

## 🎯 Key Features

### ✅ Implemented
- [x] User authentication (Supabase)
- [x] Public home page with marketing
- [x] Login/signup pages
- [x] Protected routes (login required)
- [x] Company detail pages (symbol + charts)
- [x] Portfolio management (add/remove stocks)
- [x] NIFTY 50 ticker validation
- [x] Live charts (intraday + 30-day trend)
- [x] Light theme UI
- [x] Responsive design

### 🔄 In Progress
- [ ] Store portfolios in Supabase (move from localStorage)
- [ ] Real backend integration testing
- [ ] WebSocket live updates
- [ ] Performance optimization

### 📋 TODO (Next)
- [ ] User profile page (edit settings)
- [ ] Portfolio analysis (returns, drawdown)
- [ ] Price alerts (email/push notifications)
- [ ] Backtesting results display
- [ ] Portfolio recommendation API
- [ ] Admin dashboard (manage users)
- [ ] Mobile app (React Native)

---

## 🧪 Testing the System

### Test 1: Public Home Page
```
1. Visit http://localhost:3000
2. Should show marketing content
3. Click "Get Started" → goes to /signup
4. Click "Sign In" → goes to /login
```

### Test 2: Create Account & Login
```
1. Go to /signup
2. Enter: email, full name, password
3. Should see "Check your email" message
4. Confirm email in Supabase (check inbox/spam)
5. Go to /login
6. Sign in with email + password
7. Should redirect to /dashboard
```

### Test 3: Browse Companies
```
1. On home page (authenticated), click any symbol
2. Should show company name, charts, recommendation
3. Click "Add to Portfolio" → adds to holdings
4. Go to /portfolio → see new holding
5. Click company name again → back to detail page
```

### Test 4: Manage Portfolio
```
1. Go to /portfolio
2. Click "+ Add Stock"
3. Select symbol (only NIFTY 50 allowed)
4. Enter quantity, buy price, date
5. Click "Add Position"
6. Stock should appear in table
7. Click "Remove" → deletes from portfolio
```

### Test 5: Backend Integration
```
# In terminal, run:
curl http://localhost:8000/api/recommendations

# Should return JSON with trading signals for all stocks
```

---

## 🔗 Integration Checklist

- [ ] Supabase project created with database schema
- [ ] Frontend `.env.local` configured with Supabase keys
- [ ] Python backend running on port 8000
- [ ] WebSocket server running on port 4000 (optional)
- [ ] Frontend can login/signup
- [ ] Frontend can fetch recommendations from backend
- [ ] Portfolio page stores stocks in localStorage
- [ ] Company pages show correct data
- [ ] All NIFTY 50 symbols validated

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot POST /auth/v1..." | Supabase not configured. Check env vars. |
| "Cannot GET /api/recommendations" | Backend not running. Start on port 8000. |
| "Symbol not in NIFTY 50" | Add symbol to NIFTY_50 list in `lib/supabase.ts` |
| Portfolio not saving | Using localStorage for dev. Switch to Supabase for prod. |
| WebSocket not connecting | ws-server not running. Start on port 4000. |
| Charts not displaying | Check browser console for errors. |
| Login/signup not working | Check Supabase dashboard for auth settings. |

---

## 📝 Environment Variables Reference

**Frontend** `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:4000
NODE_ENV=development
```

**Backend** `.env` (if needed):
```
DATABASE_URL=postgresql://user:password@localhost:5432/niftysignal
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🚢 Deployment Checklist

### Frontend (Vercel)
- [ ] Push to GitHub
- [ ] Connect to Vercel
- [ ] Set env vars (Supabase keys)
- [ ] Deploy

### Backend (Render/Railway)
- [ ] Push to GitHub
- [ ] Connect to Render/Railway
- [ ] Set DATABASE_URL
- [ ] Deploy

### Database (Supabase)
- [ ] Backup data before production
- [ ] Enable Row Level Security (RLS)
- [ ] Set up API rate limiting
- [ ] Enable HTTPS/RLS policies

---

## 📞 Support & Next Steps

1. **Test locally first** - Verify all endpoints work
2. **Check backend outputs** - Ensure recommendations are accurate
3. **Monitor WebSocket** - Real-time updates need stable connection
4. **Handle edge cases** - Invalid symbols, network errors, etc.
5. **Performance test** - Load test with many concurrent users

---

**Ready to go!** You now have a full-stack NiftySignal platform with authentication, portfolio management, and AI-powered recommendations.
