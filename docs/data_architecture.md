# Data Flow Architecture: National Probabilistic Mapping of Urban Thermal Vulnerability (Paper 5)

This document outlines the end-to-end data architecture for adapting the Neto-Bradley (2022) spatial stratified Iterative Proportional Fitting (IPF) framework to the UK context, investigating the "Fabric-Vulnerability Paradox" at the MSOA level.

## Phase 1: The Raw Inputs & Linking Structure

```text
  DAetiASET A: Anonymised NEED 2024       DAetiASET B: UK Census 2021           DAetiASET C: UBEM / EnergyPlus
  (The "Seed" Microdata)                (The "Spatial Constraints")         (The "Physics Baseline")
  ------------------------------        ---------------------------         ----------------------------
  Resolution: LAD level                 Resolution: MSOA level              Resolution: Archetype level
  Sample: ~4 Million rows               Sample: 6,840 MSOAs                 Sample: 32 standard UK houses
  
  [LINKING VARIABLES]                   [LINKING VARIABLES]                 [LINKING VARIABLES]
  - LAD Code                     <====> - Parent LAD Code 
  - Property Type                <====> - Property Type              <====> - Property Type
  - Property Age                 <====> - Property Age               <====> - Property Age
  
  [PAYLOAD VARIABLES]                   [PAYLOAD VARIABLES]                 [PAYLOAD VARIABLES]
  - Empirical Gas Use (kWh)             - Total Household Counts            - Theoretical Gas Need (kWh)
  - Empirical Elec Use (kWh)            - Tenure (Owned/Rented)             - Heat Loss Coefficient (HLC)
                                        - MSOA Code                  <====> [LINKS TO DAetiASET D]


                                                   DAetiASET D: IMD 2019
                                                   (The "Socio-Economic Predictors")
                                                   ---------------------------------
                                                   Resolution: LSOA -> aggregated to MSOA
                                                   
                                                   [LINKING VARIABLES]
                                            <====> - MSOA Code
                                                   
                                                   [PAYLOAD VARIABLES]
                                                   - Income Deprivation Score
                                                   - Living Environment Deprivation
```

## Phase 2: Population Synthesis (The Iterative Proportional Fitting (IPF) Step)

This phase transforms the LAD-level microdata into high-resolution MSOA-level microdata using deterministic IMD-Iterative Proportional Fitting (IPF).

1.  **Filter the Seed:** For a target MSOA, identify its **Parent LAD Code** in Dataset B. Filter Dataset A (NEED) to extract the sample households for that specific LAD.
2.  **Iterative Proportional Fitting (IPF):** Feed the filtered Dataset A and the specific Dataset B Census counts for the target MSOA into the expansion algorithm, linking on **Property Type** and **Property Age**.
3.  **Reweighting:** The algorithm iteratively adjusts the statistical weights of the NEED samples until their weighted marginal totals match the exact architectural mix of the target MSOA.
4.  **Output:** A "Synthetic Population" for the MSOA. Each simulated household possesses an **Empirical Gas Use (kWh)** probabilistically assigned based on local LAD-level behaviors for its specific building type.

## Phase 3: Calculating the Objective Measure (The "Heating Deficit")

This phase introduces building physics to determine the extent of energy rationing.

1.  **Map the Physics:** For every household in the Synthetic Population, use **Property Type** and **Property Age** to join Dataset C, assigning each household its baseline **Theoretical Gas Need (kWh)**.
2.  **Calculate the Deficit:** Calculate the objective measure for every household:
    `Heating Deficit = Theoretical Gas Need - Synthetic Empirical Gas Use`
3.  **Categorize (Extreme Rationing):** Flag households exhibiting severe deficits (e.g., empirical use below the 25th percentile of the theoretical requirement).
4.  **Aggregate to MSOA:** Calculate the MSOA-level metric: **Proportion of Households in Extreme Rationing**.

## Phase 4: The Bayesian Spatial Model

This final phase utilizes spatial statistics to isolate the economic drivers of the Heating Deficit, controlling for physical building performance.

1.  **The Join:** Use the **MSOA Code** to join the aggregated Phase 3 outputs with the socio-economic predictors from Dataset D.
2.  **The Statistical Model:** Input the combined MSOA dataset into a Bayesian Multi-Level Model (e.g., using Stan/MCMC).
3.  **The Variables:**
    *   **Target Variable:** Proportion of Extreme Rationing (from Phase 3)
    *   **Predictor 1 (Physics Control):** MSOA Average Heat Loss Coefficient (from Dataset C)
    *   **Predictor 2 (Economic Driver):** MSOA Income Deprivation Score (from Dataset D)
4.  **Spatial Smoothing (ICAR):** Implement an Intrinsic Conditional Auto-Regressive (ICAR) spatial component to account for unobserved spatial autocorrelation (e.g., off-gas-grid areas, local cultural practices).
5.  **Outputs:** 
    *   **Statistical Evidence:** Regression coefficients quantifying the influence of Income Deprivation on the Heating Deficit, independent of building physics (The Fabric-Vulnerability Paradox).
    *   **Spatial Mapping:** High-resolution national maps identifying specific MSOAs trapped in severe thermal vulnerability.
