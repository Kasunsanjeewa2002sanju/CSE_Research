"""
Master Unified Backend Runner for Colombo Stock Exchange (CSE) Research & Live Platform.

Runs the complete backend stack in a single command:
1. Validates Python environment and dependencies (auto-detects virtualenv).
2. (Optional) Executes the complete test suite (122 tests) if --test is passed.
3. Executes complete pipeline stages (0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13) end-to-end.
4. Performs immediate live news ingestion crawl.
5. Launches the FastAPI live service with Uvicorn (which auto-spawns the continuous
   live news and market polling scheduler in the background).

Usage:
    # Run entire pipeline reproduction + launch live backend API server:
    python run_backend.py

    # Fast start: launch backend API server immediately (skip pipeline recalculation):
    python run_backend.py --server-only

    # Run full test suite first, then pipeline, then launch server:
    python run_backend.py --test

    # Run pipeline stages 0-13 only and exit (no persistent server):
    python run_backend.py --pipeline-only
"""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Paths configuration
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR if (SCRIPT_DIR / "src" / "cse").exists() else (SCRIPT_DIR / "cse_research")
WORKSPACE_ROOT = PROJECT_ROOT.parent if PROJECT_ROOT.name == "cse_research" else PROJECT_ROOT

os.chdir(PROJECT_ROOT)

# ---------------------------------------------------------------------------
# 1. Environment & Virtualenv Auto-Detection
# ---------------------------------------------------------------------------
def ensure_virtualenv():
    """Ensure running inside the project's .venv. If not, re-executes with .venv python."""
    venv_dir = PROJECT_ROOT / ".venv"
    if not venv_dir.exists():
        # Check workspace root
        if (WORKSPACE_ROOT / ".venv").exists():
            venv_dir = WORKSPACE_ROOT / ".venv"

    if venv_dir.exists():
        if sys.platform == "win32":
            venv_python = venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = venv_dir / "bin" / "python"

        if venv_python.exists():
            # Compare current sys.executable with venv_python
            try:
                current_exe = Path(sys.executable).resolve()
                target_exe = venv_python.resolve()
                if current_exe != target_exe:
                    print(f"[ENV] Switching to virtual environment Python: {target_exe}")
                    # Re-execute with target python
                    env = os.environ.copy()
                    # Ensure PYTHONPATH includes src, backend, and workspace root
                    src_dir = str(PROJECT_ROOT / "src")
                    backend_dir = str(WORKSPACE_ROOT / "backend")
                    root_dir = str(WORKSPACE_ROOT)
                    paths = [src_dir, backend_dir, root_dir]
                    existing_pythonpath = env.get("PYTHONPATH", "")
                    if existing_pythonpath:
                        paths.append(existing_pythonpath)
                    env["PYTHONPATH"] = os.pathsep.join(paths)

                    result = subprocess.run([str(target_exe), str(Path(__file__).resolve())] + sys.argv[1:], env=env)
                    sys.exit(result.returncode)
            except Exception as e:
                print(f"[ENV WARNING] Could not verify virtualenv transition: {e}")

    # Set up PYTHONPATH for current process
    src_dir = str(PROJECT_ROOT / "src")
    backend_dir = str(WORKSPACE_ROOT / "backend")
    root_dir = str(WORKSPACE_ROOT)
    for p in [src_dir, backend_dir, root_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)
    
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [src_dir, backend_dir, root_dir] + ([os.environ["PYTHONPATH"]] if "PYTHONPATH" in os.environ else [])
    )

ensure_virtualenv()

