# 📊 NiftySignal Live Portfolio Dashboard

## Overview

A modern, real-time portfolio dashboard built with **Next.js 14**, **React**, **TypeScript**, and **Socket.IO** WebSockets for live streaming price updates, intraday charts, market trends, and risk assessment.

**Live URL**: `/dashboard`  
**Port**: 3000 (Next.js frontend)  
**WebSocket Server**: Port 4000 (Node.js Socket.IO)

---

## Architecture

### Frontend Stack
- **Framework**: Next.js 14 (React 18, TypeScript)
- **Charts**: Chart.js + react-chartjs-2
- **Real-time**: socket.io-client
- **Styling**: Light theme CSS (clean, modern, responsive)
- **APIs**: HTTP REST (initial) + WebSocket (streaming)

### Backend Stack
- **WebSocket Server**: Node.js + Socket.IO
- **Mock Data**: Gen erated prices, positions, risk factors (replaceable with real APIs)
- **Broadcast**: Every 2-5 seconds for smooth updates

### Data Flow

```
User visits /dashboard
    ↓
1. Initial Load (HTTP REST)
   ├─ GET /api/portfolio → Positions, positions[0] intraday
   └─ GET /api/market → Historical trend, risk score

2. Real-Time Subscriptions (WebSocket)
   ├─ socket.on('portfolio_update') → Update positions table
   ├─ socket.on('price_update') → Update individual stock prices
   ├─ socket.on('intraday') → Append to intraday chart (14-bar rolling)
   └─ socket.on('risk_update') → Update risk panel

3. Component Renders
   ├─ StockList (positions table)
   ├─ TrendChart (30-day market trend)
   ├─ IntradayChart (streaming intraday prices)
   └─ RiskPanel (macro + volatility risk)
```

---

## Components

### 1. **StockList** (`components/StockList.tsx`)
Displays user's portfolio positions in a table.

**Props**:
```tsx
type Position = {
  symbol: string      // e.g., "AAPL"
  name: string        // e.g., "Apple Inc."
  qty: number         // Quantity held
  price: number       // Current price
  changePct: number   // % change (colored: green if +, red if -)
}
```

**Features**:
- Scrollable table with clear formatting
- Green text for positive changes, red for negative
- Responsive on mobile (may wrap)

---

### 2. **TrendChart** (`components/TrendChart.tsx`)
Line chart showing 30-day market trend.

**Props**:
```tsx
{
  labels: string[]   // e.g., ["D-30", "D-29", ..., "D-0"]
  data: number[]     // Price values
  title?: string     // Chart title (default: "Market Trend")
}
```

**Features**:
- Blue line with light blue background fill
- No axis labels for clean look
- Responsive container (automatically scales to fit)

---

### 3. **IntradayChart** (`components/IntradayChart.tsx`)
Line chart for intraday (within-day) price action.

**Props**:
```tsx
{
  labels: string[]   // Times, e.g., ["09:30", "10:00", ..., "16:00"]
  data: number[]     // Intraday prices
}
```

**Features**:
- Red line with light red fill (distinct from trend)
- Rolling 14-bar window (updates every 5 sec)
- Compact height for sidebar placement

---

### 4. **RiskPanel** (`components/RiskPanel.tsx`)
Summary of market risk assessment with contributing factors.

**Props**:
```tsx
{
  riskScore: number        // 0.0-1.0, displayed as % (e.g., 27%)
  factors: Factor[]        // [{ name: "Volatility", contribution: 0.4 }, ...]
}
```

**Features**:
- Large, bold risk score display
- Pill badge for risk level (yellow = advisory, red = high)
- Top contributing factors listed
- Updates in real-time

---

### 5. **Dashboard Page** (`pages/dashboard.tsx`)
Main page orchestrating all components and WebSocket subscriptions.

**State Management**:
```tsx
const [positions, setPositions] = useState<Position[]>([])
const [trendLabels, setTrendLabels] = useState<string[]>([])
const [trendData, setTrendData] = useState<number[]>([])
const [intradayLabels, setIntradayLabels] = useState<string[]>([])
const [intradayData, setIntradayData] = useState<number[]>([])
const [risk, setRisk] = useState({ score: 0.12, factors: [] })
const [wsConnected, setWsConnected] = useState(false)  // Connection status
```

**WebSocket Event Handlers**:
- `portfolio_update` → Update positions table
- `risk_update` → Update risk score & factors
- `intraday` → Append new intraday point (keep last 14)
- `price_update` → Update individual stock prices (if needed)

**Connection Status Indicator**:
- Green dot (top-right) = Connected, real-time updates flowing
- Red dot = Offline, WebSocket disconnected (auto-reconnect enabled)

---

## API Routes

### Mock APIs (Can be replaced with real backend)

#### GET `/api/portfolio`
Returns portfolio positions and intraday data.

