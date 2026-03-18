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

## Backend (Python/FastAPI) Deployment

The Python backend provides APIs for recommendations, portfolio analysis, and market data.

### Local Development

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
# or
python app/scheduler.py
```

**API Docs**: http://localhost:8000/docs (Swagger UI)

### Environment Variables (.env)

```
DATABASE_URL=postgresql://user:password@localhost/niftysignal
# or for SQLite:
DATABASE_URL=sqlite:///./niftysignal.db

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

API_PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
```

### Docker Deployment (Backend)

**Dockerfile** for backend:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DEBUG=False
ENV API_PORT=8000

CMD ["python", "-m", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run**:
```bash
docker build -t niftysignal-backend:latest .
docker run -d \
  -e DATABASE_URL="postgresql://..." \
  -e SUPABASE_URL="..." \
  -p 8000:8000 \
  niftysignal-backend:latest
```

### Full-Stack Docker Compose

Update your `docker-compose.yml` to include the backend:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: niftysignal
      POSTGRES_USER: niftysignal
      POSTGRES_PASSWORD: your_secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://niftysignal:your_secure_password@postgres:5432/niftysignal
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_KEY: ${SUPABASE_KEY}
      DEBUG: "False"
      CORS_ORIGINS: http://frontend:3000
    depends_on:
      - postgres
    volumes:
      - ./app:/app/app  # Hot-reload in dev

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
      NEXT_PUBLIC_WS_URL: http://localhost:4000
    depends_on:
      - backend

  ws-server:
    build: ./ws-server
    ports:
      - "4000:4000"
    environment:
      NODE_ENV: production
      PORT: 4000

volumes:
  postgres_data:
```

### Production Deployment Options

#### Option 1: Linux VPS (AWS, DigitalOcean, Linode)

```bash
# SSH into server
ssh user@your-vps

# Install Python & dependencies
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip postgresql-15
python3.11 -m venv /opt/niftysignal/.venv
source /opt/niftysignal/.venv/bin/activate
pip install -r requirements.txt gunicorn

# Create systemd service for backend
sudo nano /etc/systemd/system/niftysignal-backend.service
```

**Service file content**:
```ini
[Unit]
Description=NiftySIgnal Backend
After=network.target postgresql.service

[Service]
Type=notify
User=niftysignal
WorkingDirectory=/opt/niftysignal
Environment="PATH=/opt/niftysignal/.venv/bin"
ExecStart=/opt/niftysignal/.venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app.api.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable niftysignal-backend
sudo systemctl start niftysignal-backend
```

#### Option 2: Render.com

1. Push repo to GitHub
2. Create new Web Service on Render
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn -w 4 -b 0.0.0.0:10000 app.api.main:app`
5. Add environment variables (DATABASE_URL, SUPABASE credentials)
6. Deploy

#### Option 3: Railway.app

1. Create new project on Railway
2. Add PostgreSQL database
3. Deploy from GitHub
4. Set environment variables
5. Railway auto-generates DATABASE_URL

#### Option 4: AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 niftysignal

# Create environment and deploy
eb create niftysignal-env
eb deploy
```

### Database Migrations

If using SQLAlchemy with Alembic:

```bash
# Generate migrations
alembic revision --autogenerate -m "Add users table"

# Apply migrations locally
alembic upgrade head

# In production, run during deployment
# (before starting the application)
alembic upgrade head
```

### Health Check & Monitoring

```bash
# Health endpoint (add to your FastAPI app)
@app.get("/health")
def health():
    return {"status": "healthy"}

# Test locally
curl http://localhost:8000/health

# Monitor logs
tail -f /var/log/niftysignal-backend.log
```

### Performance Tuning

**Gunicorn workers** (adjust based on CPU cores):
```bash
gunicorn -w $((2 * $(nproc) + 1)) -b 0.0.0.0:8000 app.api.main:app
```

**Database connection pooling**:
```python
# In SQLAlchemy engine creation
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    echo=False
)
```

**Caching** (Redis):
```python
from redis import Redis
redis_client = Redis(host='localhost', port=6379, db=0)

# Cache recommendations
cached = redis_client.get('recommendations')
if not cached:
    recommendations = fetch_recommendations()
    redis_client.setex('recommendations', 3600, json.dumps(recommendations))
```

### SSL/TLS with Nginx Reverse Proxy

```nginx
upstream niftysignal_backend {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://niftysignal_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Production Checklist (Full Stack)

### Security
- [ ] Set `DEBUG=False` in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL for frontend + backend
- [ ] Validate all API inputs (Pydantic models enforce this)
- [ ] Set up CORS with specific origins (not `*`)
- [ ] Use secure WebSocket (WSS) in production
- [ ] Rate limiting on APIs (see Security section below)
- [ ] Use environment variables for all secrets

### Database
- [ ] Database backups configured (daily)
- [ ] Connection pooling enabled
- [ ] Indexes created on frequently-queried columns
- [ ] Database user has minimal permissions

### Monitoring & Logging
- [ ] Centralized logging (CloudWatch, ELK, Loggly)
- [ ] Error tracking (Sentry, Rollbar)
- [ ] Uptime monitoring (UptimeRobot, Datadog)
- [ ] Performance monitoring (New Relic, DataDog)
- [ ] Alert thresholds configured

### Scaling
- [ ] Load balancer configured (if multiple backend instances)
- [ ] Auto-scaling policies set (CPU > 70%, memory > 80%)
- [ ] CDN enabled for frontend static assets
- [ ] Database read replicas (if high-traffic)

---

## Support & Resources

- **Backend Issues**: Check `app/api/main.py` and `/app` folder
- **Database Issues**: Check PostgreSQL logs
- **API Docs**: `https://yourdomain.com/docs`
- **Deployment Logs**: Check systemd journal or cloud provider logs

---

**Last Updated**: March 2026  
**Version**: 2.0
