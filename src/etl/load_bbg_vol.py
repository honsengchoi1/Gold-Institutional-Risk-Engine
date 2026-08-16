"""
Bloomberg Volatility Surface Loader
Path: src/etl/load_bbg_vol.py
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
BBG_CSV = PROJECT_ROOT / "data_raw" / "bbg_vol_surface.csv"

def load_bbg_volatility():
    print("\n[Step 5/5] Loading Bloomberg Volatility Surface...")
    if not BBG_CSV.exists():
        print(f"[Warning] BBG Vol file missing at {BBG_CSV}. Skipping.")
        return

    df = pd.read_csv(BBG_CSV)
    df.columns = [c.strip() for c in df.columns]
    
    # Rename assuming your raw CSV has 'Tenor' and 'ATM_Vol' headers
    if 'Tenor' in df.columns:
        df = df.rename(columns={'Tenor': 'tenor_type'})
    if 'ATM_Vol' in df.columns:
        df = df.rename(columns={'ATM_Vol': 'atm_vol'})
        
    # Clean percentage strings (e.g., '14.5%' -> 0.145) if necessary
    if df['atm_vol'].dtype == 'O':
        df['atm_vol'] = df['atm_vol'].str.replace('%', '').astype(float) / 100

    db_df = df[['tenor_type', 'atm_vol']].copy()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executemany("""
    INSERT OR REPLACE INTO bbg_vol_surface (tenor_type, atm_vol)
    VALUES (?, ?);
    """, db_df.values.tolist())

    conn.commit()
    conn.close()
    print(f"[Success] Loaded {len(db_df)} Volatility records into bbg_vol_surface table.")

if __name__ == "__main__":
    load_bbg_volatility()