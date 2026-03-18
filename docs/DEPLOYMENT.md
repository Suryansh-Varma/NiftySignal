# NiftySignal Portfolio Dashboard - Deployment Guide

## Overview
The dashboard consists of:
- **Frontend**: Next.js 14 app (React, TypeScript, Chart.js) on port 3000
- **WebSocket Server**: Node.js Socket.IO server on port 4000 for live price, intraday, portfolio, and risk updates
- **Backend**: Existing Python backend (universe.ts, recommendations.ts APIs)

All components use a **light theme** for optimal visualization and mobile-friendly responsive design.

---

## Local Development (Recommended for Testing)

### Prerequisites
- Node.js 18+
- npm/yarn

### 1. Frontend (Next.js dev server)
```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:3000
```

### 2. WebSocket Server (in another terminal)
```bash
cd ws-server
npm install
npm run dev
# Listens on ws://localhost:4000
```

### Environment (frontend)
Create `frontend/.env.local`:
```
NEXT_PUBLIC_WS_URL=ws://localhost:4000
```

**Both servers will auto-reload on code changes.**

---

## Local Deployment with Docker (Production-like)

### Prerequisites
- Docker & Docker Compose installed

### Single Command Startup
From the repo root:
```bash
docker compose up --build
```

This builds and runs both the frontend (port 3000) and WebSocket server (port 4000).

**Access**: http://localhost:3000

**Shutdown**: `Ctrl+C` or `docker compose down`

---

## Vercel Deployment (Frontend Only)

Vercel is ideal for the Next.js frontend; use a separate host for the WebSocket server.

### Steps

1. **Push your repo to GitHub** (if not already).

2. **Create a Vercel account** at https://vercel.com

3. **Connect repo to Vercel**:
   - Click "New Project"
   - Select your GitHub repo
   - Framework: Next.js (auto-detected)
   - Leave Build settings as default

4. **Add Environment Variables** in Vercel dashboard:
   - Key: `NEXT_PUBLIC_WS_URL`
   - Value: `wss://your-ws-server.com:4000` (use secure WSS in production)

5. **Deploy**: Vercel auto-deploys on every push to main branch.

**Notes**:
- Frontend will be deployed to `https://<your-project>.vercel.app`
- You must host the WebSocket server separately (e.g., Render, Railway, AWS, DigitalOcean)

---

## WebSocket Server Deployment (Render or Railway)

### Option A: Render.com
1. Push repo to GitHub.
2. Go to https://render.com/dashboard
3. Click "New +" > "Web Service"
4. Connect GitHub repo
5. Set Build Command: `cd ws-server && npm install`
6. Set Start Command: `npm start`
7. Set Environment:
   - `NODE_ENV=production`
   - `PORT=4000`
8. **Note the URL**: `wss://your-service.onrender.com`
9. Add this URL as `NEXT_PUBLIC_WS_URL` in Vercel dashboard.

### Option B: Railway.app
1. Go to https://railway.app
2. Create new project > GitHub
3. Select repo
4. Add `ws-server` as root directory in build settings
5. Set Start Command: `npm start`
6. Railway assigns a URL automatically
7. Update Vercel environment variable with WSS URL

---

## Full Self-Hosted Docker Deployment

For VPS/cloud providers (AWS, DigitalOcean, Linode, etc.):

### 1. SSH into your server
```bash
ssh user@your-vps-ip
```

### 2. Install Docker & Docker Compose
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Clone repo & deploy
```bash
git clone https://github.com/yourusername/NiftySIgnal.git
cd NiftySIgnal
```

### 4. Create `docker-compose.prod.yml` (optional overrides)
```yaml
version: '3.8'
services:
  frontend:
    ports:
      - '80:3000'
    environment:
      - NEXT_PUBLIC_WS_URL=wss://your-domain.com
  
  ws-server:
    ports:
      - '4000:4000'
    environment:
      - NODE_ENV=production
```

### 5. Start services
```bash
docker compose -f docker-compose.prod.yml up -d
```

**Access**: http://your-vps-ip or https://your-domain.com (with SSL reverse proxy like Nginx)

---

## Production Checklist

### Security
- [ ] Use `wss://` (secure WebSocket) with SSL certificate (Let's Encrypt)
- [ ] Validate JWT tokens in WebSocket `auth` middleware (update `ws-server/index.js`)
- [ ] Rate-limit WebSocket connections (e.g., 50/min per socket)
- [ ] Use environment variables for secrets (never hardcode)

### Scaling
- [ ] Add Redis adapter to Socket.IO for multi-server broadcasts:
  ```js
  import { createAdapter } from '@socket.io/redis-adapter'
  import { createClient } from 'redis'
  
  const pubClient = createClient({ host: 'redis-host' })
  const subClient = pubClient.duplicate()
  io.adapter(createAdapter(pubClient, subClient))
  ```
- [ ] Add horizontal scaling (load balancer, sticky sessions)
- [ ] Monitor with tools like PM2 or New Relic

### Monitoring
- [ ] Add logging (Winston, Bunyan) to track errors
- [ ] Use Sentry or similar for error tracking
- [ ] Monitor WebSocket connection count and message throughput
- [ ] Set up uptime alerts

### SSL/TLS
For self-hosted:
```bash
# Using Let's Encrypt with Nginx
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
# Renew cron job: certbot renew --quiet (runs daily)
```

---

## Live Features Enabled

✅ **Portfolio Dashboard**  
- Real-time stock listings with live price updates (via WebSocket)
- Portfolio position updates  
- Beautiful light theme with responsive layout

✅ **Charts & Visualization**  
- Intraday price action (streaming updates, 14-bar window)  
- Market trend (30-day rolling trend)  
- Risk assessment panel with volatility/macro factors

✅ **Connections**  
- HTTP REST APIs (portfolio, market initial load)
- WebSocket for live updates (price_update, intraday, portfolio_update, risk_update)  
- Auto-reconnect with exponential backoff

---

## Troubleshooting

### "Cannot GET /dashboard"
- Frontend is not running. Ensure `npm run dev` (local) or Docker is up.

### WebSocket connection refused
- WebSocket server not running. Check `ws-server/index.js` is listening on :4000
- Firewall blocking port 4000. Allow inbound on that port.
- Wrong `NEXT_PUBLIC_WS_URL`. Should be `ws://localhost:4000` locally or `wss://your-domain.com` in prod.

### Charts not updating
- Check browser DevTools Console for JS errors
- Verify WebSocket connection status (green dot in dashboard header)
- Check ws-server logs: `docker logs <container-id>`

### Out of Memory (Docker)
- Increase Docker memory limit
- Or increase Node heap: `NODE_OPTIONS="--max-old-space-size=512"`

---

## Next Steps

1. **Customize data sources**: Replace mock APIs with your actual Python backend
2. **Add authentication**: Integrate JWT/OAuth for user login
3. **Database integration**: Store user portfolios, watchlists, alerts
4. **Notifications**: Add email/push alerts on risk events or price targets
5. **A/B Testing**: Track user engagement with different layouts

---

## Support & Questions

- Frontend issues: Check `frontend/pages/dashboard.tsx` or component files
- WebSocket issues: Check `ws-server/index.js` logs
- Deployment issues: Consult Vercel / Render / Docker docs

---

**Last Updated**: February 2026  
**Version**: 1.0
