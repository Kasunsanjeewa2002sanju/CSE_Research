
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from cse.scenario import run_scenario


def test_intervals_ordered():
    out = run_scenario("President announces election", "", "2024-06-15")
    for sc in ("TRUE","FALSE"):
        for h in out["scenarios"][sc]["horizons"]:
            hh = out["scenarios"][sc]["horizons"][h]
            for lvl in ("interval_80","interval_95"):
                assert hh[lvl]["log_return_lower"] <= hh[lvl]["log_return_upper"]

def test_95_wider_than_80():
    out = run_scenario("President announces election", "", "2024-06-15")
    for sc in ("TRUE","FALSE"):
        for h in out["scenarios"][sc]["horizons"]:
            hh = out["scenarios"][sc]["horizons"][h]
            w80 = hh["interval_80"]["log_return_upper"] - hh["interval_80"]["log_return_lower"]
            w95 = hh["interval_95"]["log_return_upper"] - hh["interval_95"]["log_return_lower"]
            assert w95 >= w80

def test_true_uses_event_residuals():
    out = run_scenario("President announces election", "", "2024-06-15")
    for h in out["scenarios"]["TRUE"]["horizons"]:
        assert out["scenarios"]["TRUE"]["horizons"][h]["conformal_residuals_used"] == "event"

def test_false_uses_non_event_residuals():
    out = run_scenario("President announces election", "", "2024-06-15")
    for h in out["scenarios"]["FALSE"]["horizons"]:
        assert out["scenarios"]["FALSE"]["horizons"][h]["conformal_residuals_used"] == "non_event"
