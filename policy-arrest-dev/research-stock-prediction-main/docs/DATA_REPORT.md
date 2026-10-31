# PolitiTrade LK — Dataset Inventory & Data Quality Report

Generated: 2026-10-19 19:06:59

## 1. Overview of Data Assets

| Asset Category | Source Location | Format | Raw Count | Scope & Coverage |
| :--- | :--- | :--- | :--- | :--- |
| **Historical Stock Data** | `Dataset-Stock/` | Excel (.xls, .xlsx), CSV, Parquet | 9,772 Trading Days | 1985-01-02 to 2025-12-31 (ASPI, S&P SL20, 20+ Sectors, Turnover) |
| **Government Policies** | `Dataset-Events/Government_Policies(1).csv` | CSV | 70 Records | 2000-02-14 to 2025-02-17 (Budgets, Tax, Monetary, IMF, Foreign Exchange) |
| **Political Arrests** | `Dataset-Events/Political_Arrests.csv` | CSV | 34 Records | 2000-11-03 to 2024-10-31 (Arrests, Remands, Sentencings, Pardons, Parliamentary) |
| **Aliases Registry** | `Dataset-Events/aliases.yml` | YAML | Structured Entities | Political Figures, Parties, Regulatory & Investigatory Institutions |
| **Trusted Sources** | `backend/app/news/trusted_sources.yml` | YAML | Tiered Registry | Tier 1 (Official), Tier 2 (International), Tier 3 (Sri Lankan Broadcasters/Press) |

---

## 2. Colombo Stock Exchange (CSE) Historical Market Data

- **Primary Target Instrument:** All Share Price Index (**ASPI**)
  - Earliest Observation: `1985-01-02`
  - Latest Observation: `2025-12-31`
  - Total Trading Sessions: **9,772**
  - Minimum ASPI Value: `260.00`
  - Maximum ASPI Value: `13,462.39`
  - Data Completeness: 100% valid daily closing prices across active sessions.
- **Secondary Target Instrument:** S&P Sri Lanka 20 (**S&P SL20**)
  - Introduced in 2012; active daily values tracked from mid-2012 through 2025.
- **Market Activity Statistics:**
  - `Turnover_Equity_Mn`, `Shares_Traded_Thousand`, `Trades_Count`, `Market_Cap_Mn`.
  - Available on daily basis from 2001 to 2025.
- **Sector Indices:**
  - 20+ industry group sectors tracked across the historical period.
- **Data Hygiene Protocol:**
  - Zero synthetic price generation.
  - Forward-filling across missing sessions is forbidden; only actual active market dates constitute the trading calendar.
  - Return metric: Daily percentage return $R_t = (P_t / P_{t-1}) - 1$ and log returns.

---

## 3. Government Policy Dataset Validation

- **Total Records:** **70**
- **Temporal Span:** `2000-02-14` to `2025-02-17`
- **Identified Data Challenges & Resolutions:**
  1. *Policy_Type Homogeneity:* In raw data, 60 out of 70 records are labeled generically as "Fiscal Policy".
     - *Resolution:* Mapped into a 10-category derived taxonomy (Budget Changes, Tax Changes, Monetary Policy & Interest Rates, Foreign Exchange Policy, IMF & Debt Restructuring, Investment & Privatisation, Trade & Import Restrictions, Price Controls & Subsidies, Security & Emergency Measures, Political & Constitutional Decisions).
  2. *Policy_Magnitude Invariance:* The raw column lacks variance (predominantly "Major").
     - *Resolution:* Excluded as a predictive feature to prevent uninformative bias.
  3. *Sparse Political Metadata:* Person columns (`President_if_Relevant`, `Prime_Minister_if_Relevant`, `Finance_Minister_if_Relevant`) contain nulls.
     - *Resolution:* Imputed deterministically from historical administration timelines using `aliases.yml` where verified, otherwise preserved as unrecorded without inventing false claims.
  4. *Multi-Phase Policies:* E.g., VAT Act 2002 announcement vs. enactment; Rupee floating announcements.
     - *Resolution:* Grouped into clustered event families using normalized IDs and parent-child tracking.

---

## 4. Political Arrest Dataset Validation

- **Total Records:** **34**
- **Temporal Span:** `2000-11-03` to `2024-10-31`
- **Identified Data Challenges & Resolutions:**
  1. *Multi-Entity 'Person_Name':* Strings like `"General Anuruddha Ratwatte, Criminal Investigation Department (CID), Teldeniya Magistrate Court"` contain both persons and state bodies.
     - *Resolution:* Parsed into primary subject, secondary entities, and investigating/judicial institutions.
  2. *Misclassified Event Subtypes:* Raw `Detained_or_Remanded` labels presidential pardons (e.g. S.B. Dissanayake 2006, Sarath Fonseka 2012) as "Remanded".
     - *Resolution:* Recategorized into 7 legal event subtypes: Arrest, Detention or Remand, Sentencing, Court Proceedings, Pardon or Release, Parliamentary Action, Other Legal Development.
  3. *Presumption of Innocence:* No event or record is treated as evidence of criminal guilt. All events are recorded strictly as legal/investigatory events.

---

## 5. Summary Quality Verdict

- The historical dataset provides exceptional longitudinal depth (40 years of daily ASPI, 25 years of turnover statistics).
- Both political event datasets have been fully inventoried, audited, and prepared for event-study and machine-learning modeling.
