# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # 00 - Environment & Scaffold Verification
# Research Stage 0: Verification of environment, rules, configurations, and raw data access.

# +
import sys
from pathlib import Path

# Add src to python path if running standalone
root_dir = Path("..").resolve() if Path("..").resolve().name == "cse_research" else Path(".").resolve()
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import cse
from cse.utils.config import load_config
from cse.utils.seed import seed_everything
from cse.utils.device import get_device_info
from cse.utils.logger import get_logger

logger = get_logger("notebook.smoke")
config = load_config()

print(f"CSE Package Version: {cse.__version__}")
print(f"Project Name: {config['project']['name']}")
print(f"Configured Seed: {config['seed']}")
# -

# ## 1. Hardware Diagnostics
# Automatic detection with CPU fallback (Rule R7).

# +
device_meta = get_device_info()
print("Hardware Metadata:")
for k, v in device_meta.items():
    print(f"  {k}: {v}")
# -

# ## 2. Raw Data Integrity
# Ensure raw input files are present and uncorrupted.

# +
raw_dir = root_dir / "data" / "raw"
for filename in ["CSE_data.csv", "Elections.csv"]:
    filepath = raw_dir / filename
    assert filepath.exists(), f"Missing raw file: {filename}"
    print(f"Found {filename} ({filepath.stat().st_size:,} bytes)")
# -
