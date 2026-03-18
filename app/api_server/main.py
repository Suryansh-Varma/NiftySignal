# NiftySignal - Intelligence-Driven Portfolio Management API
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# FIX: Add project root to sys.path so 'app' module can be found
# Root is two levels up from this file (app/api_server/main.py -> app/ -> root/)
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import logging
import json
import subprocess
import threading
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Recommendations API")

# CORS configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

logger.info(f"CORS configured for origins: {allowed_origins}")

# ---------------------------------------------------------------------------
# Concurrency guard for expensive on-demand updates
#
# Problem: If two users hit POST /api/refresh_risk or /api/refresh_recommendations
# simultaneously, both spawn a full yfinance fetch + model prediction, doubling
# CPU/memory/network for zero extra benefit.
#
# Solution:
#   1. threading.Lock — only ONE update runs at a time. The second caller gets
#      HTTP 429 immediately instead of queuing behind a slow job.
#   2. 5-minute cooldown (COOLDOWN_SECS) — after an update completes, any
#      on-demand call within 5 min is rejected with a "use cached data" reply.
#      The scheduled nightly job bypasses this guard entirely.
# ---------------------------------------------------------------------------
_update_lock  = threading.Lock()
_COOLDOWN_SECS = 300   # 5 minutes

_last_risk_update: Optional[datetime] = None
_last_recs_update: Optional[datetime] = None

CSV_PATH    = Path(__file__).parent.parent.parent / "results" / "latest_recommendations.csv"
RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

# Goal strategy CSV paths
GOAL_CSV_PATHS = {
    'conservative': RESULTS_DIR / "latest_goal_recommendations_conservative.csv",
    'moderate':     RESULTS_DIR / "latest_goal_recommendations_moderate.csv",
    'aggressive':   RESULTS_DIR / "latest_goal_recommendations_aggressive.csv"
}


def _records_from_df(df: pd.DataFrame) -> List[dict]:
    """Convert DataFrame to list of dicts with null-safe JSON handling."""
    # Use to_json to convert NaN to null, then parse back to Python
    return json.loads(df.to_json(orient="records"))

