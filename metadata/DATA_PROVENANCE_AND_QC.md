# Data provenance and quality control record

## Source

- Article: Wu PP-Y, Sterkenburg N, Everett K, Chapman DW, White N, Mengersen K. 2019. *Predicting fatigue using countermovement jump force-time signatures: PCA can distinguish neuromuscular versus metabolic fatigue.* PLOS ONE 14(7):e0219295.
- Article DOI: `10.1371/journal.pone.0219295`
- Supplementary CSV DOI: `10.1371/journal.pone.0219295.s001`
- Original data status: public supplementary data associated with the peer-reviewed article.

## Source design

Ten recreationally trained athletes completed randomized crossover repeated-sprint sessions at Low, Mod and High workloads. Five CMJs were collected at baseline, immediately post-session, and 0.5, 1, 3, 6, 24 and 48 hours. The force plate sampling rate was 600 Hz.

## QC decisions

- Raw CSV dimensions: 1,250 rows × 661 columns.
- Source-consistent time mapping: raw label `1` is pre-session baseline; `P` is immediate post-session (0 h); `30`, `60`, `180`, `360`, `24` and `48` are 0.5, 1, 3, 6, 24 and 48 hours.
- Primary baseline: mean of five raw-`1` pre-session trials within each athlete-by-workload cell.
- Primary outcome: relative peak-force change from that cell-specific baseline.
- Athlete 10 was excluded from the primary analysis because the High and Mod blocks are exact duplicates after removing the workload label and row identifier.
- Athlete 8 has identical High/Mod timestamps despite different force signals; timestamps are treated as supporting metadata only.
- Primary analysis size: 9 athletes × 3 workloads × 7 post-session times including P at 0 h × 5 trials = 945 trials.
- No claim is made that timestamps independently verify every stated 96-hour session separation.
- No claim is made that the sample represents elite footballers.
- Prior results using P as baseline are superseded and must not be used in the manuscript.

## Primary model

- Fixed effects: workload, categorical post-session time, workload-by-time interaction and centered trial order.
- Primary correlated athlete random effects: intercept, High deviation and Mod deviation. A six-dimensional workload-by-time structure is sensitivity only.
- Estimation: Gaussian REML mixed model.
- Robustness: outcome winsorized at empirical 1st and 99th percentiles.
- Model-complexity note: the primary three-dimensional structure converged without primary-fit warnings and had a smallest covariance eigenvalue of 1.856. The six-dimensional sensitivity had a smallest eigenvalue of approximately 0.001 and is not used for primary inference.
- Validation: final-model leave-one-athlete-out prediction with fixed-effect uncertainty, new-athlete random-effect variance and residual variance included in prediction intervals.
