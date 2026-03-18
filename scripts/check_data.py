import pandas as pd

# Check data
df = pd.read_csv('data/processed/universe_data_regularized.csv')
print(f'Rows: {len(df)}')
print(f'Symbols: {df["Symbol"].nunique()}')
print(df.head())
