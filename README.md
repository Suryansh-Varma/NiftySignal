# NiftySignal - NSE Trading Intelligence Backend

NiftySignal is a Python-based trading intelligence backend for the Indian stock market (NSE). It generates buy, hold, and sell signals, portfolio goal suggestions, risk analysis, and supporting analytics for the NSE universe.

## Architecture

```text
Market Data Sources
  -> Ingestion & Processing (app/api, app/utils, app/data)
  -> Model Training & Signals (app/api/train_model.py, app/signals)
  -> Recommendation Outputs (results/latest_recommendations.csv)
  -> Portfolio Analysis (portfolio_goal_optimizer.py, app/portfolio)
  -> Reports & Plans (results/)

FastAPI Server (app/api_server/main.py)
  -> API Clients / CLI / Scripts
```

## Repository Structure

```text
├── app/                # Core Python backend
│   ├── api/            # Model training and recommendation logic
│   ├── api_server/     # FastAPI application server
│   ├── portfolio/      # Portfolio models and recommendation helpers
│   ├── signals/        # Signal generation engines
│   └── utils/          # Shared utility functions
├── data/               # Raw and processed datasets
├── models/             # Serialized ML model artifacts
├── docs/               # System documentation
├── results/            # Generated recommendation and analysis outputs
├── scripts/            # Maintenance and utility scripts
└── portfolio_goal_optimizer.py  # CLI portfolio optimizer
```

## Run Commands

### 1. Create and activate the Python environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the FastAPI backend
```powershell
cd app/api_server
python -m uvicorn main:app --reload --port 8000
```

### 4. Generate portfolio analysis
```powershell
python portfolio_goal_optimizer.py --portfolio "RELIANCE,TCS,INFY" --capital 100000 --num-buy 20
```

### 5. Refresh recommendations or data
```powershell
python generate_recommendations.py
python refresh_all_nse_data.py
```

## Notes

- The frontend has been removed from this repository.
- The main outputs are now the backend API, CLI tools, and generated files under `results/`.
- `results/latest_recommendations.csv` is the key input for the portfolio optimizer.

## Documentation

Useful references:
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Validation](docs/DEPLOYMENT_VALIDATION_CHECKLIST.md)
- [Goal Strategies](docs/GOAL_STRATEGIES_GUIDE.md)

*Disclaimer: This system is for educational and analytical purposes. Trading involves risk.*