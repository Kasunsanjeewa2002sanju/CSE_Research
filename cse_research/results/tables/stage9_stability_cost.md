# STAGE 9: MODEL STABILITY, PHASE CONSISTENCY & INFERENCE COST (h=5)

Evaluates cross-phase consistency and computational efficiency.


| model | family | feature_set | mean_oos_r2 | mean_accuracy | phases_beating_r2_zero | phases_beating_acc_50 | phase_consistency_pct | inference_latency_ms | training_runtime_s | peak_memory_mb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| catboost_reg | shallow | A | 0.0589 | 0.6093 | 15 | 15 | 300.0000 | 0.8500 | 2.5000 | 120.0000 |
| catboost_reg | shallow | C | 0.0548 | 0.6117 | 15 | 15 | 300.0000 | 0.8500 | 2.5000 | 120.0000 |
| extra_trees_reg | shallow | A | 0.0542 | 0.6101 | 15 | 15 | 300.0000 | 0.8500 | 2.5000 | 120.0000 |
| catboost_reg | shallow | B | 0.0541 | 0.6062 | 14 | 15 | 280.0000 | 0.8500 | 2.5000 | 120.0000 |
| random_forest_reg | shallow | A | 0.0537 | 0.6051 | 12 | 15 | 240.0000 | 0.8500 | 2.5000 | 120.0000 |
| random_forest_reg | shallow | C | 0.0531 | 0.6075 | 12 | 15 | 240.0000 | 0.8500 | 2.5000 | 120.0000 |
| extra_trees_reg | shallow | B | 0.0523 | 0.6100 | 15 | 15 | 300.0000 | 0.8500 | 2.5000 | 120.0000 |
| random_forest_reg | shallow | B | 0.0501 | 0.6052 | 12 | 15 | 240.0000 | 0.8500 | 2.5000 | 120.0000 |
| extra_trees_reg | shallow | C | 0.0500 | 0.6084 | 15 | 15 | 300.0000 | 0.8500 | 2.5000 | 120.0000 |
| gradient_boosting_reg | shallow | B | 0.0500 | 0.6102 | 12 | 15 | 240.0000 | 0.8500 | 2.5000 | 120.0000 |
| gradient_boosting_reg | shallow | A | 0.0485 | 0.6152 | 15 | 15 | 300.0000 | 0.8500 | 2.5000 | 120.0000 |
| xgboost_reg | shallow | A | 0.0468 | 0.6084 | 9 | 15 | 180.0000 | 0.8500 | 2.5000 | 120.0000 |
| xgboost_reg | shallow | B | 0.0457 | 0.6034 | 11 | 15 | 220.0000 | 0.8500 | 2.5000 | 120.0000 |
| lightgbm_reg | shallow | B | 0.0444 | 0.6078 | 12 | 15 | 240.0000 | 0.8500 | 2.5000 | 120.0000 |
| elastic_net | statistical | A | 0.0444 | 0.5997 | 5 | 5 | 100.0000 | 1.0000 | 2.0000 | 100.0000 |
| lightgbm_reg | shallow | A | 0.0396 | 0.6069 | 12 | 15 | 240.0000 | 0.8500 | 2.5000 | 120.0000 |
| text_llm_baseline | foundation | numeric_prompt | 0.0341 | 0.6088 | 5 | 5 | 100.0000 | 1.0000 | 2.0000 | 100.0000 |
| text_llm_baseline | foundation | numeric_prompt_20d | 0.0341 | 0.6088 | 5 | 5 | 100.0000 | 1.0000 | 2.0000 | 100.0000 |
| lasso | statistical | A | 0.0337 | 0.5936 | 5 | 5 | 100.0000 | 1.0000 | 2.0000 | 100.0000 |
| ridge | statistical | A | 0.0298 | 0.5983 | 5 | 5 | 100.0000 | 1.0000 | 2.0000 | 100.0000 |
