"""
Phase 3.3: Dealer Gamma Exposure (GEX) Engine - Sliced Horizons
Path: src/advanced_analytics/gex_engine.py
"""

import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import norm
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data_processed" / "gold_master.db"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

CONTRACT_SIZE = 100
RISK_FREE_RATE = 0.05

def calculate_black_scholes_gamma(S, K, T, sigma, r=RISK_FREE_RATE):
    T = np.maximum(T, 1e-5)
    sigma = np.maximum(sigma, 1e-5)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))

def analyze_gex_horizon(df_subset, S0, title):
    if df_subset.empty:
        return
        
    gex_by_strike = df_subset.groupby('strike_price')['dollar_gex_1pct'].sum().reset_index()
    total_gex = gex_by_strike['dollar_gex_1pct'].sum()
    
    call_wall_strike = gex_by_strike.loc[gex_by_strike['dollar_gex_1pct'].idxmax()]['strike_price']
    put_wall_strike = gex_by_strike.loc[gex_by_strike['dollar_gex_1pct'].idxmin()]['strike_price']
    
    regime = "STABILIZING (Sell Rips/Buy Dips)" if total_gex > 0 else "AMPLIFYING (Buy Rips/Sell Dips)"
    
    print(f"\n[ {title} ]")
    print(f"  -> Market Regime  : {regime}")
    print(f"  -> Total GEX Flow : ${total_gex:,.0f}")
    print(f"  -> Call Wall (Res): ${call_wall_strike:,.1f}")
    print(f"  -> Put Wall (Sup) : ${put_wall_strike:,.1f}")
    print("-" * 80)
    
    gex_by_strike['abs_gex'] = gex_by_strike['dollar_gex_1pct'].abs()
    top_strikes = gex_by_strike.sort_values('abs_gex', ascending=False).head(5)
    
    for _, row in top_strikes.iterrows():
        strike = f"${row['strike_price']:,.1f}"
        gex_val = row['dollar_gex_1pct']
        gex_str = f"+${gex_val:,.0f}" if gex_val > 0 else f"-${abs(gex_val):,.0f}"
        print(f"  Strike: {strike:<10} | GEX: {gex_str:>20}")

def run_gex_engine():
    print("=" * 80)
    print("      DEALER GAMMA EXPOSURE (GEX) RADAR - SLICED HORIZONS")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT c.trade_date, c.contract_month, c.option_type, c.strike_price, c.open_interest,
           COALESCE(b.atm_vol, 0.15) as atm_vol
    FROM cme_option_positioning c
    LEFT JOIN bbg_vol_surface b ON 
        CASE 
            WHEN c.tenor_type LIKE '%Weekly%' THEN '1 Week'
            WHEN c.tenor_type = 'Monthly' THEN '1 Month'
            ELSE 'Unknown'
        END = b.tenor_type
    WHERE c.trade_date = (SELECT MAX(trade_date) FROM cme_option_positioning)
      AND c.open_interest > 0;
    """
    df = pd.read_sql_query(query, conn)
    
    spot_df = pd.read_sql_query("SELECT close_price FROM historical_spot_prices ORDER BY trade_date DESC LIMIT 1", conn)
    conn.close()

    S0 = float(spot_df.iloc[0]['close_price'])
    latest_date = df['trade_date'].iloc[0]

    print(f"  -> Baseline Spot Price (S0): ${S0:,.2f}")
    
    if df['atm_vol'].mean() > 1.0:
        df['atm_vol'] = df['atm_vol'] / 100.0

    current_dt = pd.to_datetime(latest_date)
    df['contract_dt'] = pd.to_datetime(df['contract_month'], format='%b %y', errors='coerce') + pd.Timedelta(days=14)
    df['dte'] = (df['contract_dt'] - current_dt).dt.days
    df['dte'] = np.maximum(df['dte'], 1) 
    df['T'] = df['dte'] / 365.0

    df['gamma'] = calculate_black_scholes_gamma(S0, df['strike_price'], df['T'], df['atm_vol'])
    df['gex_sign'] = np.where(df['option_type'] == 'CALL', 1, -1)
    df['dollar_gex_1pct'] = df['open_interest'] * df['gamma'] * CONTRACT_SIZE * (S0**2) * 0.01 * df['gex_sign']

    # Slice the Data
    df_tactical = df[df['dte'] <= 30]
    df_structural = df[(df['dte'] > 30) & (df['dte'] <= 90)]

    analyze_gex_horizon(df_tactical, S0, "TACTICAL GEX (< 30 Days) - Controls Intraday Liquidity")
    analyze_gex_horizon(df_structural, S0, "STRUCTURAL GEX (30 to 90 Days) - Multi-Week Swing Walls")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_gex_engine()