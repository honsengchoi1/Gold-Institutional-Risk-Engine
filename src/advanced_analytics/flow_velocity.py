"""
Phase 3.2: Flow Velocity (Delta OI Tracker)
Path: src/advanced_analytics/flow_velocity.py

Tracks the velocity of institutional capital by measuring the Delta in Open Interest (OI)
between the latest trading session (T_0) and the previous session (T_-1).
Identifies massive accumulation (new positions) and distribution/covering (closed positions).
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ------------------------------------------------------------------------------
# Configuration & Paths
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_SIZE = 100

def calculate_flow_velocity():
    print("=" * 105)
    print("      PHASE 3.2: INSTITUTIONAL FLOW VELOCITY (DELTA OI RADAR)")
    print("=" * 105)

    if not DB_PATH.exists():
        raise FileNotFoundError(f"[Error] Database missing at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    # 1. Identify the two most recent distinct trade dates
    dates_query = "SELECT DISTINCT trade_date FROM cme_option_positioning ORDER BY trade_date DESC LIMIT 2"
    dates_df = pd.read_sql(dates_query, conn)
    
    if len(dates_df) < 2:
        raise ValueError("[Error] Need at least 2 distinct trade dates in the database to calculate Flow Velocity.")

    t0_date = dates_df.iloc[0]['trade_date']
    t1_date = dates_df.iloc[1]['trade_date']
    
    print(f"[1/3] Locked Temporal Horizons:")
    print(f"  -> T_0 (Current)  : {t0_date}")
    print(f"  -> T_-1 (Previous): {t1_date}\n")

    # 2. Extract Data for these exact dates
    data_query = f"""
    SELECT trade_date, tenor_type, contract_month, UPPER(option_type) as option_type, strike_price, open_interest
    FROM cme_option_positioning
    WHERE trade_date IN ('{t0_date}', '{t1_date}')
    """
    df_raw = pd.read_sql(data_query, conn)
    conn.close()

    print("[2/3] Executing Multi-Index Matrix Join for Delta Match...")
    
    # Split into T0 and T1 dataframes
    df_t0 = df_raw[df_raw['trade_date'] == t0_date].copy()
    df_t1 = df_raw[df_raw['trade_date'] == t1_date].copy()

    # Set Multi-Index for perfect alignment
    index_cols = ['tenor_type', 'contract_month', 'option_type', 'strike_price']
    df_t0 = df_t0.set_index(index_cols)
    df_t1 = df_t1.set_index(index_cols)

    # Join T0 against T1
    # We use a LEFT join from T0. If a contract existed in T-1 but expired/vanished in T0, 
    # it drops out of the active radar naturally.
    flow_df = df_t0[['open_interest']].join(df_t1[['open_interest']], lsuffix='_t0', rsuffix='_t1', how='left')
    
    # If a strike was opened today (didn't exist yesterday), fill T1 OI with 0
    flow_df['open_interest_t1'] = flow_df['open_interest_t1'].fillna(0)
    
    # 3. Calculate Core Velocity Metrics
    flow_df['delta_oi'] = flow_df['open_interest_t0'] - flow_df['open_interest_t1']
    
    # Extract strike_price from the index to calculate notional
    strikes = flow_df.index.get_level_values('strike_price')
    flow_df['flow_usd_notional'] = flow_df['delta_oi'] * CONTRACT_SIZE * strikes
    
    # Reset index to flatten the dataframe for easy sorting and exporting
    flow_df = flow_df.reset_index()
    
    # Filter out zero-flow rows to reduce noise
    flow_df = flow_df[flow_df['delta_oi'] != 0].copy()

    # 4. Export the Raw Velocity Radar Map
    output_file = OUTPUT_DIR / f"flow_velocity_{t0_date}.csv"
    flow_df.sort_values(by='flow_usd_notional', ascending=False).to_csv(output_file, index=False)
    print(f"[3/3] Exported full Flow Velocity matrix to: outputs/flow_velocity_{t0_date}.csv")

    # 5. PM Terminal Printout (Tactical HUD)
    print("\n" + "=" * 105)
    print("      TACTICAL HUD: HIGHEST VELOCITY STRIKES (T-0 vs T-1)")
    print("=" * 105)

    def print_flow_table(df_subset, title, ascending_sort):
        print(f"\n[ {title} ]")
        if df_subset.empty:
            print("  No significant flow detected.")
            return
            
        # Sort by flow_usd_notional. 
        # ascending=False gets Top Positive (Accumulation). ascending=True gets Top Negative (Distribution)
        df_sorted = df_subset.sort_values(by='flow_usd_notional', ascending=ascending_sort).head(5)
        
        header = f"{'Bucket':<30} | {'Type':<4} | {'Strike':>9} | {'T_0 OI':>8} | {'Delta OI':>10} | {'Flow Notional (USD)':>22}"
        print(header)
        print("-" * len(header))
        
        for _, row in df_sorted.iterrows():
            bucket = f"{row['tenor_type']} - {row['contract_month']}"[:29]
            opt = row['option_type']
            strike = f"{row['strike_price']:,.1f}"
            t0_oi = f"{row['open_interest_t0']:,.0f}"
            
            # Format Delta OI with +/- signs
            delta_oi_val = row['delta_oi']
            delta_oi = f"+{delta_oi_val:,.0f}" if delta_oi_val > 0 else f"{delta_oi_val:,.0f}"
            
            # Format Flow Notional with +/- signs
            notional_val = row['flow_usd_notional']
            notional = f"+${notional_val:,.0f}" if notional_val > 0 else f"-${abs(notional_val):,.0f}"
            
            print(f"{bucket:<30} | {opt:<4} | {strike:>9} | {t0_oi:>8} | {delta_oi:>10} | {notional:>22}")

    # Isolate Calls and Puts
    calls_df = flow_df[flow_df['option_type'] == 'CALL']
    puts_df = flow_df[flow_df['option_type'] == 'PUT']

    # Print Top Accumulation (Positive Flow)
    print_flow_table(calls_df, "TOP 5 CALL ACCUMULATION (NEW MONEY LONGS)", ascending_sort=False)
    print_flow_table(puts_df, "TOP 5 PUT ACCUMULATION (NEW MONEY SHORTS / HEDGES)", ascending_sort=False)
    
    # Print Top Distribution/Covering (Negative Flow)
    print_flow_table(calls_df, "TOP 5 CALL DISTRIBUTION (CLOSED POSITIONS)", ascending_sort=True)
    print_flow_table(puts_df, "TOP 5 PUT COVERING (CLOSED POSITIONS)", ascending_sort=True)
    print("=" * 105 + "\n")

if __name__ == "__main__":
    calculate_flow_velocity()