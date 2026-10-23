# Model complexity audit

## Purpose

Only nine athletes remain after the Athlete 10 data-integrity exclusion. The primary random-effects structure was therefore chosen using parsimony, convergence diagnostics, covariance eigenvalues and stability of the High-minus-Low estimand. REML likelihood values are reported descriptively and are not used as the sole model-selection criterion.

## Corrected data basis

All models use the source-consistent mapping `1` = pre-session baseline and `P` = immediate post-session (0 h), with 945 post-session observations from 9 athletes. The fixed-effects formula is workload-by-time, plus centered trial order.

| Candidate structure | Random-effects dimension | Converged | Residual SD (pp) | Smallest covariance eigenvalue | Numerical warning | Role |
|---|---:|:---:|---:|---:|---|---|
| Random intercept only | 1 | Yes | 4.95 | 3.835 | Singular covariance warning | Lower-complexity benchmark |
| Intercept + High + Mod | 3 | Yes | 4.29 | 1.856 | None | Primary model |
| Intercept + log-time | 2 | Yes | 4.91 | 0.130 | None | Temporal benchmark |
| Intercept + High + Mod + log-time | 4 | Yes | 4.20 | 0.256 | Hessian warning | Previous candidate; demoted |
| Six-dimensional workload-by-time | 6 | Yes | 4.10 | 0.001 | Near-boundary covariance | Sensitivity only |

## Interpretation

The fixed-effect High-minus-Low point estimates are identical across these structures because the estimand is driven by the same corrected data and fixed-effects design. The uncertainty intervals change with the random-effects assumptions. The 3D model is the preferred primary model because it retains athlete-specific workload heterogeneity, converges without warning and avoids the near-boundary temporal covariance seen in the 6D model. The 4D and 6D structures remain useful as transparent sensitivities, not as primary evidence for stable athlete-specific time-response parameters.

## LOAO validation of the selected primary model

The selected 3D model was refit in all nine leave-one-athlete-out folds. All folds converged with L-BFGS and no fallback was required. RMSE was 5.68 percentage points, MAE 4.33 percentage points, 95% prediction-interval coverage 92.9% and mean interval width 21.57 percentage points.

## Manuscript instruction

Describe the 3D model as the prespecified/primary parsimonious structure after the corrected data audit. Present the 6D workload-by-time structure in a sensitivity subsection and state that its near-boundary eigenvalue is why it is not used for primary inference. Do not claim that the data identify precise individual recovery curves for nine athletes.
