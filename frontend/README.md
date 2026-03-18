# Fintech Frontend (Next.js)

This Next.js frontend shows trading recommendations and company charts for the NIFTY50 universe. It reads CSV outputs from the backend located at `data/processed/` and `results/`.

Getting started:

1. Install dependencies

```powershell
cd frontend
npm install
```

2. Run dev server

```powershell
npm run dev
```

This starts the frontend at http://localhost:3000

API routes provided:
- `/api/recommendations` - returns latest recommendations from `results/latest_recommendations.csv`
- `/api/universe?symbol=SYMBOL` - returns historical rows for a symbol from `data/processed/universe_data.csv`

Notes:
- Ensure your backend CSVs exist (`data/processed/universe_data.csv` and `results/latest_recommendations.csv`).
- Add environment variables or proxying if you host backend separately.
