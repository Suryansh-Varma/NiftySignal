"""
Background Scheduler for NiftySignal - Automates Daily Updates & Weekly Retraining

This scheduler runs in the background and automatically:
1. Fetches latest market data daily at 6 PM IST (after market closes)
2. Retrains the model weekly on Sundays at 8 PM IST
3. Logs all activities for monitoring

Usage:
    python app/scheduler.py

To run in background (Linux/Mac):
    nohup python app/scheduler.py > logs/scheduler.log 2>&1 &

To run as Windows service:
    Use NSSM or Task Scheduler to run this script on startup
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import subprocess
import sys
from pathlib import Path
import logging
import os

from app.scripts.auto_update_macro_risk import compute_and_update as auto_update_macro_risk
from app.scripts.generate_recommendations import generate as generate_recommendations

# Set up logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_FETCH_SCRIPT = BASE_DIR / "app" / "api" / "main.py"
RETRAIN_SCRIPT = BASE_DIR / "retrain_model_recent.py"
ASSEMBLE_SCRIPT = BASE_DIR / "app" / "scripts" / "assemble_universe.py"


def fetch_daily_data():
    """
    Fetch latest market data and update universe CSV.
    Runs daily at 6 PM IST (after NSE market closes at 3:30 PM).
    """
    logger.info("="*70)
    logger.info("DAILY DATA FETCH STARTED")
    logger.info("="*70)
    
    try:
        # Step 1: Fetch latest data from yfinance/nselib
        logger.info("Step 1: Fetching latest market data...")
        result = subprocess.run(
            [sys.executable, str(DATA_FETCH_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        if result.returncode != 0:
            logger.error(f"Data fetch failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
        
        logger.info("Data fetch completed successfully")
        logger.info(f"Output: {result.stdout[-500:]}")  # Last 500 chars
        
        # Step 2: Assemble universe data
        logger.info("Step 2: Assembling universe data...")
        result = subprocess.run(
            [sys.executable, str(ASSEMBLE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode != 0:
            logger.warning(f"Assembly step failed: {result.stderr}")
            # Not critical, continue
        else:
            logger.info("Universe data assembled successfully")
        
        logger.info("="*70)
        logger.info("DAILY DATA FETCH COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Data fetch timed out (>10 minutes)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during daily data fetch: {e}", exc_info=True)
        return False


def retrain_model_weekly():
    """
    Retrain the model with latest 6-month data.
    Runs weekly on Sundays at 8 PM IST.
    """
    logger.info("="*70)
    logger.info("WEEKLY MODEL RETRAINING STARTED")
    logger.info("="*70)
    
    try:
        logger.info("Retraining model with recent 6-month data...")
        
        result = subprocess.run(
            [sys.executable, str(RETRAIN_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes max
        )
        
        if result.returncode != 0:
            logger.error(f"Model retraining failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
        
        logger.info("Model retraining completed successfully")
        
        # Log key metrics from output
        output = result.stdout
        if "Test accuracy:" in output or "NEW MODEL ACCURACY:" in output:
            # Extract accuracy info
            for line in output.split('\n'):
                if 'accuracy' in line.lower() or 'BUY:' in line or 'SELL:' in line:
                    logger.info(f"  {line.strip()}")
        
        logger.info("="*70)
        logger.info("WEEKLY MODEL RETRAINING COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Model retraining timed out (>30 minutes)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during model retraining: {e}", exc_info=True)
        return False

def update_macro_risk():
    """
    Fetch live VIX, gold, oil, FX data and rewrite macro_risk_factor.json.
    Runs daily at 6:30 PM IST (30 minutes after market data fetch).
    """
    logger.info("="*70)
    logger.info("DAILY MACRO RISK AUTO-UPDATE STARTED")
    logger.info("="*70)
    try:
        result = auto_update_macro_risk(dry_run=False)
        logger.info(
            f"Macro risk updated: {result['adjusted_risk_factor']:.4f} "
            f"({result['risk_level']}) "
            f"[VIX={result['raw_market_data'].get('india_vix')}, "
            f"Gold={result['raw_market_data'].get('gold_usd')}, "
            f"Oil={result['raw_market_data'].get('crude_oil_usd')}, "
            f"USDINR={result['raw_market_data'].get('usd_inr')}]"
        )
        logger.info("="*70)
        logger.info("DAILY MACRO RISK AUTO-UPDATE COMPLETED")
        logger.info("="*70)
        return True
    except Exception as e:
        logger.error(f"Macro risk update failed: {e}", exc_info=True)
        return False


def generate_daily_recommendations():
    """
    Generate fresh recommendations CSV from trained model + latest prices.
    Runs daily at 6:45 PM IST (after data fetch + macro risk update).
    """
    logger.info("="*70)
    logger.info("DAILY RECOMMENDATION GENERATION STARTED")
    logger.info("="*70)
    try:
        summary = generate_recommendations(dry_run=False)
        logger.info(
            f"Recommendations generated: {summary['total']} symbols — "
            f"BUY={summary['BUY']} HOLD={summary['HOLD']} SELL={summary['SELL']} "
            f"accuracy={summary['model_accuracy']} risk={summary['macro_risk']:.4f}"
        )
        logger.info("="*70)
        logger.info("DAILY RECOMMENDATION GENERATION COMPLETED")
        logger.info("="*70)
        return True
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}", exc_info=True)
        return False



    """
    Test run all jobs manually (for debugging).
    """
    logger.info("\n" + "="*70)
    logger.info("MANUAL TEST RUN - EXECUTING ALL JOBS")
    logger.info("="*70 + "\n")

    logger.info("Testing macro risk auto-update...")
    update_macro_risk()

    logger.info("\nTesting daily data fetch...")
    fetch_daily_data()

    logger.info("\nTesting recommendation generation...")
    generate_daily_recommendations()

    logger.info("\nTesting weekly model retraining...")
    retrain_model_weekly()

    logger.info("\n" + "="*70)
    logger.info("MANUAL TEST COMPLETED")
    logger.info("="*70 + "\n")


def start_scheduler():
    """
    Start the background scheduler with all jobs configured.
    """
    logger.info("\n" + "="*70)
    logger.info("NIFTYSIGNAL BACKGROUND SCHEDULER STARTING")
    logger.info("="*70)
    
    # Run macro risk update immediately on startup so the JSON is always fresh
    logger.info("Running startup macro risk update...")
    try:
        update_macro_risk()
    except Exception as e:
        logger.warning(f"Startup macro risk update failed (non-critical): {e}")

    # Create scheduler
    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
    
    # Schedule daily data fetch at 6:00 PM IST (after market closes)
    scheduler.add_job(
        fetch_daily_data,
        trigger=CronTrigger(hour=18, minute=0, timezone='Asia/Kolkata'),
        id='daily_data_fetch',
        name='Daily Market Data Fetch',
        replace_existing=True,
        max_instances=1
    )

    # Schedule macro risk auto-update at 6:30 PM IST (after data fetch)
    scheduler.add_job(
        update_macro_risk,
        trigger=CronTrigger(hour=18, minute=30, timezone='Asia/Kolkata'),
        id='daily_macro_risk_update',
        name='Daily Macro Risk Auto-Update',
        replace_existing=True,
        max_instances=1
    )

    # NEW: Intraday risk monitoring - runs every 15 mins during market hours (9:00 - 16:00)
    scheduler.add_job(
        update_macro_risk,
        trigger=CronTrigger(hour='9-16', minute='0,15,30,45', timezone='Asia/Kolkata'),
        id='intraday_risk_monitor',
        name='15-Minute Market Risk Monitor',
        replace_existing=True,
        max_instances=1
    )
    
    # Schedule recommendation generation at 6:45 PM IST
    # (after macro risk update at 6:30 PM)
    scheduler.add_job(
        generate_daily_recommendations,
        trigger=CronTrigger(hour=18, minute=45, timezone='Asia/Kolkata'),
        id='daily_recs_generate',
        name='Daily Recommendation Generation',
        replace_existing=True,
        max_instances=1
    )

    # Schedule weekly retraining on Sunday at 8:00 PM IST
    scheduler.add_job(
        retrain_model_weekly,
        trigger=CronTrigger(day_of_week='sun', hour=20, minute=0, timezone='Asia/Kolkata'),
        id='weekly_model_retrain',
        name='Weekly Model Retraining',
        replace_existing=True,
        max_instances=1
    )
    
    # Start scheduler
    scheduler.start()
    
    logger.info("\nScheduler started successfully!")
    logger.info("\nScheduled Jobs:")
    logger.info("  1. Daily Data Fetch")
    logger.info("     - Time: Every day at 6:00 PM IST")
    logger.info("     - Action: Fetch latest market data from yfinance/nselib")
    logger.info("     - Duration: ~5-10 minutes")
    logger.info("")
    logger.info("  2. Weekly Model Retraining")
    logger.info("     - Time: Every Sunday at 8:00 PM IST")
    logger.info("     - Action: Retrain model with latest 6-month data")
    logger.info("     - Duration: ~10-20 minutes")
    logger.info("")
    logger.info("Next scheduled runs:")
    
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        logger.info(f"  - {job.name}: {next_run}")
    
    logger.info("\n" + "="*70)
    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    logger.info("Logs are written to: logs/scheduler.log")
    logger.info("="*70 + "\n")
    
    return scheduler


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='NiftySignal Background Scheduler')
    parser.add_argument('--test', action='store_true', help='Run a test of all jobs immediately')
    args = parser.parse_args()
    
    if args.test:
        # Test mode - run jobs immediately
        test_run_all()
    else:
        # Normal mode - start scheduler
        scheduler = start_scheduler()
        
        try:
            # Keep script running
            import time
            while True:
                time.sleep(60)  # Check every minute
        except (KeyboardInterrupt, SystemExit):
            logger.info("\nShutting down scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler stopped.")
