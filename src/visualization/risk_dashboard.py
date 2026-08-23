import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PAGE SETUP & INSTITUTIONAL CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="XAU Institutional Risk Engine", layout="wide")

st.title("XAU/USD INSTITUTIONAL RISK & POSITIONING ENGINE")
st.caption("Quantitative Head-Up Display | Beta Build 1.0 | Offline Static Data Environment")
st.markdown("---")

# ---------------------------------------------------------
# 2. DATA INGESTION & INTEGER SANITIZATION
# ---------------------------------------------------------
@st.cache_data
def load_and_sanitize_data():
    var_df = pd.read_csv("outputs/historical_mc_simulation_report.csv")
    gex_df = pd.read_csv("outputs/gex_profile_2026-08-12.csv")
    flow_df = pd.read_csv("outputs/flow_velocity_2026-08-12.csv")
    walls_df = pd.read_csv("outputs/support_resistance_walls_2026-08-12.csv")

    # Clean GEX
    gex_df.columns = [c.strip() for c in gex_df.columns]
    s_col, v_col = gex_df.columns[0], gex_df.columns[1]
    gex_df[s_col] = pd.to_numeric(gex_df[s_col], errors='coerce').round(0)
    gex_df[v_col] = pd.to_numeric(gex_df[v_col], errors='coerce').round(0)
    gex_df = gex_df.dropna().sort_values(by=s_col)
    gex_filtered = gex_df[(gex_df[s_col] >= 3800) & (gex_df[s_col] <= 5200)]

    # Clean Walls & Aggregation
    walls_df['strike_price'] = pd.to_numeric(walls_df['strike_price'], errors='coerce')
    walls_filtered = walls_df[(walls_df['strike_price'] >= 3800) & (walls_df['strike_price'] <= 5200)].copy()
    
    global_walls = walls_filtered.groupby(['strike_price', 'option_type'])['total_open_interest'].sum().reset_index()

    return var_df, gex_filtered, global_walls, walls_filtered, flow_df

try:
    var_df, gex_df, global_walls, walls_raw, flow_df = load_and_sanitize_data()
except Exception as e:
    st.error(f"Data Pipeline Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. EXECUTIVE TOP-LINE RIBBON
# ---------------------------------------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Reference Spot (S0)", "$4,358", delta="Anchor T0", delta_color="off")
kpi2.metric("Implied Volatility", "22.78%", delta="Annual Vol-Weighted", delta_color="inverse")
kpi3.metric("Dealer Regime", "STABILIZING", delta="+$1,230M Gamma Buffer", delta_color="normal")
kpi4.metric("1-Day 99% VaR", "-$333,759", delta="$10M Base Portfolio", delta_color="inverse")
kpi5.metric("1-Month 99% VaR", "-$1,529,478", delta="Tail Risk Exposure", delta_color="inverse")

st.markdown("---")

# ---------------------------------------------------------
# 4. INSTITUTIONAL WORKSTATIONS
# ---------------------------------------------------------
tab_gex, tab_walls, tab_flow, tab_var = st.tabs([
    "⚡ Dealer Gamma (GEX)", 
    "🧱 Positioning Walls & Open Interest", 
    "🌊 Flow Velocity & Capital Allocation", 
    "🛡️ Monte Carlo VaR Framework"
])

# --- TAB 1: DEALER GEX RADAR ---
with tab_gex:
    st.subheader("Dealer Gamma Exposure (GEX) Distribution & Key Levels")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tactical Call Wall", "$4,400", delta="+$79M Net GEX")
        st.caption("📅 **Tenor:** Weekly (Week 2 Aug) | **OI:** 351 contracts")
    with c2:
        st.metric("Tactical Put Wall", "$4,335", delta="-$39M Net GEX", delta_color="inverse")
        st.caption("📅 **Tenor:** Weekly (Week 2 Aug) | **OI:** 465 contracts")
    with c3:
        st.metric("Structural Call Ceiling", "$4,600", delta="+$167M GEX Cap")
        st.caption("📅 **Tenor:** Monthly (OCT 26) | **OI:** 6,891 contracts")
    with c4:
        st.metric("Structural Put Floor", "$4,000", delta="-$125M GEX Floor", delta_color="inverse")
        st.caption("📅 **Tenor:** Monthly (OCT 26) | **OI:** 1,884 contracts")
    
    s_col, v_col = gex_df.columns[0], gex_df.columns[1]
    
    fig_gex = go.Figure()
    fig_gex.add_trace(go.Bar(
        x=gex_df[s_col],
        y=gex_df[v_col],
        marker_color=gex_df[v_col].apply(lambda x: '#00FF00' if x >= 0 else '#FF3333'),
        hovertemplate="<b>Strike:</b> $%{x:,.0f}<br><b>Net GEX:</b> $%{y:,.0f}<extra></extra>"
    ))
    fig_gex.add_vline(x=4358, line_dash="dash", line_color="#FFFFFF", annotation_text="Spot $4,358", annotation_position="top right")
    fig_gex.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=480,
        title="Net Dealer Gamma Exposure ($3,800 - $5,200 Strike Corridor)",
        xaxis=dict(title="Strike Price (USD)", tickformat="$,d"),
        yaxis=dict(title="Net Dealer GEX (USD)", tickformat="$,.0s")
    )
    st.plotly_chart(fig_gex, use_container_width=True)

