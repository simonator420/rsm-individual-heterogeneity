"""Final quality-gate analyses for the public CMJ secondary analysis.

This script adds two analyses required before submission:

1. Leave-one-athlete-out prediction using the final correlated mixed model.
2. A data-integrity sensitivity analysis retaining Athlete 10.

The primary estimand is the relative peak-force change (%) from the
athlete-by-workload pre-session mean. In the source CSV, raw label '1' is
pre-session and 'P' is immediate post-session. Prediction intervals for a held-out
athlete include fixed-effect uncertainty, the fitted new-athlete random-effect
variance, and residual variance; therefore the LOAO analysis is a valid
population prediction benchmark rather than an invalid no-pooling forecast.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from patsy import dmatrix
import statsmodels.api as sm


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
RANDOM_FORMULA = '1 + C(workload, Treatment(reference="Low"))'


def prepare_data(include_athlete10: bool = False) -> pd.DataFrame:
    raw = pd.read_csv(DATA)
    raw["time_raw"] = raw["D.TimeAfterTraining"].astype(str)
    mask = raw["D.Training"].isin(["High", "Low", "Mod"])
    if not include_athlete10:
        mask &= raw["D.Name"] != "Athlete 10"
    d = raw.loc[mask].copy()
    d["hours"] = d["time_raw"].map(TIME_MAP)
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
    return d


def fit_model(d: pd.DataFrame):
    X = dmatrix(FIXED_FORMULA, d, return_type="dataframe")
    Z = dmatrix(RANDOM_FORMULA, d, return_type="dataframe")
    model = sm.MixedLM(
        endog=d["y"], exog=X, groups=d["D.Name"], exog_re=Z, use_sqrt=True
    )
    all_warnings = []
    last_fit = None
    last_method = None
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
        last_method = method
        if fit.converged:
            return X, Z, fit, all_warnings, method
    return X, Z, last_fit, all_warnings, last_method


def prediction_frame(fit, train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([train, test], ignore_index=True)
    X_all = dmatrix(FIXED_FORMULA, combined, return_type="dataframe")
    Z_all = dmatrix(RANDOM_FORMULA, combined, return_type="dataframe")
    X = X_all.iloc[len(train) :].to_numpy()
    Z = Z_all.iloc[len(train) :].to_numpy()
    k = X.shape[1]
    beta = fit.fe_params.to_numpy()
    cov_beta = fit.cov_params().iloc[:k, :k].to_numpy()
    G = np.asarray(fit.cov_re)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        mean = X @ beta
        var_fixed = np.einsum("ij,jk,ik->i", X, cov_beta, X)
        var_random = np.einsum("ij,jk,ik->i", Z, G, Z)
    var = np.maximum(var_fixed + var_random + float(fit.scale), 0.0)
    sd = np.sqrt(var)
    out = test[["D.Name", "D.Training", "hours", "D.TrialNum", "y"]].copy()
    out["prediction"] = mean
    out["pi95_low"] = mean - 1.96 * sd
    out["pi95_high"] = mean + 1.96 * sd
    out["error"] = out["y"] - out["prediction"]
    out["covered_95"] = (out["y"] >= out["pi95_low"]) & (out["y"] <= out["pi95_high"])
    out["interval_width"] = out["pi95_high"] - out["pi95_low"]
    return out


def contrasts(fit, X: pd.DataFrame) -> pd.DataFrame:
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
                'C(time_f, Treatment(reference=0.0))[T.' + f"{time:g}" + "]"
            )
            if label not in names:
                label = (
                    'C(workload, Treatment(reference="Low"))[T.High]:'
                    'C(time_f, Treatment(reference=0.0))[T.' + f"{float(time)}" + "]"
                )
            c[names.index(label)] = 1.0
        estimate = float(c @ beta)
        se = float(np.sqrt(c @ cov @ c))
        rows.append({
            "time_h": time,
            "estimate_high_minus_low_pp": estimate,
            "ci95_low_pp": estimate - 1.96 * se,
            "ci95_high_pp": estimate + 1.96 * se,
        })
    return pd.DataFrame(rows)


def main() -> None:
    primary = prepare_data(False)
    athletes = sorted(primary["D.Name"].unique())
    loao_rows = []
    fold_summary = []
    for athlete in athletes:
        train = primary.loc[primary["D.Name"] != athlete].copy()
        test = primary.loc[primary["D.Name"] == athlete].copy()
        X_train, Z_train, fit, fit_warnings, fit_method = fit_model(train)
        pred = prediction_frame(fit, train, test)
        pred["held_out_athlete"] = athlete
        loao_rows.append(pred)
        fold_summary.append({
            "held_out_athlete": athlete,
            "n_train_athletes": int(train["D.Name"].nunique()),
            "n_test_observations": int(len(test)),
            "converged": bool(fit.converged),
            "fit_method": fit_method,
            "n_warnings": len(fit_warnings),
            "rmse_pp": float(np.sqrt(np.mean(pred["error"] ** 2))),
            "mae_pp": float(np.mean(np.abs(pred["error"]))),
            "coverage_95": float(pred["covered_95"].mean()),
            "mean_interval_width_pp": float(pred["interval_width"].mean()),
        })

    loao = pd.concat(loao_rows, ignore_index=True)
    loao.to_csv(OUT / "loao_predictions.csv", index=False)
    fold_df = pd.DataFrame(fold_summary)
    fold_df.to_csv(OUT / "loao_fold_summary.csv", index=False)
    loao_summary = {
        "n_athletes": len(athletes),
        "n_observations": int(len(loao)),
        "all_folds_converged": bool(fold_df["converged"].all()),
        "rmse_pp": float(np.sqrt(np.mean(loao["error"] ** 2))),
        "mae_pp": float(np.mean(np.abs(loao["error"]))),
        "coverage_95": float(loao["covered_95"].mean()),
        "mean_interval_width_pp": float(loao["interval_width"].mean()),
        "folds": fold_summary,
    }

    # Retain Athlete 10 for a prespecified data-integrity sensitivity analysis.
    all_d = prepare_data(True)
    X_all, Z_all, all_fit, all_warnings, all_method = fit_model(all_d)
    all_contrasts = contrasts(all_fit, X_all)
    all_contrasts.to_csv(OUT / "athlete10_retained_high_low_contrasts.csv", index=False)
    athlete10_sensitivity = {
        "n_observations": int(len(all_d)),
        "n_athletes": int(all_d["D.Name"].nunique()),
        "converged": bool(all_fit.converged),
        "fit_method": all_method,
        "n_warnings": len(all_warnings),
        "residual_sd_pp": float(np.sqrt(all_fit.scale)),
        "contrasts": all_contrasts.to_dict(orient="records"),
    }

    # Explicitly document the duplicate-block integrity issue.
    raw = pd.read_csv(DATA)
    a10 = raw.loc[raw["D.Name"] == "Athlete 10"].copy()
    high = a10.loc[a10["D.Training"] == "High"].drop(columns=["D.Training", "Unnamed: 0"]).reset_index(drop=True)
    mod = a10.loc[a10["D.Training"] == "Mod"].drop(columns=["D.Training", "Unnamed: 0"]).reset_index(drop=True)
    duplicate_content = bool(high.equals(mod))

    out = {
        "loao": loao_summary,
        "athlete10_retained_sensitivity": athlete10_sensitivity,
        "athlete10_duplicate_content_after_workload_label_removed": duplicate_content,
        "interpretation": (
            "LOAO population prediction should be reported as a calibration benchmark, "
            "not as evidence that an individual athlete can be predicted without any "
            "new athlete-specific observations."
        ),
    }
    (OUT / "final_quality_gate_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    lines = [
        "# Final quality-gate analyses",
        "",
        "## Leave-one-athlete-out validation",
        "",
        f"The reduced correlated mixed model was refit in {len(athletes)} leave-one-athlete-out folds using raw label 1 as the pre-session baseline and raw label P as the 0-hour immediate post-session time point. All folds converged: {loao_summary['all_folds_converged']}. Population prediction RMSE was {loao_summary['rmse_pp']:.2f} percentage points, MAE was {loao_summary['mae_pp']:.2f} percentage points, 95% prediction-interval coverage was {loao_summary['coverage_95'] * 100:.1f}%, and mean interval width was {loao_summary['mean_interval_width_pp']:.2f} percentage points.",
        "",
        "These are valid new-athlete population predictions because the intervals include fixed-effect uncertainty, the fitted random-effect variance for a new athlete, and residual variance. They should not be described as fully individualized prediction without new athlete-specific observations.",
        "",
        "## Athlete 10 retained sensitivity",
        "",
        f"When Athlete 10 was retained, the same model used {len(all_d)} observations from {all_d['D.Name'].nunique()} athletes and converged: {bool(all_fit.converged)}. The High-minus-Low contrasts are saved in athlete10_retained_high_low_contrasts.csv. The High and Mod Athlete 10 blocks are exact duplicates after removing the workload label and row identifier: {duplicate_content}. This supports excluding Athlete 10 from the primary analysis while reporting the retained-data fit transparently as a sensitivity analysis.",
        "",
        "## Submission decision",
        "",
        "The source-consistent analyses are complete for the reduced Gaussian model, winsorized sensitivity, final-model LOAO calibration, and Athlete 10 retained-data sensitivity. The richer temporal random-effects structure is sensitivity only because of the small number of athletes and its near-boundary covariance behaviour. The manuscript should keep the primary claim focused on individual heterogeneity and uncertainty calibration; the study does not establish a definitive average workload effect.",
    ]
    (OUT / "final_quality_gate_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT / "final_quality_gate_report.md")


if __name__ == "__main__":
    main()
