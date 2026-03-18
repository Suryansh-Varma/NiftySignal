# Frontend Component Architecture Guide

**Document**: Component Implementation Details  
**Status**: Complete Implementation  
**Frontend Framework**: Next.js 14 + React 18 + TypeScript  

---

## 🏗️ Architecture Overview

```
Frontend (Next.js App Router)
│
├── lib/ (Utilities & Context)
│   ├── supabase.ts       → Supabase client, NIFTY validator, company mapper
│   └── auth.tsx          → React Context for authentication state
│
├── components/ (Reusable Components)
│   ├── Navigation.tsx     → Top navbar with auth state rendering
│   ├── TrendChart.tsx     → Recharts line chart (30-day trends)
│   └── IntradayChart.tsx  → Candlestick chart (1-hour data)
│
└── pages/ (Route Handlers)
    ├── _app.tsx          → App wrapper (Auth provider + Navigation)
    ├── index.tsx         → Home page (public + authenticated modes)
    ├── login.tsx         → Supabase email/password login
    ├── signup.tsx        → New account creation
    ├── dashboard.tsx     → User portfolio overview (protected)
    ├── portfolio.tsx     → Stock position CRUD (protected)
    └── company/
        └── [symbol].tsx  → Dynamic company detail page
```

---

## 📁 File-by-File Implementation

### 1. **lib/supabase.ts** - 102 lines

**Purpose**: Initialize Supabase client and provide helper functions

**Exports**:

#### `supabase` - Supabase Client Instance
```typescript
export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```
- Used to interact with authentication and database
- Provides `.auth`, `.from()`, `.rpc()` methods

#### `NIFTY_50` - Array of 50 NIFTY Companies
```typescript
export const NIFTY_50 = [
  'RELIANCE.NS',
  'TCS.NS',
  'INFY.NS',
  // ... total 50 symbols
]
```
- Used in portfolio form dropdown
- Matches backend NIFTY_50_UNIVERSE from config.py

#### `NIFTY_COMPANY_MAP` - Symbol to Company Name Mapping
```typescript
export const NIFTY_COMPANY_MAP: Record<string, string> = {
  'RELIANCE.NS': 'Reliance Industries',
  'TCS.NS': 'Tata Consultancy Services',
  'INFY.NS': 'Infosys',
  // ... all 50
}
```
- Used to display friendly names (e.g., "TCS" → "Tata Consultancy Services")

#### `isValidNiftySymbol(symbol)` - Validation Function
```typescript
export function isValidNiftySymbol(symbol: string): boolean {
  return NIFTY_50.includes(symbol)
}
```
- Validates symbol is in NIFTY 50 list
- Used in portfolio form on submit

#### `getCompanyName(symbol)` - Name Lookup
```typescript
export function getCompanyName(symbol: string): string {
  return NIFTY_COMPANY_MAP[symbol] || symbol
}
```
- Returns friendly company name or symbol if not found

---

### 2. **lib/auth.tsx** - 56 lines

**Purpose**: React Context for managing authentication state globally

**Exports**:

#### `AuthContext` - React Context
```typescript
type AuthContextType = {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  signUp: (email: string, password: string, fullName: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}
```

#### `useAuth()` - Custom Hook
```typescript
const { user, isAuthenticated, isLoading, signUp, signIn, signOut } = useAuth()
```

**Methods**:

**`signUp(email, password, fullName)`**:
- Creates new user account with Supabase
- Sends confirmation email
- Throws error if email already exists or passwords don't match

**`signIn(email, password)`**:
- Authenticates with Supabase
- Creates JWT token stored in browser
- Syncs with Supabase session

**`signOut()`**:
- Clears JWT token
- Redirects to home page

**`isLoading`**:
- True while checking auth state on app load
- Used to prevent flickering/redirect issues

---

### 3. **components/Navigation.tsx** - 87 lines

**Purpose**: Persistent top navbar with auth-aware navigation

**Features**:

```
┌─────────────────────────────────────────────┐
│ NiftySignal Logo    Dashboard  Portfolio    │
│                     Logout (if auth)        │
│ (if not auth):                              │
│ NiftySignal Logo                Sign In     │
└─────────────────────────────────────────────┘
```