# --- TAB 2: POSITIONING WALLS & OPEN INTEREST ---
with tab_walls:
    st.subheader("Open Interest Liquidity Profile & Key Strike Inventory")
    
    calls = global_walls[global_walls['option_type'] == 'CALL'].sort_values('strike_price')
    puts = global_walls[global_walls['option_type'] == 'PUT'].sort_values('strike_price')
    
    fig_grav = go.Figure()
    fig_grav.add_trace(go.Bar(
        x=calls['strike_price'], 
        y=calls['total_open_interest'], 
        name="Call Inventory (Resistance)", 
        marker_color="#00FF00",
        hovertemplate="<b>Strike:</b> $%{x:,.0f}<br><b>Calls:</b> %{y:,.0f} contracts<extra></extra>"
    ))
    fig_grav.add_trace(go.Bar(
        x=puts['strike_price'], 
        y=-puts['total_open_interest'].abs(), 
        name="Put Inventory (Support)", 
        marker_color="#FF3333",
        hovertemplate="<b>Strike:</b> $%{x:,.0f}<br><b>Puts:</b> %{y:,.0f} contracts<extra></extra>"
    ))
    fig_grav.add_vline(x=4358, line_dash="dash", line_color="#FFFFFF", annotation_text="Spot $4,358", annotation_position="top left")
    fig_grav.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        barmode="relative",
        title="Institutional Call vs. Put Open Interest Concentration",
        xaxis=dict(title="Strike Price (USD)", tickformat="$,d"),
        yaxis=dict(title="Open Interest (Contracts)", tickformat=",.0f"),
        height=450
    )
    st.plotly_chart(fig_grav, use_container_width=True)
    
    st.markdown("### Tactical HUD: Institutional Inventory Matrix")
    
    # Format Tables Helper
    def format_hud_table(df_slice):
        df_display = df_slice.sort_values(by='total_usd_notional', ascending=False).head(10).copy()
        df_display = df_display[['expiration_bucket', 'strike_price', 'total_open_interest', 'total_usd_notional', 'total_premium_cash', 'oi_share_pct']]
        df_display.columns = ['Maturity Bucket', 'Strike', 'Open Interest', 'USD Notional', 'Est. Premium Cash', 'OI Share %']
        
        return df_display.style.format({
            'Strike': '${:,.1f}',
            'Open Interest': '{:,.0f}',
            'USD Notional': '${:,.0f}',
            'Est. Premium Cash': '${:,.0f}',
            'OI Share %': '{:.2f}%'
        })

    is_monthly = walls_raw['expiration_bucket'].str.contains('MONTHLY', case=False, na=False)
    
    subtab_monthly, subtab_weekly = st.tabs(["🏛️ Monthly Structural Horizon", "⚡ Weekly Tactical Horizon"])
    
    with subtab_monthly:
        col_m_call, col_m_put = st.columns(2)
        with col_m_call:
            st.markdown("##### Top 10 Monthly Calls (Ceilings)")
            st.dataframe(format_hud_table(walls_raw[is_monthly & (walls_raw['option_type'] == 'CALL')]), use_container_width=True)
        with col_m_put:
            st.markdown("##### Top 10 Monthly Puts (Floors)")
            st.dataframe(format_hud_table(walls_raw[is_monthly & (walls_raw['option_type'] == 'PUT')]), use_container_width=True)

    with subtab_weekly:
        col_w_call, col_w_put = st.columns(2)
        with col_w_call:
            st.markdown("##### Top 10 Weekly Calls (Resistance Pins)")
            st.dataframe(format_hud_table(walls_raw[~is_monthly & (walls_raw['option_type'] == 'CALL')]), use_container_width=True)
        with col_w_put:
            st.markdown("##### Top 10 Weekly Puts (Support Pins)")
            st.dataframe(format_hud_table(walls_raw[~is_monthly & (walls_raw['option_type'] == 'PUT')]), use_container_width=True)

