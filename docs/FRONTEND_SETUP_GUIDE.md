# Frontend Dashboard Setup Guide

## What Changed

### ✅ 1. Portfolio Database Storage (FIXED)
**Before:** Portfolio stocks were stored in browser localStorage (not persistent across devices)
**After:** Portfolio stocks now saved in Supabase PostgreSQL database (persistent, secure, multi-device)

**Files Modified:**
- `frontend/pages/portfolio.tsx` - Updated to use Supabase CRUD operations
- `frontend/supabase_setup.sql` - NEW SQL migration for portfolio table

### ✅ 2. Stock Recommendations on Dashboard (ADDED)
**Before:** Dashboard only showed portfolio positions and charts
**After:** Dashboard now displays top stock recommendations from backend API with BUY/SELL/HOLD signals

**Features:**
- Fetches recommendations from `http://localhost:8000/api/recommendations`
- Shows top 10 BUY, 5 SELL, 5 HOLD signals
- Each recommendation displays:
  - Symbol
  - Signal badge (BUY/SELL/HOLD with color coding)
  - Current price
  - Confidence %
  - Risk score %
  - "View Details" button linking to individual stock page

**Files Modified:**
- `frontend/pages/dashboard.tsx` - Added recommendations table with links to company pages

### ✅ 3. UI Cleanup (REDESIGNED)
**Before:** Soft gradients, rounded corners, AI-looking design
**After:** Clean, minimal, professional design

**Changes:**
- Removed emoji from logo (📈 → NiftySignal)
- Changed color scheme:
  - Primary: #4f46e5 → #2563eb (more professional blue)
  - Backgrounds: #f7f7fb → #fafafa (cleaner gray)
  - Text: #0b1220 → #111827 (sharper contrast)
- Reduced border radius: 8px → 4px (less rounded)
- Removed soft shadows: box-shadow → border only
- Simplified buttons and cards

**Files Modified:**
- `frontend/styles/globals.css` - Complete redesign
- `frontend/components/Navigation.tsx` - Cleaner header

---

## Setup Instructions

### Step 1: Create Supabase Portfolio Table

1. Go to your Supabase dashboard: https://app.supabase.com
2. Select your project
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**
5. Copy and paste the entire content of **`frontend/supabase_setup.sql`**
6. Click **Run** (or press Ctrl+Enter)

**Expected Output:**
```
Success. No rows returned.
```

This creates:
- `portfolios` table with columns: id, user_id, symbol, company_name, quantity, buy_price, buy_date
- Row Level Security (RLS) policies so users can only see their own portfolio
- Auto-updating `updated_at` timestamp

### Step 2: Verify Environment Variables

