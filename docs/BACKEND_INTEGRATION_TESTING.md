# Backend Integration & Testing Guide

## 🎯 Objective
Test and validate that your Python FastAPI backend correctly integrates with the Next.js frontend, ensuring accurate data flow for trading recommendations and company details.

---

## 📋 Pre-Integration Checklist

- [ ] Python backend running: `http://localhost:8000`
- [ ] Next.js frontend running: `http://localhost:3000`
- [ ] Supabase project created and credentials in `.env.local`
- [ ] All NIFTY 50 symbols in backend config match frontend validator
- [ ] Database schema deployed to Supabase (if using PostgreSQL storage)

---

## 🧪 Phase 1: Backend Health Check (No Frontend)

### Test 1.1: Verify Backend is Running

```bash
# Terminal
curl http://localhost:8000/api/health
```

**Expected Response**:
```json
{"status": "ok"}
```

**If fails**: Start backend with:
```bash
cd app/api_server
python -m uvicorn main:app --reload --port 8000
```

---

### Test 1.2: Get All Recommendations

```bash
curl http://localhost:8000/api/recommendations
```

**Expected Response**:
```json
[
  {
    "symbol": "RELIANCE.NS",
    "company_name": "Reliance Industries",
    "recommendation": "BUY",
    "confidence": 0.85,
    "expected_return": 0.12,
    "risk_score": 0.42,
    "last_price": 2850.50,
    "timestamp": "2025-02-19T10:30:00Z"
  },
  ...
]
```

**If fails**: 
- Check backend logs for errors
- Verify database connection in `app/api_server/main.py`
- Check `app/config.py` for NIFTY_50_UNIVERSE list

---

### Test 1.3: Get Single Symbol Recommendation

```bash
curl "http://localhost:8000/api/recommendations?symbol=RELIANCE.NS"
```

**Expected Response**:
```json
[
  {
    "symbol": "RELIANCE.NS",
    "company_name": "Reliance Industries",
    ...
  }
]
```

**Symbols to test**:
```
RELIANCE.NS
INFY.NS
TCS.NS
WIPRO.NS
LT.NS
MARUTI.NS
SUNPHA.NS
HCLTECH.NS
BAJAJFINSV.NS
HDFC.NS
```

**If symbol not found**: 
- Verify symbol in `app/config.py` NIFTY_50_UNIVERSE
- Check symbol format (must have `.NS` suffix)
- Case-sensitive: upper case required

---

### Test 1.4: Get Goal Strategies

```bash
curl http://localhost:8000/api/goal_strategies
```

**Expected Response**:
```json
{
  "strategies": [
    {"id": "conservative", "name": "Conservative", "description": "..."},
    {"id": "moderate", "name": "Moderate", "description": "..."},
    {"id": "aggressive", "name": "Aggressive", "description": "..."}
  ]
}
```

---

### Test 1.5: Get Goal Recommendations

```bash
curl "http://localhost:8000/api/goal_recommendations/conservative"
curl "http://localhost:8000/api/goal_recommendations/moderate"
curl "http://localhost:8000/api/goal_recommendations/aggressive"
```

**Expected Response for each**:
```json
{
  "strategy": "conservative",
  "recommendations": [
    {
      "symbol": "TCS.NS",
      "company_name": "Tata Consultancy Services",
      "recommendation": "BUY",
      "reason": "Defensive play with stable returns"
    },
    ...
  ]
}
```

---

### Test 1.6: Get NIFTY 50 Universe

```bash
curl http://localhost:8000/api/universe
```

**Expected Response**:
```json
{
  "symbols": [
    {
      "symbol": "RELIANCE.NS",
      "company_name": "Reliance Industries",
      "sector": "Energy",
      "market_cap_cr": 2500000
    },
    ...
  ],
  "total": 50
}
```

---

## 🔗 Phase 2: Frontend to Backend Integration

### Test 2.1: Verify Frontend Can Reach Backend

**In Browser Console** (`http://localhost:3000`), run:

```javascript
// Test endpoint
fetch('http://localhost:8000/api/recommendations')
  .then(r => r.json())
  .then(data => console.log('Success!', data))
  .catch(err => console.error('Error:', err))
```

**Expected**: Logs array of recommendations.

**If CORS error**:
1. Backend needs CORS headers. Add to `main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
2. Restart backend

---

### Test 2.2: Authentication Flow

1. **Sign Up**:
   - Go to `http://localhost:3000/signup`
   - Create account with email + password
   - Check email inbox for confirmation link
   - Confirm email address
   - Should redirect to login