**Conditional Rendering**:
- **Not Authenticated**: Shows "Sign In" link
- **Authenticated**: Shows dashboard/portfolio links + logout button

**Styling**:
- Sticky positioning (stays at top while scrolling)
- Light background (#f3f4f6)
- Dark text for good contrast
- 16px padding, responsive

---

### 4. **pages/_app.tsx** - Updated

**Original Structure**:
```typescript
export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}
```

**Updated Structure**:
```typescript
export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Navigation />
      <Component {...pageProps} />
    </AuthProvider>
  )
}
```

**Impact**:
- AuthContext available to all pages
- Navigation displays on all pages
- Auth state persistent across navigation

---

### 5. **pages/login.tsx** - 113 lines

**Purpose**: User login page with Supabase authentication

**Form Fields**:
- Email (required, must be valid email)
- Password (required, min 6 chars)

**Behavior**:
1. User enters email + password
2. Click "Sign In"
3. Calls `signIn(email, password)` from AuthContext
4. On success: redirects to `/dashboard`
5. On error: shows error message in red

**Functionality**:
- Loading state (button disabled while submitting)
- Link to signup page ("Don't have an account?")
- Error display if credentials wrong

---

### 6. **pages/signup.tsx** - 145 lines

**Purpose**: Create new user account with Supabase

**Form Fields**:
- Full Name (required, min 2 chars)
- Email (required, valid email format)
- Password (required, min 6 chars, shown as dots)
- Confirm Password (must match password field)

**Validation**:
- All fields required
- Email must be valid format
- Password must be at least 6 characters
- Passwords must match

**Behavior**:
1. User fills form
2. Click "Create Account"
3. Calls `signUp(email, password, fullName)`
4. If email exists: shows error
5. If success: shows "Check your email" message
6. User receives confirmation email
7. After confirming, user can login

---

### 7. **pages/index.tsx** - Updated Home Page

**Dual-Mode Rendering**:

#### Mode 1: Public (Not Authenticated)
```
┌──────────────────────────────────┐
│  Hero Section                    │
│  Get Started | Sign In buttons   │
├──────────────────────────────────┤
│  Features Grid (6 cards)         │
│  - AI-powered signals            │
│  - Real-time recommendations     │
│  - Portfolio management          │
│  - Goal-based investing          │
│  - Risk analysis                 │
│  - Performance tracking          │
├──────────────────────────────────┤
│ Call to Action                   │
│ "Ready to maximize returns?"     │
│ [Get Started Button]             │
└──────────────────────────────────┘
```

#### Mode 2: Authenticated
```
┌─────────────────────────────────────────┐
│ Recommendations Table                   │
│ Symbol | Company | Recommendation | ... │
├─────────────────────────────────────────┤
│ RELIANCE.NS | Reliance | BUY | 85%      │
│ TCS.NS | TCS | HOLD | 65%                │
│ ... (more rows)                         │
├─────────────────────────────────────────┤
│ Each row clickable → goes to /company   │
└─────────────────────────────────────────┘
```

**API Integration**:
- Calls `GET /api/recommendations` on mount
- Displays recommendations in table format
- Shows symbol, company name, recommendation, confidence %
- Click row to view company details

---

### 8. **pages/company/[symbol].tsx** - 130 lines

**Purpose**: Display detailed company information with charts and recommendations

**URL Format**: `/company/RELIANCE.NS` (dynamic [symbol])

**Data Fetching**:
```typescript
const { symbol } = router.query
// Validate symbol
if (!isValidNiftySymbol(symbol)) return <div>Invalid symbol</div>
// Fetch: GET /api/recommendations?symbol={symbol}
```

**Display Sections**:

#### 1. Company Header
- Company name (from API)
- Current price (from API)
- Recommendation badge (BUY=green, SELL=red, HOLD=yellow)

#### 2. Metrics Cards
```
┌──────────────────┐┌──────────────────┐┌──────────────────┐
│ Price            ││ Recommendation   ││ Risk Score       │
│ $2,850.50        ││ BUY              ││ 0.42 / 1.0       │
└──────────────────┘└──────────────────┘└──────────────────┘
```

#### 3. Charts
- **Intraday Chart** (1 hour, candlestick)
  - 20 hourly data points
  - Shows open, high, low, close
  - Interactive hover

- **30-Day Trend** (line chart)
  - 30 daily data points
  - Shows price movement
  - Interactive hover

#### 4. Action Button
- "Add to Portfolio" button
- Routes to `/portfolio?add={symbol}`
- Prefills symbol in portfolio form

---

### 9. **pages/portfolio.tsx** - 222 lines

**Purpose**: User portfolio management (CRUD for stock positions)

**Access**: Protected route (redirects to /login if not authenticated)

**Features**:

#### 1. Add Stock Form
```
┌────────────────────────────────────────────┐
│ Symbol: [Dropdown - All 50 NIFTY stocks]   │
│ Quantity: [Number input]                   │
│ Buy Price: [Currency input]                │
│ Buy Date: [Date picker]                    │
│ [Add Position Button]                      │
└────────────────────────────────────────────┘
```

**Symbol Dropdown**:
- Shows all 50 NIFTY companies
- Format: "RELIANCE.NS - Reliance Industries"
- User selects from list

**Quantity Field**:
- Must be positive integer
- Validates on submit

**Buy Price Field**:
- Currency input
- Must be positive
- Validates on submit

**Buy Date Field**:
- Date picker
- Can be today or past date
- Validates on submit

#### 2. Positions List
```
┌─────────────────────────────────────────────────────────┐
│ Symbol │ Company │ Qty │ Buy Price │ Total │ Actions   │
├─────────────────────────────────────────────────────────┤
│ RELIANCE.NS │ Reliance     │ 10 │ 2850  │ 28,500 │ Remove │
│ TCS.NS │ TCS │ 5 │ 3500  │ 17,500 │ Remove │
└─────────────────────────────────────────────────────────┘
```

**Total Portfolio Value**: Sum of all positions (qty × price)

**Click company name**: Routes to `/company/[symbol]`
**Click Remove**: Deletes from portfolio

#### 3. Data Persistence

**Current** (Development):
- Stored in localStorage as `portfolio_${user.id}`
- Persists across page refreshes (in same browser)

**Future** (Production):
- Will store in Supabase `portfolio_positions` table
- Syncs across devices

---

### 10. **Database Schema** (supabase_schema.sql) - 275 lines

**Tables**:

#### `user_profiles` (Extended User Info)
```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT NOT NULL,
  full_name TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
RLS POLICY: Users can only see their own profile
```

#### `portfolios` (User's Portfolio Containers)
```sql
CREATE TABLE portfolios (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  name TEXT NOT NULL,      -- e.g., "Main Portfolio"
  description TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
RLS POLICY: Users can only see their own portfolios
```

#### `portfolio_positions` (Stock Holdings)
```sql
CREATE TABLE portfolio_positions (
  id UUID PRIMARY KEY,
  portfolio_id UUID REFERENCES portfolios(id),
  symbol TEXT NOT NULL,            -- e.g., "RELIANCE.NS"
  company_name TEXT,               -- e.g., "Reliance Industries"
  quantity DECIMAL NOT NULL,
  buy_price DECIMAL NOT NULL,
  buy_date DATE NOT NULL,
  notes TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
RLS POLICY: Users can only see positions in their portfolios
```

#### `nifty_universe` (Reference List of 50 Companies)
```sql
CREATE TABLE nifty_universe (
  symbol TEXT PRIMARY KEY,         -- "RELIANCE.NS"
  company_name TEXT NOT NULL,      -- "Reliance Industries"
  sector TEXT,                      -- "Energy"
  market_cap_cr DECIMAL,            -- Market cap in crores
  description TEXT
)
-- No RLS (public reference data)
```

#### `recommendations` (Cached Trading Signals)
```sql
CREATE TABLE recommendations (
  id UUID PRIMARY KEY,
  symbol TEXT NOT NULL,
  recommendation TEXT,              -- "BUY", "SELL", "HOLD"
  confidence DECIMAL,               -- 0.0 to 1.0
  expected_return DECIMAL,
  risk_score DECIMAL,
  last_price DECIMAL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
-- No RLS (public trading data)
```

---

## 🔄 Data Flow Diagrams

### Authentication Flow
```
User visits signup
    ↓
Fills form (name, email, password)
    ↓
Calls signUp() from AuthContext
    ↓
Sends to Supabase Auth API
    ↓
Email confirmation sent
    ↓
User confirms email
    ↓
User can now login
    ↓
Calls signIn() with email/password
    ↓
Supabase returns JWT token
    ↓
Frontend stores in browser
    ↓
All subsequent requests include token
    ↓
Can access protected routes
```

### Company Detail Page Flow
```
User clicks symbol "RELIANCE.NS"
    ↓
Router reads [symbol] param
    ↓
Validates: isValidNiftySymbol('RELIANCE.NS')
    ↓
Fetches: GET /api/recommendations?symbol=RELIANCE.NS
    ↓
Backend returns recommendation object
    ↓
Displays:
  - Company name (Reliance Industries)
  - Current price
  - Recommendation badge
  - Intraday candlestick chart
  - 30-day line chart
  - Risk score
  - "Add to Portfolio" button
    ↓
User clicks "Add to Portfolio"
    ↓
Routes to /portfolio?add=RELIANCE.NS
    ↓
Portfolio page pre-fills symbol field
```

### Portfolio Management Flow
```
User visits /portfolio
    ↓
Auth check: if not logged in → redirect to /login
    ↓
Fetches existing positions from localStorage
    ↓
Displays list: [SYMBOL | Company | Qty | Price | Total | Remove]
    ↓
User selects symbol from dropdown (all 50 NIFTY)
    ↓
Enters quantity, buy price, buy date
    ↓
Clicks "Add Position"
    ↓
Validates:
  - Symbol in NIFTY 50
  - Quantity > 0
  - Price > 0
    ↓
Stores in localStorage as portfolio_data
    ↓
Position appears in list
    ↓
Total portfolio value updates
    ↓
User can remove position
    ↓
On page refresh → data loads from localStorage
    ↓
(Future) On Supabase connected → loads from DB instead
```

---

## 🎨 UI Component Hierarchy

```
<App>
  <AuthProvider>
    <Navigation />
    <Page Component>
      {if company page}
        <CompanyHeader />
        <MetricsCards />
        <TrendChart />
        <IntradayChart />
      {if portfolio page}
        <AddStockForm />
        <PositionsList />
      {if home page}
        <HeroSection />
        <FeaturesGrid />
        <CallToAction />
    </Page>
  </AuthProvider>
</App>
```

---

## 📊 State Management Pattern

**Supabase Auth State**:
```typescript
const { user, session } = useAuth()
// - user: { id, email, user_metadata }
// - session: JWT token (auto-managed by Supabase)
```

**Component Local State**:
```typescript
const [formData, setFormData] = useState({ symbol: '', quantity: 0, ... })
const [positions, setPositions] = useState([])
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState('')
```

**No Redux/Zustand**: Used simple React Context + hooks (sufficient for this scale)

---

## 🔐 Protected Routes Implementation

```typescript
// pages/portfolio.tsx (example)

export default function Portfolio() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) return <div>Loading...</div>
  if (!isAuthenticated) return null

  return <PortfolioPage />
}
```

**Logic**:
1. Check if authenticated
2. If still loading → show spinner
3. If not authenticated → redirect to login
4. If authenticated → render page

---

## 📈 Performance Optimizations

1. **Code Splitting**: Next.js automatically splits routes
2. **Image Optimization**: (Not used yet, but available via next/image)
3. **API Caching**: Can add caching headers to Supabase responses
4. **Chart Lazy Loading**: Charts load with data (after fetch)
5. **Debouncing**: Form inputs debounced if needed

---

## 🚀 Future Enhancements

1. **Real-time Updates**: Add WebSocket subscriptions to Supabase
2. **Performance Tracking**: Show portfolio returns/drawdown
3. **Alerts**: User can set price alerts
4. **Social**: Share portfolios with other users
5. **Mobile**: React Native app for iOS/Android
6. **Analytics**: Dashboard showing user behavior
7. **Export**: Download portfolio as CSV/PDF
8. **Backtesting**: Show historical performance

---

**All components implemented and ready for testing!**
