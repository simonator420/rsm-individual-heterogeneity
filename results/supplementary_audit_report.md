# Corrected supplementary audit and exploratory checks

## Critical time-label correction

The original analysis scripts incorrectly treated raw label `P` as the baseline and omitted raw label `1` from the post-session workflow. The source article and raw timestamps support the corrected mapping: `1` = pre-session baseline, `P` = immediate post-session (0 h), followed by `30` = 0.5 h, `60` = 1 h, `180` = 3 h, `360` = 6 h, `24` = 24 h and `48` = 48 h. All results previously generated with P as baseline are superseded and must not be used.

## Corrected primary analysis

- Primary QC dataset: 9 athletes, 3 workloads, 7 post-session time points, 5 trials per cell = 945 post-session observations.
- Athlete 10 is excluded because the High and Mod blocks are exact duplicates after removing the workload label and row identifier; a 1,050-observation retained-data sensitivity is reported separately.
- High minus Low model-based estimates: +1.11 pp at 0 h, −0.25 pp at 0.5 h, −1.20 pp at 1 h, −0.21 pp at 3 h, +1.02 pp at 6 h, +1.04 pp at 24 h and +0.25 pp at 48 h. All 95% intervals include zero.
- Trial-order estimate: −0.83 percentage points per trial, SE 0.10.
- Primary residual SD: 4.29 percentage points; smallest random-effects covariance eigenvalue: 1.856.
- The reduced primary random-effects structure contains only the correlated athlete intercept, High deviation and Mod deviation. The six-dimensional workload-by-time sensitivity has a smallest eigenvalue of approximately 0.001 and is therefore not used for primary inference.

## Repeatability and trial order

The current relative-change outcome is centered near zero, so a naive within-cell coefficient of variation based on `SD / |mean|` is not an appropriate reliability statistic and is intentionally not reported here. The reproducible trial-order check shows a mean trial-5 minus trial-1 change of approximately −3.66 percentage points across the corrected primary dataset. The manuscript should model centered trial order and avoid presenting the five repeated jumps as exchangeable independent observations.

## Force-time columns

- The V14–V660 columns behave plausibly as padded force-time signals.
- The maximum V-signal correlated with the reported relative peak-force variable at r = 0.964.
- 93.1% of rows had an exact maximum match.
- The CSV contains no explicit time vector and uses zero padding. Any fPCA or curve analysis must detect the active segment, remove padding and resample within each training fold before being treated as more than exploratory.

## Corrected validation benchmark

The reduced correlated-model leave-one-athlete-out analysis achieved RMSE 5.68 percentage points, MAE 4.33 percentage points, 92.9% 95% prediction-interval coverage and 21.57 percentage points mean interval width. All nine folds converged with L-BFGS and no fallback was required. These are population-prediction calibration metrics for an unseen athlete, not proof of fully individualized clinical prediction.
