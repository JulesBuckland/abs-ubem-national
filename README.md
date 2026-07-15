# ABS-UBEM: Agent-Based Spatial Urban Building Energy Model

A highly-scalable, methodologically rigorous Bayesian inference pipeline for decoupling physical building efficiency from socioeconomic energy rationing (fuel poverty).

## Execution (Out-of-the-Box)
To run the fully reproducible Bayesian pipeline:

```bash
# Execute the beautiful Rich CLI interface
python -m src.cli.run_inference
```

## System Architecture (C4 Model)
This repository is structured according to strict SOLID principles and the Gentzkow & Shapiro guidelines for reproducibility. Below is the C4 architecture mapping the flow of data through the Bayesian components.

```mermaid
graph TD
    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff;
    classDef system fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#fff;
    classDef extSystem fill:#999999,stroke:#6b6b6b,stroke-width:2px,color:#fff;
    classDef container fill:#438dd5,stroke:#2f6295,stroke-width:2px,color:#fff;
    classDef database fill:#438dd5,stroke:#2f6295,stroke-width:2px,color:#fff;

    subgraph "System Context (Level 1)"
        User[Energy Researcher]:::person
        ABSUBEM[ABS-UBEM Platform]:::system
        PySAL[PySAL/GeoPandas\nSpatial Boundary Engine]:::extSystem
    end

    User -- "Executes CLI Pipeline" --> ABSUBEM
    ABSUBEM -- "Calculates Contiguity" --> PySAL

    subgraph "Container Diagram (Level 2)"
        CLI[src/cli/run_inference.py\nRich CLI Entry Point]:::container
        GP[Gaussian Process Emulator\nReplaces Power-Law Scaling]:::container
        RSR[Restricted Spatial Regression\nOrthogonal Projection]:::container
        MCMC[PyMC NUTS Sampler\nSparse 1D ICAR Formulation]:::container
        Data[(Processed Data Store\nParquet / CSV)]:::database
    end

    ABSUBEM -. "Decomposes into" .-> CLI
    CLI -- "Loads Population" --> Data
    CLI -- "Triggers" --> GP
    GP -- "T* Predictions" --> RSR
    RSR -- "Orthogonal Z-Confounders" --> MCMC
    Data -- "Empirical KWh" --> MCMC
    MCMC -- "Exports Decoupled T*" --> Data
```


