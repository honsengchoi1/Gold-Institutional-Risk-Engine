# XAU Positioning Pipeline - Project State & Architecture
**Last Updated:** 2026-08-17
**Project Name:** XAU_Positioning_Pipeline
**Current Phase:** Executing Phase 3 (Advanced Analytics) - Transitioning to Phase 3.2
**Notional Scope:** $10 Million USD Notional Spot Gold Book (Positioning Radar via CME Options & BBG Data)

---

## 1. Project Goal & Scope
Build an automated institutional quantitative analytics engine for a **$10M USD Notional Spot Gold** portfolio using CME Volume/Open Interest (VOI) options data and Bloomberg market inputs as a positioning/volatility radar.

The pipeline ingests raw CME VOI reports and Bloomberg outputs into a local SQLite database (`gold_master.db`). It calculates forward-looking parametric VaR, maps structural Support/Resistance walls, tracks institutional flow velocity, and simulates portfolio PnL via Monte Carlo stochastic modeling.

**Critical Math Rules & Formulae:**
* $\text{USD Notional} = \text{Open Interest} \times 100\text{ (oz)} \times \text{Strike Price}$
* $\text{Parametric VaR}_{\alpha} = \text{Portfolio Notional} \times Z_{\alpha} \times \sigma_{\text{period}}$
* $\text{Geometric Brownian Motion}: dS_t = \mu S_t dt + \sigma S_t dW_t$
* $\text{Volume-Weighted Vol} = \frac{\sum (\text{Bucket Notional} \times \text{Bucket Volatility})}{\text{Total Portfolio Notional}}$

---

## 2. Permanent Directives & Data-Loss Prevention Protocol
* **Formal Timestamping:** Every response must start with a formal EDT/UTC timestamp.
* **Context Synchronization (Zero Data Leak):** Maintained synchronously across threads to guarantee instant recovery. 
* **The Collaborative Workflow Loop:** Discuss -> Brainstorm -> Teach -> Learn -> Confirm -> Proceed.
* **Elite Pro Standard:** Balance structural modularity against unnecessary complexity. Standardize data cleaning strictly at the ETL layer.
* **Strict Architecture Decoupling:** The mathematical analytics engines (e.g., Monte Carlo, VaR) must remain mathematically pure. All visual charting (matplotlib/D3) is strictly decoupled into a separate visualization layer to prevent pipeline bloat.
* **Optimize for Inheritability:** Prioritize explicit, highly readable scripts over implicit software-engineering consolidation.
* **Proxy/Mock Execution:** Always run lightweight diagnostic scripts before executing heavy analytical engines.

---

## 3. Directory Structure & File Inventory (Locked Git Baseline)
XAU_Positioning_Pipeline/
├── .gitignore 
├── docs/
│   ├── docs_design_methodology.md
│   ├── project_goals.md
│   ├── project_state.md 
│   └── quantitative_insights.md (Market mechanics and PM scratchpad)
├── data_processed/
│   ├── staging/ 
│   └── gold_master.db (Target SQLite Data Warehouse)
├── data_raw/
│   ├── bbg_futures_curve.csv 
│   ├── bbg_vol_surface.csv 
│   ├── cme_voi_*.xlsx 
│   └── historical_gold_data.csv 
├── outputs/ 
│   ├── executive_risk_dashboard_*.csv
│   ├── global_strike_gravity_*.csv
│   ├── historical_mc_simulation_report.csv
│   └── simulated_paths_*.csv (Raw distributional data for visualizations)
└── src/                               
    ├── etl/
    │   ├── extract_cme_options.py (Completed)
    │   ├── init_database.py (Completed)
    │   ├── load_cme_positioning.py (Completed)
    │   ├── load_historical_prices.py (Completed)
    │   ├── load_bbg_vol.py (Completed)
    │   └── run_pipeline.py (Completed)
    ├── analytics/
    │   └── analytics_engine.py (Completed - Core 1D/1W/1M VaR, 4-Sigma Filter)
    ├── advanced_analytics/ 
    │   ├── historical_simulator.py (Completed - Vectorized GBM Monte Carlo 10k Paths)
    │   ├── flow_velocity.py (Pending Phase 3.2 - T-1 vs T-0 Delta OI Tracker)
    │   └── gex_engine.py (Pending Phase 3.3 - Dealer Gamma Exposure Radar)
    ├── visualization/
    │   └── risk_dashboard.py (Pending Phase 4 - Decoupled charting module)
    └── utils/
        ├── db_warmup_check.py (Completed)
        └── cluster_exporter.py (Completed)

---

## 4. Confirmed Data Schemas & Engineering Rules
* **Functional Purity (ETL):** Module 1 cleans data, parses `.xlsx` sub-headers, and standardizes formats before staging.
* **Database Idempotency:** `INSERT OR IGNORE` logic tied to a UNIQUE index prevents OI double-counting.
* **Reference Data Centralization:** All reference files explicitly staged into SQLite for native high-speed SQL JOIN operations.
* **Atomic Version Control:** Commits must be atomic and logically isolated. Remote pushes are entirely optional; local saves are the priority.

---

## 5. Current Milestones Reached
- [x] **Phase 1 (ETL):** Built Core ETL Pipeline, database schemas, and spot price loader.
- [x] **Phase 2.1 (Analytics):** Built VaR models and Multi-Horizon Aggregations.
- [x] **Phase 2.2 (Institutional PM Polish):** Deployed 4-Sigma dynamic price boundaries and Tabular HUD.
- [x] **Phase 3.1 (Simulation):** Executed Historical Monte Carlo Simulator (`historical_simulator.py`).
- [x] Decoupled simulation data generation from visual charting (exported raw paths arrays to CSV).
- [x] Formalized 10,000-path statistical benchmark for statistical convergence vs latency.
- [ ] **Phase 3.2:** Build Flow Velocity / Delta OI Tracker (`flow_velocity.py`).
- [ ] **Phase 3.3:** Build Dealer Gamma Exposure Radar (`gex_engine.py`).
- [ ] **Phase 4:** Build Decoupled Visualization Engine (`risk_dashboard.py`).