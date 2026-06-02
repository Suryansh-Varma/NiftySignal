from pathlib import Path
import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    AdaBoostClassifier,
    GradientBoostingClassifier,
    ExtraTreesClassifier,
    VotingClassifier,
    StackingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# XGBoost — best-in-class for tabular financial data
try:
    from xgboost import XGBClassifier as _XGBClassifier

    XGBOOST_AVAILABLE = True
except ImportError:
    _XGBClassifier = None
    XGBOOST_AVAILABLE = False
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

from app.features.risk_factors import (
    RiskFactorCalculator,
    adjust_signal_by_risk,
    normalize_predictions_with_risk,
)


class MLSignalGenerator:
    def __init__(
        self,
        feature_columns: Optional[List[str]] = None,
        forward_days: int = 5,
        return_threshold: float = 0.02,
        test_size: float = 0.2,
        random_state: int = 42,
        model_type: str = "random_forest",
        use_risk_adjustment: bool = True,
    ) -> None:
        """
        ML-based trading signal generator with risk adjustment.

        Args:
            feature_columns: List of feature column names to use for training
            forward_days: Number of days to look ahead for returns
            return_threshold: Return threshold for buy/sell signals
            test_size: Fraction of data to use for testing
            random_state: Random seed for reproducibility
            model_type: Type of model - "random_forest", "adaboost", or "gradient_boost"
            use_risk_adjustment: Whether to adjust signals using risk factors
        """
        self.feature_columns = feature_columns
        self.forward_days = forward_days
        self.return_threshold = return_threshold
        self.test_size = test_size
        self.random_state = random_state
        self.model_type = model_type
        self.use_risk_adjustment = use_risk_adjustment

        # Initialize model based on type
        if model_type == "adaboost":
            self.model = AdaBoostClassifier(
                n_estimators=100, learning_rate=0.8, random_state=random_state
            )
        elif model_type == "gradient_boost":
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=3,
                min_samples_split=20,
                subsample=0.8,
                random_state=random_state,
            )
        elif model_type == "extra_trees":
            self.model = ExtraTreesClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                class_weight="balanced",
                random_state=random_state,
            )
        elif model_type == "ensemble":
            rf = RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                min_samples_split=20,
                min_samples_leaf=10,
                class_weight="balanced",
                random_state=random_state,
            )
            gb = GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                random_state=random_state,
            )
            et = ExtraTreesClassifier(
                n_estimators=200,
                max_depth=12,
                min_samples_split=20,
                min_samples_leaf=10,
                class_weight="balanced",
                random_state=random_state,
            )
            base_estimators = [("rf", rf), ("gb", gb), ("et", et)]

            # Add XGBoost if available (best single model for tabular data)
            if XGBOOST_AVAILABLE and _XGBClassifier is not None:
                xgb = _XGBClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=5,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    use_label_encoder=False,
                    eval_metric="mlogloss",
                    random_state=random_state,
                    verbosity=0,
                )
                base_estimators.append(("xgb", xgb))

            self.model = StackingClassifier(
                estimators=base_estimators,
                final_estimator=LogisticRegression(
                    C=1.0, max_iter=1000, solver="lbfgs"
                ),
                passthrough=False,
                cv=3,
            )
        else:  # random_forest (default)
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                class_weight="balanced",
                random_state=random_state,
            )

        self.scaler = StandardScaler()
        self.risk_calculator = RiskFactorCalculator(lookback_period=30)

        self.is_fitted = False
        self.feature_importance_ = None
        self.training_metrics = None
        self.test_metrics = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Tuple[dict, dict]:
        """
        Train the model and return performance metrics.
        """
        # Save feature column names for future predictions
        self.feature_columns = list(X.columns)

        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            shuffle=False,  # Keep temporal order
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True

        # Get feature importance
        model_importances = getattr(self.model, "feature_importances_", None)
        if model_importances is not None:
            self.feature_importance_ = dict(zip(X.columns, model_importances))
        elif hasattr(self.model, "estimators_"):
            # For ensembles like VotingClassifier, average feature importances from base estimators if they exist
            importances = []
            for est in self.model.estimators_:
                est_importances = getattr(est, "feature_importances_", None)
                if est_importances is not None:
                    importances.append(est_importances)

            if importances:
                avg_importance = np.mean(importances, axis=0)
                self.feature_importance_ = dict(zip(X.columns, avg_importance))
            else:
                self.feature_importance_ = {col: 0.0 for col in X.columns}
        else:
            self.feature_importance_ = {col: 0.0 for col in X.columns}

        # Get predictions
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)

        # Calculate detailed metrics
        train_metrics = {
            "accuracy": accuracy_score(y_train, y_pred_train),
            "precision": precision_score(
                y_train, y_pred_train, average="weighted", zero_division=0
            ),
            "recall": recall_score(
                y_train, y_pred_train, average="weighted", zero_division=0
            ),
            "f1": f1_score(y_train, y_pred_train, average="weighted", zero_division=0),
            "classification_report": classification_report(
                y_train, y_pred_train, output_dict=True
            ),
            "confusion_matrix": confusion_matrix(y_train, y_pred_train).tolist(),
        }

        test_metrics = {
            "accuracy": accuracy_score(y_test, y_pred_test),
            "precision": precision_score(
                y_test, y_pred_test, average="weighted", zero_division=0
            ),
            "recall": recall_score(
                y_test, y_pred_test, average="weighted", zero_division=0
            ),
            "f1": f1_score(y_test, y_pred_test, average="weighted", zero_division=0),
            "classification_report": classification_report(
                y_test, y_pred_test, output_dict=True
            ),
            "confusion_matrix": confusion_matrix(y_test, y_pred_test).tolist(),
        }

        # Store metrics
        self.training_metrics = train_metrics
        self.test_metrics = test_metrics

        return train_metrics, test_metrics

    def _align_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Internal helper to ensure X matches fitted feature names and order."""
        if hasattr(self.scaler, "feature_names_in_"):
            expected = self.scaler.feature_names_in_
            # If it's a DataFrame, just reorder and drop extra columns
            if isinstance(X, pd.DataFrame):
                # Check for missing columns
                missing = set(expected) - set(X.columns)
                if missing:
                    for col in missing:
                        X[col] = 0.0
                return X[expected]
        return X

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate trading signals for new data.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_aligned = self._align_features(X)
        X_scaled = self.scaler.transform(X_aligned)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities for each class.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_aligned = self._align_features(X)
        X_scaled = self.scaler.transform(X_aligned)
        return np.asarray(self.model.predict_proba(X_scaled))

    def predict_with_risk(
        self, X: pd.DataFrame, risk_factors: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate trading signals adjusted by risk factors.

        Args:
            X: Feature dataframe
            risk_factors: Risk factor array (0-1 scale). If None, no adjustment applied.

        Returns:
            Adjusted predictions and adjusted confidence scores
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")

        X_aligned = self._align_features(X)
        X_scaled = self.scaler.transform(X_aligned)
        predictions = self.model.predict(X_scaled)
        probabilities = np.asarray(self.model.predict_proba(X_scaled))

        if risk_factors is not None and self.use_risk_adjustment:
            # Map class labels to indices: -1 -> 0, 0 -> 1, 1 -> 2
            class_map = {-1: 0, 0: 1, 1: 2}
            reverse_map = {0: -1, 1: 0, 2: 1}

            adjusted_preds = []
            adjusted_confs = []

            for i in range(len(predictions)):
                pred_signal = predictions[i]
                pred_prob = float(np.max(probabilities[i]))
                risk = risk_factors[i] if i < len(risk_factors) else 0.5

                adj_signal, adj_conf = adjust_signal_by_risk(
                    pred_signal, pred_prob, risk
                )

                adjusted_preds.append(adj_signal)
                adjusted_confs.append(adj_conf)

            return np.array(adjusted_preds), np.array(adjusted_confs)

        # Return max probability as confidence if no risk adjustment
        confidences = np.max(probabilities, axis=1)
        return predictions, confidences

    def save(self, path: str) -> None:
        """
        Save the trained model to disk.

        Args:
            path: File path to save the model
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before saving")

        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "scaler": self.scaler,
                    "feature_columns": self.feature_columns,
                    "forward_days": self.forward_days,
                    "return_threshold": self.return_threshold,
                    "is_fitted": self.is_fitted,
                    "feature_importance_": self.feature_importance_,
                    "model_type": self.model_type,
                    "training_metrics": self.training_metrics,
                    "test_metrics": self.test_metrics,
                    "use_risk_adjustment": self.use_risk_adjustment,
                },
                f,
            )

    @classmethod
    def load(cls, path: str) -> "MLSignalGenerator":
        """Load a trained model from disk."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
        except ModuleNotFoundError as e:
            missing_mod = getattr(e, "name", "unknown")
            raise RuntimeError(
                f"Unable to load model because dependency '{missing_mod}' is missing. "
                "Install the dependency used during training (for example, 'pip install xgboost') "
                "or retrain the model in the current environment."
            ) from e

        instance = cls(
            feature_columns=data["feature_columns"],
            forward_days=data["forward_days"],
            return_threshold=data["return_threshold"],
            model_type=data.get("model_type", "random_forest"),
            use_risk_adjustment=data.get("use_risk_adjustment", True),
        )

        instance.model = data["model"]
        instance.scaler = data["scaler"]
        instance.is_fitted = data["is_fitted"]
        instance.feature_importance_ = data["feature_importance_"]
        instance.training_metrics = data.get("training_metrics")
        instance.test_metrics = data.get("test_metrics")

        return instance

    def get_comparison_summary(self) -> Dict:
        """
        Get a comparison summary of model performance.

        Returns:
            Dictionary with model type and key metrics
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before getting comparison summary")

        test_metrics: Dict[str, Any] = self.test_metrics or {}
        training_metrics: Dict[str, Any] = self.training_metrics or {}

        return {
            "model_type": self.model_type,
            "test_accuracy": test_metrics.get("accuracy", 0),
            "test_precision": test_metrics.get("precision", 0),
            "test_recall": test_metrics.get("recall", 0),
            "test_f1": test_metrics.get("f1", 0),
            "train_accuracy": training_metrics.get("accuracy", 0),
            "train_f1": training_metrics.get("f1", 0),
        }
