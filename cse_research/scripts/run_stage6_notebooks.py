"""Execute Stage 6 notebooks cell by cell, capturing stdout and plots, and saving to notebooks/executed/*.ipynb."""

import base64
import contextlib
import io
import os
import sys
from pathlib import Path

# Setup environment
os.environ["MPLCONFIGDIR"] = "d:/SLIIT/YEAR 04/Research/NEW Dev/cse_research/.cache/matplotlib"
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

root = Path("d:/SLIIT/YEAR 04/Research/NEW Dev/cse_research").resolve()
sys.path.insert(0, str(root / "src"))

import jupytext
import matplotlib.pyplot as plt
import nbformat
from nbformat.v4 import new_output

executed_dir = root / "notebooks" / "executed"
executed_dir.mkdir(parents=True, exist_ok=True)

notebook_specs = [
    ("06_statistical.py", "06_statistical.ipynb"),
    ("06_shallow.py", "06_shallow.ipynb"),
]

for py_name, ipynb_name in notebook_specs:
    py_path = root / "notebooks" / py_name
    out_path = executed_dir / ipynb_name
    print(f"\n--- Processing {py_name} -> {ipynb_name} ---")
    
    nb = jupytext.read(str(py_path))
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
            cell.outputs.append(
                new_output(output_type="stream", name="stdout", text=stdout_val)
            )
            
        # Check if an active matplotlib figure was created
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
    print(f"Successfully executed and saved: {out_path} ({len(nb.cells)} cells)")

print("\nAll Stage 6 notebooks executed and saved to notebooks/executed/ successfully!")
