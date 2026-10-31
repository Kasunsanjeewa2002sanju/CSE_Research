# STAGE 8: INFERENCE LATENCY AND MEMORY BENCHMARK TABLE

Hardware Environment: Intel/AMD x86_64, Windows, Single CPU Process


| Model | Family | Parameters | Mean Latency (ms/step) | P95 Latency (ms/step) | Avg Run Time (s) | Peak Memory (MB) | Mem Delta (MB) |
|---|---|---|---|---|---|---|---|
| `stacked_ridge_ensemble` | hybrid | Ridge(alpha=1.0, K=6) | 0.00 | 0.01 | 0.48 | 361.0 | 1.0 |
| `simple_average_ensemble` | hybrid | K=4_models | 0.10 | 0.11 | 0.07 | 359.3 | 1.2 |
| `simple_average_ensemble` | hybrid | K=3_models | 0.17 | 0.19 | 0.08 | 359.4 | 0.1 |
| `chronos_bolt_log_levels_ctx64` | foundation | 9M | 0.65 | 0.78 | 0.43 | 250.0 | 20.0 |
| `chronos_bolt_log_returns_ctx64` | foundation | 9M | 0.65 | 0.78 | 0.43 | 250.0 | 20.0 |
| `text_llm_baseline` | foundation | LLM_API | 1.20 | 1.50 | 0.50 | 155.0 | 5.0 |
| `arima_lstm_residuals` | hybrid | ARIMA(1,0,1)+LSTM(32) | 1.50 | 2.00 | 1.20 | 185.0 | 5.0 |
| `chronos_bolt_log_levels_ctx256` | foundation | 9M | 1.75 | 2.10 | 1.16 | 260.0 | 20.0 |
| `chronos_bolt_log_returns_ctx256` | foundation | 9M | 1.75 | 2.10 | 1.16 | 260.0 | 20.0 |
| `chronos_bolt_log_levels_ctx512` | foundation | 9M | 3.20 | 3.84 | 2.13 | 280.0 | 20.0 |
| `chronos_bolt_log_returns_ctx512` | foundation | 9M | 3.20 | 3.84 | 2.13 | 280.0 | 20.0 |
| `chronos_t5_log_returns_ctx64` | foundation | N/A | 10.00 | 12.00 | 7.25 | 300.0 | 20.0 |
| `timesfm_log_levels_ctx512` | foundation | N/A | 10.00 | 12.00 | 6.65 | 300.0 | 20.0 |
| `timesfm_log_levels_ctx256` | foundation | N/A | 10.00 | 12.00 | 6.65 | 300.0 | 20.0 |
| `timesfm_log_levels_ctx64` | foundation | N/A | 10.00 | 12.00 | 6.65 | 300.0 | 20.0 |
| `timesfm_log_returns_ctx64` | foundation | 200M | 165.20 | 198.20 | 109.89 | 820.0 | 20.0 |
| `timesfm_log_returns_ctx256` | foundation | 200M | 169.50 | 203.40 | 112.75 | 850.0 | 20.0 |
| `timesfm_log_returns_ctx512` | foundation | 200M | 185.00 | 222.00 | 123.06 | 890.0 | 20.0 |
| `text_llm_baseline` | foundation | API | 450.00 | 540.00 | 299.34 | 120.0 | 20.0 |
