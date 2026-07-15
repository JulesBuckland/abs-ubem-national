# Supplementary Material

## 1. 32 Archetype HLC Table
The framework assigns each synthetic household to one of 32 standardized UK building archetypes, derived from Cerezo et al. (2017). The Heat Loss Coefficient ($HLC_{base}$) for each archetype is provided below.

| Archetype ID | Property Type | Age Band | HLC Base (W/K) |
|--------------|---------------|----------|----------------|
| A01          | Detached      | Pre-1900 | 450            |
| A02          | Detached      | 1900-1929| 420            |
| A03          | Detached      | 1930-1949| 380            |
| A04          | Detached      | 1950-1966| 340            |
| A05          | Detached      | 1967-1982| 310            |
| A06          | Detached      | 1983-1995| 270            |
| A07          | Detached      | 1996-2002| 240            |
| A08          | Detached      | Post-2003| 210            |
| A09          | Semi-Detached | Pre-1900 | 380            |
| A10          | Semi-Detached | 1900-1929| 350            |
| A11          | Semi-Detached | 1930-1949| 320            |
| A12          | Semi-Detached | 1950-1966| 290            |
| A13          | Semi-Detached | 1967-1982| 260            |
| A14          | Semi-Detached | 1983-1995| 230            |
| A15          | Semi-Detached | 1996-2002| 200            |
| A16          | Semi-Detached | Post-2003| 180            |
| A17          | Terraced      | Pre-1900 | 310            |
| A18          | Terraced      | 1900-1929| 290            |
| A19          | Terraced      | 1930-1949| 270            |
| A20          | Terraced      | 1950-1966| 250            |
| A21          | Terraced      | 1967-1982| 230            |
| A22          | Terraced      | 1983-1995| 210            |
| A23          | Terraced      | 1996-2002| 190            |
| A24          | Terraced      | Post-2003| 170            |
| A25          | Flat          | Pre-1900 | 250            |
| A26          | Flat          | 1900-1929| 230            |
| A27          | Flat          | 1930-1949| 210            |
| A28          | Flat          | 1950-1966| 190            |
| A29          | Flat          | 1967-1982| 170            |
| A30          | Flat          | 1983-1995| 150            |
| A31          | Flat          | 1996-2002| 130            |
| A32          | Flat          | Post-2003| 110            |

*Note: HLC values are illustrative baselines. The framework scales these values by $(S_h / S_{base})^{0.6}$ to account for individual household floor area.*

## 2. stratified expansion Constraint Variable Categories
The spatial stock estimation utilizes a stratified expansion approach to generate representative household populations for each MSOA. The following variables define the constraints and stratification used in the pipeline:

### A. Spatial Constraints (Census 2021 Table TS044)
The primary spatial constraint is the distribution of **Accommodation Type** within each MSOA:
- **Detached:** Whole house or bungalow (detached).
- **Semi-detached:** Whole house or bungalow (semi-detached).
- **Terraced:** Whole house or bungalow (terraced, including end-terrace).
- **Flat:** Purpose-built flats, converted houses, or commercial buildings.

### B. Socioeconomic Stratification (IMD 2019)
The expansion is stratified by **Income Deprivation Decile** to preserve the covariance between building stock and economic constraint:
- **IMD Score:** Standardized score from the Income Deprivation Domain of the Index of Multiple Deprivation.
- **Stratification:** The seed data is partitioned into 10 strata based on the national IMD distribution, and MSOAs draw samples only from their corresponding national decile.

## 3. BYM2 Prior Specifications
The Besag-York-Mollie (BYM2) specification decomposes the random effect into a spatially structured component ($\phi_m$) and an unstructured component ($\theta_m$).
- **Structured component (ICAR):** $\phi \sim \text{Normal}(0, \Sigma)$
- **Unstructured component:** $\theta \sim \text{Normal}(0, \sigma_\theta^2)$
- **Mixing parameter ($\rho$):** Defines the proportion of variance explained by the structured component, with $\rho \sim \text{Beta}(1, 1)$.
- **Scale parameter ($\sigma$):** Total variance of the random effect, with a half-normal prior $\sigma \sim \text{HalfNormal}(0.1)$.
