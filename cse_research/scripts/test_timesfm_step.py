import time
import numpy as np
import pandas as pd
from cse.eval.harness import EvaluationHarness
from cse.models.foundation.timesfm_model import TimesFMForecaster

print("Initializing harness...")
harness = EvaluationHarness()
print("Initializing TimesFMForecaster...")
tfm = TimesFMForecaster(context_length=64, series_type="log_returns")
phase_split = harness.splitter.get_phase("P1")
print("Running forecast_validation...")
t0 = time.time()
df_preds, telem = tfm.forecast_validation(harness.df, phase_split, horizon=1)
print(f"SUCCESS in {time.time()-t0:.2f}s! Steps: {len(df_preds)}")
print("Telemetry:", telem)
