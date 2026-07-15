# The Trojan Horse Plan: ABS-UBEM Benchmark & Scaling Strategy

This document outlines the end-to-end strategy to mathematically prove that the AutoDiff Bayesian Surrogate (ABS-UBEM) is the superior paradigm for national-scale energy modeling, circumventing the flaws of both traditional engineering models (LiDAR/Physics) and traditional statistical models.

## Part 1: Problem Decomposition
To prove we are the best, we must first mathematically define why everyone else fails. We decompose the UBEM problem into three distinct failure modes:

1. **The Physics Fallacy (Equifinality of the Envelope):** Engineering models (AutoBEM, CityBES) assume energy variance is driven strictly by 3D geometry (LiDAR). They fail because identical buildings consume vastly different energy depending on the occupant's socio-demographics (The Performance Gap).
2. **The Statistical Fallacy (The Geometric Blindspot):** Pure Bayesian models (Neto-Bradley) capture the socio-demographics but treat buildings as homogenized archetypes. They fail because they cannot isolate variance caused by unique physical geometry, leading to bloated uncertainty bounds ($\sigma$).
3. **The Computational Choke-Point:** Combining these two (running deterministic 3D physics inside a Bayesian MCMC loop) scales at $O(N \cdot T \cdot M)$, where $N$ is buildings, $T$ is timesteps, and $M$ is MCMC draws. It is computationally impossible at a national scale.

---

## Part 2: The Tri-Model Benchmark
We will generate a synthetic "Ground Truth City" where consumption $Y$ is a function of both **Synthetic LiDAR** (Volume, Surface-to-Volume Ratio, Glazing) and **Socio-Demographics** (Income, Spatial Field). 

We will then run three separate pipelines against this city:

### Competitor A: "The Traditional Engineer" (Physics-Only)
* **Architecture:** A deterministic neural surrogate mapping LiDAR features to energy demand. No socio-demographic inputs; no spatial correlation.
* **Expected Failure:** Will systematically underpredict demand in fuel-rich areas and overpredict in fuel-poor areas.

### Competitor B: "The Traditional Statistician" (Social-Only)
* **Architecture:** A Bayesian ICAR model mapping Census demographics to energy demand. Uses flat "archetype" physics, ignoring the synthetic LiDAR features.
* **Expected Failure:** Will capture spatial clusters but will fail on building-to-building variance, resulting in massive, uninformative posterior uncertainty bounds.

### Our Model: ABS-UBEM (The Synthesis)
* **Architecture:** Ingests LiDAR features into a differentiable PyTensor surrogate to compute the physics baseline gradient, while simultaneously using Sparse ICAR to infer the socio-demographic spatial gradients.
* **Expected Success:** Recovers both physical and social ground-truth parameters perfectly.

---

## Part 3: Proving Superiority (The Mathematical Tests)
We will not rely on simple R-squared metrics. We will prove superiority using three rigorous structural and statistical tests:

1. **Parameter Recovery (RMSE of the Truth):** Because it is a synthetic city, we know the exact values of $\beta_{physics}$ and $\beta_{social}$. We will measure the Root Mean Square Error (RMSE) between the models' predictions and the known ground truth. ABS-UBEM must have an RMSE near zero.
2. **Widely Applicable Information Criterion (WAIC):** WAIC measures the out-of-sample predictive accuracy of a Bayesian model while penalizing for overfitting. A lower WAIC score for ABS-UBEM mathematically proves it provides a better fit than Competitor B without merely memorizing the noise.
3. **The Orthogonal Jacobian Test (Identifiability):** We will evaluate the Fisher Information Matrix during the NUTS tuning phase. We must show that the mass matrix is full-rank, proving that the Differentiable Surrogate and the ICAR field do not collapse into equifinality. 

---

## Part 4: Computing the Scaling (The "Big O" Proof)
To justify this for a national-scale model, we must prove that ABS-UBEM scales elegantly. We will measure compute using the `run_exponential_tests.ps1` script (Tiny $\to$ Medium $\to$ Large $\to$ Full).

We will track **CPU Seconds** and **Peak RAM (GB)** across the four scales and map them to their Big O time complexity:

1. **Deterministic Physics Scaling (Competitor A):**
   * Traditional EnergyPlus scales linearly: $O(N)$. However, for 30 million buildings, $O(N)$ takes years.
   * *Our Surrogate:* Scales at $O(1)$ batch inference on a GPU, or highly vectorized $O(N)$ on a CPU taking milliseconds.
2. **Dense Bayesian Scaling (The Old Way):**
   * Traditional spatial models invert dense covariance matrices, scaling at $O(N^3)$. 6,800 MSOAs would crash any standard server.
3. **Sparse ICAR Scaling (ABS-UBEM):**
   * By framing the spatial field as a sparse graph network (edge lists), our PyTensor implementation reduces the matrix inversion to $O(E)$, where $E$ is the number of shared geographic boundaries. 
   * **The Proof:** We will plot a logarithmic chart of our runtimes. The line for $O(N^3)$ will curve violently upward and crash at 2,000 MSOAs. Our empirical runtime curve will remain near-linear $O(E)$, proving that ABS-UBEM can theoretically process the entire planet.