2. **Sign In**:
   - Go to `http://localhost:3000/login`
   - Sign in with email + password
   - Should redirect to `/dashboard`
   - Navigation bar should show logout button

3. **Access Protected Route**:
   - Logout, then visit `/dashboard` directly
   - Should redirect to `/login`
   - This confirms protected routes work

---

### Test 2.3: Home Page (Public)

1. Visit `http://localhost:3000`
2. Should see:
   - NiftySignal logo
   - "Get Started" button (goes to signup)
   - "Sign In" button (goes to login)
   - Features grid (6 cards)
   - If logged in: Recommendations table

**Test 2.3a: Recommendations Table**
- Log in first
- Visit home page
- Should display table with columns:
  - Symbol | Company | Recommendation | Confidence | Return
- Verify data matches backend response

---

### Test 2.4: Company Detail Page

1. **Log in** first
2. **Visit**: `http://localhost:3000/company/RELIANCE.NS`
3. Should display:
   - ✅ Company name: "Reliance Industries"
   - ✅ Current price: (fetched from backend)
   - ✅ Recommendation: BUY/SELL/HOLD (colored badge)
   - ✅ Confidence %
   - ✅ Intraday chart (candlestick 1H)
   - ✅ 30-day trend chart
   - ✅ "Add to Portfolio" button
   - ✅ Risk score

4. **Test Chart Data**:
   - Intraday should show 20 data points (hourly)
   - 30-day should show 30 data points (daily)
   - Charts should be interactive (hover shows values)

5. **Test "Add to Portfolio" Button**:
   - Click button
   - Should redirect to `/portfolio?add=RELIANCE.NS`
   - Form should pre-fill symbol field

**Test invalid symbol**:
- Visit: `http://localhost:3000/company/INVALID.NS`
- Should show error: "Symbol not in NIFTY 50"
- Button to go back

---

### Test 2.5: Portfolio Page

1. **Log in** first
2. **Visit**: `http://localhost:3000/portfolio`
3. Should display:
   - Form to add new stock:
     - Symbol dropdown (all 50 NIFTY companies listed)
     - Quantity field
     - Buy price field
     - Buy date field
   - Existing positions list (initially empty)
   - Total portfolio value

4. **Add a Stock**:
   - Select "RELIANCE.NS" from dropdown
   - Enter quantity: 10
   - Enter buy price: 2850
   - Enter date: 2025-02-01
   - Click "Add Position"
   - Should appear in list with values:
     - Symbol | Company | Qty | Buy Price | Total | Actions
   - Total portfolio = 10 × 2850 = 28,500

5. **Test Symbol Validation**:
   - Submit with symbol not in dropdown
   - Should show error: "Invalid NIFTY symbol"

6. **Remove Position**:
   - Click "Remove" button on position
   - Should disappear from list
   - Total recalculates

7. **Refresh page**:
   - Positions should persist (localStorage)
   - After Supabase integration: should load from database

---

## 🔍 Phase 3: Data Validation

### Test 3.1: NIFTY 50 Symbol Synchronization

**Backend symbols** (from `app/config.py`):
```python
NIFTY_50_UNIVERSE = [
    'RELIANCE.NS',
    'TCS.NS',
    'INFY.NS',
    ...
]
```

**Frontend symbols** (from `frontend/lib/supabase.ts`):
```typescript
export const NIFTY_50 = [
    'RELIANCE.NS',
    'TCS.NS',
    'INFY.NS',
    ...
]
```

**Verify**: Both lists contain same 50 symbols in same order.

```bash
# In terminal, compare lists
grep -o "'[A-Z]*\.NS'" app/config.py | sort > backend_symbols.txt
grep -o "'[A-Z]*\.NS'" frontend/lib/supabase.ts | sort > frontend_symbols.txt
diff backend_symbols.txt frontend_symbols.txt
```

**Should produce**: No differences (both should have 50 symbols)

---

### Test 3.2: Recommendation Data Structure

**Backend response** should include:
```json
{
  "symbol": "RELIANCE.NS",           // Required
  "company_name": "Reliance...",      // Required
  "recommendation": "BUY",            // Required: BUY|SELL|HOLD
  "confidence": 0.85,                 // Required: 0.0-1.0
  "expected_return": 0.12,            // Required: percentage
  "risk_score": 0.42,                 // Required: 0.0-1.0
  "last_price": 2850.50,              // Required: latest price
  "timestamp": "2025-02-19T..."       // Required: ISO 8601
}
```

