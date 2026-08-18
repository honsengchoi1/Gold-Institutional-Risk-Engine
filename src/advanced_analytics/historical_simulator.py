# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 14:37:18 2026

@author: hchoi
"""

"""
Phase 3.1: Historical Replay & Monte Carlo Simulator
Path: src/advanced_analytics/historical_simulator.py

Extracts historical spot prices from SQLite, calculates log returns to derive
drift and volatility, and simulates 10,000 forward paths using Geometric Brownian Motion.
Outputs multi-horizon VaR (Value at Risk) to outputs/.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. Configuration & Paths
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NOTIONAL_USD = 10_000_000  # $10M Book
SIMULATION_PATHS = 10_000  # Institutional Standard

# ------------------------------------------------------------------------------
# 2. Data Extraction & Parameter Calibration
# ------------------------------------------------------------------------------
def fetch_historical_prices() -> pd.DataFrame:
    """Pulls historical spot prices from gold_master.db."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"[Error] Database missing at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    query = "SELECT trade_date, close_price FROM historical_spot_prices ORDER BY trade_date ASC"
    df = pd.read_sql(query, conn)
    conn.close()
   
    if df.empty:
        raise ValueError("[Error] historical_spot_prices table is empty.")
       
    return df

def calibrate_gbm_parameters(df: pd.DataFrame):
    """Calculates daily log returns, drift, and volatility."""
    # Log Returns: ln(P_t / P_{t-1})
    df['log_return'] = np.log(df['close_price'] / df['close_price'].shift(1))
    df = df.dropna()
   
    daily_volatility = df['log_return'].std()
    daily_drift = df['log_return'].mean()
   
    latest_price = df['close_price'].iloc[-1]
    latest_date = df['trade_date'].iloc[-1]
   
    return latest_price, latest_date, daily_drift, daily_volatility

# ------------------------------------------------------------------------------
# 3. Vectorized Monte Carlo Engine (Geometric Brownian Motion)
# ------------------------------------------------------------------------------
def run_monte_carlo(S0: float, mu: float, sigma: float, days: int) -> np.ndarray:
    """
    Executes vectorized GBM simulation.
    Formula: S_T = S_0 * exp((mu - 0.5 * sigma^2)*T + sigma * sqrt(T) * Z)
    """
    # Generate random standard normal variables for 10,000 paths
    Z = np.random.standard_normal(SIMULATION_PATHS)
   
    # Calculate simulated prices at day T
    simulated_prices = S0 * np.exp((mu - 0.5 * sigma**2) * days + sigma * np.sqrt(days) * Z)
    return simulated_prices

def calculate_var_metrics(simulated_prices: np.ndarray, current_price: float, horizon_name: str) -> dict:
    """Calculates Portfolio PnL and VaR thresholds."""
    # Convert prices to Portfolio PnL
    pct_changes = (simulated_prices - current_price) / current_price
    pnl_distribution = pct_changes * NOTIONAL_USD
   
    # Calculate Risk Thresholds (Lower Tail)
    var_68 = np.percentile(pnl_distribution, 100 - 68)  # Operational Variance
    var_95 = np.percentile(pnl_distribution, 100 - 95)  # Active Trading Risk
    var_99 = np.percentile(pnl_distribution, 100 - 99)  # Black Swan Tail Risk
   
    return {
        'Horizon': horizon_name,
        'Expected_Price_Mean': np.mean(simulated_prices),
        'Operational_VaR_68': var_68,
        'Trading_VaR_95': var_95,
        'Black_Swan_VaR_99': var_99
    }

# ------------------------------------------------------------------------------
# 4. Master Execution
# ------------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("      PHASE 3.1: VECTORIZED MONTE CARLO SIMULATOR (10,000 PATHS)")
    print("=" * 70)
    
    # 1. Fetch & Calibrate
    print("[1/3] Calibrating Stochastic Parameters from SQLite...")
    df = fetch_historical_prices()
    S0, last_date, mu, sigma = calibrate_gbm_parameters(df)
    
    print(f"  -> Latest Date    : {last_date}")
    print(f"  -> Spot Price     : ${S0:,.2f}")
    print(f"  -> Daily Drift (u): {mu:.6f}")
    print(f"  -> Daily Vol (o)  : {sigma:.6f}")
    
    # 2. Run Simulations
    print(f"\n[2/3] Executing {SIMULATION_PATHS:,} GBM Paths via NumPy...")
    
    # UPDATED: Added file-friendly suffixes for the CSV exports
    horizons = {
        '1-Day': (1, '1D'),
        '1-Week (5d)': (5, '1W'),
        '1-Month (21d)': (21, '1M')
    }
    
    results = []
    # UPDATED: Unpacking the tuple to get days and file_suffix
    for name, (days, file_suffix) in horizons.items():
        sim_prices = run_monte_carlo(S0, mu, sigma, days)
        metrics = calculate_var_metrics(sim_prices, S0, name)
        results.append(metrics)
        
        # === THE NEW PATCH: Exporting Raw Paths for Visualization Engine ===
        pd.DataFrame({'simulated_price': sim_prices}).to_csv(
            OUTPUT_DIR / f"simulated_paths_{file_suffix}.csv", index=False
        )
        # ===================================================================
        
    # 3. Save & Report
    print("\n[3/3] Generating Executive Risk Dashboard...")
    results_df = pd.DataFrame(results)
    
    output_file = OUTPUT_DIR / "historical_mc_simulation_report.csv"
    results_df.to_csv(output_file, index=False)
    
    print("\n" + "-" * 70)
    print(f"PORTFOLIO RISK ($10M NOTIONAL) - BENCHMARKED AT {last_date}")
    print("-" * 70)
    for index, row in results_df.iterrows():
        print(f"Horizon: {row['Horizon'].ljust(15)} | 95% VaR: ${row['Trading_VaR_95']:,.2f}")
    
    print("-" * 70)
    print(f"[Success] Full report saved to: {output_file}")
    print(f"[Success] Raw distribution arrays saved to outputs/simulated_paths_*.csv")
    print("=" * 70)

if __name__ == "__main__":
    main()