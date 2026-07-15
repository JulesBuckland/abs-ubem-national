# ABS-UBEM: The Lossless Theoretical Foundation

This document serves as the immutable "Golden Source of Truth" for the theoretical framing, novelty claims, and mathematical architecture of the AutoDiff Bayesian Surrogate (ABS-UBEM) paper. It integrates all adversarial peer-review corrections to ensure the claims are strictly empirical, reviewer-safe, and distinct from state-of-the-art prior art.

## 1. The Core Mathematical Architecture
The model unifies bottom-up 3D building physics with top-down socio-spatial demographics into a single probabilistic inference graph. The energy demand $Y$ for building $i$ in neighborhood $j$ is defined as:

$$ \log(Y_{i,j}) = f_{\theta}(\text{LiDAR}_i) + \beta \cdot X_j + \phi_j + \epsilon_{i,j} $$

*   $f_{\theta}(\text{LiDAR}_i)$: A **Differentiable Physics Surrogate** taking in building geometry (e.g., Footprint, Height, S/V Ratio).
*   $\beta \cdot X_j$: The **Socio-Demographic** linear regression coefficient (e.g., Census Income, Age).
*   $\phi_j$: The **Sparse ICAR** (Intrinsic Conditional Autoregressive) spatial-smoothing prior.

## 2. The Refined Novelty Claim
**The Claim:** *To our knowledge, no published work has successfully executed the joint, gradient-based sampling (via NUTS/HMC) of a differentiable, geometry-conditioned physics surrogate simultaneously with an explicit graph-smoothing spatial prior (ICAR).*

We are emphatically **not** claiming the invention of ICAR (which is inherently sparse by Besag's 1974 design), nor are we claiming the invention of surrogate HMC or DNN surrogates. We are claiming the mathematically stable integration of these isolated components to solve the urban "Performance Gap" without hitting dense matrix scaling limits.

## 3. The Building Blocks vs. The Competitors
To preempt reviewer concerns, the paper strictly defines what is a foundational building block vs. what is a gap.

**The Building Blocks (What we build upon):**
*   *DNN Surrogates for UBEMs:* We acknowledge that deep neural networks are already used to replace slow urban energy simulators (e.g., the 2025 Singapore Zernike moments study) and that differentiable surrogates are used for gradient-descent calibration. 
*   *NREL Tabular Diffusion (2025):* Generative models exist for large building stocks, but they solve missing attribute imputation, not spatially-smoothed energy inference.
*   *Biljecki & Nagy (2024-2025):* Bleeding-edge work uses Graph Neural Networks (GNNs) for building characteristics via learned message-passing, and spatio-temporal calibration. They are the closest neighbors, but they do not use explicit hierarchical Bayesian ICAR priors optimized jointly via NUTS.

**The Gaps (What we solve):**
*   *Kennedy-O'Hagan (KOH) Calibration:* KOH strictly uses Gaussian Processes (GPs), which require $O(N^3)$ dense matrix inversions that fail at urban scales. Our differentiable surrogate bypasses this.
*   *French National Scale NUTS (Artiges 2021):* Maps grey-box RC models to spatial zones but lacks any explicit neighbor-graph adjacency structure (ICAR) or neural emulators.
*   *Spatially-Explicit Estimation (Zhuravchak 2021):* Uses MLE-style univariate density fitting on a 1x1km grid, completely lacking Bayesian spatial autoregression or HMC.

## 4. The Engineering Tradeoffs & Safeties
*   **The Convex Fallback:** We explicitly acknowledge that the neural surrogate is not "magic"—it is a flexible basis function. Deep neural networks inside a Hamiltonian potential energy function often cause pathological sampling ($\hat{R}$ explosion). If HMC mixing fails, we trade expressiveness for stability by enforcing a strictly convex or monotonic emulator structure, effectively acting as an advanced parametric grey-box model.
*   **Breaking the Inverse Crime:** We do not generate synthetic data using our own equations. The Data Generating Process (DGP) is explicitly misspecified. The "Ground Truth" city is simulated using a deterministic physics engine paired with a chaotic Agent-Based Model (ABM). This forces ABS-UBEM to empirically bridge regimes rather than memorize a tautology.
*   **The Formal Compute Bound:** The scalability limit is formally defined as $O(E + B \cdot d \cdot L_{max})$. This accounts for the sparse ICAR edges ($E$), the number of buildings in a batch ($B$), the FLOP cost of the surrogate forward/backward pass ($d$), and the maximum allowed leapfrog steps per NUTS trajectory ($L_{max}$).
