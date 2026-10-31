# Results Directory Hierarchy (Rule R1, R6)

All outputs must be written to disk in persistent files:
- `metrics/`: Standardized evaluation metric tables per model, phase, and horizon (`.json`, `.csv`).
- `predictions/`: Out-of-sample prediction arrays with schema `[date, actual_log_return, pred_log_return, pred_direction, uncertainty]` (`.parquet` or `.csv`).
- `figures/`: Diagnostic plots, return distributions, event study charts, equity curves (`.png`, `.pdf`).
- `tables/`: Summary latex/markdown tables for reports and papers.
- `logs/`: Structured JSON log files recording runtime, hardware, seeds, and execution trajectories.
