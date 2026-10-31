"""Execute Stage 8 notebook cell by cell, capturing stdout and plots, saving to notebooks/executed/08_foundation_hybrid.ipynb."""

import base64
import contextlib
import io
import os
import sys
from pathlib import Path

# Setup environment
root = Path("d:/SLIIT\YEAR 04/Research/NEW Dev/cse_research").resolve()
os.chdir(root)
os.environ["MPLCONFIGDIR"] = str(root / ".cache" / "matplotlib")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
sys.path.insert(0, str(root / "src"))

import jupytext
import matplotlib.pyplot as plt
import nbformat
from nbformat.v4 import new_output

executed_dir = root / "notebooks" / "executed"
executed_dir.mkdir(parents=True, exist_ok=True)

py_path = root / "notebooks" / "08_foundation_hybrid.py"
out_path = executed_dir / "08_foundation_hybrid.ipynb"

print(f"\n--- Executing {py_path.name} -> {out_path.name} ---")

with open(py_path, "r", encoding="utf-8") as f:
    text = f.read()

nb = jupytext.reads(text, fmt="py:light")
global_env = {"__file__": str(py_path), "__name__": "__main__"}

execution_count = 1
for idx, cell in enumerate(nb.cells):
    if cell.cell_type != "code":
        continue

    cell.execution_count = execution_count
    execution_count += 1
    cell.outputs = []

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    # Close any prior dangling figures
    plt.close("all")

    try:
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            exec(cell.source, global_env)
    except Exception as e:
        err_msg = f"Error in cell {idx}: {e}"
        print(err_msg)
        cell.outputs.append(
            new_output(
                output_type="error",
                ename=type(e).__name__,
                evalue=str(e),
                traceback=[str(e)],
            )
        )
        continue

    stdout_val = stdout_buf.getvalue()
    if stdout_val:
        print(f"Cell {idx} output:\n{stdout_val.strip()}")
        cell.outputs.append(
            new_output(output_type="stream", name="stdout", text=stdout_val)
        )

    # Check if active matplotlib figures were created
    figs = [plt.figure(i) for i in plt.get_fignums()]
    for fig in figs:
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format="png", bbox_inches="tight")
        img_buf.seek(0)
        img_b64 = base64.b64encode(img_buf.read()).decode("utf-8")
        cell.outputs.append(
            new_output(
                output_type="display_data",
                data={"image/png": img_b64, "text/plain": "<Figure size>"},
                metadata={},
            )
        )
    plt.close("all")

with open(out_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"\nSuccessfully executed and saved: {out_path} ({len(nb.cells)} cells)")
