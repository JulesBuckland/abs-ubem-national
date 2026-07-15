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
    %% University of Manchester Brand Theme - C4 Model
    classDef person fill:#660099,color:#FFFFFF,stroke:#333333,stroke-width:2px;
    classDef system fill:#660099,color:#FFFFFF,stroke:#FFCC33,stroke-width:3px;
    classDef extSystem fill:#333333,color:#FFFFFF,stroke:#FFCC33,stroke-width:2px,stroke-dasharray: 5 5;
    classDef container fill:#FFCC33,color:#333333,stroke:#660099,stroke-width:2px;
    classDef database fill:#FFCC33,color:#333333,stroke:#333333,stroke-width:2px;

    subgraph "System Context (Level 1)"
        User[Energy Researcher]:::person
        ABSUBEM[ABS-UBEM Platform]:::system
        PySAL[PySAL/GeoPandas\nSpatial Boundary Engine]:::extSystem
    end

    User -- "Executes CLI Pipeline" --> ABSUBEM
    ABSUBEM -- "Calculates Contiguity" --> PySAL

    subgraph "Container Diagram (Level 2)"
        CLI[CLI Orchestrator\nRich CLI Entry Point]:::container
        GP[GP Emulator\nReplaces Power-Law Scaling]:::container
        RSR[RSR Component\nOrthogonal Projection]:::container
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


