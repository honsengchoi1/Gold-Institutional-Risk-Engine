"""
CME Options Positioning Loader
Path: src/etl/load_cme_positioning.py

Ingests standardized CME staging CSVs into the gold_master.db database.
Uses strict INSERT OR IGNORE logic to prevent data duplication.
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
STAGING_CSV = PROJECT_ROOT / "data_processed" / "staging" / "cme_voi_latest.csv"

def load_cme_options():
    print(f"=== Running CME Options Loader ===")
   
    if not DB_PATH.exists():
        raise FileNotFoundError(f"[Error] Database missing at {DB_PATH}. Run init_database.py first.")
    if not STAGING_CSV.exists():
        raise FileNotFoundError(f"[Error] Staging file missing at {STAGING_CSV}.")

    df = pd.read_csv(STAGING_CSV)
   
    # Format DataFrame for DB insertion
    db_df = df[['trade_date', 'tenor', 'contract_month', 'option_type', 'strike', 'open_interest', 'volume', 'usd_notional']].copy()
    db_df = db_df.rename(columns={'tenor': 'tenor_type', 'strike': 'strike_price'})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # IDEMPOTENCY LOCK: INSERT OR IGNORE prevents duplicates based on the UNIQUE index
    cursor.executemany("""
    INSERT OR IGNORE INTO cme_option_positioning (
        trade_date, tenor_type, contract_month, option_type, strike_price, open_interest, volume, usd_notional
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, db_df.values.tolist())

    conn.commit()
    conn.close()
   
    print(f"[Success] Processed {len(db_df)} records from staging into cme_option_positioning table.")

if __name__ == "__main__":
    load_cme_options()

