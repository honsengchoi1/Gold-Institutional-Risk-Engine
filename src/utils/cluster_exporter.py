"""
Utility: Options Cluster & Anomaly Checker
Path: src/utils/cluster_exporter.py

Dumps a human-readable CSV of the latest trade date's options data.
Pre-calculates Notional and OI Share Percentages for manual Excel auditing.
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def export_cluster_check():
    print("=== EXPORTING CLUSTER CHECK DIAGNOSTIC ===")
    
    if not DB_PATH.exists():
        print(f"[Error] Master database not found at {DB_PATH}")
        return
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Extract only the latest date's data to prevent double-counting
    query = """
    SELECT 
        trade_date,
        tenor_type,
        contract_month,
        UPPER(option_type) as option_type,
        strike_price,
        open_interest,
        usd_notional
    FROM cme_option_positioning
    WHERE trade_date = (SELECT MAX(trade_date) FROM cme_option_positioning)
      AND open_interest > 0
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("[Warning] No data found in the database.")
        return

    latest_date = df['trade_date'].iloc[0]
    
    # 1. Create a unified maturity column (e.g., "Monthly - DEC 26")
    df['maturity_bucket'] = df['tenor_type'] + " - " + df['contract_month']
    
    # 2. Calculate the Expiration OI Share (The "Whale" Metric)
    bucket_totals = df.groupby('maturity_bucket')['open_interest'].sum().reset_index()
    bucket_totals = bucket_totals.rename(columns={'open_interest': 'bucket_total_oi'})
    
    df = df.merge(bucket_totals, on='maturity_bucket')
    df['oi_share_pct'] = (df['open_interest'] / df['bucket_total_oi']) * 100
    
    # 3. Clean up the final DataFrame for Excel readability
    export_cols = [
        'maturity_bucket',
        'option_type',
        'strike_price',
        'open_interest',
        'usd_notional',
        'oi_share_pct'
    ]
    df_export = df[export_cols].copy()
    
    # 4. Sort by absolute largest USD Notional descending
    df_export = df_export.sort_values(by=['usd_notional', 'oi_share_pct'], ascending=[False, False])
    
    # Format the float columns for cleaner CSV viewing (optional but helpful)
    df_export['usd_notional'] = df_export['usd_notional'].round(0)
    df_export['oi_share_pct'] = df_export['oi_share_pct'].round(2)
    
    out_path = OUTPUT_DIR / f"cluster_check_{latest_date}.csv"
    df_export.to_csv(out_path, index=False)
    
    print(f"[Success] Cluster check file exported for Trade Date: {latest_date}")
    print(f"  -> Total Strike Rows : {len(df_export):,}")
    print(f"  -> Saved To          : {out_path}")
    print("\nYou can now open this CSV in Excel to manually filter and inspect raw positioning clusters.")

if __name__ == "__main__":
    export_cluster_check()