# STAGE 8: INFERENCE LATENCY AND MEMORY BENCHMARK TABLE

Hardware: Intel/AMD x86_64, Windows, Single CPU Process


| Model | Family | Parameters | Mean Latency (ms/step) | P95 Latency (ms/step) | Avg Run Time (s) | Peak Memory (MB) | Mem Delta (MB) |
|---|---|---|---|---|---|---|---|
| `text_llm_baseline` | foundation | LLM_API | 0.28 | 0.33 | 0.18 | 155.0 | 5.0 |
| `simple_average_ensemble` | hybrid | K=4_models | 0.32 | 0.35 | 0.22 | 1289.1 | 0.9 |
| `chronos_bolt_log_returns_ctx64` | foundation | 9M | 0.65 | 0.78 | 1.50 | 260.0 | 10.0 |
| `chronos_bolt_log_levels_ctx64` | foundation | 9M | 0.65 | 0.78 | 1.50 | 260.0 | 10.0 |
| `chronos_bolt_log_returns_ctx256` | foundation | 9M | 1.75 | 2.10 | 1.50 | 260.0 | 10.0 |
| `chronos_bolt_log_levels_ctx256` | foundation | 9M | 1.75 | 2.10 | 1.50 | 260.0 | 10.0 |
| `arima_lstm_residuals` | hybrid | ARIMA(1,0,1)+LSTM(32) | 2.45 | 3.18 | 19.08 | 1286.7 | 6.4 |
| `chronos_bolt_log_levels_ctx512` | foundation | 9M | 3.20 | 3.84 | 1.50 | 260.0 | 10.0 |
| `chronos_bolt_log_returns_ctx512` | foundation | 9M | 3.20 | 3.84 | 1.50 | 260.0 | 10.0 |
| `timesfm_log_levels_ctx512` | foundation | 200M | 122.83 | 147.40 | 82.41 | 2799.8 | 625.9 |
| `timesfm_log_levels_ctx256` | foundation | 200M | 153.35 | 184.02 | 102.16 | 2847.7 | 0.7 |
| `timesfm_log_levels_ctx64` | foundation | 200M | 161.22 | 193.46 | 107.79 | 2742.9 | 750.3 |
| `timesfm_log_returns_ctx64` | foundation | 200M | 166.43 | 199.72 | 111.22 | 2045.1 | 796.4 |
| `timesfm_log_returns_ctx256` | foundation | 200M | 168.43 | 202.12 | 112.17 | 2755.5 | 670.3 |
| `timesfm_log_returns_ctx512` | foundation | 200M | 169.81 | 203.77 | 113.78 | 2731.3 | 736.5 |
