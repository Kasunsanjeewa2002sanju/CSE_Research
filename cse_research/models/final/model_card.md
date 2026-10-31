# MODEL CARD: CatBoost ASPI Weekly Return Forecaster (`catboost_reg_c`)

## Model Details
- **Model Architecture:** CatBoost Gradient Boosted Decision Trees (`CatBoostRegressor`)
- **Version:** 1.0.0 (Frozen Final Release)
- **Date:** October 12, 2026
- **License:** Apache-2.0
- **Input Features:** Feature Set C (57 features: financial technicals, macroeconomic indicators, foreign exchange, interest rates, electoral stage encodings).
- **Primary Forecast Target:** 5-Day Forward ASPI Log Return ($y_{\text{ret}}^{(5)}$).
- **Secondary Target:** 1-Day Forward ASPI Log Return ($y_{\text{ret}}^{(1)}$).

## Intended Use
- **Primary Domain:** Quantitative risk management, portfolio rebalancing, and political regime forecasting on the Colombo Stock Exchange (CSE) All Share Price Index (ASPI).
- **Deployment Horizon:** 1 to 5 trading days forward.
- **Out-of-Scope Use:** High-frequency intraday algorithmic trading; extrapolation to illiquid single-stock securities without cross-asset market depth.

## Training Data & Methodology
- **Training Coverage:** 7,635 daily trading sessions from January 3, 1994 to December 23, 2025.
- **Walk-Forward Validation:** 5 non-overlapping expanding validation windows (2012–2025) guarded by 10-day embargoes (Rule R2).
- **Hyperparameter Selection:** Tuned strictly on inner chronological validation slices (last 15% of historical training blocks).

## Empirical Performance (Out-of-Sample 2012–2025)
- **Weekly Horizon ($h=5$):**
  - **Mean OOS $R^2$:** **0.0548** [95% CI: 0.0312, 0.0784]
  - **Directional Accuracy:** **60.79%** [95% CI: 59.12%, 62.45%]
  - **Pesaran-Timmermann Test:** $PT = 12.15, p < 10^{-30}$ (Highly statistically significant directional predictability)
  - **Phase Consistency:** 5 out of 5 phases beating historical mean baseline (100% stability)
- **Daily Horizon ($h=1$):**
  - **Mean OOS $R^2$:** **0.0897** [95% CI: 0.0650, 0.1144]
  - **Directional Accuracy:** **61.29%** [95% CI: 59.63%, 62.94%]
  - **Diebold-Mariano Test vs Random Walk:** $DM_{\text{HLN}} = -5.78, p = 8.38 \times 10^{-9}$ (Decisively superior to random walk)
  - **Diebold-Mariano Test vs Historical Mean:** $DM_{\text{HLN}} = -5.67, p = 1.57 \times 10^{-8}$

## Limitations & Risks
1. **Regime Shifts:** Extreme non-linear macroeconomic shocks (e.g. 2022 sovereign debt default) may cause transient volatility spikes exceeding tree leaf bounds.
2. **Execution Slippage:** Model predictions assume trading at official market close without execution friction.
3. **Political Shocks:** The model conditions on known electoral stages; unexpected snap dissolutions or emergency court rulings exhibit immediate announcement day price impact before feature updates.
