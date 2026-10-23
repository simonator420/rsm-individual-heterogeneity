# Final correlated hierarchical model

## Decision

The primary model converged with a parsimonious, fully correlated three-dimensional athlete-level random-effects structure. A winsorized outcome sensitivity and a richer six-dimensional temporal sensitivity were also fitted. The primary structure is preferred because only nine athletes remain after QC.

## Data and model

The analysis used 945 post-session trials from 9 athletes after excluding Athlete 10. Raw label 1 was used as the pre-session baseline and P was retained as the 0-hour immediate post-session time point. The outcome was relative peak-force change (%) from the athlete-by-workload pre-session mean. Fixed effects were workload, time, workload-by-time interactions and centered trial order. Primary random effects were a fully correlated athlete intercept, High deviation and Mod deviation; a richer workload-by-time random-effects structure was evaluated only as sensitivity.

## Primary High minus Low contrasts

| Time | Estimate (percentage points) | 95% CI |
|---:|---:|:---|
| 0 h | 1.11 | -2.19 to 4.40 |
| 0.5 h | -0.25 | -3.54 to 3.05 |
| 1 h | -1.20 | -4.50 to 2.09 |
| 3 h | -0.21 | -3.50 to 3.08 |
| 6 h | 1.02 | -2.27 to 4.31 |
| 24 h | 1.04 | -2.26 to 4.33 |
| 48 h | 0.25 | -3.05 to 3.54 |

## Winsorized sensitivity

The outcome was winsorized at the empirical 1st and 99th percentiles before refitting the same model. The resulting contrasts are reported below; this is a robustness check, not a replacement for the prespecified primary analysis.

| Time | Estimate (percentage points) | 95% CI |
|---:|---:|:---|
| 0 h | 1.08 | -2.13 to 4.30 |
| 0.5 h | -0.25 | -3.46 to 2.97 |
| 1 h | -0.96 | -4.17 to 2.25 |
| 3 h | -0.21 | -3.42 to 3.00 |
| 6 h | 1.02 | -2.19 to 4.23 |
| 24 h | 0.93 | -2.28 to 4.15 |
| 48 h | 0.24 | -2.97 to 3.45 |

## Diagnostics

Primary model: converged=True; REML log-likelihood=-2730.31; residual SD=4.29 percentage points; smallest random-effects covariance eigenvalue=1.856.
Centered trial order estimate: -0.83 percentage points per trial (SE 0.10).
Six-dimensional workload-by-time random-effects sensitivity: converged=True; residual SD=4.10 percentage points.

## Manuscript interpretation

The corrected final correlated model uses the source-consistent pre-session baseline. The main claim should concern individual heterogeneity and uncertainty calibration, not a definitive workload effect.

The source-consistent reanalysis is complete for the reduced Gaussian primary model, winsorized sensitivity and LOAO calibration. The richer temporal random-effects model is retained as sensitivity only; the manuscript should report optimizer warnings and avoid presenting the small-sample covariance structure as definitive evidence of stable individual time-response parameters.
