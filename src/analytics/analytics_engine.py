"""
Analytics Engine Module (Phase 2.2 - Institutional Horizon Slicing)
Author: Quantitative Analytics & Risk Management
Path: src/analytics/analytics_engine.py

Segments CME Options Open Interest and Notional walls across distinct
liquidity horizons (Weekly, Monthly, Long-Term Macro) and outputs structured reports.
Always filters for the LATEST available trade date to prevent OI double-counting.
Strict Risk Protocol: Fails execution if Bloomberg Volatility mapping is incomplete.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Suppress pandas chained assignment warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

PORTFOLIO_NOTIONAL = 10_000_000
CONTRACT_SIZE = 100            

def run_analytics_engine():
    print("=== GOLD QUANTITATIVE RISK & POSITIONING ENGINE ===")
    
    if not DB_PATH.exists():
        raise FileNotFoundError(f"[Error] Master database not found at {DB_PATH}")
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # ELITE PRO FIX: Native SQL CASE mapping + LEFT JOIN
    query = """
    WITH mapped_cme AS (
        SELECT 
            trade_date,
            tenor_type,
            contract_month,
            UPPER(option_type) as option_type,
            strike_price,
            open_interest,
            volume,
            CASE 
                WHEN tenor_type LIKE '%Weekly%' THEN '1 Week'
                WHEN tenor_type = 'Monthly' THEN '1 Month'
                ELSE 'Unknown'
            END as bbg_join_key
        FROM cme_option_positioning
        WHERE trade_date = (SELECT MAX(trade_date) FROM cme_option_positioning)
          AND open_interest > 0
    )
    SELECT 
        c.trade_date,
        c.tenor_type,
        c.contract_month,
        c.option_type,
        c.strike_price,
        c.open_interest,
        c.volume,
        b.atm_vol
    FROM mapped_cme c
    LEFT JOIN bbg_vol_surface b ON c.bbg_join_key = b.tenor_type;
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Extract Spot Price for the Math Filter (S_0)
    spot_query = "SELECT close_price FROM historical_spot_prices WHERE trade_date = (SELECT MAX(trade_date) FROM historical_spot_prices)"
    spot_df = pd.read_sql_query(spot_query, conn)
    conn.close()
    
    if df.empty:
        print("[Warning] No matched data returned from query.")
        return
        
    if spot_df.empty:
        raise ValueError("[CRITICAL RISK FAILURE] Missing Spot Price data in historical_spot_prices table.")

    current_spot = float(spot_df.iloc[0]['close_price'])
    latest_date = df['trade_date'].iloc[0]
    print(f"  -> Locked Analytics Horizon to Latest Trade Date: {latest_date}")
    print(f"  -> Baseline Spot Price (S_0): ${current_spot:,.2f}")

    # STRATEGIC TIME FILTER: Strip out long-dated monthlies (> 4 months away)
    current_dt = pd.to_datetime(latest_date)
    df['contract_dt'] = pd.to_datetime(df['contract_month'], format='%b %y', errors='coerce')
    
    time_mask = (~df['tenor_type'].str.contains('Monthly', case=False, na=False)) | (df['contract_dt'] <= current_dt + pd.DateOffset(months=4))
    df = df[time_mask].copy()

    # HARD FAIL RISK CONTROL
    if df['atm_vol'].isnull().any():
        missing_tenors = df[df['atm_vol'].isnull()]['tenor_type'].unique()
        raise ValueError(f"\n[CRITICAL RISK FAILURE] Missing Bloomberg Volatility data for CME tenors: {missing_tenors}.\nThe VaR model cannot run safely without accurate market data.")

    # NORMALIZATION CONTROL
    if df['atm_vol'].mean() > 1.0:
        df['atm_vol'] = df['atm_vol'] / 100.0
        
    # 1. Global USD Notional Calculation
    df['global_usd_notional'] = df['open_interest'] * CONTRACT_SIZE * df['strike_price']

    # 2. Micro Portfolio Risk Calculations ($10M Mandate)
    total_global_notional = df['global_usd_notional'].sum()
    weighted_atm_vol = (df['atm_vol'] * df['global_usd_notional']).sum() / total_global_notional
    
    vol_1d = weighted_atm_vol * np.sqrt(1 / 252)
    vol_1w = weighted_atm_vol * np.sqrt(5 / 252)
    vol_1m = weighted_atm_vol * np.sqrt(21 / 252)

    Z_68 = 1.000
    Z_99 = 2.326

    dashboard_data = {
        "Metric": [
            "Macro: Volume-Weighted Implied Vol (Annual)",
            "----------------------------------------",
            "Portfolio: Base Notional Exposure",
            "Portfolio: 1-Day Operational Variance (68%)",
            "Portfolio: 1-Day Black Swan VaR (99%)",
            "Portfolio: 1-Week Operational Variance (68%)",
            "Portfolio: 1-Week Black Swan VaR (99%)",
            "Portfolio: 1-Month Operational Variance (68%)",
            "Portfolio: 1-Month Black Swan VaR (99%)"
        ],
        "Value": [
            f"{weighted_atm_vol * 100:.2f}%",
            "",
            f"${PORTFOLIO_NOTIONAL:,.0f}",
            f"${PORTFOLIO_NOTIONAL * Z_68 * vol_1d:,.2f}",
            f"${PORTFOLIO_NOTIONAL * Z_99 * vol_1d:,.2f}",
            f"${PORTFOLIO_NOTIONAL * Z_68 * vol_1w:,.2f}",
            f"${PORTFOLIO_NOTIONAL * Z_99 * vol_1w:,.2f}",
            f"${PORTFOLIO_NOTIONAL * Z_68 * vol_1m:,.2f}",
            f"${PORTFOLIO_NOTIONAL * Z_99 * vol_1m:,.2f}"
        ]
    }

    dashboard_df = pd.DataFrame(dashboard_data)
    dashboard_df.to_csv(OUTPUT_DIR / f"executive_risk_dashboard_{latest_date}.csv", index=False)

    # 3. Apply 4-Sigma Math Boundary
    df['expiration_bucket'] = df['tenor_type'] + ' - ' + df['contract_month']
    upper_bound = current_spot * (1 + (vol_1m * 4))
    lower_bound = current_spot * (1 - (vol_1m * 4))
    df_filtered = df[(df['strike_price'] >= lower_bound) & (df['strike_price'] <= upper_bound)].copy()
    
    # Aggregate Walls for Tabular HUD
    bucket_totals = df_filtered.groupby('expiration_bucket')['open_interest'].sum().reset_index()
    bucket_totals = bucket_totals.rename(columns={'open_interest': 'bucket_total_oi'})
    
    walls_df = df_filtered.groupby(['expiration_bucket', 'strike_price', 'option_type']).agg(
        total_open_interest=('open_interest', 'sum'),
        total_usd_notional=('global_usd_notional', 'sum')
    ).reset_index()
    
    walls_df = walls_df.merge(bucket_totals, on='expiration_bucket')
    walls_df['oi_share_pct'] = (walls_df['total_open_interest'] / walls_df['bucket_total_oi']) * 100

    # 4. Global Strike Gravity Export (The "Valley" Map)
    global_gravity_df = df_filtered.groupby(['strike_price', 'option_type']).agg(
        total_open_interest=('open_interest', 'sum'),
        total_usd_notional=('global_usd_notional', 'sum')
    ).reset_index()
    total_horizon_oi = global_gravity_df['total_open_interest'].sum()
    global_gravity_df['global_oi_share_pct'] = (global_gravity_df['total_open_interest'] / total_horizon_oi) * 100
    global_gravity_df = global_gravity_df.sort_values(by=['total_usd_notional'], ascending=[False])
    global_gravity_df.to_csv(OUTPUT_DIR / f"global_strike_gravity_{latest_date}.csv", index=False)

    # 5. Console Executive Printout (Risk Dashboard)
    print("\n" + "="*105)
    print(f"      EXECUTIVE RISK DASHBOARD (AS OF {latest_date})")
    print("="*105)
    for _, row in dashboard_df.iterrows():
        if row['Metric'].startswith("---"):
            print("-" * 105)
        else:
            print(f"  {row['Metric']:<48} : {row['Value']}")

    # 6. PM Tabular HUD Printout
    print("\n" + "="*105)
    print("      TACTICAL HUD: TOP 10 STRIKES BY USD NOTIONAL (4-SIGMA & 4-MONTH HORIZON)")
    print("="*105)
    
    monthly_mask = walls_df['expiration_bucket'].str.contains('MONTHLY', case=False, na=False)
    monthly_walls = walls_df[monthly_mask]
    weekly_walls = walls_df[~monthly_mask]

    def print_pm_table(df_subset, title):
        print(f"\n[ {title} ]")
        if df_subset.empty:
            print("  No data available for this horizon.")
            return
            
        df_sorted = df_subset.sort_values(by='total_usd_notional', ascending=False).head(10)
        
        header = f"{'Maturity Bucket':<40} | {'Type':<4} | {'Strike':>9} | {'Open Interest':>13} | {'USD Notional':>18} | {'OI Share %':>10}"
        print(header)
        print("-" * len(header))
        
        for _, row in df_sorted.iterrows():
            mat = str(row['expiration_bucket'])[:39]
            opt = row['option_type']
            strike = f"{row['strike_price']:,.1f}"
            oi = f"{row['total_open_interest']:,.0f}"
            notional = f"${row['total_usd_notional']:,.0f}"
            share = f"{row['oi_share_pct']:.2f}%"
            
            print(f"{mat:<40} | {opt:<4} | {strike:>9} | {oi:>13} | {notional:>18} | {share:>10}")

    print_pm_table(monthly_walls[monthly_walls['option_type'] == 'CALL'], "TOP 10 MONTHLY CALLS")
    print_pm_table(monthly_walls[monthly_walls['option_type'] == 'PUT'], "TOP 10 MONTHLY PUTS")
    print_pm_table(weekly_walls[weekly_walls['option_type'] == 'CALL'], "TOP 10 WEEKLY CALLS")
    print_pm_table(weekly_walls[weekly_walls['option_type'] == 'PUT'], "TOP 10 WEEKLY PUTS")
    print("="*105 + "\n")

if __name__ == "__main__":
    run_analytics_engine()