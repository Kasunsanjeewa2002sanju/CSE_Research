"""Root workspace launcher for CSE Research Backend."""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "cse_research" / "run_backend.py"

if __name__ == "__main__":
    if not TARGET.exists():
        print(f"Error: Target runner {TARGET} not found.", file=sys.stderr)
        sys.exit(1)
    
    # Forward all arguments directly to cse_research/run_backend.py
    cmd = [sys.executable, str(TARGET)] + sys.argv[1:]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)
