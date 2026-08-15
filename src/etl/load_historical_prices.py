"""
Historical Spot Price Loader
Path: src/etl/load_historical_prices.py
"""

import pandas as pd
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data_raw" / "historical_gold_data.csv"
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"

def load_historical_prices():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"[Error] Target file missing: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip().capitalize() for c in df.columns]

    # Clean and reformat columns
    df['Trade_date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    df = df.rename(columns={
        'Open': 'open_price',
        'High': 'high_price',
        'Low': 'low_price',
        'Close': 'close_price'
    })

    db_df = df[['Trade_date', 'open_price', 'high_price', 'low_price', 'close_price']].copy()
    db_df = db_df.rename(columns={'Trade_date': 'trade_date'})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Idempotent insert or replace
    cursor.executemany("""
    INSERT OR REPLACE INTO historical_spot_prices (trade_date, open_price, high_price, low_price, close_price)
    VALUES (?, ?, ?, ?, ?)
    """, db_df.values.tolist())

    conn.commit()
    conn.close()
    print(f"[Success] Loaded {len(db_df)} historical price records into gold_master.db")

if __name__ == "__main__":
    load_historical_prices()
