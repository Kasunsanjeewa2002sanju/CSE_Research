"""Master verification runner executing Stage 1 through Stage 8 diagnostics sequentially."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root and src/scripts are in sys.path
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set cache directory to local folder to prevent permissions issues
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / "data" / "cache" / "matplotlib"))

from cse.utils.config import find_project_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cse.verify_all")

ROOT_DIR = find_project_root()
VERIFICATION_DIR = ROOT_DIR / "reports" / "verification"
MASTER_DIR = VERIFICATION_DIR / "master"


def load_manifest(stage: str) -> List[Dict[str, Any]]:
    """Read a stage manifest.json file."""
    manifest_file = VERIFICATION_DIR / stage / "manifest.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.warning("Could not read %s: %s", manifest_file, e)
    return []


def run_all_stages() -> Dict[str, Any]:
    """Execute all verification stages sequentially with fault isolation."""
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    logger.info("Starting Master Verification Suite for Stages 1 to 8...")

    stages_to_run = [
        ("stage1", "scripts.verify_stage1", "run_stage1_verification"),
        ("stage2", "scripts.verify_stage2", "run_stage2_verification"),
        ("stage3", "scripts.verify_stage3", "run_stage3_verification"),
        ("stage4", "scripts.verify_stage4", "run_stage4_verification"),
        ("stage5", "scripts.verify_stage5", "run_stage5_verification"),
        ("stage6", "scripts.verify_stage6", "run_stage6_verification"),
        ("stage7", "scripts.verify_stage7", "run_stage7_verification"),
        ("stage8", "scripts.verify_stage8", "run_stage8_verification"),
    ]

    results: List[Dict[str, Any]] = []

    for stage_name, mod_name, func_name in stages_to_run:
        logger.info(">>> Executing %s (%s)...", stage_name.upper(), mod_name)
        stage_start = time.time()
        try:
            mod = __import__(mod_name, fromlist=[func_name])
            func = getattr(mod, func_name)
            res = func()
            stage_elapsed = time.time() - stage_start
            
            manifest = load_manifest(stage_name)
            charts_count = len(manifest) if manifest else res.get("charts_count", 0)

            results.append({
                "stage": stage_name,
                "charts": charts_count,
                "status": res.get("status", "PASS"),
                "key_metric": res.get("key_metric", "Completed"),
                "elapsed_sec": round(stage_elapsed, 2),
                "error": None,
            })
        except Exception as e:
            stage_elapsed = time.time() - stage_start
            tb = traceback.format_exc()
            logger.error("Failed executing %s: %s\n%s", stage_name, e, tb)
            manifest = load_manifest(stage_name)
            results.append({
                "stage": stage_name,
                "charts": len(manifest),
                "status": "FAIL",
                "key_metric": f"Error: {type(e).__name__}",
                "elapsed_sec": round(stage_elapsed, 2),
                "error": str(e),
            })

    total_time = round(time.time() - start_time, 2)
    total_charts = sum(r["charts"] for r in results)
    all_passed = all(r["status"] == "PASS" for r in results)

    # Master run summary dict
    summary_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_charts": total_charts,
        "total_time_seconds": total_time,
        "overall_status": "ALL PASSED" if all_passed else "SOME FAILED",
        "stages": results,
    }

    summary_file = MASTER_DIR / "run_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    logger.info("Saved run summary to %s", summary_file)

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'CSE NEWS-IMPACT PREDICTION SYSTEM - MASTER VERIFICATION REPORT':^90}")
    print("=" * 90)
    print(f"{'Stage':<10} | {'Charts':<6} | {'Status':<8} | {'Time (s)':<8} | {'Key Metric'}")
    print("-" * 90)
    for r in results:
        print(f"{r['stage']:<10} | {r['charts']:<6} | {r['status']:<8} | {r['elapsed_sec']:<8.2f} | {r['key_metric']}")
    print("=" * 90)
    print(f"Total Charts Saved: {total_charts} | Total Elapsed Time: {total_time:.2f}s | Overall: {summary_data['overall_status']}")
    print("=" * 90 + "\n")

    return summary_data


if __name__ == "__main__":
    run_all_stages()
