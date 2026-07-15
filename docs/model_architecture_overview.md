### Project: National Probabilistic Mapping of the behaviorally-adjusted thermal requirement

**Objective:** To replace theoretical, physics-only EPC ratings with a robust behaviorally-adjusted thermal requirement ($T^*$). By applying a Bayesian multi-level spatial model to 4 million empirical energy records, we mathematically isolate the "Physics" (the true energy requirement of the building envelope) from the "Vulnerability" (economic rationing/under-heating driven by poverty and spatial inequalities).

---

### Phase 1: Data Integration & Population Synthesis (The Iterative Proportional Fitting (IPF) Engine)
*Goal: To probabilistically map anonymised, regional energy data down to the high-resolution neighborhood (MSOA) level.*

1.  **The Microdata Seed:** Anonymised NEED 2024 (~4 million UK properties).
    *   *Payload:* Annual Gas Consumption (kWh).
    *   *Linking Variables:* Property Type (e.g., Semi-Detached), Property Age Band (e.g., Pre-1919), Floor Area Band (e.g., 51-100m²).
    *   *Geography:* Local Authority District (LAD) - *Broad resolution.*
2.  **The Spatial Constraints:** UK Census 2021.
    *   *Payload:* Exact counts of households.
    *   *Linking Variables:* Property Type, Property Age Band.
    *   *Geography:* MSOA (Middle Layer Super Output Area) - *High resolution.*
3.  **The Synthesis (Iterative Proportional Fitting (IPF)):** For every MSOA in England, the expansion algorithm extracts the NEED microdata from its parent LAD. It iteratively re-weights those NEED records until their architectural makeup (Type/Age) perfectly matches the exact Census counts for that specific MSOA.
4.  **Output:** A synthetic population of households for England. Every household has a probabilistically assigned **Empirical Gas Consumption (kWh)** that realistically reflects both its physical archetype and its broad regional location.

---

### Phase 2: The Bayesian Multi-Level Spatial Model
*Goal: To analyze the synthetic population, controlling for physical building traits to isolate the true impact of socio-economic constraint (The Fabric-Vulnerability Paradox).*

1.  **The Predictors (Physical Confounders):**
    *   Property Type (Categorical: Detached, Flat, etc.)
    *   Property Age Band (Categorical: Pre-1919, 1993-1999, etc.)
    *   Floor Area Band (Categorical)
2.  **The Predictors (Socio-Economic Confounders):**
    *   IMD Income Deprivation Score (Continuous, mapped at the MSOA level).
3.  **The Target Variable:** Empirical Gas Consumption (kWh).
4.  **The Spatial Component (ICAR):** An Intrinsic Conditional Auto-Regressive model. This looks at the spatial adjacency of the 6,840 MSOAs to capture unobserved, hyper-local spatial effects (e.g., off-gas-grid areas, local cultural heating habits, regional weather microclimates).

**The Core Equation (Simplified):**
`Gas_Consumption ~ Property_Type + Property_Age + Floor_Area + IMD_Income + ICAR_Spatial_Effect`

---

### Phase 3: Generating the Outputs (The behaviorally-adjusted thermal requirement)
*Goal: Extracting the policy-relevant metrics from the Bayesian posterior distributions.*

1.  **The Fabric-Vulnerability Paradox (Statistical Proof):** The model outputs the coefficient for the `IMD_Income` variable. This provides a massive, statistically robust proof ($R^2$) of exactly how much gas consumption drops purely due to poverty, holding the physical building entirely constant. 
2.  **The behaviorally-adjusted thermal requirement (The "Better EPC"):** By looking at the coefficients for the physical variables (`Property_Type`, `Age`, `Area`) *while holding the `IMD_Income` variable at zero (no deprivation)*, the model calculates the true, un-rationed empirical energy demand for every architectural archetype in England. This creates a ground-truthed baseline that replaces theoretical EPCs.
3.  **The National Vulnerability Map:** The model outputs the **ICAR Spatial Random Effects**. This generates a high-resolution map of England highlighting specific MSOAs that consume significantly less (or more) energy than their physical housing stock and local poverty levels predict, pinpointing hidden pockets of extreme thermal vulnerability for targeted policy intervention.
