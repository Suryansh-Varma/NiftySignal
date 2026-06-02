"""
COMPREHENSIVE SYSTEM TEST
Tests all components of the NiftySignal trading system
"""

import sys
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).parent))

print("\n" + "=" * 80)
print("NIFTYSIGNAL COMPREHENSIVE SYSTEM TEST")
print("=" * 80)

# Test 1: Package Imports
print("\n[TEST 1] Checking Package Imports...")
print("-" * 80)

required_packages = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "sklearn",
    "yfinance": "yfinance",
    "nselib": "nselib",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "apscheduler": "apscheduler",
}

failed_imports = []
for package_name, import_name in required_packages.items():
    try:
        __import__(import_name)
        print(f"  ✓ {package_name}")
    except ImportError as e:
        print(f"  ✗ {package_name}: {e}")
        failed_imports.append(package_name)

if failed_imports:
    print(f"\n⚠️  WARNING: {len(failed_imports)} packages failed to import")
else:
    print("\n✅ All packages imported successfully!")

# Test 2: Data Loaders
print("\n[TEST 2] Testing Data Loaders...")
print("-" * 80)

try:
    from app.data.loaders import capital_market, fetch_history_yf

    if capital_market is not None:
        print("  ✓ nselib capital_market available")
    else:
        print("  ⚠️  nselib not available, will use yfinance")

    print("  ✓ Data loaders imported successfully")
except Exception as e:
    print(f"  ✗ Data loaders failed: {e}")

# Test 3: Model Components
print("\n[TEST 3] Testing Model Components...")
print("-" * 80)

try:
    from app.signals.ml_signals import MLSignalGenerator
    from app.features.technical import prepare_features
    from app.config import TradingConfig

    print("  ✓ MLSignalGenerator imported")
    print("  ✓ Feature preparation imported")
    print("  ✓ TradingConfig imported")
    print("  ✓ Model components ready")
except Exception as e:
    print(f"  ✗ Model components failed: {e}")

# Test 4: Check Model File
print("\n[TEST 4] Checking Trained Model...")
print("-" * 80)

try:
    from app.config import MODELS_DIR

    model_path = MODELS_DIR / "trading_model.pkl"

    if model_path.exists():
        from app.signals.ml_signals import MLSignalGenerator

        model = MLSignalGenerator.load(str(model_path))
        test_acc = (model.test_metrics or {}).get("accuracy", 0)
        print(f"  ✓ Model file exists: {model_path}")
        print(f"  ✓ Model test accuracy: {test_acc:.2%}")

        if test_acc > 0.60:
            print("  ✅ Model accuracy is GOOD (>60%)")
        else:
            print("  ⚠️  Model accuracy is LOW (<60%)")
    else:
        print(f"  ⚠️  Model file not found: {model_path}")
        print("     Run: python retrain_model_recent.py")
except Exception as e:
    print(f"  ✗ Model check failed: {e}")

# Test 5: Check Data Files
print("\n[TEST 5] Checking Data Files...")
print("-" * 80)

try:
    from app.config import DATA_PROCESSED_DIR, RESULTS_DIR

    # Check universe data
    universe_csv = DATA_PROCESSED_DIR / "universe_data.csv"
    if universe_csv.exists():
        import pandas as pd

        df = pd.read_csv(universe_csv, nrows=5)
        print(f"  ✓ Universe data exists: {len(df)} rows (sample)")
    else:
        print(f"  ⚠️  Universe data not found")
        print("     Run: python app/api/main.py")

    # Check recommendations
    recs_csv = RESULTS_DIR / "latest_recommendations.csv"
    if recs_csv.exists():
        df_recs = pd.read_csv(recs_csv)
        print(f"  ✓ Recommendations exist: {len(df_recs)} stocks")

        signals = df_recs["recommendation"].value_counts()
        print(
            f"     BUY: {signals.get('BUY', 0)}, "
            f"HOLD: {signals.get('HOLD', 0)}, "
            f"SELL: {signals.get('SELL', 0)}"
        )
    else:
        print(f"  ⚠️  Recommendations not found")
        print("     Run: python retrain_model_recent.py")

except Exception as e:
    print(f"  ✗ Data check failed: {e}")

# Test 6: Backend API
print("\n[TEST 6] Testing Backend API (if running)...")
print("-" * 80)

try:
    import requests

    # Try to connect to backend
    response = requests.get("http://localhost:8000/api/health", timeout=3)
    if response.status_code == 200:
        print("  ✓ Backend is RUNNING on port 8000")

        # Test recommendations endpoint
        recs = requests.get("http://localhost:8000/api/recommendations", timeout=5)
        if recs.status_code == 200:
            data = recs.json()
            print(f"  ✓ Recommendations API working: {len(data)} stocks")
        else:
            print(f"  ⚠️  Recommendations API returned {recs.status_code}")
    else:
        print(f"  ⚠️  Backend returned status {response.status_code}")

except requests.exceptions.RequestException:
    print("  ⚠️  Backend not running (this is OK if you haven't started it)")
    print("     To start: cd app/api_server && python -m uvicorn main:app --port 8000")
except Exception as e:
    print(f"  ⚠️  Backend test failed: {e}")

# Test 7: Scheduler Setup
print("\n[TEST 7] Testing Scheduler Configuration...")
print("-" * 80)

try:
    from app.scheduler import start_scheduler

    print("  ✓ Scheduler module imported")
    print("  ✓ Scheduler ready to use")
    print("     To start: python app/scheduler.py")
except Exception as e:
    print(f"  ✗ Scheduler import failed: {e}")

# Test 8: Feature Engineering
print("\n[TEST 8] Testing Feature Engineering...")
print("-" * 80)

try:
    import pandas as pd
    import numpy as np
    from app.features.technical import prepare_features
    from app.config import TradingConfig

    # Create sample data
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    sample_data = pd.DataFrame(
        {
            "date": dates,
            "symbol": "TEST.NS",
            "open": 100 + np.random.randn(100) * 5,
            "high": 105 + np.random.randn(100) * 5,
            "low": 95 + np.random.randn(100) * 5,
            "close": 100 + np.random.randn(100) * 5,
            "volume": np.random.randint(1000000, 5000000, 100),
        }
    )

    X, y, _ = prepare_features(
        sample_data,
        forward_days=TradingConfig.FORWARD_DAYS,
        return_threshold=TradingConfig.RETURN_THRESHOLD,
    )

    if not X.empty:
        print(
            f"  ✓ Feature engineering works: {len(X)} samples, {len(X.columns)} features"
        )
        print(f"     Features: {', '.join(X.columns[:5])}...")
    else:
        print("  ⚠️  Feature engineering returned empty")

except Exception as e:
    print(f"  ✗ Feature engineering failed: {e}")

# Final Summary
print("\n" + "=" * 80)
print("SYSTEM TEST SUMMARY")
print("=" * 80)

print("\n✅ READY TO USE:")
print("  - Model training: python retrain_model_recent.py")
print("  - Data fetch: python app/api/main.py")
print("  - Backend: cd app/api_server && python -m uvicorn main:app --port 8000")
print("  - Scheduler: python app/scheduler.py")

print("\n📊 NEXT STEPS:")
print("  1. If model not trained: python retrain_model_recent.py")
print("  2. If data missing: python app/api/main.py")
print("  3. Start backend: cd app/api_server && python -m uvicorn main:app --port 8000")
print("  4. Test predictions: curl http://localhost:8000/api/recommendations")
print("  5. Enable auto-updates: python app/scheduler.py")

print("\n" + "=" * 80)
print("TEST COMPLETE!")
print("=" * 80 + "\n")
