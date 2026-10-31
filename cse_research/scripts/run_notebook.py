"""CLI helper to execute and persist Jupyter/Jupytext notebooks with cell outputs (Rule R6)."""

import argparse
import sys
from pathlib import Path

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from cse.utils.notebook_runner import execute_notebook


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute notebook and save with outputs")
    parser.add_argument("notebook", type=str, help="Path to notebook (.py or .ipynb)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output executed notebook path")
    parser.add_argument("--timeout", "-t", type=int, default=1200, help="Execution timeout in seconds")

    args = parser.parse_args()
    dest = execute_notebook(args.notebook, output_path=args.output, timeout=args.timeout)
    print(f"Executed notebook saved to: {dest}")


if __name__ == "__main__":
    main()
