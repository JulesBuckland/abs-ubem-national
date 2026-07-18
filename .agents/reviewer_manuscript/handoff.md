# Handoff Report: Manuscript Review and Critique

## 1. Observation
* **Inference Discrepancy**:
  * `manuscript.tex` (Line 37) claims: `"The 4-chain NUTS sampler (3,000 tune, 3,000 draw iterations per chain) completed the full 6,853-MSOA national graph in approximately 2.5 hours."`
  * `supplementary_material.tex` (Lines 235–239) states: `"Given the computational intractability of full HMC/NUTS across a 6,840-node spatial graph, the national model was estimated using Automatic Differentiation Variational Inference (ADVI). NUTS was utilized exclusively on a 353-MSOA subset (Greater Manchester)..."`
  * `src/config/settings.py` (Lines 88–89) defines: `MCMC_SAMPLES = 50` and `MCMC_TUNE = 50`.
* **Fabricated Metrics**:
  * `manuscript.tex` (Line 346) claims: `"The national physics-informed model yielded an absolute elpd_WAIC = 7569.24 (SE = 67.21, p_WAIC = 2986.97)."`
  * `data/processed/nuts_waic.txt` (Line 2) reports: `"WAIC not available in this ArviZ version."`
* **Scale Mismatches and Formulation Errors**:
  * `manuscript.tex` (Lines 245–246) defines: `\bm{y}_m \sim \text{Normal}(\bm{\mu}_m, \sigma_y^2)` where $y_m$ is later defined as unlogged Total Delivered Thermal Energy (Line 317), creating a scale mismatch with the logged mean $\mu_m$.
  * `manuscript.tex` (Line 296) specifies the Jensen's correction as: `\log(y_m) \sim \text{Normal}\left( \log(T_m) - \frac{\sigma_{y}^2}{2}, \dots \right)` where $\sigma_y^2$ is the observational variance of the likelihood (i.e. $\sigma_{err}^2$).
  * `src/inference/model_unified.py` (Line 302) implements: `mu = theory_log - (T_var / 2.0) + beta_th + beta_inc * income_z + omega_star`, where `T_var` is the within-MSOA variance of the physical baseline, not the likelihood variance.
* **Numerical Inconsistencies**:
  * `manuscript.tex` (Line 405) states: `"The 90th percentile for T* is identified at 12,852.80 kWh/year, and the 95th percentile at 12,791 kWh/year."` (A mathematical impossibility).
  * Run results (`check_percent.py` on `msoa_unified_results.csv`):
    * 90th percentile of `T_star_kwh`: **12,318.39 kWh/year**
    * 95th percentile of `T_star_kwh`: **12,792.19 kWh/year**
    * Joint top decile of $T^*$ and IMD 1–2 percentage: **0.7296%** (50 out of 6,853 MSOAs), contradicting the **0.14%** reported on Line 405.
* **Literature Mismatches**:
  * `papers/phan2019composable.pdf` metadata author: `"Vyacheslav P. Spiridonov"`, title: (None) (Actually arXiv:1912.11514v2 about Seiberg dualities, not Du Phan et al. (2019) about NumPyro).
  * `papers/Kennedy2001.pdf` metadata title: `"Nonparametric Bayesian Calibration of Computer Models"`, author: `"Haiyi Shi; Lei Yang; Jiarui Chi; ..."` (Actually arXiv:2509.22597v4 from 2026, not Kennedy & O'Hagan (2001)).
  * `papers/Batty2018.pdf` metadata title: `"Digital Twins"`, author: `"Dirk Hartmann; Herman Van der Auweraer"` (Actually a Siemens preprint from 2020, not Michael Batty (2018)).

## 2. Logic Chain
1. We read the main manuscript (`manuscript.tex`) and the supplementary material (`supplementary_material.tex`) to extract key claims and mathematical formulations.
2. We inspected the configuration file `src/config/settings.py` and model definition `src/inference/model_unified.py` to check the actual parameters and mathematical expressions implemented in code.
3. We checked the log file `nuts_waic.txt` and empirical results `msoa_unified_results.csv` to compare outputs with the reported figures.
4. Step 1 reveals a direct logical contradiction between `manuscript.tex` (claiming NUTS MCMC was run on the national scale) and `supplementary_material.tex` (admitting ADVI was run on the national scale and scaled post-hoc).
5. Step 2 proves that the WAIC scores reported in the manuscript were not computed by the program (which logged `WAIC not available`), indicating data fabrication or transposition from an undocumented run.
6. Step 3 reveals that the 90th and 95th percentiles reported in the text are mathematically impossible (95th smaller than 90th) and mismatch the empirical quantiles. It also shows the joint deprivation-thermal requirement percentage is 0.73% rather than the reported 0.14%.
7. Step 4 demonstrates that the likelihood scale is mathematically inconsistent (logged mean with unlogged observed values), and the Aggregation Variance Correction formula in the text conflates the model's residual variance ($\sigma_{err}^2$) with the physical stock variance (`T_var`).
8. Step 5 shows that three of the downloaded PDFs are mis-downloaded preprints/articles that do not match their filename or citation keys.
9. Combining these steps leads to the conclusion that the manuscript contains major logical contradictions, mathematical inconsistencies, incorrect citations, and fabricated/incorrect results.

## 3. Caveats
No caveats. The codebase, output logs, and results file are fully populated, and the discrepancies are verifiable directly.

## 4. Conclusion
The verdict for the current work is **REQUEST_CHANGES** due to:
* Critical logical contradiction regarding the computational method (MCMC vs. ADVI).
* Fabricated WAIC goodness-of-fit metrics in the main text.
* Mathematical scale and variance-correction formulation inconsistencies.
* Incorrect numerical figures (impossible percentiles and joint distribution counts).
* Mismatched reference literature in the repository.

All detailed line-by-line suggested edits have been written to `manuscript/review_notes.md`.

## 5. Verification Method
To verify these findings, inspect the following files:
1. Compare `manuscript/manuscript.tex` (Line 37 and Line 346) against `manuscript/supplementary_material.tex` (Line 233) and `data/processed/nuts_waic.txt` (Line 2).
2. Review the model formula in `src/inference/model_unified.py` (Line 302) and compare it with Equation 3 in `manuscript/manuscript.tex` (Line 296).
3. Run `scratch_scripts/check_percent.py` to recalculate the percentiles and joint probabilities from `data/processed/msoa_unified_results.csv`.
4. Run `scratch_scripts/inspect_pdfs.py` to extract PDF metadata and confirm the content/author mismatches.
