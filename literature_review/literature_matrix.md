# Literature Matrix & Novelty Claim

## Literature Matrix

This matrix extracts recent and seminal papers at the intersection of Urban Building Energy Modeling (UBEM), Bayesian Calibration, Surrogates, and Spatial Fields.

| Citation | Methodology | Key Findings | Limitations | Future Work |
| :--- | :--- | :--- | :--- | :--- |
| **Sokol et al. (2017)**<br>*Validation of a Bayesian-based method for defining residential archetypes in urban building energy models* | Uses traditional Bayesian calibration (likely MCMC sampling without AutoDiff) to define building archetypes for UBEMs. | Validates that Bayesian calibration improves archetype accuracy, replacing deterministic assumptions. | Relies on archetype groupings rather than spatially granular, building-level models. Computationally heavy for large-scale. | Extend calibration methods to handle higher-resolution building characteristics and spatial parameters. |
| **Johari et al. (2020)**<br>*Bayesian calibration at the urban scale: a case study on a large residential heating demand application in Amsterdam* | Bottom-up UBEM using GIS and 3D city models, calibrated via Bayesian methods. | Demonstrates feasibility of large-scale Bayesian calibration on heating demand. | Lack of explicit spatial autocorrelation modeling; computationally bottlenecked by non-differentiable simulation runs. | Incorporate faster surrogate models and spatial dependencies. |
| **Nageler et al. (2018)**<br>*Hierarchical calibration of archetypes for urban building energy modeling* | Hierarchical Bayesian calibration applied to building archetypes. | Shows hierarchical models effectively capture parameter variance across building groups. | Does not model explicit geospatial correlation (ICAR) between neighboring buildings. | Develop methodologies that replace strict archetypes with continuous spatial variation. |
| **Nutkiewicz et al. (2021)**<br>*Influence of data acquisition on the Bayesian calibration of urban building energy models* | Analyzes how data availability affects Bayesian calibration accuracy in UBEMs. | Confirms that more data improves calibration, but computational limits restrict full uncertainty quantification. | Limited to non-differentiable workflows. Struggles with high-dimensional parameter spaces. | Explore machine learning or differentiable surrogates to overcome computational bottlenecks. |
| **Park et al. (2024)**<br>*Reducing Uncertainty of Building Shape Information in Urban Building Energy Modeling using Bayesian Calibration* | Bayesian calibration applied specifically to geometric/shape uncertainties in UBEM. | Shape information uncertainty can be significantly reduced using Bayesian techniques. | Models remain non-differentiable, preventing the use of advanced gradient-based samplers (NUTS). | Combine shape uncertainty models with faster simulation proxies. |

## The Zero-Crossover Novelty Claim

**The Gap:** 
Following the "Gap Hunter" methodology, we identify a clear **Conceptual and Methodological Gap** in the current state-of-the-art for Urban Building Energy Modeling (UBEM). Current approaches to Bayesian calibration in UBEM (e.g., Sokol 2017, Johari 2020) rely on traditional, non-differentiable simulators and archetype-based simplifications. While these models quantify uncertainty, they are computationally bottlenecked by gradient-free sampling (e.g., standard MCMC) and fail to explicitly model geospatial dependencies (spatial autocorrelation) between individual buildings. 

Conversely, modern machine learning has introduced Auto-Differentiable Surrogates, and spatial statistics possesses robust Bayesian Spatial Fields (like Intrinsic Conditional Autoregressive - ICAR models). However, there is a **zero-crossover** point in the literature combining these three domains. 

**The Claim:**
No existing paper has successfully integrated **PyMC/PyTensor ICAR spatial models** with **physics-based differentiable surrogates** to achieve scalable, spatially-aware Bayesian calibration for **UBEM**.

**Our Contribution (Occupying the Niche):**
The AutoDiff Bayesian Surrogate (ABS-UBEM) model is the first to achieve this integration. By replacing the non-differentiable UBEM with a differentiable surrogate, ABS-UBEM unlocks the use of gradient-based sampling (NUTS) across thousands of buildings. Furthermore, by embedding an ICAR spatial field directly into the PyTensor computation graph, the model natively captures spatial autocorrelation (e.g., urban heat island effects, shared microclimates) without the computational collapse experienced by traditional archetype models. This provides a fundamental shift in the level of evidence and scalability available for urban-scale energy calibration.
