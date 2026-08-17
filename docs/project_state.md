# XAU Positioning Pipeline - Project State & Architecture
**Last Updated:** 2026-08-17 11:05 AM EDT
**Project Name:** XAU_Positioning_Pipeline
**Current Phase:** Transitioning from Phase 2 (Quantitative Analytics) to Phase 3 (Advanced Analytics)
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
* **Context Synchronization (Zero Data Leak):** Maintained synchronously across threads to guarantee instant recovery. By explicitly defining schemas and logic here, the AI reconstructs the database map without needing local queries. Zero data loss permitted during thread transitions.
* **The Collaborative Workflow Loop:** Discuss -> Brainstorm -> Teach -> Learn -> Confirm -> Proceed.
* **Elite Pro Standard:** Balance structural modularity against unnecessary complexity. Standardize data cleaning strictly at the ETL layer.
* **Optimize for Inheritability:** Prioritize explicit, highly readable scripts over implicit software-engineering consolidation.
* **Proxy/Mock Execution:** Always run lightweight diagnostic scripts ("Warm-Ups") before executing heavy analytical engines.

---

## 3. Directory Structure & File Inventory (Locked Git Baseline)
XAU_Positioning_Pipeline/
├── .gitignore (Shielding *.db, __pycache__, .env, and local path scanners)
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
│   ├── cme_voi_20260811.xlsx 
│   ├── cme_voi_20260812.xlsx 
│   └── historical_gold_data.csv 
├── outputs/ 
└── src/                               
    ├── etl/
    │   ├── extract_cme_options.py (Completed - CME Sub-Header Parser & Regex Tenor Mapping)
    │   ├── init_database.py (Completed - Idempotent Schema Setup incl. BBG table)
    │   ├── load_cme_positioning.py (Completed - INSERT OR IGNORE Loader)
    │   ├── load_historical_prices.py (Completed - Spot Price Loader with explicit parsing)
    │   ├── load_bbg_vol.py (Completed - BBG CSV to DB Stager)
    │   └── run_pipeline.py (Completed - Master ETL Orchestrator)
    ├── analytics/
    │   └── analytics_engine.py (Completed - Core 1D/1W/1M VaR, 4-Sigma Filter, PM Tabular HUD)
    ├── advanced_analytics/ 
    │   ├── historical_simulator.py (Pending Phase 3.1 - Monte Carlo Math & Output Refinement)
    │   ├── flow_velocity.py (Pending Phase 3.2 - T-1 vs T-0 Delta OI Smart Money Tracker)
    │   └── gex_engine.py (Pending Phase 3.3 - Dealer Gamma Exposure & Premium Pricing Radar)
    └── utils/
        ├── db_warmup_check.py (Completed - Database Diagnostic Suite & Sanity Printout)
        └── cluster_exporter.py (Completed - Raw tabular anomaly hunter utility)

---

## 4. Confirmed Data Schemas & Engineering Rules
* **Functional Purity (ETL):** Module 1 cleans data, parses `.xlsx` sub-headers, and standardizes formats before staging.
* **Database Idempotency:** `load_cme_positioning.py` uses strict `INSERT OR IGNORE` logic tied to a UNIQUE index to prevent OI double-counting.
* **Reference Data Centralization:** All reference files (Bloomberg) are explicitly staged into SQLite to enable native, high-speed SQL JOIN operations.
* **Decoupled Advanced Analytics:** Engines inside `src/advanced_analytics/` run vectorized matrix math in-memory via Pandas/NumPy. (Visualization is explicitly decoupled from the math engines).
* **Atomic Version Control:** Initial root commit executed. All future commits must be atomic and logically isolated.

---

## 5. Pipeline Execution Sequence (Phase 1)
The Master Orchestrator (`src/etl/run_pipeline.py`) strictly enforces a 5-step process:
1. **Initialize DB Schema:** `init_database.py`
2. **Load Spot Prices:** `load_historical_prices.py` 
3. **Extract CME Data:** `extract_cme_options.py` 
4. **Load CME Data:** `load_cme_positioning.py` 
5. **Load Bloomberg Data:** `load_bbg_vol.py` 
6. **Audit & Sanity Check:** `db_warmup_check.py`

---

## 6. Quantitative Analytics Engine (Phase 2)
*File:* `src/analytics/analytics_engine.py` & `src/utils/cluster_exporter.py`
- Performs native SQL `LEFT JOIN` using a `CASE` statement mapping CME strings ("Weekly"/"Monthly") directly to Bloomberg standard tenors ("1 Week"/"1 Month").
- **Risk Constraint 1:** Explicitly isolates `MAX(trade_date)` to prevent time-series OI aggregation errors.
- **Risk Constraint 2 (Hard Fail Protocol):** Instantly terminates execution via `ValueError` if Bloomberg volatility mapping fails, preventing silent VaR under-calculations.
- **Risk Constraint 3 (Normalization Protocol):** Dynamically traps and normalizes whole-number Bloomberg volatility integers (e.g., 22.68) into decimal formats (0.2268) to prevent mathematical VaR blow-ups.
- **Strategic Time & Volatility Filters:** Deploys a $4\sigma$ dynamic math boundary and a 4-Month forward horizon mask to eliminate deep OTM long-dated noise.
- **Outputs:** `executive_risk_dashboard_{date}.csv`, `global_strike_gravity_{date}.csv`, and `cluster_check_{date}.csv`.

---

## 7. Current Milestones Reached
- [x] **Phase 0:** Environment Setup & Workstation Directory Replication.
- [x] **Phase 1 (ETL):** Built Core ETL Pipeline, database schemas, and spot price loader.
- [x] Extracted multi-dimensional CME formatting into strict 1D relational tables.
- [x] Patched memory leak warning in Pandas datetime logic.
- [x] Solved Weekly vs Monthly contract undercounting (Regex tenor extraction).
- [x] Migrated loose Volatility CSVs into structured SQLite tables.
- [x] Deployed automated QA Sanity Check (Terminal Readout).
- [x] **Phase 2.1 (Analytics):** Built VaR models and Multi-Horizon Aggregations.
- [x] Implemented Institutional Hard Fail for missing volatility data.
- [x] Corrected Floating Point Volatility multiplier inflation (Normalization patch).
- [x] **Phase 2.2 (Institutional PM Polish):** Deployed 4-Sigma dynamic price boundaries.
- [x] Created PM-facing Tactical Tabular HUD directly in terminal.
- [x] Built out-of-band `cluster_exporter.py` for raw Excel anomaly hunting.
- [x] Calculated Global Strike Gravity ("The Valley") to map overall market skew.
- [ ] **Phase 3.1:** Execute & Validate Phase 3 Monte Carlo Simulator (`historical_simulator.py`).
- [ ] **Phase 3.2:** Build Flow Velocity / Delta OI Tracker (`flow_velocity.py`).
- [ ] **Phase 3.3:** Build Dealer Gamma Exposure Radar (`gex_engine.py`) and Option Premium Estimator.

---