# STAGE 9: PAIRWISE DIEBOLD-MARIANO TEST MATRIX (h=5)
Row model loss minus Column model loss. Negative t-statistic indicates row model has lower forecast error.

### HLN Test Statistics (t-stat):
| Model | CatBoost (Set C) | CatBoost (Set A) | Extra Trees (Set A) | Random Forest (Set A) | TimesFM (ctx64) | Chronos-Bolt (ctx64) |
| --- | --- | --- | --- | --- | --- | --- |
| CatBoost (Set C) | 0.0000 | 1.2617 | 0.1727 | 0.1422 | -0.2724 | -0.3235 |
| CatBoost (Set A) | -1.2617 | 0.0000 | -1.3229 | -0.7876 | -0.4867 | -0.5450 |
| Extra Trees (Set A) | -0.1727 | 1.3229 | 0.0000 | -0.0075 | -0.2757 | -0.3201 |
| Random Forest (Set A) | -0.1422 | 0.7876 | 0.0075 | 0.0000 | -0.2849 | -0.3294 |
| TimesFM (ctx64) | 0.2724 | 0.4867 | 0.2757 | 0.2849 | 0.0000 | -0.2473 |
| Chronos-Bolt (ctx64) | 0.3235 | 0.5450 | 0.3201 | 0.3294 | 0.2473 | 0.0000 |

### Holm-Bonferroni Adjusted p-values:
| Model | CatBoost (Set C) | CatBoost (Set A) | Extra Trees (Set A) | Random Forest (Set A) | TimesFM (ctx64) | Chronos-Bolt (ctx64) |
| --- | --- | --- | --- | --- | --- | --- |
| CatBoost (Set C) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| CatBoost (Set A) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Extra Trees (Set A) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Random Forest (Set A) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| TimesFM (ctx64) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Chronos-Bolt (ctx64) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
