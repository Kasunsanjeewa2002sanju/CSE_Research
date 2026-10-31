
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from cse.scenario import run_scenario


def test_returns_dict():
    assert isinstance(run_scenario("President announces election", "", "2024-06-15"), dict)

def test_required_keys():
    out = run_scenario("President announces election", "", "2024-06-15")
    for k in ["input","extraction","market_context","scenarios","impact",
              "historical_evidence","explanation"]:
        assert k in out

def test_scenarios_true_false():
    out = run_scenario("President announces election", "", "2024-06-15")
    assert "TRUE" in out["scenarios"] and "FALSE" in out["scenarios"]

def test_horizons():
    out = run_scenario("President announces election", "", "2024-06-15")
    for h in ["1","2","5","10"]:
        assert h in out["scenarios"]["TRUE"]["horizons"]
        assert h in out["scenarios"]["FALSE"]["horizons"]

def test_intervals_80_95():
    out = run_scenario("President announces election", "", "2024-06-15")
    h1 = out["scenarios"]["TRUE"]["horizons"]["1"]
    assert h1["interval_80"]["coverage_pct"] == 80.0
    assert h1["interval_95"]["coverage_pct"] == 95.0

def test_prob_up_range():
    out = run_scenario("President announces election", "", "2024-06-15")
    for sc in ("TRUE","FALSE"):
        for h in out["scenarios"][sc]["horizons"]:
            p = out["scenarios"][sc]["horizons"][h]["prob_up"]
            assert 0.0 <= p <= 1.0

def test_evidence_block():
    out = run_scenario("President announces election", "", "2024-06-15")
    for k in ["n_events","mean_car","permutation_pvalue","evidence_strength"]:
        assert k in out["historical_evidence"]
