# NiftySignal - Intelligence-Driven NSE Trading Terminal

NiftySignal is a state-of-the-art trading intelligence platform designed for the Indian stock market (NSE). It leverages machine learning and technical analysis to provide high-precision buy/sell signals across the entire NSE universe (3000+ stocks).

![Dashboard Preview](docs/assets/dashboard_preview.png) *(Placeholder - see documentation for visual guide)*

## 🚀 Key Features

- **Omniscient Surveillance**: Monitoring 3000+ NSE stocks with real-time intelligence.
- **ML Signaling**: Proprietary machine learning models trained on price action, volume, and volatility.
- **Strategic Goal Optimizer**: Intelligent portfolio allocation based on target returns and time horizons.
- **Risk Quantum**: Real-time risk analysis incorporating macro factors and sectoral rotation.
- **Institutional-Grade UI**: A premium, skeuomorphic "terminal" interface built with Next.js and Tailwind.
- **On-Demand Intelligence**: Smart hybrid data fetching (nselib + yfinance) for maximum reliability.

## 📁 Repository Structure

```
├── app/                # Core Python Backend
│   ├── api/            # ML models, training scripts, & data logic
│   ├── api_server/     # FastAPI application server
│   ├── portfolio/      # Portfolio Management logic
│   ├── signals/        # Signal generation engines
│   └── utils/          # Shared utility functions
├── frontend/           # Next.js Web Interface (Strategic Terminal)
├── data/               # Persistent data storage (Raw & Processed)
├── models/             # Serialized ML model containers
├── docs/               # System documentation & architectural maps
├── scripts/            # Maintenance & utility scripts
└── results/            # Performance analytics & recommendation logs
```

## 🛠️ Technical Stack

- **Frontend**: Next.js 14, React 18, Chart.js, Tailwind CSS, TypeScript
- **Backend API**: FastAPI (Python 3.12+), Uvicorn
- **ML Engine**: Scikit-Learn, Pandas, NumPy, TA-Lib
- **Storage**: Supabase (PostgreSQL), PyArrow (Local Caching)
- **Data Pipeline**: nselib, yfinance

## 📥 Quick Start

### 1. Backend Setup
```bash
# Initialize Python environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install critical dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Launch the Terminal
The easiest way to start the ecosystem is using the integrated startup script:
```bash
python start_fullstack.py
```

## 🚢 Deployment Strategy

The system is architected for containerized deployment.

1. **Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Manual Deployment**:
   - Deploy the **FastAPI Backend** (e.g., AWS App Runner, DigitalOcean App Platform).
   - Deploy the **Next.js Frontend** (e.g., Vercel, Netlify).
   - Configure environment variables listed in `frontend/.env.local`.

## 📈 Documentation

Comprehensive guides are located in the `docs/` directory:
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Deployment Validation](docs/DEPLOYMENT_VALIDATION_CHECKLIST.md)
- [Strategic Goal Guide](docs/GOAL_STRATEGIES_GUIDE.md)

---
*Disclaimer: This system is for educational/analytical purposes. Trading involves risk.*