"""
Phase 3.2: Flow Velocity (Delta OI & Premium Cash Tracker)
Path: src/advanced_analytics/flow_velocity.py

Tracks institutional capital velocity by measuring the Delta in Open Interest (OI)
between T_0 and T_-1. Estimates the actual Premium Cash deployed or extracted.
"""

import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import norm
from pathlib import Path

# ------------------------------------------------------------------------------
# Configuration & Paths
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

CONTRACT_SIZE = 100
RISK_FREE_RATE = 0.05

def calculate_black_scholes_premium(S0: float, K: float, T: float, sigma: float, option_type: str, r: float = RISK_FREE_RATE) -> float:
    T = np.maximum(T, 1e-5)
    sigma = np.maximum(sigma, 1e-5)
    d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type.upper() == 'CALL':
        premium = S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        premium = K * np.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)
    return np.maximum(premium, 0.0)

def calculate_flow_velocity():
    print("=" * 115)
    print("      PHASE 3.2: INSTITUTIONAL FLOW VELOCITY (DELTA OI & CAPITAL DEPLOYMENT RADAR)")
    print("=" * 115)

    conn = sqlite3.connect(DB_PATH)

    # 1. Temporal Bounds & Spot Price
    dates_df = pd.read_sql("SELECT DISTINCT trade_date FROM cme_option_positioning ORDER BY trade_date DESC LIMIT 2", conn)
    spot_df = pd.read_sql("SELECT close_price FROM historical_spot_prices ORDER BY trade_date DESC LIMIT 1", conn)
    S0 = float(spot_df.iloc[0]['close_price'])
    
    t0_date = dates_df.iloc[0]['trade_date']
    t1_date = dates_df.iloc[1]['trade_date']
    
    print(f"[1/3] Locked Temporal Horizons: T_0 ({t0_date}) vs T_-1 ({t1_date}) | Spot: ${S0:,.2f}")

    # 2. Extract Data & Join Volatility
    query = f"""
    SELECT c.trade_date, c.tenor_type, c.contract_month, UPPER(c.option_type) as option_type, 
           c.strike_price, c.open_interest, COALESCE(b.atm_vol, 0.15) as atm_vol
    FROM cme_option_positioning c
    LEFT JOIN bbg_vol_surface b ON 
        CASE 
            WHEN c.tenor_type LIKE '%Weekly%' THEN '1 Week'
            WHEN c.tenor_type = 'Monthly' THEN '1 Month'
            ELSE 'Unknown'
        END = b.tenor_type
    WHERE c.trade_date IN ('{t0_date}', '{t1_date}')
    """
    df_raw = pd.read_sql(query, conn)
    conn.close()

    if df_raw['atm_vol'].mean() > 1.0:
        df_raw['atm_vol'] = df_raw['atm_vol'] / 100.0

    print("[2/3] Executing Multi-Index Matrix Join & Black-Scholes Estimation...")
    
    # 3. Calculate DTE and Unit Premium
    current_dt = pd.to_datetime(t0_date)
    df_raw['contract_dt'] = pd.to_datetime(df_raw['contract_month'], format='%b %y', errors='coerce') + pd.Timedelta(days=14)
    df_raw['dte'] = np.maximum((df_raw['contract_dt'] - current_dt).dt.days, 1)
    df_raw['T'] = df_raw['dte'] / 365.0
    
    df_raw['unit_premium'] = df_raw.apply(
        lambda r: calculate_black_scholes_premium(S0, r['strike_price'], r['T'], r['atm_vol'], r['option_type']), axis=1
    )

    df_t0 = df_raw[df_raw['trade_date'] == t0_date].copy()
    df_t1 = df_raw[df_raw['trade_date'] == t1_date].copy()

    index_cols = ['tenor_type', 'contract_month', 'option_type', 'strike_price', 'unit_premium']
    df_t0 = df_t0.set_index(index_cols)
    df_t1 = df_t1.set_index(index_cols)

    flow_df = df_t0[['open_interest']].join(df_t1[['open_interest']], lsuffix='_t0', rsuffix='_t1', how='left')
    flow_df['open_interest_t1'] = flow_df['open_interest_t1'].fillna(0)
    flow_df['delta_oi'] = flow_df['open_interest_t0'] - flow_df['open_interest_t1']
    flow_df = flow_df.reset_index()
    
    flow_df['flow_usd_notional'] = flow_df['delta_oi'] * CONTRACT_SIZE * flow_df['strike_price']
    flow_df['flow_premium_cash'] = flow_df['delta_oi'] * CONTRACT_SIZE * flow_df['unit_premium']
    
    flow_df = flow_df[flow_df['delta_oi'] != 0].copy()
    flow_df.sort_values(by='flow_premium_cash', ascending=False).to_csv(OUTPUT_DIR / f"flow_velocity_{t0_date}.csv", index=False)
    print(f"[3/3] Exported Velocity matrix to: outputs/flow_velocity_{t0_date}.csv")

    def print_flow_table(df_subset, title, ascending_sort):
        print(f"\n[ {title} ]")
        if df_subset.empty:
            print("  No significant flow detected.")
            return
            
        df_sorted = df_subset.sort_values(by='flow_premium_cash', ascending=ascending_sort).head(5)
        header = f"{'Bucket':<30} | {'Type':<4} | {'Strike':>9} | {'Delta OI':>10} | {'Flow Notional':>17} | {'Flow Premium Cash':>19}"
        print(header)
        print("-" * len(header))
        
        for _, row in df_sorted.iterrows():
            bucket = f"{row['tenor_type']} - {row['contract_month']}"[:29]
            opt = row['option_type']
            strike = f"{row['strike_price']:,.1f}"
            delta_oi = f"+{row['delta_oi']:,.0f}" if row['delta_oi'] > 0 else f"{row['delta_oi']:,.0f}"
            not_val = row['flow_usd_notional']
            notional = f"+${not_val:,.0f}" if not_val > 0 else f"-${abs(not_val):,.0f}"
            prem_val = row['flow_premium_cash']
            premium = f"+${prem_val:,.0f}" if prem_val > 0 else f"-${abs(prem_val):,.0f}"
            
            print(f"{bucket:<30} | {opt:<4} | {strike:>9} | {delta_oi:>10} | {notional:>17} | {premium:>19}")

    calls_df = flow_df[flow_df['option_type'] == 'CALL']
    puts_df = flow_df[flow_df['option_type'] == 'PUT']

    print("\n" + "=" * 115)
    print_flow_table(calls_df, "TOP 5 CALL ACCUMULATION (NEW MONEY DEPLOYED)", ascending_sort=False)
    print_flow_table(puts_df, "TOP 5 PUT ACCUMULATION (NEW HEDGES DEPLOYED)", ascending_sort=False)
    print_flow_table(calls_df, "TOP 5 CALL DISTRIBUTION (CASH EXTRACTED / POSITIONS CLOSED)", ascending_sort=True)
    print_flow_table(puts_df, "TOP 5 PUT COVERING (CASH EXTRACTED / POSITIONS CLOSED)", ascending_sort=True)
    print("=" * 115 + "\n")

if __name__ == "__main__":
    calculate_flow_velocity()