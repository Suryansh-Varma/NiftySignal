# NiftySignal - Quick Reference Guide

**Last Updated**: February 19, 2026  
**Version**: 1.0 Full Stack  
**Status**: 🟢 Ready for Testing

---

## 🚀 Start Here (5 Minutes)

### 1. Setup Supabase (Once)
```bash
1. Go to https://supabase.com → Create Account
2. Create new project
3. Copy SQL from supabase_schema.sql → paste into Supabase SQL Editor
4. Settings → API → Copy Project URL and Anon Key
```

### 2. Configure Frontend
```bash
cd frontend
# Create .env.local with Supabase keys:
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=your_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:4000
EOF

npm install
npm run dev
# Frontend: http://localhost:3000
```

### 3. Start Backend
```bash
cd app/api_server
python -m uvicorn main:app --reload --port 8000
# Backend: http://localhost:8000/api/health
```

### 4. Test
- Visit http://localhost:3000
- Sign up, log in
- Add stocks to portfolio
- View company details

---

## 📱 Pages & Routes

| Route | Access | Purpose |
|-------|--------|---------|
| `/` | Public | Home page (marketing + recs if auth) |
| `/login` | Public | Sign in with email/password |
| `/signup` | Public | Create new account |
| `/dashboard` | Auth | Portfolio overview |
| `/portfolio` | Auth | Add/remove stocks |
| `/company/[symbol]` | Auth | Company details + charts |

---

## 🔑 Key Features

✅ **Authentication**: Email/password signup, Supabase managed  
✅ **Company Pages**: Symbol search, charts, recommendations  
✅ **Portfolio Management**: Add/remove stocks, track holdings  
✅ **NIFTY Validation**: Only 50 authorized stocks allowed  
✅ **Real-time Recommendations**: API integration with trading signals  
✅ **Light UI**: High contrast, accessible design  

---

## 📊 API Endpoints (Backend)

**All return JSON**

| Endpoint | Method | Params | Returns |
|----------|--------|--------|---------|
| `/api/health` | GET | - | `{status}` |
| `/api/recommendations` | GET | `?symbol=RELIANCE.NS` | `[{symbol, recommendation, confidence, ...}]` |
| `/api/goal_strategies` | GET | - | `{strategies}` |
| `/api/goal_recommendations/{strategy}` | GET | strategy=conservative/moderate/aggressive | `{strategy, recommendations}` |
| `/api/universe` | GET | - | `{symbols: [50 companies]}` |

**Test**:
```bash
curl http://localhost:8000/api/recommendations
```

---

## 🛠️ Frontend Files (New/Modified)

### Core Files
- `lib/supabase.ts` - Supabase client + NIFTY validator
- `lib/auth.tsx` - Authentication context
- `components/Navigation.tsx` - Top navbar

### Pages
- `pages/_app.tsx` - App wrapper (updated)
- `pages/index.tsx` - Home (updated)
- `pages/login.tsx` - Login form
- `pages/signup.tsx` - Signup form
- `pages/portfolio.tsx` - Stock management
- `pages/company/[symbol].tsx` - Company detail

### Config
- `frontend/.env.local` - Environment variables
- `supabase_schema.sql` - Database schema

---

## 🔐 Authentication

**Sign Up**:
1. Visit `/signup`
2. Fill form: name, email, password
3. Confirm email (check inbox)
4. Log in

**Sign In**:
1. Visit `/login`
2. Email + password
3. Redirects to `/dashboard`

**Protected Routes**:
- `/portfolio`, `/dashboard`, `/company/[symbol]`
- Redirect to `/login` if not authenticated

---

## 💾 Data Storage

**Currently**: localStorage (browser storage)  
**After Supabase**: PostgreSQL (cloud database)

**What's stored**:
- User accounts (Supabase Auth)
- Portfolios (table: portfolios)
- Stock positions (table: portfolio_positions)
- Company list (table: nifty_universe)
- Trading recommendations (table: recommendations)

---

## 📋 NIFTY 50 Companies

All symbols use `.NS` suffix format:

```
RELIANCE.NS    → Reliance Industries
TCS.NS         → Tata Consultancy Services
INFY.NS        → Infosys
WIPRO.NS       → Wipro
... (50 total)
```

