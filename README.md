# Between-athlete heterogeneity in countermovement-jump responses

Minimal reproducibility repository for the manuscript **Between-athlete heterogeneity and predictive uncertainty in countermovement-jump responses to repeated-sprint exercise**.

The repository contains the public analysis-ready dataset, the numerical analysis scripts, compact result tables/reports, and the figure-generation script. Manuscript files, submission documents, working archives, local environments, and fitted posterior chains are intentionally excluded.

## Repository structure

- `data/` — public anonymized input data and its provenance note
- `analysis/` — model fitting, quality gates, figure generation, and validation scripts
- `results/` — compact analysis outputs used by the manuscript
- `metadata/` — data provenance and quality-control documentation
- `CITATION.cff` and `.zenodo.json` — citation and Zenodo metadata

## Reproduce the analysis

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis/run_all.py
python analysis/validate_release.py
python analysis/make_figures.py
```

`run_all.py` recreates the numerical model outputs in `results/`. The figure script writes generated figures to `results/figures/`, which is ignored by Git because the figures are derived outputs and are supplied separately in the manuscript submission package.

## Key release outputs

The final analysis retains 945 trials from 9 athletes after exclusion of Athlete 10 under the prespecified quality-control rule. The primary high-versus-low contrasts range from −1.20 to +1.11 percentage points, with all 95% intervals crossing zero. Leave-one-athlete-out validation gives an RMSE of approximately 5.68 percentage points and 92.9% empirical 95% coverage. These results support a cautious interpretation of individual heterogeneity rather than a claim of a consistent population-level effect.

## Data provenance

The input file is the public anonymized supplementary dataset associated with the source article cited in `data/README.md`. Please retain the source attribution and consult the source article's data-licensing terms when redistributing the data.

## Citation and license

Please cite the associated manuscript and this repository using `CITATION.cff`. Code and repository documentation are released under the MIT License. The included source dataset remains subject to its original source terms.
