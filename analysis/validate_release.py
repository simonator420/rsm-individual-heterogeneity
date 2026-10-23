"""Validate that the compact release contains the expected inputs and outputs."""

from pathlib import Path
import json
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
data = ROOT / "data" / "pone.0219295.s001.csv"
results = ROOT / "results"

assert data.exists(), data
raw = pd.read_csv(data)
assert raw.shape == (1250, 661), raw.shape
assert set(raw["D.Name"].unique()) >= {"Athlete 10"}

primary = pd.read_csv(results / "primary_high_low_contrasts.csv")
assert len(primary) == 7
assert (primary["ci95_low_pp"] <= 0).all()
assert (primary["ci95_high_pp"] >= 0).all()

summary = json.loads((results / "final_quality_gate_summary.json").read_text())
assert summary["loao"]["n_athletes"] == 9
assert summary["loao"]["all_folds_converged"] is True
assert abs(summary["loao"]["rmse_pp"] - 5.68) < 0.02
assert abs(summary["loao"]["coverage_95"] - 0.929) < 0.002
print("Release validation passed.")

