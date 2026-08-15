"""
Master ETL Pipeline Orchestrator
Path: src/etl/run_pipeline.py

Sequentially initializes database schema, ingests spot price history,
and loads standardized CME option positioning data into gold_master.db.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.etl.init_database import init_db
from src.etl.load_historical_prices import load_historical_prices
from src.utils.db_warmup_check import run_db_diagnostic
from src.etl.load_cme_positioning import load_cme_options

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
    print("\n[Step 1/3] Initializing Database Schema...")
    init_db()

    # Step 2: Load Historical Spot Prices
    print("\n[Step 2/3] Loading Spot Price History...")
    try:
        load_historical_prices()
    except Exception as e:
        print(f"[ERROR] Historical price loading failed: {e}")
        return

    # Step 3: Load CME Options Positioning
    print("\n[Step 3/3] Loading CME Options Positioning...")
    try:
        load_cme_options()
    except Exception as e:
        print(f"[ERROR] CME Options loading failed: {e}")
        return

    # Post-Execution Audit
    print("\n" + "=" * 70)
    print("               RUNNING POST-ETL SANITY AUDIT")
    print("=" * 70)
    run_db_diagnostic()

if __name__ == "__main__":
    # Standard daily execution (does not delete existing data)
    execute_full_pipeline(rebuild_db=False)
