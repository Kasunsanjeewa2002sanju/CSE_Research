"""Notebook execution harness for Colab-style persistent outputs (Rule R6)."""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from cse.utils.logger import get_logger

logger = get_logger("cse.notebook_runner")


def execute_notebook(
    input_path: str,
    output_path: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    timeout: int = 1200,
) -> Path:
    """Execute a Jupyter/Jupytext notebook and save it with all cell outputs.

    Parameters
    ----------
    input_path : str
        Path to source notebook (.ipynb or .py via jupytext).
    output_path : Optional[str]
        Path to save executed notebook with outputs. If None, saves to notebooks/executed/.
    parameters : Optional[Dict[str, Any]]
        Parameters dictionary to pass via papermill.
    timeout : int
        Maximum execution time per cell or notebook in seconds.

    Returns
    -------
    Path
        Path to the executed output notebook.
    """
    src_file = Path(input_path)
    if not src_file.exists():
        raise FileNotFoundError(f"Notebook not found: {src_file.resolve()}")

    # Determine destination
    if output_path is None:
        exec_dir = src_file.parent / "executed"
        if not exec_dir.exists():
            exec_dir = Path("notebooks/executed")
        exec_dir.mkdir(parents=True, exist_ok=True)
        dest_file = exec_dir / f"{src_file.stem}_executed.ipynb"
    else:
        dest_file = Path(output_path)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert .py to .ipynb via jupytext if needed
    run_input = src_file
    temp_ipynb = None
    if src_file.suffix == ".py":
        import jupytext
        import nbformat
        temp_ipynb = dest_file.parent / f"_temp_{src_file.stem}.ipynb"
        logger.info(f"Converting Jupytext source {src_file} -> {temp_ipynb}")
        nb = jupytext.read(str(src_file))
        with open(temp_ipynb, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)
        run_input = temp_ipynb

    try:
        # Try running with papermill first
        cmd_exec = [
            sys.executable,
            "-m",
            "papermill",
            str(run_input),
            str(dest_file),
            "--execution-timeout",
            str(timeout),
        ]
        if parameters:
            for k, v in parameters.items():
                cmd_exec.extend(["-p", str(k), str(v)])

        logger.info(f"Executing notebook: {' '.join(cmd_exec)}")
        subprocess.run(cmd_exec, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Papermill execution failed or not installed; falling back to nbconvert...")
        cmd_nbconvert = [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            str(run_input),
            "--output",
            str(dest_file.resolve()),
        ]
        subprocess.run(cmd_nbconvert, check=True)
    finally:
        if temp_ipynb and temp_ipynb.exists():
            try:
                temp_ipynb.unlink()
            except OSError:
                pass

    logger.info(f"Successfully executed and saved notebook at: {dest_file}")
    return dest_file
