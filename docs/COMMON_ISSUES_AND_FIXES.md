# Common Issues & Fixes

## 🔴 Critical Issues

### Issue 1: "Cannot find module '@supabase/supabase-js'"

**Symptom**:
```
Error: Cannot find module '@supabase/supabase-js'
```

**Fix**:
```bash
cd frontend
npm install @supabase/supabase-js
npm run dev
```

---

### Issue 2: "NEXT_PUBLIC_SUPABASE_URL is not defined"

**Symptom**:
```
TypeError: Cannot read property 'split' of undefined
# or
Missing environment variable
```

**Fix**:
1. Create `frontend/.env.local` with:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:4000
```

2. Restart frontend:
```bash
npm run dev
```

---

### Issue 3: "Failed to load recommendations" on company page

**Symptom**:
- Company page shows loading spinner indefinitely
- Browser console shows: `GET http://localhost:8000/api/recommendations?symbol=... 404 Not Found`

**Causes & Fixes**:

**A) Backend not running**:
```bash
cd app/api_server
python -m uvicorn main:app --reload --port 8000
```

**B) CORS error** (console shows CORS error):
```python
# Add to app/api_server/main.py (before @app routes)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Then restart backend.

**C) Wrong API URL in .env.local**:
- Check: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Restart frontend with: `npm run dev`

**D) Endpoint doesn't exist**:
- Test with: `curl http://localhost:8000/api/recommendations?symbol=RELIANCE.NS`
- Check backend code at `app/api_server/main.py`

---

### Issue 4: "Symbol not in NIFTY 50" error on portfolio page

**Symptom**:
- When adding stock to portfolio, it says symbol is invalid
- But symbol is shown in dropdown

**Possible causes**:

**A) Symbol format mismatch**:
- Backend might use `RELIANCE` (no .NS)
- Frontend validates `RELIANCE.NS`
- Verify both match in `app/config.py` and `frontend/lib/supabase.ts`

**B) Symbol list out of sync**:
```bash
# Check if lists match:
diff <(grep "'[A-Z]*\.NS'" app/config.py | sort) \
     <(grep "'[A-Z]*\.NS'" frontend/lib/supabase.ts | sort)
```

**Fix**: Update one list to match the other (add .NS suffix to all)

---

### Issue 5: Login/Signup not working

**Symptom**:
- Form appears to submit but nothing happens
- No error message shown
- Page doesn't redirect

**Causes & Fixes**:

**A) Supabase not configured**:
- Check `frontend/.env.local` has `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Go to https://supabase.com → Your Project → Settings → API
- Copy Project URL and Anon Key
- Update `.env.local`
- Restart frontend: `npm run dev`

**B) Supabase auth not enabled**:
1. Go to supabase.com → Your Project → Authentication
2. Check "Enable" auth providers (Email/Password)
3. Settings → Auth Providers → Email → Enable

**C) Check browser console for errors**:
- Open DevTools (F12)
- Go to Console tab
- Look for error messages
- May need to confirm email first

---

## 🟡 Common Issues

### Issue 6: Portfolio positions not saving

**Symptom**:
- Add a stock to portfolio
- Refresh page
- Stock is gone

**Cause**:
- Currently using localStorage (browser storage)
- localStorage is per-domain and browser

**Temporary fix** (for development):
- This is expected behavior until Supabase is connected
- Each user's portfolio is stored locally in their browser

**Permanent fix**:
1. Deploy Supabase schema (see FULLSTACK_SETUP.md)
2. Update portfolio.tsx to use:
```typescript
// Instead of loadPortfolio() with localStorage:
const { data: positions } = await supabase
  .from('portfolio_positions')
  .select('*')
  .eq('user_id', user.id)
```

---

### Issue 7: Charts not displaying in company page

**Symptom**:
- Canvas element shows but no data
- Chart appears blank

**Causes & Fixes**:

**A) Chart.js not installed**:
```bash
cd frontend
npm install chart.js react-chartjs-2
npm run dev
```

**B) Chart dimensions**:
- Canvas container too small (try making it wider)
- Charts need minimum 300px width

**C) Data not generating**:
- Check browser console for errors
- Verify mock data generator in pages/company/[symbol].tsx
- If real data: verify API response includes prices

---

### Issue 8: Page shows "Redirecting to login..." forever

**Symptom**:
- Click on protected route (/portfolio, /dashboard)
- Shows loading message but never loads

**Cause**:
- useAuth() check running on client, but still evaluating

**Fix**:
```typescript
// In component, add null check:
const { isAuthenticated, isLoading } = useAuth()

if (isLoading) return <div>Loading...</div>

if (!isAuthenticated) {
  router.push('/login')
  return null
}

