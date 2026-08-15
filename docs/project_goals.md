# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 12:47:33 2026

@author: hchoi
"""

# Project Goals: XAU Positioning Pipeline

## Overview
The XAU Positioning Pipeline is an institutional quantitative analytics engine designed to process raw market derivatives data, map structural market liquidity, evaluate forward-looking risk, and generate actionable trading insights for a $10 Million USD Notional gold position.

## Core Project Goals

### 1. Automated Data Ingestion & Centralization
* **Objective:** Eliminate manual copy-pasting and human error from daily reporting.
* **Execution:** Utilize an automated parser ("State Machine") to ingest messy, multi-layered CME Volume & Open Interest (VOI) reports and Bloomberg derivatives outputs, storing them historically within a local SQLite database (`gold_master.db`).

### 2. Mapping Institutional Support & Resistance (Billion-Dollar Walls)
* **Objective:** Identify physical liquidity barriers where major market participants defend positions.
* **Execution:** Convert raw Open Interest contracts into USD Notional values ($\text{Open Interest} \times 100 \text{ oz} \times \text{Strike Price}$). Group by Call options (Resistance Ceilings) and Put options (Support Floors).

### 3. Short-Term Price Gravity, Gamma Pinning & Flow Velocity
* **Objective:** Forecast tactical weekly price boundaries, expiration pins, and active session bias.
* **Execution:** Segregate Weekly and Monthly option tenors. Isolate high-concentration strikes to calculate "Maximum Pain" zones. Critically, incorporate the **`Change` column metrics** to track net daily Open Interest velocity—differentiating between fresh institutional positioning vs. panic liquidation.

### 4. Quantifying Institutional Bias & Volatility Skew
* **Objective:** Measure underlying systemic fear and institutional hedging demand.
* **Execution:** Cross-reference aggregate Put/Call Notional imbalances against the Bloomberg Volatility Surface to capture changes in out-of-the-money skew and directional bias.

### 5. Dynamic Value at Risk (VaR) Engine ($10M Notional Baseline)
* **Objective:** Monitor forward-looking tail risk for a standardized $10,000,000 USD Notional gold portfolio.
* **Execution:** Calculate parametric, volatility-adjusted VaR across 1-Day, 1-Week, and 1-Month horizons using live Implied Volatility ($\sigma$) scaled via the square root of time, evaluated at strict confidence intervals (95% and 99%).

### 6. Automated Visual Output
* **Objective:** Translate millions of data points into instant, executive-level visual intelligence.
* **Execution:** Generate automated daily positioning charts (`gold_options_positioning.png`) highlighting critical walls, expected moves, and risk thresholds.