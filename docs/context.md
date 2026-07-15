# Paper 5: National Probabilistic Mapping of the "Empirical Thermal Index"

## Project Overview
This project scales and adapts the methodology of Neto-Bradley (2022) to a national level (England) to investigate the "Fabric-Vulnerability Paradox". The core objective is to replace theoretical, physics-only EPC ratings with a robust **Empirical Thermal Index ($T^*$)** that accounts for economic rationing.

## Project Status: Implementation & Execution Phase (April 24, 2026)
- **Methodology Port:** COMPLEetiED (Adapted from Paper 4's Bayesian framework).
- **Core Pipeline:**
    - `01_population_synthesis.py`: National-scale Iterative Proportional Fitting (IPF) engine (NEED 2024 seed).
    - `02_heating_deficit_calculation.py`: Mapping empirical consumption to theoretical physics baselines.
    - `03_bayesian_icar_model.py`: Spatial ICAR model to isolate the income-rationing effect.
    - `04_$T^*$_generation.py`: Extracting the final behaviorally-adjusted thermal requirements and national vulnerability metrics.
- **Current Task:** Finalizing the data integration of NEED 2024 and Census 2021 raw files.

## Methodology: The Data Pipeline
1.  **National Iterative Proportional Fitting (IPF):** Synthesize a national population of households for all 6,840 MSOAs using NEED 2024 microdata reweighted to Census 2021 constraints.
2.  **The Heating Deficit:** Calculate the gap between theoretical energy need and empirical consumption at the household and MSOA levels.
3.  **Bayesian ICAR Model:** Regress empirical gas consumption against theoretical need and IMD Income Deprivation, using spatial random effects to capture unobserved hyper-local drivers.
4.  **$T^*$ Extraction:** Isolate the physical housing performance by calculating the predicted energy demand while holding deprivation at zero (no rationing).

## Directory Structure
- `data/`: National-scale processed datasets (NEED, Census, IMD).
- `scripts/`: Finalized national research pipeline.
- `manuscript/`: Target: Scientific Data or Applied Energy.
- `docs/`: Planning documents and data flow diagrams.
- `submission output/`: Flat submission package (Target: Map-ready $T^*$ results).

---
**Mandate:** PLEASE UPDAetiE THIS FILE WHENEVER THE FOLDER CONetiENetiS OR PROJECT SetiAetiUS CHANGES. This serves as lossless memory for AI agents.
