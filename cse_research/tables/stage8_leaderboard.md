# STAGE 8 LEADERBOARD (FOUNDATION & HYBRID MODELS)

Aggregated across 5 Walk-Forward Validation Phases (P1-P5).


| model | family | horizon | oos_r2 | accuracy | balanced_accuracy | rmse | mae |
| --- | --- | --- | --- | --- | --- | --- | --- |
| text_llm_baseline | foundation | 5 | 0.0341 | 0.6088 | 0.5960 | 0.0245 | 0.0174 |
| timesfm_log_returns_ctx64 | foundation | 5 | 0.0297 | 0.5967 | 0.5833 | 0.0245 | 0.0175 |
| timesfm_log_levels_ctx512 | foundation | 5 | 0.0256 | 0.5668 | 0.5727 | 0.0246 | 0.0175 |
| timesfm_log_returns_ctx256 | foundation | 5 | 0.0253 | 0.5942 | 0.5785 | 0.0246 | 0.0176 |
| chronos_bolt_log_returns_ctx64 | foundation | 5 | 0.0243 | 0.5846 | 0.5698 | 0.0246 | 0.0175 |
| timesfm_log_returns_ctx512 | foundation | 5 | 0.0239 | 0.6030 | 0.5895 | 0.0246 | 0.0176 |
| chronos_bolt_log_returns_ctx256 | foundation | 5 | 0.0184 | 0.5894 | 0.5735 | 0.0247 | 0.0176 |
| chronos_bolt_log_returns_ctx512 | foundation | 5 | 0.0161 | 0.5903 | 0.5727 | 0.0247 | 0.0177 |
| chronos_bolt_log_levels_ctx512 | foundation | 5 | 0.0015 | 0.5799 | 0.5648 | 0.0250 | 0.0178 |
| timesfm_log_levels_ctx256 | foundation | 5 | -0.0017 | 0.5544 | 0.5627 | 0.0250 | 0.0178 |
| arima_lstm_residuals | hybrid | 5 | -0.0020 | 0.5179 | 0.5000 | 0.0249 | 0.0179 |
| stacked_ridge_ensemble | hybrid | 5 | -0.0031 | 0.5303 | 0.5006 | 0.0248 | 0.0178 |
| chronos_bolt_log_levels_ctx64 | foundation | 5 | -0.0607 | 0.5594 | 0.5495 | 0.0256 | 0.0184 |
| chronos_bolt_log_levels_ctx256 | foundation | 5 | -0.0768 | 0.5637 | 0.5418 | 0.0260 | 0.0185 |
| timesfm_log_levels_ctx64 | foundation | 5 | -0.0781 | 0.5038 | 0.5042 | 0.0259 | 0.0184 |
| simple_average_ensemble | hybrid | 5 | -0.1661 | 0.5672 | 0.5483 | 0.0273 | 0.0202 |
| chronos_bolt_log_returns_ctx512 | foundation | 1 | 0.0504 | 0.5994 | 0.5899 | 0.0087 | 0.0058 |
| timesfm_log_returns_ctx512 | foundation | 1 | 0.0441 | 0.6081 | 0.5979 | 0.0087 | 0.0059 |
| chronos_bolt_log_returns_ctx256 | foundation | 1 | 0.0427 | 0.5928 | 0.5823 | 0.0087 | 0.0059 |
| timesfm_log_levels_ctx512 | foundation | 1 | 0.0310 | 0.5820 | 0.5894 | 0.0088 | 0.0060 |
| timesfm_log_returns_ctx256 | foundation | 1 | 0.0290 | 0.5936 | 0.5824 | 0.0088 | 0.0059 |
| text_llm_baseline | foundation | 1 | 0.0269 | 0.5828 | 0.5717 | 0.0088 | 0.0059 |
| timesfm_log_levels_ctx256 | foundation | 1 | 0.0116 | 0.5666 | 0.5724 | 0.0089 | 0.0060 |
| chronos_t5_log_returns_ctx64 | foundation | 1 | 0.0048 | 0.6000 | 0.5906 | 0.0070 | 0.0048 |
| timesfm_log_returns_ctx64 | foundation | 1 | 0.0045 | 0.5942 | 0.5839 | 0.0089 | 0.0060 |
| stacked_ridge_ensemble | hybrid | 1 | -0.0051 | 0.5261 | 0.5010 | 0.0089 | 0.0061 |
| arima_lstm_residuals | hybrid | 1 | -0.0098 | 0.4833 | 0.5000 | 0.0090 | 0.0061 |
| chronos_bolt_log_returns_ctx64 | foundation | 1 | -0.0212 | 0.5940 | 0.5837 | 0.0091 | 0.0061 |
| timesfm_log_levels_ctx64 | foundation | 1 | -0.0737 | 0.5208 | 0.5194 | 0.0092 | 0.0063 |
| simple_average_ensemble | hybrid | 1 | -0.1535 | 0.5872 | 0.5765 | 0.0093 | 0.0065 |
| chronos_bolt_log_levels_ctx64 | foundation | 1 | -0.2322 | 0.5670 | 0.5594 | 0.0099 | 0.0068 |
| chronos_bolt_log_levels_ctx512 | foundation | 1 | -0.2716 | 0.5685 | 0.5614 | 0.0101 | 0.0073 |
| chronos_bolt_log_levels_ctx256 | foundation | 1 | -0.4220 | 0.5716 | 0.5590 | 0.0107 | 0.0078 |