# ---------------------------------------------------------------------------
# 2. Dependency Sanity Check
# ---------------------------------------------------------------------------
def check_dependencies():
    """Check required dependencies and warn if missing."""
    missing = []
    for pkg in ["fastapi", "uvicorn", "feedparser", "apscheduler", "pandas", "yaml"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[WARNING] Missing dependencies: {missing}")
        print("[INFO] Attempting to install requirements...")
        req_file = PROJECT_ROOT / "requirements.txt"
        if req_file.exists():
            # Try uv first, then pip
            uv_cmd = shutil.which("uv")
            if uv_cmd:
                cmd = [uv_cmd, "pip", "install", "-r", str(req_file)]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
            subprocess.run(cmd, check=False)


# ---------------------------------------------------------------------------
# 3. Main Orchestration
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Unified All-In-One Backend Runner for CSE Research & Live Scenario Engine.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Execute full test suite (pytest tests) before running pipeline.",
    )
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Skip pipeline recalculation and launch live API server immediately.",
    )
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Alias for --server-only: do not re-run stages 0 to 13.",
    )
    parser.add_argument(
        "--pipeline-only",
        action="store_true",
        help="Execute stages 0 to 13 end-to-end and exit without starting persistent server.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind Uvicorn server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind Uvicorn server.",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload for Uvicorn.",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("      COLOMBO STOCK EXCHANGE (CSE) RESEARCH & LIVE ENGINE")
    print("                     UNIFIED BACKEND RUNNER")
    print("=" * 80)
    print(f"Working Directory  : {PROJECT_ROOT}")
    print(f"Python Interpreter : {sys.executable}")
    print(f"Python Version     : {sys.version.split()[0]}")
    print("=" * 80)

    check_dependencies()

    skip_pipeline = args.server_only or args.skip_pipeline

    # Step A: Optional full pytest suite
    if args.test:
        print("\n" + "#" * 80)
        print("  STEP 1: RUNNING FULL TEST SUITE (pytest)")
        print("#" * 80)
        res = subprocess.run([sys.executable, "-m", "pytest", "tests"], check=False)
        if res.returncode != 0:
            print("\n[ERROR] Tests failed! Aborting backend execution.", file=sys.stderr)
            sys.exit(res.returncode)
        print("\n[OK] All test suites passed successfully!")

    # Step B: Run empirical research pipeline stages 0 to 13
    if not skip_pipeline:
        print("\n" + "#" * 80)
        print("  STEP 2: EXECUTING REPRODUCIBLE RESEARCH PIPELINE (STAGES 0 to 13)")
        print("#" * 80)
        print("Executing modular stages: Smoke, Ingestion, Events, Splits, Feature Matrix,")
        print("Model Comparison, Validation, Backtesting, Live News Crawl & Audit Report...")
        
        res = subprocess.run([sys.executable, "-m", "cse.run", "--all"], check=False)
        if res.returncode != 0:
            print(f"\n[ERROR] Pipeline failed with exit code {res.returncode}", file=sys.stderr)
            sys.exit(res.returncode)

        print("\n[OK] Complete Research Pipeline Stages (0 to 13) Finished Successfully!")
    else:
        print("\n[INFO] Skipping pipeline recalculation (--server-only or --skip-pipeline enabled).")

    # Step C: If pipeline-only, stop here
    if args.pipeline_only:
        print("\n" + "=" * 80)
        print("  ALL REQUESTED PIPELINE STAGES COMPLETED. EXITING (--pipeline-only).")
        print("=" * 80)
        sys.exit(0)

    # Step D: Launch FastAPI / Uvicorn Server with background scheduler
    print("\n" + "#" * 80)
    print(f"  STEP 3: LAUNCHING LIVE FASTAPI SERVER (UVICORN) ON {args.host}:{args.port}")
    print("#" * 80)
    print("Services starting:")
    print(f"  - REST API & Endpoints   : http://{args.host}:{args.port}")
    print(f"  - Interactive API Docs   : http://{args.host}:{args.port}/docs")
    print(f"  - Health Endpoint        : http://{args.host}:{args.port}/health")
    print(f"  - Scenario Predict API   : http://{args.host}:{args.port}/predict")
    print(f"  - Market SSE Stream      : http://{args.host}:{args.port}/api/v1/stream")
    print("  - Live News Scheduler    : ACTIVE (Background Polling every 30m)")
    print("=" * 80)
    print("Press Ctrl+C to stop the backend server.\n")

    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "cse.news.api:app",
        "--host", args.host,
        "--port", str(args.port),
    ]
    if not args.no_reload:
        uvicorn_cmd.append("--reload")

    try:
        subprocess.run(uvicorn_cmd, check=True)
    except KeyboardInterrupt:
        print("\n[INFO] Backend server stopped by user (Ctrl+C). Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
