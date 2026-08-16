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
    print("=== Starting Module 3: Quantitative Analytics Engine (Multi-Horizon) ===")
    
    if not DB_PATH.exists():
        raise FileNotFoundError(f"[Error] Master database not found at {DB_PATH}")
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # ELITE PRO FIX: Native SQL CASE mapping + LEFT JOIN
    # Maps CME strings to exact Bloomberg strings. No silent fallbacks.
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
    conn.close()
    
    if df.empty:
        print("[Warning] No matched data returned from query.")
        return

    latest_date = df['trade_date'].iloc[0]
    print(f"  -> Locked Analytics Horizon to Latest Trade Date: {latest_date}")

    # HARD FAIL RISK CONTROL: Prevent silent VaR calculation if Volatility is missing
    if df['atm_vol'].isnull().any():
        missing_tenors = df[df['atm_vol'].isnull()]['tenor_type'].unique()
        raise ValueError(f"\n[CRITICAL RISK FAILURE] Missing Bloomberg Volatility data for CME tenors: {missing_tenors}.\nThe VaR model cannot run safely without accurate market data.")

    # NORMALIZATION CONTROL: If Bloomberg provides whole numbers (e.g., 22.68) instead of decimals (0.2268), divide by 100
    if df['atm_vol'].mean() > 1.0:
        df['atm_vol'] = df['atm_vol'] / 100.0
    # 1. Global USD Notional Calculation
    df['global_usd_notional'] = df['open_interest'] * CONTRACT_SIZE * df['strike_price']

    # 2. Multi-Horizon Wall Aggregation
    walls_df = df.groupby(['tenor_type', 'strike_price', 'option_type']).agg(
        total_open_interest=('open_interest', 'sum'),
        total_usd_notional=('global_usd_notional', 'sum')
    ).reset_index()

    walls_df = walls_df.sort_values(by=['tenor_type', 'total_usd_notional'], ascending=[True, False])
    walls_df.to_csv(OUTPUT_DIR / f"support_resistance_walls_{latest_date}.csv", index=False)
    
    # 3. Micro Portfolio Risk Calculations ($10M Mandate)
    total_global_notional = df['global_usd_notional'].sum()
    weighted_atm_vol = (df['atm_vol'] * df['global_usd_notional']).sum() / total_global_notional
    
    vol_1d = weighted_atm_vol * np.sqrt(1 / 252)
    vol_1w = weighted_atm_vol * np.sqrt(5 / 252)
    vol_1m = weighted_atm_vol * np.sqrt(21 / 252)

    Z_68 = 1.000
    Z_99 = 2.326

    dashboard_data = {
        "Metric": [
            "Macro: Global USD Notional ($)",
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
            f"${total_global_notional:,.0f}",
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

    print("\n" + "="*70)
    print(f"      EXECUTIVE RISK DASHBOARD (AS OF {latest_date})")
    print("="*70)
    for _, row in dashboard_df.iterrows():
        if row['Metric'].startswith("---"):
            print("-" * 70)
        else:
            print(f"  {row['Metric']:<48} : {row['Value']}")

    # 4. Console Executive Printout
    print("\n" + "="*70)
    print("      SEGMENTED STRUCTURAL WALLS BY EXPIRATION HORIZON")
    print("="*70)
    
    for tenor in walls_df['tenor_type'].unique():
        tenor_subset = walls_df[walls_df['tenor_type'] == tenor]
        top_calls = tenor_subset[tenor_subset['option_type'] == 'CALL'].head(2)
        top_puts = tenor_subset[tenor_subset['option_type'] == 'PUT'].head(2)
        
        print(f"\n[HORIZON: {tenor.strip().upper()}]")
        print("  -> Top Resistance (Call Walls):")
        for _, row in top_calls.iterrows():
            print(f"     Strike: {row['strike_price']:,.1f} | Notional: ${row['total_usd_notional']:,.0f}")
            
        print("  -> Top Support (Put Walls):")
        for _, row in top_puts.iterrows():
            print(f"     Strike: {row['strike_price']:,.1f} | Notional: ${row['total_usd_notional']:,.0f}")
            
    print("="*70 + "\n")

if __name__ == "__main__":
    run_analytics_engine()