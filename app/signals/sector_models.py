"""
Sector-Specialized Model Manager
Trains and manages one ML model per market sector for higher accuracy.
Each sector model is trained on only the stocks in that sector,
so it learns sector-specific patterns (e.g., banking rate sensitivity,
pharma regulatory risk, tech earnings cycles).
"""
from pathlib import Path
import pickle
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.features.market_context import NIFTY_SECTOR_MAP, get_symbol_sector
from app.signals.ml_signals import MLSignalGenerator

logger = logging.getLogger(__name__)

# Path where sector models are saved
SECTOR_MODELS_DIR = Path(__file__).parent.parent.parent / "models" / "sector_models"

# Minimum samples required to train a dedicated sector model
MIN_SECTOR_SAMPLES = 100

# Sectors that benefit from aggressive (deeper) models
AGGRESSIVE_SECTORS = {"Banking", "Finance", "Infrastructure", "Auto", "Metals", "Energy"}


class SectorModelManager:
    """
    Manages per-sector ML models. Falls back to the global model
    if a sector does not have enough data for a dedicated model.
    """

    def __init__(
        self,
        global_model: Optional[MLSignalGenerator] = None,
        model_type: str = "ensemble",
        forward_days: int = 5,
        return_threshold: float = 0.02,
    ):
        self.global_model = global_model
        self.model_type = model_type
        self.forward_days = forward_days
        self.return_threshold = return_threshold
        self.sector_models: Dict[str, MLSignalGenerator] = {}
        self.sector_stats: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit_all_sectors(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        df_with_symbols: pd.DataFrame
    ) -> Dict[str, dict]:
        """
        Train one model per sector using the supplied feature matrix.
        Uses sector-specific hyperparameters for best accuracy.
        """
        SECTOR_MODELS_DIR.mkdir(parents=True, exist_ok=True)

        # Map each row to its sector
        symbols = df_with_symbols["symbol"].values
        sectors = np.array([get_symbol_sector(s) for s in symbols])
        unique_sectors = np.unique(sectors)

        results = {}

        for sector in unique_sectors:
            mask = sectors == sector
            n_samples = mask.sum()

            if n_samples < MIN_SECTOR_SAMPLES:
                logger.info(
                    f"[{sector}] Only {n_samples} samples — skipping (need {MIN_SECTOR_SAMPLES})"
                )
                results[sector] = {"skipped": True, "n_samples": int(n_samples)}
                continue

            logger.info(f"[{sector}] Training on {n_samples} samples...")
            X_sec = X[mask]
            y_sec = y[mask]

            # Sector-specific threshold: volatile sectors need wider thresholds
            sector_threshold = 0.025 if sector in AGGRESSIVE_SECTORS else self.return_threshold

            model = MLSignalGenerator(
                model_type=self.model_type,
                forward_days=self.forward_days,
                return_threshold=sector_threshold,
                use_risk_adjustment=False,
            )

            try:
                train_m, test_m = model.fit(X_sec, y_sec)
                self.sector_models[sector] = model

                sector_result = {
                    "n_samples": int(n_samples),
                    "train_accuracy": train_m["accuracy"],
                    "test_accuracy": test_m["accuracy"],
                    "test_f1": test_m["f1"],
                }
                self.sector_stats[sector] = sector_result
                results[sector] = sector_result

                # Save sector model to disk
                model_path = SECTOR_MODELS_DIR / f"{sector.lower().replace(' ', '_')}_model.pkl"
                model.save(str(model_path))
                logger.info(
                    f"[{sector}] Saved — test acc: {test_m['accuracy']:.2%}"
                )

            except Exception as e:
                logger.error(f"[{sector}] Training failed: {e}")
                results[sector] = {"error": str(e)}

        return results

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_symbol(
        self, symbol: str, X_row: pd.DataFrame
    ) -> Tuple[int, float]:
        """
        Generate signal for a single stock row using its sector model.
        Falls back to global model if no sector model exists.

        Returns:
            (signal, confidence) — signal is -1 / 0 / 1
        """
        sector = get_symbol_sector(symbol)
        model = self.sector_models.get(sector, self.global_model)

        if model is None:
            return 0, 0.5

        try:
            pred = model.predict(X_row)[0]
            proba = model.predict_proba(X_row)[0]
            confidence = float(np.max(proba))
            return int(pred), confidence
        except Exception as e:
            logger.warning(f"Prediction failed for {symbol}: {e}")
            return 0, 0.5

    def predict_batch(
        self, symbols: List[str], X: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict signals for a list of stocks.
        Routes each stock to its sector model (or global fallback).

        Returns:
            (signals array, confidences array)
        """
        signals = np.zeros(len(symbols), dtype=int)
        confidences = np.full(len(symbols), 0.5)

        for i, sym in enumerate(symbols):
            x_row = X.iloc[i : i + 1]
            sig, conf = self.predict_symbol(sym, x_row)
            signals[i] = sig
            confidences[i] = conf

        return signals, confidences

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load_all(
        cls, global_model: Optional[MLSignalGenerator] = None
    ) -> "SectorModelManager":
        """Load all saved sector models from disk."""
        manager = cls(global_model=global_model)

        if not SECTOR_MODELS_DIR.exists():
            logger.warning("No sector models directory found")
            return manager

        for model_file in SECTOR_MODELS_DIR.glob("*_model.pkl"):
            sector = model_file.stem.replace("_model", "").replace("_", " ").title()
            try:
                model = MLSignalGenerator.load(str(model_file))
                manager.sector_models[sector] = model
                logger.info(f"Loaded sector model: {sector}")
            except Exception as e:
                logger.warning(f"Failed to load {model_file.name}: {e}")

        return manager

    def summary(self) -> pd.DataFrame:
        """Return a summary DataFrame of all sector model accuracies."""
        rows = []
        for sector, stats in self.sector_stats.items():
            rows.append({
                "Sector": sector,
                "Samples": stats.get("n_samples", 0),
                "Train Acc": f"{stats.get('train_accuracy', 0):.2%}",
                "Test Acc": f"{stats.get('test_accuracy', 0):.2%}",
                "Test F1": f"{stats.get('test_f1', 0):.2%}",
                "Status": "Skipped" if stats.get("skipped") else ("Error" if "error" in stats else "OK"),
            })
        return pd.DataFrame(rows).sort_values("Test Acc", ascending=False) if rows else pd.DataFrame()
