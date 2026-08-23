# Gold Market Microstructure: XAU/USD Institutional Positioning Pipeline

**Architect:** Hon Seng Choi | Director of Market & Risk Analytics
**Target Scope:** $10 Million USD Notional Spot Gold (XAU/USD) Portfolio
**Core Infrastructure:** Python, SQLite, NumPy, Plotly, Streamlit (Decoupled OLAP Model)

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
*   **Dealer Gamma Exposure (GEX) Profiler (`gex_engine.py`):** Translates Open Interest into Dollar Gamma Exposure ($\text{OI} \times \Gamma \times 100 \times S_0^2 \times 0.01 \times \text{Sign}$) across Tactical (<30 Days) and Structural (30–90 Days) horizons. Identifies market regimes (Stabilizing / Long Gamma vs. Amplifying / Short Gamma).
*   **Institutional Flow Velocity (`flow_velocity.py`):** Executes a multi-index matrix join between $T_0$ and $T_{-1}$ clearinghouse reports. Calculates daily delta Open Interest ($\Delta\text{OI}$) and capital velocity to separate institutional accumulation from panic liquidation.
*   **Vectorized Monte Carlo VaR Simulator (`historical_simulator.py`):** Runs 10,000 Geometric Brownian Motion (GBM) paths to project forward-looking Value at Risk (VaR) across 1-Day, 1-Week, and 1-Month horizons at 95% and 99% confidence intervals.

---

## 3. System Architecture: Dual-Engine Model

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
    │  [ DECOUPLED VISUALIZATION LAYER ] (Streamlit Web Engine)                        │
    │  └── Pure CSV Input Ingestion ──► Interactive Web HUD (risk_dashboard.py)        │
    │                                                                                  │
    └──────────────────────────────────────────────────────────────────────────────────┘

---

## 4. Quick Start & Execution Protocol

This pipeline is designed for immediate local execution utilizing the bundled sample data.

**1. Environment & Database Initialization (ETL)**
Install dependencies and run the master orchestrator to build the SQLite database and ingest raw staging data:
*   `conda env create -f environment.yml`
*   `conda activate xau_pipeline`
*   `python src/etl/run_pipeline.py`

**2. Execute Quantitative Analytics Engines**
Run the decoupled mathematical models to map structural walls, simulate stochastic VaR, track flow velocity, and model dealer gamma:
*   `python src/analytics/analytics_engine.py`
*   `python src/advanced_analytics/historical_simulator.py`
*   `python src/advanced_analytics/flow_velocity.py`
*   `python src/advanced_analytics/gex_engine.py`

**3. Render the Decoupled Visual HUD**
Execute the Streamlit visualization script to ingest the newly generated analytics CSVs and render the interactive dashboard:
*   `streamlit run src/visualization/risk_dashboard.py`

---

## 5. Database Architecture & Live Integration Notes

This beta utilizes static data. If integrated into a live desk via FIX API or Bloomberg, the local SQLite warehouse can seamlessly migrate to PostgreSQL using this exact schema map:
*   `cme_option_positioning`: Implements a composite `UNIQUE` constraint (`trade_date`, `tenor_type`, `contract_month`, `option_type`, `strike_price`) to categorically prevent Open Interest double-counting.
*   `historical_spot_prices`: Tracks daily baseline prices ($S_0$) for parametric VaR log-return calibration.
*   `bbg_vol_surface`: Tenor-mapped Volatility ($\sigma$), converting standard percentage points into pure decimals for matrix math.