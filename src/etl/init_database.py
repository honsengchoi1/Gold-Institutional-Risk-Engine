"""
Database Initialization Module
Path: src/etl/init_database.py
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: CME Options Positioning Data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cme_option_positioning (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT NOT NULL,
        tenor_type TEXT NOT NULL,
        contract_month TEXT NOT NULL,
        option_type TEXT NOT NULL,
        strike_price REAL NOT NULL,
        open_interest INTEGER NOT NULL,
        volume INTEGER NOT NULL,
        usd_notional REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(trade_date, tenor_type, contract_month, option_type, strike_price)
    );
    """)

    # Table 2: Historical Spot Prices (Data Warehouse Persistence)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historical_spot_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT UNIQUE NOT NULL,
        open_price REAL NOT NULL,
        high_price REAL NOT NULL,
        low_price REAL NOT NULL,
        close_price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 3: Bloomberg Volatility Surface
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bbg_vol_surface (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenor_type TEXT UNIQUE NOT NULL,
        atm_vol REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print(f"[Success] Database initialized with core tables at {DB_PATH}")

if __name__ == "__main__":
    init_db()