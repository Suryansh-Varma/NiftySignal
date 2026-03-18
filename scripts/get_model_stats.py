import pandas as pd
from pathlib import Path

def get_stats():
    csv_path = Path('results/trades.csv')
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        recent = df.tail(100)
        # Check if 'roi' column exists
        if 'roi' in recent.columns:
            wins = len(recent[recent['roi'] > 0])
            accuracy = (wins / len(recent)) * 100
            avg_roi = recent['roi'].mean()
            print(f"--- RECENT TRADE PERFORMANCE (Last 100) ---")
            print(f"Win Rate: {accuracy:.2f}%")
            print(f"Average ROI: {avg_roi:.4%}")
        else:
            print("Column 'roi' not found in trades.csv")
        
    rec_path = Path('results/latest_recommendations.csv')
    if rec_path.exists():
        rdf = pd.read_csv(rec_path)
        if 'confidence' in rdf.columns:
            avg_conf = rdf['confidence'].mean()
            print(f"\n--- CURRENT MODEL STATS (March 2026) ---")
            print(f"Average Signal Confidence: {avg_conf:.2%}")
        else:
            print("Column 'confidence' not found in latest_recommendations.csv")

if __name__ == "__main__":
    get_stats()
