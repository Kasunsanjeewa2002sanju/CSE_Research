# Model Artifact Storage Standard (Rule R5, R6, R7)

Models and their checkpoints are saved adhering strictly to the hierarchy:
```
models/<family>/<model_name>/<phase>/
  ├── model.<bin|pt|pkl|json>
  └── meta.json
```

## Schema for `meta.json`
Every model checkpoint must be accompanied by a `meta.json` documenting:
- `model_id`: Unique identifier (e.g., `stat_arima_p1`)
- `family`: One of `statistical`, `shallow`, `deep`, `foundation`, `hybrid`
- `model_name`: Standardized model name
- `phase`: Associated pipeline phase (e.g., `phase_1`)
- `horizon`: Target forecast horizon (`h1`, `h5`, `h20`)
- `seed`: Random seed used for initialization/training
- `train_date_range`: `[start_date, end_date]`
- `features`: Exact list of input feature names used
- `hyperparameters`: Dictionary of trained hyperparameter settings
- `metrics`: Out-of-sample validation metrics (RMSE, MAE, R2, Direction Accuracy, etc.)
- `environment`: Python version, package versions, device (CPU/GPU), run timestamp
