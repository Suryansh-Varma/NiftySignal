import pandas as pd
from pathlib import Path

csv_path = Path('results/trades.csv')
if csv_path.exists():
    df = pd.read_csv(csv_path)
    # Take last 500 trades for a better sample
    recent = df.tail(500)
    # Column is lowercase 'roi'
    wins = len(recent[recent['roi'] > 0])
    accuracy = (wins / len(recent)) * 100
    avg_roi = recent['roi'].mean()
    print(f"Recent Accuracy (Win Rate): {accuracy:.2f}%")
    print(f"Average ROI of last 500 trades: {avg_roi:.4%}")
else:
    print("results/trades.csv not found")
