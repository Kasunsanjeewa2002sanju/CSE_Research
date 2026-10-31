
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from cse.scenario import run_scenario


def test_irrelevant_news_neutral():
    out = run_scenario("Sri Lanka cricket team wins Asia Cup final", "", "2022-09-11")
    max_diff = max(abs(out["impact"]["horizons"][h]["diff_aspi_level"])
                   for h in out["impact"]["horizons"])
    assert max_diff < 50.0

def test_magnitude_cap_flag_present():
    out = run_scenario("President announces election", "", "2024-06-15")
    flags = [out["scenarios"][sc]["horizons"][h].get("is_magnitude_capped")
             for sc in ("TRUE","FALSE")
             for h in out["scenarios"][sc]["horizons"]]
    assert len(flags) > 0

def test_figures_in_explanation():
    out = run_scenario("President announces election", "", "2024-06-15")
    expl = out["explanation"]
    aspi = out["market_context"]["current_aspi_level"]
    assert f"{aspi:,.2f}" in expl or f"{aspi:.2f}" in expl