// Rest of component...
```

---

### Issue 9: WebSocket connection fails

**Symptom**:
- Expected real-time updates not happening
- Browser console: `WebSocket connection failed`

**Causes & Fixes**:

**A) WebSocket server not running**:
```bash
cd ws-server
npm install
npm run dev
```

**B) Wrong WebSocket URL**:
- Check `.env.local`: `NEXT_PUBLIC_WS_URL=ws://localhost:4000`
- Should use `ws://` (not `http://`)

**C) CORS issue on WebSocket**:
- Add to ws-server `index.js`:
```javascript
const io = require('socket.io')(PORT, {
  cors: {
    origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
    methods: ['GET', 'POST']
  }
})
```

---

### Issue 10: "Too many redirects" error

**Symptom**:
- Page keeps redirecting (infinite loop)
- Browser shows "ERR_TOO_MANY_REDIRECTS"

**Cause**:
- Auth check redirecting to login
- Login page also checking auth and redirecting

**Fix**:
- Don't check auth on login/signup pages
```typescript
// pages/login.tsx - Remove auth check
// Just let page render
```

---

## 🟢 Warnings (Not Critical)

### Warning 1: "useLayoutEffect does nothing on the server"

**Cause**:
- Next.js warning about hooks running during server render

**Fix** (if it bothers you):
```typescript
// Use useEffect instead of useLayoutEffect:
import { useEffect } from 'react'
```

---

### Warning 2: "Hydration mismatch"

**Cause**:
- Server render differs from client render (common with auth)

**Fix**:
```typescript
const [isMounted, setIsMounted] = React.useState(false)

useEffect(() => {
  setIsMounted(true)
}, [])

if (!isMounted) return null

// Render component
```

---

### Warning 3: "Max listeners exceeded"

**Cause**:
- Node.js warning about event listeners

**Info**: Usually harmless in development, fix before production

---

## 🔧 Debugging Tips

### 1. Check Backend Logs
```bash
# Terminal running FastAPI backend shows:
# INFO: GET /api/recommendations?symbol=RELIANCE.NS
# INFO: Returning [...]
```

Look for errors like:
- `KeyError: 'symbol'` → URL param not passed
- `ModuleNotFoundError` → Missing dependency
- `ConnectionError` → Database not connected

---

### 2. Check Frontend Console (DevTools F12)

**Network tab**:
- Click "Company/RELIANCE.NS"
- Go to Network tab
- Should see requests:
  - GET /api/recommendations?symbol=RELIANCE.NS (200 OK)
  - GET /api/recommendations (200 OK on home)

**Console tab**:
- Look for red errors
- Look for yellow warnings
- Run test code:
```javascript
fetch('/api/recommendations')
  .then(r => r.json())
  .then(d => console.log('Success:', d))
  .catch(e => console.log('Error:', e))
```

---

### 3. Check Environment Variables

```bash
# terminal
cat frontend/.env.local
```

Should show:
```
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### 4. Check If Ports Are In Use

```bash
# Windows - Check if port 3000 is in use
netstat -ano | findstr :3000

# If in use, kill process:
taskkill /PID <PID> /F

# Or start on different port:
cd frontend
npm run dev -- -p 3001
```

---

### 5. Test Endpoints Directly

```bash
# Test backend health:
curl http://localhost:8000/api/health

# Test recommendations:
curl "http://localhost:8000/api/recommendations?symbol=RELIANCE.NS"

# Test from browser console:
fetch('http://localhost:8000/api/recommendations')
  .then(r => r.json())
  .then(d => console.table(d))
```

---

## 📋 Quick Restart Checklist

If things break, try this in order:

1. **Clear Node cache**:
```bash
cd frontend
rm -r node_modules/.cache
npm run dev
```

2. **Restart frontend**:
```bash
cd frontend
npm run dev
```

3. **Restart backend**:
```bash
cd app/api_server
python -m uvicorn main:app --reload --port 8000
```

4. **Check environment variables**:
```bash
cat frontend/.env.local
# Verify all are present and correct
```

5. **Check ports are correct**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- WebSocket: ws://localhost:4000

6. **Hard refresh browser**:
- Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clears cache and reloads

---

## 📞 Getting Help

**Before asking for help, gather**:
1. Error message (exact text)
2. Which page/feature was using
3. Browser console errors (F12 → Console)
4. Backend logs (what was printed)
5. Environment variables (check if all set)

**Then check**:
- [ ] Is backend running on port 8000?
- [ ] Is frontend running on port 3000?
- [ ] Are all env vars set in .env.local?
- [ ] Are NIFTY symbols in both backend and frontend?
- [ ] Any CORS errors in console?
- [ ] Any typos in file paths or URLs?

---

**Most issues are solved by**:
1. Restarting backend
2. Restarting frontend
3. Checking .env.local
4. Hard refresh browser (Ctrl+Shift+R)

If that doesn't work, check sections above for your specific error message.
