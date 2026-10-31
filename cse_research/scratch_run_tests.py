import os
import sys

PROJECT_DIR = r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research"
os.chdir(PROJECT_DIR)
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))

print("Current dir:", os.getcwd())
print("Python:", sys.executable)

import pytest

test_file = os.path.join(PROJECT_DIR, "tests", "test_stage3_storage_stats.py")
args = [
    "-v",
    "--rootdir=" + PROJECT_DIR,
    "-c", os.path.join(PROJECT_DIR, "pytest.ini"),
    test_file
]
print("Running pytest with args:", args)
ret = pytest.main(args)
print("Exit code:", ret)
sys.exit(ret)
