# Final quality-gate analyses

## Leave-one-athlete-out validation

The reduced correlated mixed model was refit in 9 leave-one-athlete-out folds using raw label 1 as the pre-session baseline and raw label P as the 0-hour immediate post-session time point. All folds converged: True. Population prediction RMSE was 5.68 percentage points, MAE was 4.33 percentage points, 95% prediction-interval coverage was 92.9%, and mean interval width was 21.57 percentage points.

These are valid new-athlete population predictions because the intervals include fixed-effect uncertainty, the fitted random-effect variance for a new athlete, and residual variance. They should not be described as fully individualized prediction without new athlete-specific observations.

## Athlete 10 retained sensitivity

When Athlete 10 was retained, the same model used 1050 observations from 10 athletes and converged: True. The High-minus-Low contrasts are saved in athlete10_retained_high_low_contrasts.csv. The High and Mod Athlete 10 blocks are exact duplicates after removing the workload label and row identifier: True. This supports excluding Athlete 10 from the primary analysis while reporting the retained-data fit transparently as a sensitivity analysis.

## Submission decision

The source-consistent analyses are complete for the reduced Gaussian model, winsorized sensitivity, final-model LOAO calibration, and Athlete 10 retained-data sensitivity. The richer temporal random-effects structure is sensitivity only because of the small number of athletes and its near-boundary covariance behaviour. The manuscript should keep the primary claim focused on individual heterogeneity and uncertainty calibration; the study does not establish a definitive average workload effect.
