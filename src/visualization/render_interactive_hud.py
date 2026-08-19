"""
Phase 4: Interactive Risk Dashboard (Web-Ready)
Path: src/visualization/risk_dashboard.py

Ingests mathematically pure CSV outputs from the analytics engine and renders
a fully interactive HTML dashboard using Plotly. Decoupled from the math engines.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import glob

# ------------------------------------------------------------------------------
# Configuration & Paths
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DASHBOARD_OUT = OUTPUT_DIR / "xau_interactive_hud.html"

def get_latest_file(pattern: str) -> str:
    """Finds the most recent file matching a pattern in the outputs directory."""
    files = glob.glob(str(OUTPUT_DIR / pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {pattern} found in {OUTPUT_DIR}")
    return max(files) # Grabs the latest date based on string sorting

def build_interactive_dashboard():
    print("=" * 80)
    print("      PHASE 4: VISUALIZATION ENGINE (PLOTLY WEB-READY HUD)")
    print("=" * 80)

    # 1. Load the Latest Data
    latest_walls_file = get_latest_file("support_resistance_walls_*.csv")
    print(f"[1/3] Ingesting Tactical Data: {Path(latest_walls_file).name}")
    df = pd.read_csv(latest_walls_file)

    # Clean data to focus on immediate Tactical/Structural strikes (e.g., Top 50 by OI)
    df = df.sort_values(by='total_open_interest', ascending=False).head(100)

    calls = df[df['option_type'] == 'CALL'].sort_values(by='strike_price')
    puts = df[df['option_type'] == 'PUT'].sort_values(by='strike_price')

    print("[2/3] Rendering Interactive HTML Dashboard...")

    # 2. Initialize Subplots
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            "Institutional Supply/Demand: Open Interest Profile",
            "Conviction Heatmap: Estimated Premium Cash Spent (USD)"
        ),
        vertical_spacing=0.15
    )

    # --- CHART 1: OPEN INTEREST WALLS (Calls vs Puts) ---
    fig.add_trace(go.Bar(
        x=calls['strike_price'], 
        y=calls['total_open_interest'],
        name='Call OI (Resistance)',
        marker_color='rgba(39, 174, 96, 0.7)', # Institutional Green
        hovertemplate="<b>Strike:</b> $%{x:,.1f}<br><b>Call OI:</b> %{y:,.0f}<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=puts['strike_price'], 
        y=-puts['total_open_interest'], # Invert for two-sided effect
        name='Put OI (Support)',
        marker_color='rgba(231, 76, 60, 0.7)', # Institutional Red
        hovertemplate="<b>Strike:</b> $%{x:,.1f}<br><b>Put OI:</b> %{y:,.0f}<extra></extra>"
    ), row=1, col=1)

    # --- CHART 2: PREMIUM CASH CONVICTION ---
    fig.add_trace(go.Scatter(
        x=calls['strike_price'], 
        y=calls['total_premium_cash'],
        mode='markers+lines',
        name='Call Premium Cash',
        marker=dict(color='#27ae60', size=8),
        line=dict(dash='solid', width=2),
        hovertemplate="<b>Strike:</b> $%{x:,.1f}<br><b>Cash Spent:</b> $%{y:,.0f}<extra></extra>"
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=puts['strike_price'], 
        y=puts['total_premium_cash'],
        mode='markers+lines',
        name='Put Premium Cash',
        marker=dict(color='#e74c3c', size=8),
        line=dict(dash='solid', width=2),
        hovertemplate="<b>Strike:</b> $%{x:,.1f}<br><b>Cash Spent:</b> $%{y:,.0f}<extra></extra>"
    ), row=2, col=1)

    # 3. Format Layout and Styling
    fig.update_layout(
        title_text="<b>XAU Institutional Positioning Radar</b>",
        title_font_size=24,
        title_x=0.5,
        template="plotly_dark",
        barmode='relative',
        hovermode="x unified",
        height=900,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Format Axes
    fig.update_yaxes(title_text="Open Interest (Contracts)", row=1, col=1)
    fig.update_yaxes(title_text="Est. Premium Cash ($)", tickprefix="$", row=2, col=1)
    fig.update_xaxes(title_text="Strike Price", tickprefix="$", row=2, col=1)

# 4. Export to Interactive HTML
    fig.write_html(str(DASHBOARD_OUT))
    print(f"[3/3] Success! Web-ready dashboard saved to: {DASHBOARD_OUT}")
    print(" -> Double-click 'xau_interactive_hud.html' to open the interactive HUD in your web browser.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    build_interactive_dashboard()