**Response**:
```json
{
  "positions": [
    { "symbol": "AAPL", "name": "Apple Inc.", "qty": 12, "price": 172.45, "changePct": 0.82 },
    { "symbol": "MSFT", "name": "Microsoft Corp.", "qty": 5, "price": 338.12, "changePct": -0.34 },
    { "symbol": "TSLA", "name": "Tesla Inc.", "qty": 3, "price": 184.01, "changePct": 1.23 }
  ],
  "intraday": {
    "AAPL": [
      { "t": "09:30", "v": 172.1 },
      { "t": "10:00", "v": 172.3 },
      ...
    ]
  }
}
```

#### GET `/api/market`
Returns market trend and risk assessment.

**Response**:
```json
{
  "trend": {
    "labels": ["D-30", "D-29", ..., "D-0"],
    "values": [1000.5, 1001.2, ..., 1041.3]
  },
  "riskScore": 0.27,
  "factors": [
    { "name": "Volatility", "contribution": 0.4 },
    { "name": "Macro Uncertainty", "contribution": 0.35 },
    { "name": "Liquidity", "contribution": 0.25 }
  ]
}
```

---

## WebSocket Events

### Server → Client (Broadcasts)

#### `price_update`
Emitted when a symbol's price changes.

```json
{
  "symbol": "AAPL",
  "price": 172.45,
  "changePct": 0.82,
  "ts": 1676779200000
}
```

#### `intraday`
Emitted when a new intraday tick arrives.

```json
{
  "symbol": "AAPL",
  "point": { "t": "09:30", "v": 172.1 },
  "ts": 1676779200000
}
```

#### `portfolio_update`
Emitted when portfolio changes (new position, size change, etc.).

```json
{
  "positions": [
    { "symbol": "AAPL", "qty": 12, "price": 172.45, "changePct": 0.82 },
    ...
  ],
  "ts": 1676779200000
}
```

#### `risk_update`
Emitted when risk score or factors change.

```json
{
  "riskScore": 0.27,
  "factors": [
    { "name": "Volatility", "contribution": 0.4 },
    ...
  ],
  "ts": 1676779200000
}
```

### Client → Server (Subscriptions)

#### `subscribe_portfolio`
Subscribe to portfolio updates.

#### `subscribe_risk`
Subscribe to risk updates.

#### `subscribe` (symbol)
Subscribe to a symbol's price updates.

Example:
```js
socket.emit('subscribe', 'AAPL')  // Subscribe to AAPL price updates
socket.emit('subscribe_portfolio')
socket.emit('subscribe_risk')
```

---

## Light Theme Design

### Color Palette
- **Background**: `#f7f7fb` (very light blue-gray)
- **Card**: `#ffffff` (white)
- **Text (primary)**: `#0b1220` (dark blue-black)
- **Text (secondary)**: `#475569` (muted gray)
- **Accent (primary)**: `#4f46e5` (indigo, for buttons/highlights)
- **Positive**: `#166534` (green, for gains)
- **Negative**: `#7f1d1d` (dark red, for losses)
- **Borders**: `#e6e9ef` (light gray)

### Key Features
- **High Contrast**: Text easily readable on light backgrounds
- **Soft Shadows**: `0 2px 6px rgba(12,20,32,0.04)` for depth without harshness
- **Rounded Corners**: 6-8px border-radius for modern feel
- **Responsive Typography**: System fonts for fast rendering
- **Mobile-First**: Stacks well on small screens

### UI Patterns
- **Cards**: White with subtle shadow, 16px padding
- **Tables**: Striped rows with light borders
- **Buttons**: Indigo primary, white outline secondary
- **Inputs**: Light gray border, indigo focus outline
- **Status Indicators**: Green/red colored dots or pills

---

## Deployment

### Local Development
```bash
# Terminal 1: WebSocket Server
cd ws-server
npm install
npm run dev

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Visit: http://localhost:3000/dashboard
```

### Docker
```bash
docker compose up --build
# Access: http://localhost:3000
```

### Production (Vercel + Render)
1. Deploy frontend to Vercel
2. Deploy WebSocket server to Render/Railway
3. Set `NEXT_PUBLIC_WS_URL` env var
4. Done!

See `DEPLOYMENT.md` for full details.

---

## Future Improvements

- [ ] Add user authentication (JWT, OAuth)
- [ ] Store user portfolios in database
- [ ] Custom watchlists
- [ ] Price alerts & notifications
- [ ] Export portfolio as CSV/PDF
- [ ] Performance analytics (Sharpe ratio, max drawdown)
- [ ] Backtesting integration
- [ ] Mobile native app (React Native)
- [ ] Real data integration (Finnhub, Polygon.io, NSE API)
- [ ] Redis scaling for multi-server deployments

---

## License

MIT - See LICENSE file

---

**Last Updated**: February 2026  
**Maintainer**: NiftySignal Team