Make sure your `frontend/.env.local` file has:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=http://localhost:4000
```

### Step 3: Start Backend Server

```bash
# In the root directory
python -m uvicorn app.api_server.main:app --reload --port 8000
```

**Verify:** Open http://localhost:8000/api/recommendations in browser - should see JSON with 47 stocks

### Step 4: Start Frontend

```bash
cd frontend
npm install  # If not already installed
npm run dev
```

**Verify:** Open http://localhost:3000

### Step 5: Test End-to-End Flow

1. **Signup/Login**
   - Go to http://localhost:3000
   - Click "Sign In" → Create account or login

2. **View Dashboard**
   - After login, you should see:
     - ✅ "Stock Recommendations" section at the top
     - ✅ Table with BUY/SELL/HOLD signals
     - ✅ Each row has "View Details" button
     - ✅ Clean, professional design (no AI-looking gradients)

3. **View Stock Details**
   - Click "View Details" on any recommendation
   - Should navigate to `/company/SYMBOL.NS`
   - Should see:
     - ✅ Company name and symbol
     - ✅ Current price, recommendation badge, risk score
     - ✅ Intraday chart
     - ✅ 30-day trend chart
     - ✅ "Add to Portfolio" button

4. **Add to Portfolio**
   - Click "Add to Portfolio"
   - Fill in: Quantity, Buy Price, Buy Date
   - Click "Add Position"
   - **Expected:** Success message "Added [Company] to portfolio"

5. **Verify Database Storage**
   - Go to Supabase dashboard → Table Editor → portfolios
   - **Expected:** You should see your portfolio entry with:
     - user_id (your UUID)
     - symbol
     - company_name
     - quantity
     - buy_price
     - buy_date
     - created_at

6. **View Portfolio**
   - Click "Portfolio" in navigation
   - **Expected:** See your added stocks in a table
   - **Test Remove:** Click "Remove" on a stock → should delete from database

---

## Troubleshooting

### Issue: "Failed to add stock to database"
**Cause:** Supabase table not created or RLS policies blocking
**Fix:**
1. Run the SQL in `supabase_setup.sql` again
2. Check Supabase → Authentication → Users - make sure you're logged in
3. Check Supabase → Table Editor → portfolios → RLS is enabled

### Issue: "No recommendations available"
**Cause:** Backend API not running or returning empty data
**Fix:**
1. Check backend is running: http://localhost:8000/api/health
2. Check recommendations: http://localhost:8000/api/recommendations
3. If empty, retrain model: `python retrain_model_recent.py`

### Issue: Company page shows "Failed to load company data"
**Cause:** Invalid symbol or backend API down
**Fix:**
1. Check symbol format is `SYMBOL.NS` (e.g., BRITANNIA.NS)
2. Verify symbol is in NIFTY 50 list (see `frontend/lib/supabase.ts`)

### Issue: UI still looks "AI-like"
**Cause:** Browser cache not cleared
**Fix:**
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Restart frontend dev server: `npm run dev`

---

## Next Steps (Optional Enhancements)

### 1. Real-time Intraday Data
Currently using mock data. To integrate real-time:
- Update `ws-server/index.js` to fetch from nselib or broker API
- See `DAILY_UPDATE_GUIDE.md` for real-time data options

### 2. Portfolio Analytics
Add to dashboard:
- Total portfolio value
- Daily P&L
- Top gainers/losers
- Performance chart

### 3. Alerts & Notifications
- Email alerts when BUY/SELL signal changes
- Browser push notifications
- Webhook integration

### 4. Advanced Filters
Add to recommendations table:
- Filter by signal (BUY/SELL/HOLD)
- Sort by confidence/risk
- Search by symbol

---

## Summary of Files Changed

| File | Status | Description |
|------|--------|-------------|
| `frontend/pages/dashboard.tsx` | ✅ Modified | Added stock recommendations display |
| `frontend/pages/portfolio.tsx` | ✅ Modified | Switched from localStorage to Supabase |
| `frontend/styles/globals.css` | ✅ Modified | Cleaner, professional design |
| `frontend/components/Navigation.tsx` | ✅ Modified | Removed emoji, updated colors |
| `frontend/supabase_setup.sql` | ✅ NEW | SQL migration for portfolios table |
| `frontend/pages/company/[symbol].tsx` | ✅ Exists | Already has charts (no changes needed) |

Backend files (no changes needed):
- `app/api_server/main.py` - Already serves recommendations
- `models/trading_model.pkl` - Retrained model (71.79% accuracy)
- `results/latest_recommendations.csv` - 47 stocks with signals

---

## Testing Checklist

- [ ] Supabase portfolio table created
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can signup/login successfully
- [ ] Dashboard shows stock recommendations
- [ ] Stock recommendations have BUY/SELL/HOLD badges
- [ ] "View Details" button works and navigates to company page
- [ ] Company page shows charts and recommendation
- [ ] Can add stock to portfolio
- [ ] Portfolio stock appears in Supabase database
- [ ] Portfolio page displays added stocks
- [ ] Can remove stock from portfolio
- [ ] UI looks clean and professional (not AI-like)

---

**Ready to test!** Run through the steps above and let me know if you encounter any issues.