def _ensure_evaluation_json() -> Path:
    """Ensure evaluation JSON exists by running evaluator if needed."""
    eval_json = RESULTS_DIR / "goal_strategy_evaluation.json"
    if not eval_json.exists():
        evaluator = Path(__file__).parent.parent / "api" / "evaluate_strategies.py"
        if not evaluator.exists():
            raise HTTPException(status_code=500, detail="Evaluator script missing")
        try:
            subprocess.run([sys.executable, str(evaluator)], check=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to evaluate strategies: {e}")
    return eval_json

def _load_best_evaluation() -> dict:
    eval_json = _ensure_evaluation_json()
    try:
        with open(eval_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load evaluation JSON: {e}")


def _read_recommendations() -> List[dict]:
    try:
        if not CSV_PATH.exists():
            raise FileNotFoundError(f"Recommendations CSV not found: {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)
        if df.empty:
            logger.warning("Recommendations CSV is empty")
            return []
        
        # Transform column names to match frontend expectations
        # CSV: symbol, close, date, signal, confidence, buy_prob, sell_prob
        # Frontend expects: symbol, recommendation, last_price, last_date, confidence, buy_prob, sell_prob
        if 'close' in df.columns:
            df['last_price'] = df['close']
        if 'date' in df.columns:
            df['last_date'] = df['date']
        if 'signal' in df.columns:
            df['recommendation'] = df['signal']
        
        # Add risk_score based on confidence (inverse: lower confidence = higher risk)
        if 'confidence' in df.columns:
            df['risk_score'] = 1 - df['confidence'].fillna(0.5)
        else:
            df['risk_score'] = 0.5
        
        # Normalize dtypes and replace NaN with None for JSON
        return _records_from_df(df)
    except pd.errors.EmptyDataError:
        logger.error(f"Recommendations CSV is empty or corrupted: {CSV_PATH}")
        raise HTTPException(status_code=500, detail="Recommendations data is corrupted")
    except Exception as e:
        logger.error(f"Error reading recommendations: {e}")
        raise

def _read_goal_recommendations(strategy: str) -> List[dict]:
    """Read goal recommendations for a specific strategy."""
    csv_path = GOAL_CSV_PATHS.get(strategy)
    try:
        if not csv_path:
            raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}. Choose from: conservative, moderate, aggressive")
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Goal recommendations CSV not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        if df.empty:
            logger.warning(f"Goal recommendations CSV is empty for {strategy}")
            return []
        return _records_from_df(df)
    except pd.errors.EmptyDataError:
        logger.error(f"Goal recommendations CSV is empty or corrupted: {csv_path}")
        raise HTTPException(status_code=500, detail="Goal recommendations data is corrupted")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(status_code=404, detail=f"Recommendations not found for {strategy} strategy. Please run training first.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading goal recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/recommendations")
def get_recommendations(symbol: Optional[str] = Query(None, description="Filter by symbol, e.g. RELIANCE.NS")):
    try:
        records = _read_recommendations()
    except FileNotFoundError as e:
        logger.error(f"Recommendations file not found: {e}")
        raise HTTPException(status_code=404, detail="Recommendations not found. Please run model training first.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching recommendations")
    
    if symbol:
        filtered = [r for r in records if r.get("symbol") == symbol]
        if not filtered:
            logger.info(f"No recommendations found for symbol: {symbol}")
        return JSONResponse(content=filtered)
    return JSONResponse(content=records)


@app.get("/api/predict/{symbol}")
def predict_live(symbol: str):
    """
    GENERATE LIVE PREDICTION FOR ONE SYMBOL.
    
    Unlike /api/recommendations (which reads the daily CSV), this endpoint:
      1. Fetches the latest 60-day history for the symbol via yfinance.
      2. Computes fresh technical features.
      3. Loads the latest macro risk from disk.
      4. Runs the ensemble model for an 'up-to-the-minute' signal.
    
    This is highly efficient (0.5s) compared to refreshing the entire list.
    """
    try:
        from app.data.loaders import fetch_history_yf
        from app.features.technical import prepare_features
        from app.signals.ml_signals import MLSignalGenerator
        from app.features.risk_factors import RiskFactorCalculator
        
        # 1. Fetch latest data (just for this symbol)
        logger.info(f"Live predict: Fetching latest data for {symbol}")
        df_live = fetch_history_yf([symbol], period="60d", force_refresh=True)
        if df_live.empty:
            raise HTTPException(status_code=404, detail=f"No live data found for {symbol}")
            
        # 2. Prepare features
        X_live, _ = prepare_features(df_live, forward_days=5, return_threshold=0.015)
        if X_live.empty:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {symbol} to generate features")
            
        # 3. Load Model & Predict
        model_path = Path(__file__).parent.parent.parent / "models" / "trading_model.pkl"
        if not model_path.exists():
            raise HTTPException(status_code=500, detail="Model file missing. Please train the model first.")
            
        model = MLSignalGenerator.load(str(model_path))
        
        # Align features
        training_features = model.feature_columns
        X_latest = X_live[training_features].iloc[-1:]
        
        # Run prediction
        signal = int(model.predict(X_latest)[0])
        proba = model.predict_proba(X_latest)[0]
        confidence = float(np.max(proba))
        
        # 4. Apply current Macro Risk
        risk_calc = RiskFactorCalculator()
        macro_risk = risk_calc.get_macro_risk_factor()
        
        from app.features.risk_factors import adjust_signal_by_risk
        adj_signal, adj_confidence = adjust_signal_by_risk(signal, confidence, macro_risk)
        
        signal_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
        
        return JSONResponse(content={
            "symbol": symbol,
            "last_price": round(float(df_live.iloc[-1]['close']), 2),
            "last_date": str(df_live.iloc[-1]['date'].iloc[-1] if hasattr(df_live.iloc[-1]['date'], 'iloc') else df_live.iloc[-1]['date']),
            "recommendation": signal_map.get(adj_signal, "HOLD"),
            "confidence": round(adj_confidence, 4),
            "buy_prob": round(float(proba[list(model.model.classes_).index(1)]), 4) if 1 in model.model.classes_ else 0.0,
            "sell_prob": round(float(proba[list(model.model.classes_).index(-1)]), 4) if -1 in model.model.classes_ else 0.0,
            "macro_risk_applied": round(macro_risk, 4),
            "is_live": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Live prediction failed for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/goal_recommendations/{strategy}")
def get_goal_recommendations(
    strategy: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol, e.g. RELIANCE.NS")
):
    """
    Get goal-based recommendations for a specific strategy.
    
    Strategies:
    - conservative: 5% return in 6 months (lower risk)
    - moderate: 10% return in 6 months (balanced)
    - aggressive: 15% return in 3 months (higher risk)
    """
    try:
        records = _read_goal_recommendations(strategy)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_goal_recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    if symbol:
        filtered = [r for r in records if r.get("symbol") == symbol]
        if not filtered:
            logger.info(f"No goal recommendations found for symbol: {symbol} in {strategy} strategy")
        return JSONResponse(content=filtered)
    return JSONResponse(content=records)


@app.get("/api/goal_strategies")
def get_goal_strategies():
    """Get available goal-based strategies with descriptions."""
    strategies = {
        'conservative': {
            'name': 'Conservative',
            'target_return': '5%',
            'horizon': '6 months',
            'description': 'Lower risk, steady growth',
            'risk_level': 'Low'
        },
        'moderate': {
            'name': 'Moderate',
            'target_return': '10%',
            'horizon': '6 months',
            'description': 'Balanced risk-reward',
            'risk_level': 'Medium'
        },
        'aggressive': {
            'name': 'Aggressive',
            'target_return': '15%',
            'horizon': '3 months',
            'description': 'Higher risk, faster returns',
            'risk_level': 'High'
        }
    }
    return JSONResponse(content=strategies)

@app.get("/api/goal_best")
def get_best_strategy():
    """Return recommended best strategy based on evaluation JSON; compute if missing."""
    data = _load_best_evaluation()
    return JSONResponse(content=data)

@app.get("/api/goal_recommendations/best")
def get_best_recommendations(symbol: Optional[str] = Query(None, description="Filter by symbol, e.g. RELIANCE.NS")):
    """Proxy recommendations for the currently recommended strategy."""
    best_json = _load_best_evaluation()
    strategy = best_json.get("recommended")
    if not strategy:
        raise HTTPException(status_code=500, detail="No recommended strategy available")
    try:
        records = _read_goal_recommendations(strategy)
    except HTTPException:
        raise
    if symbol:
        records = [r for r in records if r.get("symbol") == symbol]
    return JSONResponse(content={"strategy": strategy, "rows": records})

@app.post("/api/refresh_universe")
def refresh_universe():
    """Fetch latest data for NIFTY universe and update processed CSV."""
    fetcher = Path(__file__).parent.parent / "api" / "main.py"
    if not fetcher.exists():
        raise HTTPException(status_code=500, detail="Fetcher script missing")
    try:
        subprocess.run([sys.executable, str(fetcher)], check=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh universe: {e}")
    return JSONResponse(content={"status": "ok", "message": "Universe data refreshed"})


@app.post("/api/refresh_risk")
def refresh_risk():
    """
    On-demand macro risk refresh — fetches live VIX, gold, oil, USD/INR and
    rewrites macro_risk_factor.json.

    Concurrency rules:
      • Only ONE refresh can run at a time (threading.Lock).
        A second concurrent call gets HTTP 429 immediately.
      • After a refresh completes, the next on-demand call is blocked for
        5 minutes (COOLDOWN_SECS). The nightly scheduler job is unaffected.
    """
    global _last_risk_update

    # Cooldown check
    if _last_risk_update and datetime.now() - _last_risk_update < timedelta(seconds=_COOLDOWN_SECS):
        remaining = int(_COOLDOWN_SECS - (datetime.now() - _last_risk_update).total_seconds())
        raise HTTPException(
            status_code=429,
            detail=(
                f"Risk data was updated {int((datetime.now() - _last_risk_update).total_seconds())}s ago. "
                f"Next on-demand refresh available in {remaining}s. "
                "The nightly scheduler updates this automatically at 6:30 PM IST."
            ),
        )

    # Concurrency lock — non-blocking acquire
    if not _update_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail=(
                "Another update is already in progress. "
                "Please wait a minute and try again, or use the cached risk data."
            ),
        )

    try:
        logger.info("On-demand risk refresh triggered via API")
        from app.scripts.auto_update_macro_risk import compute_and_update
        result = compute_and_update(dry_run=False)
        _last_risk_update = datetime.now()
        logger.info(f"On-demand risk refresh complete: {result['adjusted_risk_factor']:.4f} ({result['risk_level']})")
        return JSONResponse(content={
            "status":           "ok",
            "macro_risk":       result["adjusted_risk_factor"],
            "risk_level":       result["risk_level"],
            "position_sizing":  result["position_sizing"],
            "raw_market_data":  result["raw_market_data"],
            "updated_at":       result["update_date"],
        })
    except Exception as e:
        logger.error(f"On-demand risk refresh failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Risk refresh failed: {e}")
    finally:
        _update_lock.release()


@app.post("/api/refresh_recommendations")
def refresh_recommendations():
    """
    On-demand recommendation refresh — loads the trained model, generates fresh
    BUY/HOLD/SELL signals using latest prices + current macro risk, and writes
    latest_recommendations.csv.

    Concurrency rules: same as /api/refresh_risk (shared lock + cooldown).
    """
    global _last_recs_update

    # Cooldown check
    if _last_recs_update and datetime.now() - _last_recs_update < timedelta(seconds=_COOLDOWN_SECS):
        remaining = int(_COOLDOWN_SECS - (datetime.now() - _last_recs_update).total_seconds())
        raise HTTPException(
            status_code=429,
            detail=(
                f"Recommendations were refreshed {int((datetime.now() - _last_recs_update).total_seconds())}s ago. "
                f"Next on-demand refresh available in {remaining}s. "
                "The nightly scheduler regenerates recommendations at 6:45 PM IST."
            ),
        )

    # Concurrency lock — non-blocking
    if not _update_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail=(
                "Another update is already in progress. "
                "Please wait a moment — recommendations refresh in the background."
            ),
        )

    try:
        logger.info("On-demand recommendation refresh triggered via API")
        from app.scripts.generate_recommendations import generate
        summary = generate(dry_run=False)
        _last_recs_update = datetime.now()
        logger.info(f"On-demand recs refresh complete: {summary}")
        return JSONResponse(content={
            "status":         "ok",
            "total":          summary["total"],
            "BUY":            summary["BUY"],
            "HOLD":           summary["HOLD"],
            "SELL":           summary["SELL"],
            "model_accuracy": summary["model_accuracy"],
            "macro_risk":     summary["macro_risk"],
            "risk_level":     summary["risk_level"],
            "generated_at":   summary["generated_at"],
        })
    except Exception as e:
        logger.error(f"On-demand recs refresh failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Recommendation refresh failed: {e}")
    finally:
        _update_lock.release()


@app.get("/api/universe")
def get_universe():
    """Return list of NIFTY universe companies/symbols from config."""
    try:
        from app.config import NIFTY_50_UNIVERSE
        universe = NIFTY_50_UNIVERSE
        return JSONResponse(content={"count": len(universe), "symbols": universe})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load universe: {e}")

@app.get("/api/market_risk")
def get_market_risk():
    """Return current market risk assessment from macro_risk_factor.json."""
    try:
        macro_risk_file = Path(__file__).parent.parent.parent / "data" / "macro_risk_factor.json"
        if not macro_risk_file.exists():
            return JSONResponse(content={
                "risk_score": 0.5,
                "risk_level": "MODERATE",
                "factors": [],
                "update_date": None
            })
        
        with open(macro_risk_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Convert risk_factors dict to list format for frontend
        risk_factors_dict = data.get("risk_factors", {})
        factors = [
            {"name": k.replace("_", " ").title(), "contribution": v}
            for k, v in risk_factors_dict.items()
        ]
        
        return JSONResponse(content={
            "risk_score": data.get("adjusted_risk_factor", data.get("macro_risk_factor", 0.5)),
            "risk_level": data.get("risk_level", "MODERATE"),
            "factors": factors,
            "update_date": data.get("update_date"),
            "position_sizing": data.get("position_sizing", {})
        })
    except Exception as e:
        logger.error(f"Error reading market risk: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load market risk: {e}")


@app.get("/api/market_trend")
def get_market_trend():
    """Return market trend data from universe_data.csv (NIFTY 50 index proxy)."""
    try:
        data_file = Path(__file__).parent.parent.parent / "data" / "processed" / "universe_data.csv"
        if not data_file.exists():
            return JSONResponse(content={"labels": [], "values": []})
        
        df = pd.read_csv(data_file)
        df['date'] = pd.to_datetime(df['date'])
        
        # Get last 30 days of data, use aggregated close as market proxy
        latest_date = df['date'].max()
        start_date = latest_date - pd.Timedelta(days=30)
        
        daily_data = df[df['date'] >= start_date].groupby('date').agg({
            'close': 'mean'  # Average close price as market proxy
        }).reset_index().sort_values('date')
        
        labels = daily_data['date'].dt.strftime('%b %d').tolist()
        values = daily_data['close'].round(2).tolist()
        
        return JSONResponse(content={"labels": labels, "values": values})
    except Exception as e:
        logger.error(f"Error reading market trend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load market trend: {e}")


@app.get("/api/portfolio_optimizer")
def portfolio_optimizer(
    capital: float = Query(100000, description="Investment capital in INR"),
    target: float = Query(40, description="Target return percentage")
):
    """
    Goal-based portfolio optimizer.
    Returns strategies with stock allocations to achieve target return.
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    try:
        # Load recommendations
        recs = _read_recommendations()
        recs_df = pd.DataFrame(recs)
        
        buy_signals = recs_df[recs_df['recommendation'] == 'BUY'].copy()
        
        if len(buy_signals) == 0:
            return JSONResponse(content={"error": "No BUY signals available"}, status_code=404)
        
        def create_strategy(risk_level, num_stocks, max_per_stock, expected_monthly):
            selected = buy_signals.nlargest(num_stocks, 'buy_prob')
            weight = 1.0 / len(selected)
            selected = selected.copy()
            selected['weight'] = np.minimum(weight, max_per_stock)
            selected['weight'] = selected['weight'] / selected['weight'].sum()
            selected['allocation'] = (selected['weight'] * capital).round(0)
            selected['shares'] = (selected['allocation'] / selected['last_price']).astype(int)
            selected['actual_allocation'] = selected['shares'] * selected['last_price']
            
            # Timeline calculation
            target_pct = target / 100
            if expected_monthly > 0:
                months = np.log(1 + target_pct) / np.log(1 + expected_monthly) * 1.3
            else:
                months = 999
            
            target_date = datetime.now() + timedelta(days=months * 30)
            
            return {
                'risk_level': risk_level,
                'num_stocks': len(selected),
                'expected_monthly_return': expected_monthly * 100,
                'estimated_months': int(months),
                'target_date': target_date.strftime('%B %Y'),
                'total_allocated': float(selected['actual_allocation'].sum()),
                'cash_remaining': float(capital - selected['actual_allocation'].sum()),
                'stocks': selected[['symbol', 'last_price', 'shares', 'actual_allocation', 'buy_prob', 'confidence']].to_dict('records')
            }
        
        strategies = {
            'conservative': create_strategy('conservative', min(15, len(buy_signals)), 0.10, 0.025),
            'moderate': create_strategy('moderate', min(10, len(buy_signals)), 0.15, 0.04),
            'aggressive': create_strategy('aggressive', min(7, len(buy_signals)), 0.25, 0.06)
        }
        
        # Recommendation
        target_pct = target / 100
        if target_pct <= 0.20:
            recommended = 'conservative'
        elif target_pct <= 0.40:
            recommended = 'moderate'
        else:
            recommended = 'aggressive'
        
        return JSONResponse(content={
            'capital': capital,
            'target_return': target,
            'target_amount': capital * (1 + target_pct),
            'strategies': strategies,
            'recommended': recommended,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Portfolio optimizer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/portfolio/analyze")
def analyze_portfolio(holdings: List[Dict]):
    """
    On-demand analysis for any set of holdings.
    Expects list of: {"symbol": "RELIANCE.NS", "shares": 10}
    """
    from app.portfolio.manager import PortfolioManager
    from app.portfolio.models import Portfolio, Holding
    
    try:
        # Create a transient portfolio for analysis
        temp_portfolio = Portfolio(user_id="temp", name="Analysis")
        for h in holdings:
            temp_portfolio.add_holding(Holding(
                symbol=h["symbol"], 
                shares=float(h["shares"]), 
                avg_buy_price=float(h.get("avg_buy_price", 0))
            ))
        
        # We need a hacky way to pass this temp portfolio to the analytics method
        # or just modify the analytics method to accept a portfolio object.
        # For now, let's just run the logic here or similar.
        manager = PortfolioManager()
        
        # We'll save it temporarily and load it (simplest way without refactoring manager)
        temp_portfolio.save(manager.portfolio_dir)
        analytics = manager.get_portfolio_analytics("temp")
        
        return JSONResponse(content=analytics)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


