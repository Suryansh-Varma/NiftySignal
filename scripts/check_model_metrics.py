import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.signals.ml_signals import MLSignalGenerator


def check_model_metrics():
    model_path = Path("models/trading_model.pkl")
    if not model_path.exists():
        print(f"Model file not found at {model_path}")
        return

    model = MLSignalGenerator.load(str(model_path))

    print(f"Model Type: {model.model_type}")

    train_metrics = model.training_metrics
    if train_metrics:
        print(f"Training Accuracy: {train_metrics.get('accuracy', 0):.2%}")

    test_metrics = model.test_metrics
    if test_metrics:
        print(f"Test Accuracy: {test_metrics.get('accuracy', 0):.2%}")

        # Detailed report
        report = test_metrics.get("classification_report")
        if report:
            print("\nClassification Report (Test Set):")
            for label, metrics in report.items():
                if isinstance(metrics, dict):
                    print(
                        f"  {label:10s}: Precision: {metrics.get('precision', 0):.2%}, Recall: {metrics.get('recall', 0):.2%}, F1: {metrics.get('f1-score', 0):.2%}"
                    )


if __name__ == "__main__":
    check_model_metrics()
