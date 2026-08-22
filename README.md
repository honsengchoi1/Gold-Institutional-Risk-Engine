# Gold Market Microstructure: XAU/USD Institutional Positioning Pipeline

**Architect:** Hon Seng Choi | Director of Market & Risk Analytics

**Target Scope:** $10 Million USD Notional Spot Gold (XAU/USD) Portfolio

**Core Infrastructure:** Python, SQLite, NumPy, Plotly (Decoupled OLAP Model)

---

## 1. Executive Summary & Business Objective
This repository contains an institutional-grade ELT pipeline and quantitative risk engine designed to model market microstructure and capital velocity in COMEX Gold derivatives.

Traditional trading operations frequently rely on static notional caps (e.g., "Max $10M Book") and 1-Dimensional spot technicals. Fixed capital limits do not tell the whole story, as they fail to reflect regime shifts in underlying volatility. This engine replaces static assumptions with dynamic, volatility-adjusted mathematical governors. By programmatically ingesting CME clearinghouse Open Interest (OI) reports and Bloomberg volatility surfaces, the pipeline maps the structural liquidity barriers and dealer hedging zones that dictate spot market mechanics.

---

## 2. Quantitative Engine Capabilities

### A. Base Analytics Engine (`src/analytics/analytics_engine.py`)
*   **Structural Liquidity Mapping:** Translates raw contract counts into Gross USD Notional ($\text{OI} \times 100 \times \text{Strike}$) to identify physical delivery ceilings (Call Walls) and floors (Put Walls).
*   **4-Sigma Outlier Filtering:** Filters raw option chains across a 4-Sigma boundary and 4-Month horizon to eliminate deep OTM noise.
*   **Volume-Weighted Implied Volatility:** Aggregates multi-tenor Bloomberg volatility surfaces into a single portfolio-weighted baseline ($\sigma = 22.78\%$).
*   **Black-Scholes Premium Cash Integration:** Calculates the actual cash committed per strike ($\text{OI} \times 100 \times \text{BS Premium}$), isolating true institutional conviction from cheap OTM tail options.

### B. Advanced Analytics Suite (`src/advanced_analytics/`)
1.  **Dealer Gamma Exposure (GEX) Profiler (`gex_engine.py`):** Translates Open Interest into Dollar Gamma Exposure ($\text{OI} \times \Gamma \times 100 \times S_0^2 \times 0.01 \times \text{Sign}$) across Tactical (<30 Days) and Structural (30–90 Days) horizons. Identifies market regimes (**Stabilizing / Long Gamma** vs. **Amplifying / Short Gamma**).
2.  **Institutional Flow Velocity (`flow_velocity.py`):** Executes a multi-index matrix join between $T_0$ and $T_{-1}$ clearinghouse reports. Calculates daily delta Open Interest ($\Delta\text{OI}$) and capital velocity to separate institutional accumulation from panic liquidation.
3.  **Vectorized Monte Carlo VaR Simulator (`historical_simulator.py`):** Runs 10,000 Geometric Brownian Motion (GBM) paths to project forward-looking Value at Risk (VaR) across 1-Day, 1-Week, and 1-Month horizons at 95% and 99% confidence intervals.

---

## 3. System Architecture: Dual-Engine Model

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         INSTITUTIONAL PIPELINE ARCHITECTURE                      │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [ RAW DATA INGESTION ]                                                          │
│  ├── CME VOI Clearinghouse Reports (cme_voi_*.xlsx)                              │
│  ├── Bloomberg Volatility Surfaces & Risk Reversals (bbg_vol_surface.csv)        │
│  └── Historical Spot Price Series (historical_gold_data.csv)                     │
│                           │                                                      │
│                           ▼                                                      │
│  [ ETL & STAGING LAYER ] (Stateless State-Machine Parser)                        │
│  ├── CME Sub-Header Parsing (Dynamic Tenor, Month, Option Type Extraction)       │
│  ├── Volatility Normalization Check (if mean(vol) > 1.0 => vol / 100.0)          │
│  └── Staging Audit Trail (data_processed/staging/cme_voi_latest.csv)             │
│                           │                                                      │
│                           ▼                                                      │
│  [ DATA WAREHOUSE LAYER ] (SQLite / OLAP Engine)                                 │
│  ├── gold_master.db                                                              │
│  │   ├── cme_option_positioning (UNIQUE Index Idempotency Lock)                  │
│  │   ├── historical_spot_prices (Spot Close Persistence)                         │
│  │   └── bbg_vol_surface (Tenor-Mapped Volatility Surfaces)                      │
│                           │                                                      │
│                           ▼                                                      │
│  [ IN-MEMORY QUANTITATIVE COMPUTATION ENGINE ] (C-Backed NumPy Matrix Math)      │
│  ├── Base Engine: Support/Resistance Walls & Black-Scholes Premium Cash          │
│  ├── Advanced Suite: Dollar GEX Profiler & 24-Hr Flow Velocity Matrix            │
│  └── Stochastic Engine: 10,000-Path GBM Monte Carlo VaR Simulation               │
│                           │                                                      │
│                           ▼                                                      │
│  [ DECOUPLED VISUALIZATION LAYER ] (Plotly Web Engine)                           │
│  └── Pure CSV Input Ingestion ──► Interactive Web HUD (xau_interactive_hud.html) │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