**Frontend expects** (see `pages/company/[symbol].tsx`):
- `symbol` - displayed as title
- `company_name` - displayed below symbol
- `recommendation` - colored badge (green=BUY, red=SELL, yellow=HOLD)
- `confidence` - percentage
- `expected_return` - percentage
- `risk_score` - 0-1 scale
- `last_price` - used in charts

**If mismatch**: Update backend response to match frontend expectations

---

### Test 3.3: Price Feed Accuracy

**Check that prices are realistic**:
1. Visit company page for RELIANCE.NS
2. Note `last_price` shown
3. Compare with real NSE price (Google: "RELIANCE NSE price")
4. Should be within 5% (if using cached data) or exact if live feed

**If prices are wrong**:
- Check backend data source in `app/api_server/main.py`
- Verify data refresh mechanism
- May need to fetch from real API (yfinance, NSE API, etc.)

---

## 🐛 Phase 4: Error Handling

### Test 4.1: Invalid Symbol

```bash
curl "http://localhost:8000/api/recommendations?symbol=INVALID.NS"
```

**Expected**: Empty array `[]` or error response

**Frontend behavior**:
- Should show error message
- Suggest valid NIFTY 50 symbols
- Allow user to go back

---

### Test 4.2: Network Error

1. **Stop backend**
2. Visit `http://localhost:3000/company/RELIANCE.NS`
3. Should show: "Failed to load recommendations"
4. Should have "Retry" button
5. **Restart backend**
6. Click "Retry" → should load data

---

### Test 4.3: Authentication Error

1. **Logout**
2. Visit `/portfolio` (protected route)
3. Should redirect to `/login`
4. **Sign in**
5. Should be able to access `/portfolio`

---

## ✅ Integration Checklist

- [ ] Backend returns 200 for all test endpoints
- [ ] Frontend receives and parses all API responses
- [ ] NIFTY 50 symbols match between backend and frontend
- [ ] Company detail pages show real API data
- [ ] Portfolio page can add/remove stocks
- [ ] Authentication redirects work correctly
- [ ] Chart data is accurate (intraday + 30-day)
- [ ] Error messages display properly
- [ ] All data types match (string, number, date)
- [ ] No CORS errors in console
- [ ] No response validation errors
- [ ] Symbols formatted correctly (.NS suffix)

---

## 📊 Test Results Template

Copy this and fill in after testing:

```
Date: 2025-02-19
Tester: [Your Name]

BACKEND TESTS:
✅ Health check: PASS/FAIL
✅ Get all recommendations: PASS/FAIL
✅ Get single symbol: PASS/FAIL
✅ Get goal strategies: PASS/FAIL
✅ Get goal recommendations: PASS/FAIL
✅ Get NIFTY universe: PASS/FAIL

FRONTEND TESTS:
✅ Home page (public): PASS/FAIL
✅ Home page (authenticated): PASS/FAIL
✅ Login/Signup flow: PASS/FAIL
✅ Company detail page: PASS/FAIL
✅ Portfolio page (add stock): PASS/FAIL
✅ Portfolio page (remove stock): PASS/FAIL
✅ Protected routes: PASS/FAIL

DATA VALIDATION:
✅ Symbol lists match: PASS/FAIL
✅ Response structure matches: PASS/FAIL
✅ Prices are realistic: PASS/FAIL

ISSUES FOUND:
1. [Issue description] - FIXED/PENDING
2. [Issue description] - FIXED/PENDING

NOTES:
[Any additional observations]
```

---

## 🚀 Next Steps After Integration Tests

1. **If all tests pass**: 
   - Switch portfolio storage from localStorage → Supabase
   - Deploy both services (frontend to Vercel, backend to Railway)
   - Set up live data feeds

2. **If tests fail**:
   - Check specific error messages in browser console
   - Verify backend logs for API errors
   - Review CORS policy if making cross-origin requests
   - Check environment variables in `.env.local`

3. **Performance optimization**:
   - Add API response caching
   - Implement pagination for recommendations
   - Add lazy loading for charts
   - Optimize WebSocket messages

---

**Ready to test!** Run through Phase 1, then Phase 2. Let me know which tests fail so I can help debug.
