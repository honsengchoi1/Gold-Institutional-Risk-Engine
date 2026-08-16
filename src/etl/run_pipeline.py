"""
Master ETL Pipeline Orchestrator
Path: src/etl/run_pipeline.py

Sequentially initializes database schema, ingests spot price history,
extracts raw CME Excel files, and loads standardized CME option positioning data into gold_master.db.
"""

import sys
from pathlib import Path

# 1. Inject Project Root into Python's Path FIRST
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# 2. NOW import the project modules
from src.etl.init_database import init_db
from src.etl.load_historical_prices import load_historical_prices
from src.etl.extract_cme_options import main as extract_cme_data
from src.etl.load_cme_positioning import load_cme_options
from src.etl.load_bbg_vol import load_bbg_volatility
from src.utils.db_warmup_check import run_db_diagnostic

def execute_full_pipeline(rebuild_db: bool = False):
    print("=" * 70)
    print("         XAU POSITIONING PIPELINE: MASTER ETL EXECUTION")
    print("=" * 70)

    db_file = PROJECT_ROOT / "data_processed" / "gold_master.db"

    # Defensive Guard 1: Optional Fresh Rebuild
    if rebuild_db and db_file.exists():
        print("[WARNING] Rebuild requested. Removing existing gold_master.db...")
        db_file.unlink()

    # Step 1: Initialize Database Schemas
    print("\n[Step 1/5] Initializing Database Schema...")
    init_db()

    # Step 2: Load Historical Spot Prices
    print("\n[Step 2/5] Loading Spot Price History...")
    try:
        load_historical_prices()
    except Exception as e:
        print(f"[ERROR] Historical price loading failed: {e}")
        return

    # Step 3: Extract & Transform Raw CME Excel Files
    print("\n[Step 3/5] Extracting & Staging Raw CME Options Data...")
    try:
        extract_cme_data()
    except Exception as e:
        print(f"[ERROR] CME Options extraction failed: {e}")
        return

    # Step 4: Load Standardized CME Options Positioning
    print("\n[Step 4/5] Loading Staged CME Options into Database...")
    try:
        load_cme_options()
    except Exception as e:
        print(f"[ERROR] CME Options loading failed: {e}")
        return

    # Step 5: Load Bloomberg Volatility Surface
    print("\n[Step 5/5] Loading Bloomberg Volatility Surface...")
    try:
        load_bbg_volatility()
    except Exception as e:
        print(f"[ERROR] BBG Vol loading failed: {e}")
        return

    # Post-Execution Audit
    print("\n" + "=" * 70)
    print("               RUNNING POST-ETL SANITY AUDIT")
    print("=" * 70)
    run_db_diagnostic()

if __name__ == "__main__":
    # WARNING: Set to True for this run ONLY to rebuild the new database schemas
    execute_full_pipeline(rebuild_db=True)