# --- TAB 3: FLOW VELOCITY & CAPITAL ACCUMULATION ---
with tab_flow:
    st.subheader("Institutional Flow Velocity (Delta OI & Capital Allocation)")
    st.caption("Net day-over-day institutional capital shifts (T0: 2026-08-12 vs T-1: 2026-08-11)")
    
    def format_flow_table(df_slice):
        cols = ['tenor_type', 'contract_month', 'strike_price', 'delta_oi', 'flow_usd_notional', 'flow_premium_cash']
        d = df_slice[cols].copy()
        d['Bucket'] = d['tenor_type'] + ' - ' + d['contract_month']
        d = d[['Bucket', 'strike_price', 'delta_oi', 'flow_usd_notional', 'flow_premium_cash']]
        d.columns = ['Bucket', 'Strike', 'Delta OI', 'Flow Notional', 'Flow Premium Cash']
        return d.style.format({
            'Strike': '${:,.1f}',
            'Delta OI': '{:+,.0f}',
            'Flow Notional': '${:+,.0f}',
            'Flow Premium Cash': '${:+,.0f}'
        })

    flow_c1, flow_c2 = st.columns(2)
    with flow_c1:
        st.markdown("#### Top Institutional Call Deployments")
        st.dataframe(format_flow_table(flow_df[flow_df['option_type'] == 'CALL'].head(10)), use_container_width=True)
            
    with flow_c2:
        st.markdown("#### Top Institutional Put Deployments")
        st.dataframe(format_flow_table(flow_df[flow_df['option_type'] == 'PUT'].head(10)), use_container_width=True)

# --- TAB 4: RISK & MONTE CARLO VaR ---
with tab_var:
    st.subheader("Value-at-Risk (VaR) Engine & Parametric Governors")
    
    def format_var_table(df_in):
        d = df_in.copy()
        d.columns = ['Horizon', 'Expected Spot Mean', 'Operational VaR (68%)', 'Trading VaR (95%)', 'Black Swan VaR (99%)']
        return d.style.format({
            'Expected Spot Mean': '${:,.2f}',
            'Operational VaR (68%)': '${:,.2f}',
            'Trading VaR (95%)': '${:,.2f}',
            'Black Swan VaR (99%)': '${:,.2f}'
        })
        
    st.dataframe(format_var_table(var_df), use_container_width=True)
    
    p1, p2, p3 = st.columns(3)
    p1.info("**Portfolio Notional Base:** $10,000,000 USD")
    p2.info("**1-Day Operational Vol (68%):** -$143,491 USD")
    p3.info("**1-Month Tail Risk (99%):** -$1,529,478 USD")