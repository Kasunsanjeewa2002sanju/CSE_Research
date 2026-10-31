
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import os


def test_backtest_outputs_exist():
    # Back-test files created by running the backtest script
    root = Path(__file__).resolve().parents[2]
    assert (root / "results" / "scenario").is_dir()

def test_engine_callable():
    from cse.scenario import run_scenario
    out = run_scenario("President announces election", "", "2024-06-15")
    assert "scenarios" in out
