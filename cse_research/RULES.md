# PERMANENT RULES

R1 REAL DATA ONLY. Use only CSE_data.csv and Elections.csv (plus news fetched live in later stages). Never invent, simulate, hard-code or "illustrate" data, dates, prices, metrics or results. Every number in any report, README or notebook text must be produced by code from a saved results file.
R2 NO LOOKAHEAD. A feature for date t may use only information available at the close of day t. Targets are forward values (t+h). No random shuffling and no random K-fold on time series. Scalers, encoders and imputers are fitted on the training window only.
R3 SUSPICIOUS-RESULT RULE. Daily or weekly direction accuracy above 60%, or out-of-sample R-squared above 0.10 on returns, is almost certainly a bug. Stop, run the leakage tests, and report to me before continuing.
R4 Models predict log returns; levels are reconstructed afterwards. Never train on raw ASPI level as the target.
R5 Every model uses the same protocol: same phases, horizons, metrics and prediction-file schema.
R6 Save everything (models, predictions, metrics, configs, logs, figures). Nothing may exist only on screen.
R7 Reproducibility: seeds in config, pinned requirements, data hashes, library versions and hardware logged per run.
R8 Honest reporting: report negative results. If a model does not beat the naive baseline, say so. No cherry-picking.
R9 Ambiguity: choose the most defensible default, record it with the reason in DECISIONS.md, and continue. Ask me only if the choice changes the research design or needs data I have not supplied.
R10 Stage discipline: do only the current stage. End with STAGE_REPORT.md (what was done, files created, key numbers, problems, open decisions) and STOP.
R11 Do not state external facts from memory (election dates, feed URLs, model availability, library behaviour). Verify from my files or by a live check, record the source, otherwise mark UNKNOWN.
R12 Code quality: a typed, modular package src/cse/, docstrings, unit tests for data and leakage logic. Notebooks only call package code; no logic lives only in notebooks.
