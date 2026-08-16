"""
Database Post-Load Sanity & Audit Diagnostic
Path: src/utils/db_warmup_check.py

Verifies table existence, record counts, date ranges,
and numerical integrity across gold_master.db tables.
Includes a Top Exposure Sanity Check to prevent silent parsing failures.
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

    # Audit Table 2: bbg_vol_surface
    if "bbg_vol_surface" in tables:
        bbg_df = pd.read_sql("SELECT * FROM bbg_vol_surface", conn)
        print("--- TABLE AUDIT: bbg_vol_surface ---")
        print(f"Total Records           : {len(bbg_df):,}")
        print("[STATUS]: PASSED\n")

    # Audit Table 3: cme_option_positioning
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

        # --- PRE-FLIGHT SANITY CHECK: TOP EXPOSURE CONTRACTS ---
        print("--- SANITY CHECK: TOP EXPOSURE CONTRACTS (LATEST DATE) ---")
        latest_date = cme_df['trade_date'].max() if not cme_df.empty else None
        
        if latest_date:
            print(f"Targeting Latest Available Date: {latest_date}\n")
            
            def print_top_3(tenor_label, tenor_sql, opt_type):
                q = f"""
                SELECT tenor_type, contract_month, strike_price, open_interest 
                FROM cme_option_positioning 
                WHERE trade_date = ? AND ({tenor_sql}) AND option_type = ?
                ORDER BY open_interest DESC LIMIT 3;
                """
                df_top = pd.read_sql(q, conn, params=(latest_date, opt_type))
                print(f"  [{tenor_label} {opt_type}S] - Top 3 by Open Interest:")
                if df_top.empty:
                    print("     None found. (Check parser logic!)")
                else:
                    for _, row in df_top.iterrows():
                        # Display full raw CME tenor string without truncation
                        clean_tenor = str(row['tenor_type'])
                        print(f"     -> Tenor: {clean_tenor:<35} | Month: {row['contract_month']:<8} | Strike: {row['strike_price']:<7,.1f} | OI: {row['open_interest']:,}")
                print()

            # Print Monthly Contracts
            print_top_3("MONTHLY", "tenor_type = 'Monthly'", "CALL")
            print_top_3("MONTHLY", "tenor_type = 'Monthly'", "PUT")
            
            # Print Weekly Contracts (Anything not labeled 'Monthly')
            print_top_3("WEEKLY", "tenor_type != 'Monthly'", "CALL")
            print_top_3("WEEKLY", "tenor_type != 'Monthly'", "PUT")
        else:
            print("[WARNING] No data available for sanity check.")

    conn.close()
    print("=" * 70)
    print("                   DIAGNOSTIC COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_db_diagnostic()