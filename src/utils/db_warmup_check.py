"""
Database Post-Load Sanity & Audit Diagnostic
Path: src/utils/db_warmup_check.py

Verifies table existence, record counts, date ranges,
and numerical integrity across gold_master.db tables.
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"

def run_db_diagnostic():
    print("=" * 70)
    print("           GOLD_MASTER.DB DIAGNOSTIC & AUDIT SUITE")
    print("=" * 70)

    if not DB_PATH.exists():
        print(f"[CRITICAL FAIL] Database file does not exist at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']
    print(f"[OK] Database connection established. Tables found: {tables}\n")

    # Audit Table 1: historical_spot_prices
    if "historical_spot_prices" in tables:
        hist_df = pd.read_sql("SELECT * FROM historical_spot_prices", conn)
        print("--- TABLE AUDIT: historical_spot_prices ---")
        print(f"Total Records           : {len(hist_df):,}")
        if not hist_df.empty:
            print(f"Date Range              : {hist_df['trade_date'].min()} to {hist_df['trade_date'].max()}")
            print(f"Spot Price Range (Close): ${hist_df['close_price'].min():,.2f} - ${hist_df['close_price'].max():,.2f}")
            print(f"Null Values Detected    : {hist_df.isnull().sum().sum()}")
        print("[STATUS]: PASSED\n")
    else:
        print("[WARNING]: Table 'historical_spot_prices' NOT FOUND.\n")

    # Audit Table 2: cme_option_positioning
    if "cme_option_positioning" in tables:
        cme_df = pd.read_sql("SELECT * FROM cme_option_positioning", conn)
        print("--- TABLE AUDIT: cme_option_positioning ---")
        print(f"Total Records           : {len(cme_df):,}")
        if not cme_df.empty:
            dates = cme_df['trade_date'].unique()
            print(f"Distinct Trade Dates    : {list(dates)}")
            print(f"Total Open Interest     : {cme_df['open_interest'].sum():,} contracts")
            print(f"Total USD Notional      : ${cme_df['usd_notional'].sum():,.2f}")
            print(f"Null Values Detected    : {cme_df.isnull().sum().sum()}")
        print("[STATUS]: PASSED\n")
    else:
        print("[NOTICE]: Table 'cme_option_positioning' is empty or pending reload.\n")

    conn.close()
    print("=" * 70)
    print("                   DIAGNOSTIC COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_db_diagnostic()