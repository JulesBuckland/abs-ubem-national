# ABS-UBEM — project instructions

National-scale Bayesian framework separating a dwelling's physical thermal requirement
from occupants' behavioural/economic rationing. Paper 5 submitted to *Energy and Buildings*
2026-07-27. Paper 2 (retrofit natural experiment) is in planning.

**Read `docs/paper2_plan_v2.md` before doing any Paper 2 work.** It supersedes the three
`docs/next_paper_*.md` files, which are kept for the reasoning trail.

## Verified constants — do NOT recompute these

| Quantity | Value | Source |
|---|---|---|
| Synthetic population | **685,300** households | `national_synthetic_population_eti.parquet` |
| MSOAs (England) | **6,853** (6,856 − 3 Census gaps) | same |
| NEED seed | 50,000 properties, gas panel `Gcons2005..2022` | `need_2024_official_50k.csv` |
| Gas-heated dwellings | 40,313 (`MAIN_HEAT_FUEL==1`) | verified 2026-07-26 |
| CWI treated (installed 2008–2019, w/ gas history) | **4,080** | verified 2026-07-26 |
| Loft treated, same window | **5,126** | verified 2026-07-26 |
| Never-treated gas controls | **25,633** | verified 2026-07-26 |
| INLA coefficients | β_th = −0.2874, β_inc = 0.0427 | `run_inla.py`, national fit |
| National INLA runtime | 201 s (vs NUTS 2.5 h) | — |
| UKHLS convergent check | Spearman **r = −0.75, p = 0.020, n = 9** | regenerated 2026-07-26 |
| Zenodo (version DOI, cited in paper) | 10.5281/zenodo.21629037 | — |
| Zenodo (concept DOI, all versions) | 10.5281/zenodo.21629036 | — |

⚠️ The `docs/next_paper_*.md` files cite the UKHLS check as `r=−0.67, p=0.07`. That is
**stale** — it predates the INLA regeneration. Use −0.75 / 0.020.

## Environment

- Python: **`./.venv/Scripts/python.exe`** — the system `python` lacks matplotlib/geopandas.
  Run modules as `./.venv/Scripts/python.exe -m src.research.<module>` from the repo root.
- R + INLA are called via subprocess (`src/inference/inla/fit_inla.R`). Same pattern is the
  precedent if Paper 2 needs R's `did` package.
- LaTeX: MiKTeX (`pdflatex`, `bibtex`, `pdftotext`, `pdftoppm` all available). No pandoc.
- **`manuscript/` is gitignored.** Figures there are NOT in version control — regenerate them
  with `src/research/regenerate_*.py` rather than assuming they exist. A missing figure makes
  pdflatex silently emit a blank box instead of erroring, so check the log for `not found`.

## Conventions

- Manuscript uses **American spelling** throughout (behavioral, neighborhood). Repo docs use
  British. Don't mix inside the manuscript.
- Figures are **generated from data at draw time**, never hardcoded. The old
  `archive/legacy_scripts/utils/draw_fig1.py` hardcoded 684,000 and drifted from the real
  685,300 — that's the failure mode the regeneration scripts exist to prevent.
- Verify numbers against the data before putting them in prose. Several stale figures have
  already been caught this way.

## Layout

```
src/inference/inla/     primary engine (R-INLA, BYM2 + PC priors + RSR)
src/inference/          NUTS path (model_unified.py), GP emulator, lhs_sampler.py
src/research/           regenerate_*.py figure + validation scripts
data/processed/         msoa_unified_results_inla.csv, gp_emulator.pkl, synthetic population
docs/                   research plans, literature matrix, research_notebook.md
manuscript/             .tex, figures, submission files (gitignored)
archive/legacy_scripts/ superseded code, kept not deleted
```

## Working style

- State uncertainty explicitly; flag stale/unverifiable numbers rather than passing them on.
- Push back on weak reasoning — Jules wants the critique, not agreement.
- Don't spawn subagents or run long research workflows unless asked.
