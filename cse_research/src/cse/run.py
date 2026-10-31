"""Stage execution CLI runner for CSE Research (Rule R5, R7, R10).

Usage:
    python -m cse.run --stage 0
    python -m cse.run --stage 1
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

from cse.utils.config import load_config
from cse.utils.seed import seed_everything
from cse.utils.device import get_device_info
from cse.utils.logger import get_logger, setup_logger


def execute_stage(stage: int, config: Dict[str, Any]) -> int:
    """Execute the pipeline steps corresponding to the specified stage.

    Parameters
    ----------
    stage : int
        Stage index to execute.
    config : Dict[str, Any]
        Parsed project configuration dictionary.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure).
    """
    logger = get_logger("cse.run")
    logger.info(f"--- Initializing Stage {stage} Execution ---")

    # Hardware & Seed Logging (Rule R7)
    seed = config.get("seed", 42)
    applied_seed = seed_everything(seed)
    device_info = get_device_info()
    logger.info(f"Applied Random Seed: {applied_seed}")
    logger.info(f"Active Hardware Device: {device_info['device_type']} ({device_info['device_name']})")

    if stage == 0:
        logger.info("Executing Stage 0: Environment Verification & Smoke Test")
        logger.info(f"Project Name: {config.get('project', {}).get('name')}")
        logger.info(f"Active Horizons: {list(config.get('horizons', {}).keys())}")
        logger.info("Stage 0 scaffold validation passed successfully.")
        return 0

    elif stage == 1:
        logger.info("Executing Stage 1: Data Ingestion & Integrity Validation")
        import subprocess
        # Run stage 1 audit script using current Python interpreter
        script_path = Path("scripts/stage1_audit.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage1_audit.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("Stage 1 completed successfully.")
        return res.returncode

    elif stage == 2:
        logger.info("Executing Stage 2: Event Calendar Construction & Trading Day Mapping")
        import subprocess
        script_path = Path("scripts/stage2_events.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage2_events.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("Stage 2 completed successfully.")
        return res.returncode

    elif stage == 3:
        logger.info("Executing Stage 3: Validation Protocol Definition & Shared Evaluation Harness")
        import subprocess
        script_path = Path("scripts/stage3_validation_harness.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage3_validation_harness.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("Stage 3 completed successfully.")
        return res.returncode

    elif stage == 4:
        logger.info("Executing Stage 4: Event Study Analysis on ASPI around Electoral Stages")
        import subprocess
        script_path = Path("scripts/stage4_event_study.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage4_event_study.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("Stage 4 completed successfully.")
        return res.returncode

    elif stage == 5:
        logger.info("Executing Stage 5: Feature Engineering Matrix, Pipelines & Sequence Window Generation")
        import subprocess
        script_path = Path("scripts/stage5_features.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage5_features.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        logger.info("Stage 5 completed successfully.")
        return res.returncode

    elif stage == 6:
        logger.info("Executing Stage 6: Statistical & Shallow ML Forecasting Models")
        import subprocess
        script_path = Path("scripts/stage6_train_eval.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage6_train_eval.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        return res.returncode

    elif stage == 9:
        logger.info("Executing Stage 9: Final Model Comparison, Statistical Testing & Selection")
        import subprocess
        script_path = Path("scripts/stage9_model_selection.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage9_model_selection.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        return res.returncode

    elif stage == 10:
        logger.info("Executing Stage 10: Semantic Event Extraction & Prompt Injection Defense")
        import subprocess
        script_path = Path("scripts/stage10_validate.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage10_validate.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        return res.returncode

    elif stage == 11:
        logger.info("Executing Stage 11: Counterfactual Scenario Back-Testing Engine")
        import subprocess
        script_path = Path("scripts/stage11_backtest.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage11_backtest.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        return res.returncode

    elif stage == 12:
        logger.info("Executing Stage 12: Live News Ingestion & Scenario Evaluation Pipeline")
        from cse.news.pipeline import NewsPipeline
        pipeline = NewsPipeline()
        summary = pipeline.run(since="24h")
        logger.info(f"Stage 12 completed successfully: {summary}")
        return 0 if summary.get("status") == "SUCCESS" else 1

    elif stage == 13:
        logger.info("Executing Stage 13: Skeptical Audit & Research Report Asset Generation")
        import subprocess
        script_path = Path("scripts/stage13_audit_and_report.py")
        if not script_path.exists():
            script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "stage13_audit_and_report.py"
        res = subprocess.run([sys.executable, str(script_path)], check=True)
        return res.returncode

    else:
        logger.error(f"Unrecognized stage number: {stage}.")
        return 1



def main() -> None:
    """CLI Entry point for python -m cse.run (--stage N or --all)."""
    parser = argparse.ArgumentParser(
        description="CSE Research Pipeline Stage Runner (SLIIT Research)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        "-s",
        type=int,
        default=None,
        help="Stage number to execute (e.g. 0, 1, 2, ...)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Execute all backend pipeline stages (0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13) end-to-end as one.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Optional custom path to config.yaml",
    )

    args = parser.parse_args()

    if not args.all and args.stage is None:
        parser.error("Must specify either --stage <number> or --all.")

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize structured logger
    log_file = config.get("logging", {}).get("log_file", "results/logs/cse_research.log")
    setup_logger(name="cse.run", log_file=log_file)

    if args.all:
        logger = get_logger("cse.run")
        logger.info("=== Executing Full Research Backend Pipeline End-to-End ===")
        all_stages = [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13]
        for stg in all_stages:
            print(f"\n{'='*78}\n  RUNNING STAGE {stg}\n{'='*78}")
            code = execute_stage(stg, config)
            if code != 0:
                logger.error(f"Stage {stg} failed with exit code {code}. Aborting pipeline.")
                print(f"Error: Stage {stg} failed with code {code}", file=sys.stderr)
                sys.exit(code)
        logger.info("=== All Backend Pipeline Stages Completed Successfully! ===")
        print(f"\n{'='*78}\n  FULL BACKEND PIPELINE COMPLETED SUCCESSFULLY!\n{'='*78}\n")
        sys.exit(0)

    exit_code = execute_stage(args.stage, config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
