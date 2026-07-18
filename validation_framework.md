# ABS-UBEM Validation Framework and Empirical Methodology

This document outlines the validation framework, empirical metrics, and the epistemic defense used to evaluate the Agent-Based Surrogate Urban Building Energy Model (ABS-UBEM) against traditional baseline methodologies. The goal is to mathematically and empirically demonstrate both the superior predictive accuracy of the model and its structural capability to represent socioeconomically constrained energy behaviors (e.g., fuel poverty) that physics-only models fundamentally miss.

## 1. Baseline Definitions

We establish three core models for comparative evaluation:

### 1.1. Competitor A (Physics-Only Baseline)
- **Description**: An advanced physics-based surrogate model (e.g., trained on EnergyPlus simulations) that predicts household energy demand strictly from physical geometry, building fabric properties, and exogenous weather inputs.
- **Hypothesis**: This model assumes that occupants perfectly heat their homes to normative setpoints. It lacks awareness of socioeconomic constraints.

### 1.2. Competitor B (Stats-Only Baseline)
- **Description**: A Bayesian demographic mapping or purely statistical regression model that predicts energy consumption relying entirely on socioeconomic features, ignoring fundamental thermodynamics and physical building geometry.
- **Hypothesis**: This model assumes that physical building characteristics are secondary to demographic drivers, failing to generalize across varying built environments.

### 1.3. ABS-UBEM (Synthesis Model)
- **Description**: A unified, differentiable model merging Bayesian cognitive agent behaviors (modeling subjective utility, budgets, and thermal preferences) with a physics-informed surrogate core.
- **Hypothesis**: This model predicts actual realized demand by mathematically constraining the physical thermodynamic demand with socioeconomic rationality and fuel poverty behaviors.

---

## 2. Empirical Validation Metrics

To demonstrate superiority and evaluate model fits, we compute the following metrics.

### 2.1. Parameter Recovery via RMSE
To evaluate the capability of the inference pipeline (e.g., Stochastic Variational Inference) to recover true ground-truth behavioral parameters (such as the thermal sensitivity $\beta$ or income constraint thresholds):
$$ \text{RMSE}(\theta) = \sqrt{ \frac{1}{N} \sum_{i=1}^{N} (\hat{\theta}_i - \theta_i^*)^2 } $$
where $\hat{\theta}_i$ is the predicted parameter posterior mean for household $i$, and $\theta_i^*$ is the known ground-truth value (assessed via synthetic data tests).

### 2.2. Out-of-Sample Predictive Fit via WAIC / LOO-CV
To measure how well the models generalize to unseen data while penalizing over-parameterization, we will compute the Widely Applicable Information Criterion (WAIC) and Leave-One-Out Cross-Validation (LOO-CV):
$$ \text{WAIC} = -2 \left( \text{LLPD} - p_{\text{WAIC}} \right) $$
where $\text{LLPD}$ is the log pointwise predictive density and $p_{\text{WAIC}}$ is the effective number of parameters computed via posterior variance.
Lower WAIC indicates better out-of-sample predictive performance. 

### 2.3. Computational Complexity
We will benchmark the scaling performance of the synthesis model against traditional microscopic simulation (e.g., full EnergyPlus coupled runs).
- **Traditional Model (Competitor A Baseline Full Simulation)**: Scales as $\mathcal{O}(N^2)$ or worse when handling inter-building shadowing and complex dynamic routing for $N$ buildings.
- **ABS-UBEM (Surrogate)**: Leverages differentiable tensor operations, scaling as $\mathcal{O}(E)$ where $E$ represents the number of edges (e.g., geographic adjacency or network constraints) in sparse matrix formulations, enabling tractability at the city scale.

### 2.4. Identifiability via Fisher Information Matrix (FIM)
To guarantee that the socio-physical parameters are identifiable and not highly collinear, we approximate the Fisher Information Matrix:
$$ \mathcal{I}(\theta) = - \mathbb{E} \left[ \nabla_\theta^2 \log p(Y | X, \theta) \right] $$
A well-conditioned FIM (i.e., strictly positive eigenvalues) proves that the socio-demographic parameters (e.g., price elasticity, thermal preference) and physical parameters can be distinctly decoupled from the likelihood.

---

## 3. The Epistemic Defense

### 3.1. The Structural Failure of Physics-Only Models
A common critique from reviewers is that discrepancies in energy demand modeling can be solved simply by employing a "cutting-edge" physics engine or a more granular surrogate. The **Epistemic Defense** mathematically invalidates this claim.

Physics-based models (Competitor A) assume normative consumption—that households will utilize energy to reach thermal comfort regardless of financial constraint. In reality, households facing fuel poverty severely ration their energy. Therefore, a physics-only model will consistently overpredict demand in low-income areas.

### 3.2. Statistical Proof of Epistemic Failure
We define the **Performance Gap Residual**, $\epsilon_A$, as:
$$ \epsilon_A^{(i)} = \hat{Y}_{A}^{(i)} - Y_{\text{actual}}^{(i)} $$
where $\hat{Y}_{A}^{(i)}$ is the energy demand predicted by Competitor A (Physics-Only) and $Y_{\text{actual}}^{(i)}$ is the empirically observed energy demand.

To prove that the failure of Competitor A is *epistemic* (i.e., a fundamental structural flaw rather than a parameter tuning issue), we map the residual $\epsilon_A$ against a standardized deprivation metric, the **Index of Multiple Deprivation (IMD)** (or local equivalent).

We perform a correlation test (Pearson's $r$ for linear dependency, and Spearman's rank correlation $\rho$ for monotonic dependency):
$$ \rho(\epsilon_A, \text{IMD}) = \frac{\text{cov}(\text{rank}(\epsilon_A), \text{rank}(\text{IMD}))}{\sigma_{\text{rank}(\epsilon_A)} \sigma_{\text{rank}(\text{IMD})}} $$

**Hypothesis Test:**
- $H_0: \rho(\epsilon_A, \text{IMD}) = 0$ (Errors are randomly distributed; physics engine simply needs better calibration).
- $H_1: \rho(\epsilon_A, \text{IMD}) > 0$ (Errors systematically scale with poverty).

### 3.3. Conclusion of the Defense
If $H_1$ holds statistically significant ($p < 0.05$), it proves mathematically that the residual error is socioeconomically structured. A physics-only surrogate cannot solve this because it has no mathematical formulation of socioeconomic state. Thus, ABS-UBEM's incorporation of Bayesian demographic constraints is strictly necessary to bridge this epistemic gap.
