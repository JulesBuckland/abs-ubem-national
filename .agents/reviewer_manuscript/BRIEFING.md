# BRIEFING — 2026-07-16T10:42:51+01:00

## Mission
Critically review manuscript.tex for logical gaps, mathematical inconsistencies, and alignment with downloaded papers, and write the review notes to review_notes.md.

## 🔒 My Identity
- Archetype: reviewer and adversarial critic
- Roles: reviewer, critic
- Working directory: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\reviewer_manuscript
- Original parent: e50891bf-90a2-47e7-8ca1-b87dd813a845
- Milestone: Manuscript review
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code (do not modify manuscript.tex)
- Do not cheat, hardcode, or bypass checks
- Ground critiques in the downloaded literature (Hills2012, petrou2024bayesian, Gelman2006, etc.)
- Output review notes to C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\manuscript\review_notes.md

## Current Parent
- Conversation ID: e50891bf-90a2-47e7-8ca1-b87dd813a845
- Updated: 2026-07-16T10:46:00+01:00

## Review Scope
- **Files to review**: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\manuscript\manuscript.tex
- **Interface contracts**: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\PROJECT.md
- **Review criteria**: logical gaps, mathematical inconsistencies, literature alignment

## Key Decisions Made
- Performed Python-based PDF text inspection to check metadata and abstracts.
- Checked model configuration (`settings.py`), implementation (`model_unified.py`), log outputs (`nuts_waic.txt`), and results (`msoa_unified_results.csv`) to verify claims made in `manuscript.tex` and `supplementary_material.tex`.
- Uncovered major discrepancies (fabricated WAIC, MCMC vs ADVI methodology contradiction, scale inconsistencies, wrong aggregation variance correction, and corrupted/mismatched reference PDFs).

## Artifact Index
- C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\manuscript\review_notes.md — Review notes containing suggested line-by-line edits.

## Review Checklist
- **Items reviewed**: `manuscript.tex`, `supplementary_material.tex`, `model_unified.py`, `settings.py`, `nuts_waic.txt`, `msoa_unified_results.csv`, `generate_supplementary_data.py`.
- **Verdict**: REQUEST_CHANGES
- **Unverified claims**: None.

## Attack Surface
- **Hypotheses tested**: Checked WAIC calculation, verified NUTS iteration counts, verified joint percentiles of $T^*$ and IMD, verified PDF contents against citation keys.
- **Vulnerabilities found**: 
  - Fabricated WAIC score (reported despite being "not available" in log file).
  - Methodological contradiction (manuscript claims NUTS on national scale; supplementary material admits ADVI was used with 3.17x scaling).
  - Dummy MCMC configuration (`MCMC_SAMPLES = 50` in settings instead of the claimed 3,000).
  - Mathematical scale mismatch in likelihood (using unlogged $y_m$ with logged mean).
  - Incorrect Jensen's correction formula in text (conflates observational variance with within-MSOA variance).
  - Unscaled spatial ICAR component (violates BYM2 spec).
  - Mathematical error in percentiles (95th percentile smaller than 90th percentile).
  - Misnamed/mismatched PDF reference files in `papers/`.
- **Untested angles**: None.
