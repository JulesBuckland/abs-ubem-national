# microsimulation Methodology (Neto-Bradley, Choudhary, & Challenor, 2022)

This document describes the methodology for the urban energy microsimulation as implemented in Paper 4, based on the approach by Neto-Bradley et al. (2022).

## 1. Synthetic Population Synthesis
The first stage involves generating a representative population of synthetic households that matches the aggregate characteristics of a specific geographic area (e.g., MSOA or Ward).

- **Method:** Deterministic IMD-Iterative Proportional Fitting (IPF) (Iterative Proportional Fitting (IPF)).
- **Inputs:**
    - **Microdata (Seed):** Household-level survey data (e.g., EHS, LC&F) containing detailed socio-economic attributes.
    - **Constraint Tables:** Aggregate census data (e.g., Census 2021) providing counts of households by specific categories (Tenure, Dwelling Type, etc.) for each target area.
- **Output:** A weight for each microdata record per target area, which can be sampled to create a discrete synthetic population.

## 2. Behavioral Assignment (Fuel/Energy Choice)
Assign each synthetic household to a specific behavior or technology group.

- **Method:** Categorical Logistic Regression.
- **Predictors:** Socio-economic variables like income, household size, and building type.
- **Output:** Predicted probability of belonging to a specific group (e.g., primary heating fuel, energy efficiency class).

## 3. Bayesian Multi-level Modeling of Consumption
Estimating the actual energy use (or Weighted Failure Hours) for each household using a hierarchical framework.

- **Model Structure:**
    $$fuel[i] \sim N(a_{0[j]} + a_{1[j]}size_i + a_{2[j]}income_i + \phi_{w[i]} + \theta_{w[i]}, \sigma)$$
    - **Household-level components:** Predictors like household size and income.
    - **Group-level components ($j$):** Coefficients ($a_0, a_1, a_2$) vary based on the fuel/behavior group assigned in Step 2.
    - **Spatial Effects ($\phi_w$):** Intrinsic Conditional Auto-Regressive (ICAR) component to capture spatial dependencies between neighboring areas.
    - **Random Effects ($\theta_w$):** Unstructured ward/area-level effects capturing local extrinsic features.

## 4. Uncertainty Propagation
- **Markov Chain Monte Carlo (MCMC):** Used to estimate the posterior distributions of the model parameters.
- **Monte Carlo Sampling:** Propagating both parameter uncertainty (from the Bayesian model) and population heterogeneity (from the synthetic population) to generate probabilistic outcomes at the aggregate level.

## 5. Implementation in Paper 4
For this project, we adapt this to calculate **Weighted Failure Hours (WFH)** and validate the **Fabric-Vulnerability Paradox**:
1. **Iterative Proportional Fitting (IPF):** Generate 1.2M synthetic households for Greater Manchester.
2. **Bayesian Calibration:** Use Bayesian "unmixing" of macro gas consumption data (DESNZ 2022) to anchor the Heat Loss Coefficient (HLC) distributions for 24 building archetypes.
3. **Simulation:** Calculate WFH for each synthetic household using its specific income-based behavioral rationing and calibrated HLC.
4. **Validation (Final Regression):** A **Spatial Error Model (SEM)** is used to confirm the WFH as a predictor for COPD hospital admissions, controlling for:
    - **Environmental Confounders:** NO2 air pollution at the MSOA level.
    - **Biological Baseline:** Percentage of population over 65.
    - **Socio-economic Factors:** Smoking prevalence, income, and employment deprivation.
    - **Non-Linearity:** A squared WFH term to capture the exponential health impact of severe cold exposure.
5. **Spatial Diagnostics:** Moran's I is used to ensure the SEM successfully neutralizes spatial autocorrelation in the residuals ($I \approx 0$).
