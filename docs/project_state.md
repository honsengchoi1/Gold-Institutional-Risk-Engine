# project_state.md (Thread Transition State Document)
**Last Updated:** 2026-08-13 03:20 PM EDT  
**Project Name:** XAU_Positioning_Pipeline  
**Notional Scope:** $10 Million USD Notional Spot Gold Book (Positioning Radar via CME Options & BBG Data)

---

## 1. Project Goal & Scope
Build an automated institutional quantitative analytics engine for a **$10M USD Notional Spot Gold** portfolio using CME Volume/Open Interest (VOI) options data and Bloomberg market inputs as a positioning/volatility radar.

The pipeline ingests raw CME VOI reports and Bloomberg outputs into a local SQLite database (`gold_master.db`). It calculates forward-looking parametric VaR, maps structural Support/Resistance walls, tracks institutional flow velocity, and simulates portfolio PnL via Monte Carlo stochastic modeling.

**Critical Math Rules & Formulae:**
* $\text{USD Notional} = \text{Open Interest} \times 100\text{ (oz)} \times \text{Strike Price}$
* $\text{Parametric VaR}_{\alpha} = \text{Portfolio Notional} \times Z_{\alpha} \times \sigma_{\text{period}}$
* $\text{Geometric Brownian Motion}: dS_t = \mu S_t dt + \sigma S_t dW_t$

**Standardized Risk Terminology:**
* **Operational PnL Variance:** The 68% statistical boundary ($Z = 1.000$).
* **Active Trading Risk:** 95% Confidence Interval VaR ($Z = 1.645$).
* **The Black Swan:** 99% Tail-Risk VaR ($Z = 2.326$).

---

## 2. Permanent Directives & Data-Loss Prevention Protocol
* **Formal Timestamping:** Every response must start with a formal EDT/UTC timestamp.
* **State Preservation (`project_state.md`):** Maintained synchronously across threads to guarantee instant recovery.
* **The Collaborative Workflow Loop:** Discuss -> Brainstorm -> Teach -> Learn -> Confirm -> Proceed.
* **Elite Pro Standard:** Balance structural modularity against unnecessary complexity. Standardize data cleaning strictly at the ETL layer.
* **Optimize for Inheritability:** Prioritize explicit, highly readable scripts over implicit software-engineering consolidation.
* **Proxy/Mock Execution:** Always run lightweight diagnostic scripts ("Warm-Ups") before executing heavy analytical engines.

---

## 3. Directory Structure & File Inventory
XAU_Positioning_Pipeline/
├── .gitignore (Ignores __pycache__, .env, and data_raw/archive/)
├── path_scanner.py (Root folder inspector utility)
├── docs/
│   ├── docs_design_methodology.md (Contains Dual-Engine Architecture diagram)
│   ├── project_goals.md
│   ├── project_roadmap.md
│   ├── project_state.md (Current active thread state)
│   └── quant_knowledge_base.md (Institutional desk mechanics & VaR math)
├── data_processed/
│   ├── staging/ (Holds staging CSVs & audit_flags.csv)
│   └── gold_master.db (SQLite Data Warehouse - Populated & Audited)
├── data_raw/
│   ├── cme_voi_20260811.xlsx (T-1 CME VOI Data)
│   ├── cme_voi_20260812.xlsx (T-0 CME VOI Data)
│   ├── historical_gold_data.csv (2026 Spot Gold OHLC Timeseries)
│   ├── bbg_futures_curve.csv
│   ├── bbg_vol_surface.csv
│   └── archive/ (Holds retired legacy files)
├── outputs/
│   ├── executive_risk_dashboard.csv
│   ├── historical_mc_simulation_report.csv
│   └── support_resistance_walls_segmented.csv
└── src/                            
    ├── etl/
    │   ├── extract_transform.py (Completed - Robust CME Sub-Header Parser)
    │   ├── init_database.py (Database initialization script)
    │   ├── load_cme_positioning.py (Idempotent CME Options Loader)
    │   ├── load_historical_prices.py (Spot Price Loader)
    │   └── run_pipeline.py (Master ETL Orchestrator)
    ├── analytics/
    │   └── analytics_engine.py (Core 1D/1W/1M VaR & Wall Segmenter)
    ├── advanced_analytics/ (Specialized Decoupled Quant Engines)
    │   ├── historical_simulator.py (Completed - Historical Replay & Monte Carlo)
    │   ├── flow_velocity.py (Pending Phase 3 - T-1 vs T-0 Delta OI Smart Money Tracker)
    │   └── gex_engine.py (Pending Phase 3 - Black-Scholes Dealer Gamma Exposure Radar)
    └── utils/
        ├── cme_auditor.py
        └── db_warmup_check.py (Database Diagnostic Suite)

---

## 4. Confirmed Data Schemas & Engineering Rules
* **Functional Purity (ETL):** Module 1 cleans data, parses `.xlsx` sub-headers, and standardizes formats before staging.
* **Database Idempotency:** `load_cme_positioning.py` uses strict `INSERT OR IGNORE` logic tied to a UNIQUE index to prevent duplicate records on multiple runs.
* **Decoupled Advanced Analytics:** Engines inside `src/advanced_analytics/` run vectorized matrix math in-memory via Pandas/NumPy, keeping core database schemas untouched.

---

## 5. Current Progress & Roadmap Tracker

### Completed Milestones
* [x] **Phase 0:** Environment Setup, Git Identity Config, Directory Architecture.
* [x] **Phase 1:** Built Core ETL Pipeline, database schema initialization, and spot price loader.
* [x] **Phase 2:** Built Core Analytics Engine calculating parametric VaR and multi-horizon market walls.
* [x] **Phase 3.1:** Built Historical Replay & Monte Carlo Simulator (`historical_simulator.py`).
* [x] **Data Refactor:** Upgraded ETL to parse complex `.xlsx` CME sub-headers. Loaded contiguous T-1/T-0 dates seamlessly.

### Pending Next Steps (New Thread Readiness)
1. **Build Engine 2 - Flow Velocity (`flow_velocity.py`):** Calculate $\Delta\text{OI}$ between $T-1$ and $T-0$ to flag institutional smart-money accumulation.
2. **Build Engine 3 - Dealer Gamma Exposure (`gex_engine.py`):** Calculate Black-Scholes Net Dealer Gamma ($\Gamma$) profiles across strikes to map volatility pinning vs acceleration regimes.