**Validation**: `isValidNiftySymbol('RELIANCE.NS')` → true

---

## ❌ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Cannot find module @supabase/supabase-js" | `npm install @supabase/supabase-js` |
| "NEXT_PUBLIC_SUPABASE_URL not defined" | Add to `.env.local` |
| "Cannot get /api/recommendations" | Start backend on port 8000 |
| CORS error | Backend CORS middleware configured |
| Login won't work | Check Supabase keys in .env.local |
| Portfolio won't save | Expected (localStorage) until Supabase setup |
| Charts blank | Check API response data |

**Full troubleshooting**: See COMMON_ISSUES_AND_FIXES.md

---

## 📈 Performance Targets

- API response time: < 500ms
- Page load time: < 2s
- Frontend bundle: < 500KB
- Database query: < 100ms

---

## 🧪 Testing Checklist

- [ ] Backend health check: `curl http://localhost:8000/api/health`
- [ ] Get recommendations: `curl http://localhost:8000/api/recommendations`
- [ ] Frontend loads: `http://localhost:3000`
- [ ] Sign up works
- [ ] Sign in works
- [ ] Company page loads with data
- [ ] Portfolio page can add stocks
- [ ] Charts display correctly

---

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| FULLSTACK_SETUP.md | Complete setup guide |
| BACKEND_INTEGRATION_TESTING.md | Testing procedures |
| COMMON_ISSUES_AND_FIXES.md | Troubleshooting |
| DEPLOYMENT_VALIDATION_CHECKLIST.md | Pre-production checklist |
| FRONTEND_COMPONENT_ARCHITECTURE.md | Component details |

---

## 🚀 Next Steps

**Immediate** (You):
1. Create Supabase project
2. Deploy schema
3. Add credentials to `.env.local`
4. Run tests (see BACKEND_INTEGRATION_TESTING.md)

**Then** (Agent):
1. Fix any issues found during testing
2. Optimize performance
3. Deploy to production
4. Set up monitoring

---

## 🎯 Architecture at a Glance

```
Frontend (Next.js)          Backend (FastAPI)        Database (Postgres)
├─ Login/Signup       →     ├─ /api/health   →       ├─ users
├─ Dashboard          →     ├─ /api/recs     →       ├─ portfolios
├─ Company Pages      →     ├─ /api/goal     →       ├─ positions
├─ Portfolio CRUD     →     └─ /api/universe →       ├─ nifty_universe
└─ Charts                                            └─ recommendations

All secured with:
- Supabase Auth (JWT tokens)
- Row-Level Security (RLS policies)
- CORS middleware
```

---

## 💡 Key Concepts

**NIFTY 50**: 50 largest Indian companies (NSE index)  
**Symbol Format**: RELIANCE.NS (name + .NS suffix)  
**Recommendation**: BUY (↑), SELL (↓), HOLD (→)  
**Confidence**: 0-100% (how sure the signal is)  
**Risk Score**: 0-1.0 (volatility measure)  

---

## 📞 Support Resources

**Error in console?** → Check COMMON_ISSUES_AND_FIXES.md  
**Don't know how to test?** → See BACKEND_INTEGRATION_TESTING.md  
**Need to deploy?** → Read DEPLOYMENT_VALIDATION_CHECKLIST.md  
**Want component details?** → See FRONTEND_COMPONENT_ARCHITECTURE.md  
**Confused about setup?** → Read FULLSTACK_SETUP.md  

---

## ✅ System Status

| Component | Status |
|-----------|--------|
| Frontend code | ✅ Complete |
| Backend code | ✅ Complete |
| Database schema | ✅ Complete |
| Documentation | ✅ Complete |
| Local testing | ✅ Ready |
| Supabase setup | 🟡 Waiting for you |
| Production deploy | ⏳ After testing |

---

**Ready to start? Begin with "Setup Supabase" above → then run tests!**

Questions? See detailed docs in this folder:
- `FULLSTACK_SETUP.md` - Step-by-step setup
- `COMMON_ISSUES_AND_FIXES.md` - Troubleshooting
- `BACKEND_INTEGRATION_TESTING.md` - Validation
