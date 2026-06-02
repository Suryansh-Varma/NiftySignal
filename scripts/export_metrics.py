"""
Export model metrics to tmp_metrics.json.
Shows BOTH global model accuracy and sector-weighted accuracy.
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.signals.ml_signals import MLSignalGenerator


def compute_weighted_sector_accuracy():
    """Compute weighted-average accuracy from all trained sector models."""
    stats_path = Path("results/sector_model_stats.json")
    if not stats_path.exists():
        return None, {}

    with open(stats_path) as f:
        stats = json.load(f)

    total_weight = 0
    weighted_sum = 0
    sector_accs = {}

    for sector, data in stats.items():
        if data.get("skipped") or "test_accuracy" not in data:
            continue
        n = data["n_samples"]
        acc = data["test_accuracy"]
        weighted_sum += acc * n
        total_weight += n
        sector_accs[sector] = {
            "samples": n,
            "test_accuracy": round(acc, 4),
            "test_f1": round(data.get("test_f1", 0), 4),
        }

    if total_weight == 0:
        return None, {}

    weighted_avg = weighted_sum / total_weight
    return weighted_avg, sector_accs


def check_model_metrics():
    model_path = Path("models/trading_model.pkl")
    if not model_path.exists():
        print("Model file not found")
        return

    model = MLSignalGenerator.load(str(model_path))
    train_metrics = model.training_metrics or {}
    test_metrics = model.test_metrics or {}

    global_test_acc = test_metrics.get("accuracy", 0)
    global_train_acc = train_metrics.get("accuracy", 0)
    report = test_metrics.get("classification_report", {})

    # Sector-weighted accuracy
    weighted_avg, sector_accs = compute_weighted_sector_accuracy()

    results = {
        "model_type": model.model_type,
        "train_accuracy": global_train_acc,
        "test_accuracy": global_test_acc,
        "sector_weighted_accuracy": round(weighted_avg, 4) if weighted_avg else None,
        "report": report,
        "sector_breakdown": sector_accs,
    }

    with open("tmp_metrics.json", "w") as f:
        json.dump(results, f, indent=4)

    print("=== NiftySignal Model Accuracy ===")
    print(f"Global Model Test Accuracy:   {global_test_acc:.2%}")
    if weighted_avg:
        print(f"Sector-Weighted Accuracy:     {weighted_avg:.2%}  ← TRUE overall acc")
        print()
        print("Per-Sector Breakdown:")
        for sec, d in sorted(sector_accs.items(), key=lambda x: -x[1]["test_accuracy"]):
            bar = "█" * int(d["test_accuracy"] * 20)
            print(f"  {sec:28s}: {d['test_accuracy']:.2%}  {bar}")
    print()
    print("Metrics written to tmp_metrics.json")


if __name__ == "__main__":
    check_model_metrics()
