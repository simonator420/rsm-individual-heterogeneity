"""Final correlated athlete-level model for the public CMJ dataset.

The script is deliberately reproducible and keeps all QC decisions explicit:
Athlete 10 is excluded from the primary analysis because the High and Mod
blocks are exact duplicates apart from the workload label. The primary outcome
is relative peak-force change from the athlete-by-workload pre-session mean.
In the source CSV, raw label '1' is pre-session, 'P' is immediately
post-session, and '30'/'60'/'180'/'360'/'24'/'48' are 0.5/1/3/6/24/48 h.

The primary model is a parsimonious correlated linear mixed model with:
  * fixed workload-by-time effects and centered trial order;
  * a fully correlated athlete random intercept, High deviation and Mod
    deviation.

The richer six-dimensional random-effects model with workload-specific temporal
deviations is retained as a sensitivity analysis, not as the primary model,
because only nine athletes remain after QC.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pone.0219295.s001.csv"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

POST_TIMES = [0.0, 0.5, 1.0, 3.0, 6.0, 24.0, 48.0]
TIME_MAP = {"P": 0.0, "30": 0.5, "60": 1.0, "180": 3.0, "360": 6.0, "24": 24.0, "48": 48.0}
FIXED_FORMULA = (
    '1 + C(workload, Treatment(reference="Low"))*'
    'C(time_f, Treatment(reference=0.0)) + trial_c'
)
PRIMARY_RANDOM_FORMULA = (
    '1 + C(workload, Treatment(reference="Low"))'
)
RICH_RANDOM_FORMULA = (
    '1 + C(workload, Treatment(reference="Low")) + np.log1p(hours) + '
    'C(workload, Treatment(reference="Low")):np.log1p(hours)'
)


def prepare_data() -> pd.DataFrame:
    raw = pd.read_csv(DATA)
    raw["time_raw"] = raw["D.TimeAfterTraining"].astype(str)
    d = raw[
        raw["D.Training"].isin(["High", "Low", "Mod"])
        & (raw["D.Name"] != "Athlete 10")
    ].copy()
    d["hours"] = d["time_raw"].map(TIME_MAP)

    # Baseline is the mean of the five pre-session CMJs labelled '1' in the
    # same athlete-by-workload cell. Raw label 'P' is immediate post-session.
    baseline = (
        d.loc[d["time_raw"] == "1"]
        .groupby(["D.Name", "D.Training"])["D.MaxForceScaled"]
        .mean()
        .rename("baseline")
    )
    d = d.join(baseline, on=["D.Name", "D.Training"])
    d["y"] = (d["D.MaxForceScaled"] / d["baseline"] - 1.0) * 100.0
    d = d.loc[d["time_raw"].isin(TIME_MAP)].copy()
    d["trial_c"] = d["D.TrialNum"] - 3.0
    d["workload"] = d["D.Training"]
    d["time_f"] = pd.Categorical(d["hours"], categories=POST_TIMES, ordered=True)

    expected = 9 * 3 * 7 * 5
    if len(d) != expected:
        raise ValueError(f"Unexpected primary row count: {len(d)}; expected {expected}")
    if d["D.Name"].nunique() != 9:
        raise ValueError("Unexpected number of athletes after QC")
    if d["y"].isna().any():
        raise ValueError("Missing outcome after baseline construction")
    return d


def design_matrices(d: pd.DataFrame, random_formula: str):
    X = dmatrix(FIXED_FORMULA, d, return_type="dataframe")
    Z = dmatrix(random_formula, d, return_type="dataframe")
    return X, Z


def fit_model(d: pd.DataFrame, random_formula: str):
    X, Z = design_matrices(d, random_formula)
    model = sm.MixedLM(
        endog=d["y"],
        exog=X,
        groups=d["D.Name"],
        exog_re=Z,
        use_sqrt=True,
    )
    all_warnings = []
    last_fit = None
    for method in ("lbfgs", "powell", "nm"):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                fit = model.fit(reml=True, method=method, maxiter=2000, disp=False)
            except Exception as exc:
                all_warnings.append(f"{method}: {exc}")
                continue
        all_warnings.extend(f"{method}: {w.message}" for w in caught)
        last_fit = fit
        if fit.converged:
            return X, Z, fit, all_warnings
    return X, Z, last_fit, all_warnings


def high_low_contrasts(fit, X: pd.DataFrame) -> pd.DataFrame:
    names = list(X.columns)
    k = X.shape[1]
    beta = fit.fe_params.to_numpy()
    cov = fit.cov_params().iloc[:k, :k].to_numpy()
    rows = []
    for time in POST_TIMES:
        c = np.zeros(k)
        c[names.index('C(workload, Treatment(reference="Low"))[T.High]')] = 1.0
        if time != 0.0:
            label = (
                'C(workload, Treatment(reference="Low"))[T.High]:'
                'C(time_f, Treatment(reference=0.0))[T.'
                f"{time:g}"
                "]"
            )
            if label not in names:
                label = (
                    'C(workload, Treatment(reference="Low"))[T.High]:'
                    'C(time_f, Treatment(reference=0.0))[T.'
                    f"{float(time)}"
                    "]"
                )
            c[names.index(label)] = 1.0
        estimate = float(c @ beta)
        se = float(np.sqrt(c @ cov @ c))
        rows.append(
            {
                "time_h": time,
                "estimate_high_minus_low_pp": estimate,
                "se_pp": se,
                "ci95_low_pp": estimate - 1.96 * se,
                "ci95_high_pp": estimate + 1.96 * se,
            }
        )
    return pd.DataFrame(rows)


def diagnostics(d: pd.DataFrame, fit, Z: pd.DataFrame) -> dict:
    re_cov = np.asarray(fit.cov_re)
    residuals = np.asarray(fit.resid)
    fixed = fit.fe_params
    trial_name = "trial_c"
    return {
        "converged": bool(fit.converged),
        "n_observations": int(len(d)),
        "n_athletes": int(d["D.Name"].nunique()),
        "n_random_effect_dimensions": int(Z.shape[1]),
        "reml_log_likelihood": float(fit.llf),
        "residual_scale": float(fit.scale),
        "residual_sd": float(np.sqrt(fit.scale)),
        "random_effect_eigenvalues": [float(x) for x in np.linalg.eigvalsh(re_cov)],
        "random_effect_sd": [float(x) for x in np.sqrt(np.diag(re_cov))],
        "trial_order_estimate_pp_per_trial": float(fixed[trial_name]),
        "trial_order_se": float(np.sqrt(fit.cov_params().loc[trial_name, trial_name])),
        "residual_quantiles_pp": {
            p: float(np.quantile(residuals, p)) for p in [0.0, 0.01, 0.05, 0.5, 0.95, 0.99, 1.0]
        },
    }


def write_summary(primary_fit, primary_X, primary_Z, primary_warnings, rich_fit, rich_X, rich_Z, rich_warnings, robust_fit, robust_X, robust_Z, robust_warnings, d, robust_d):
    contrasts = high_low_contrasts(primary_fit, primary_X)
    contrasts.to_csv(OUT / "primary_high_low_contrasts.csv", index=False)
    robust_contrasts = high_low_contrasts(robust_fit, robust_X)
    robust_contrasts.to_csv(OUT / "winsorized_high_low_contrasts.csv", index=False)

    summary = {
        "data_source": str(DATA),
        "primary_model": {
            "fixed_formula": FIXED_FORMULA,
            "random_formula": PRIMARY_RANDOM_FORMULA,
            "observation_model": "Gaussian REML mixed model; robust residual sensitivity is required before submission",
            "qc": "Athlete 10 excluded; raw label 1 used as pre-session baseline; P retained as 0 h post-session; 0.5-48 h retained",
        },
        "primary_diagnostics": diagnostics(d, primary_fit, primary_Z),
        "rich_sensitivity_diagnostics": diagnostics(d, rich_fit, rich_Z),
        "winsorized_sensitivity_diagnostics": diagnostics(robust_d, robust_fit, robust_Z),
        "warnings": {"primary": primary_warnings, "rich_sensitivity": rich_warnings},
    }
    (OUT / "model_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Final correlated hierarchical model",
        "",
        "## Decision",
        "",
        "The primary model converged with a parsimonious, fully correlated three-dimensional athlete-level random-effects structure. A winsorized outcome sensitivity and a richer six-dimensional temporal sensitivity were also fitted. The primary structure is preferred because only nine athletes remain after QC.",
        "",
        "## Data and model",
        "",
        f"The analysis used {len(d)} post-session trials from {d['D.Name'].nunique()} athletes after excluding Athlete 10. Raw label 1 was used as the pre-session baseline and P was retained as the 0-hour immediate post-session time point. The outcome was relative peak-force change (%) from the athlete-by-workload pre-session mean. Fixed effects were workload, time, workload-by-time interactions and centered trial order. Primary random effects were a fully correlated athlete intercept, High deviation and Mod deviation; a richer workload-by-time random-effects structure was evaluated only as sensitivity.",
        "",
        "## Primary High minus Low contrasts",
        "",
        "| Time | Estimate (percentage points) | 95% CI |",
        "|---:|---:|:---|",
    ]
    for row in contrasts.itertuples(index=False):
        lines.append(f"| {row.time_h:g} h | {row.estimate_high_minus_low_pp:.2f} | {row.ci95_low_pp:.2f} to {row.ci95_high_pp:.2f} |")
    lines += [
        "",
        "## Winsorized sensitivity",
        "",
        "The outcome was winsorized at the empirical 1st and 99th percentiles before refitting the same model. The resulting contrasts are reported below; this is a robustness check, not a replacement for the prespecified primary analysis.",
        "",
        "| Time | Estimate (percentage points) | 95% CI |",
        "|---:|---:|:---|",
    ]
    for row in robust_contrasts.itertuples(index=False):
        lines.append(f"| {row.time_h:g} h | {row.estimate_high_minus_low_pp:.2f} | {row.ci95_low_pp:.2f} to {row.ci95_high_pp:.2f} |")
    pdg = diagnostics(d, primary_fit, primary_Z)
    rdg = diagnostics(d, rich_fit, rich_Z)
    lines += [
        "",
        "## Diagnostics",
        "",
        f"Primary model: converged={pdg['converged']}; REML log-likelihood={pdg['reml_log_likelihood']:.2f}; residual SD={pdg['residual_sd']:.2f} percentage points; smallest random-effects covariance eigenvalue={min(pdg['random_effect_eigenvalues']):.3f}.",
        f"Centered trial order estimate: {pdg['trial_order_estimate_pp_per_trial']:.2f} percentage points per trial (SE {pdg['trial_order_se']:.2f}).",
        f"Six-dimensional workload-by-time random-effects sensitivity: converged={rdg['converged']}; residual SD={rdg['residual_sd']:.2f} percentage points.",
        "",
        "## Manuscript interpretation",
        "",
        "The corrected final correlated model uses the source-consistent pre-session baseline. The main claim should concern individual heterogeneity and uncertainty calibration, not a definitive workload effect.",
        "",
        "The source-consistent reanalysis is complete for the reduced Gaussian primary model, winsorized sensitivity and LOAO calibration. The richer temporal random-effects model is retained as sensitivity only; the manuscript should report optimizer warnings and avoid presenting the small-sample covariance structure as definitive evidence of stable individual time-response parameters.",
    ]
    (OUT / "final_model_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    d = prepare_data()
    primary_X, primary_Z, primary_fit, primary_warnings = fit_model(d, PRIMARY_RANDOM_FORMULA)
    rich_X, rich_Z, rich_fit, rich_warnings = fit_model(d, RICH_RANDOM_FORMULA)
    robust_d = d.copy()
    low_q, high_q = robust_d["y"].quantile([0.01, 0.99])
    robust_d["y"] = robust_d["y"].clip(lower=low_q, upper=high_q)
    robust_X, robust_Z, robust_fit, robust_warnings = fit_model(robust_d, PRIMARY_RANDOM_FORMULA)
    if not primary_fit.converged:
        raise RuntimeError("Primary correlated model did not converge")
    if not robust_fit.converged:
        raise RuntimeError("Winsorized sensitivity model did not converge")
    write_summary(primary_fit, primary_X, primary_Z, primary_warnings, rich_fit, rich_X, rich_Z, rich_warnings, robust_fit, robust_X, robust_Z, robust_warnings, d, robust_d)
    print(OUT / "final_model_report.md")


if __name__ == "__main__":
    main()
