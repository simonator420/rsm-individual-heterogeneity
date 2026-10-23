"""Run the numerical analyses from the repository root."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
for script in ("fit_correlated_hierarchical_model.py", "run_final_quality_gates.py"):
    subprocess.run([sys.executable, str(ROOT / "analysis" / script)], cwd=ROOT, check=True)

