# BS-UBEM: Auto-Differentiable Bayesian Surrogate for Urban Building Energy Modeling

A highly-scalable, methodologically rigorous Bayesian inference pipeline for decoupling physical building efficiency from socioeconomic energy rationing (fuel poverty).

## Execution (Out-of-the-Box)
To run the fully reproducible Bayesian pipeline:

```bash
# Execute the beautiful Rich CLI interface
python -m src.cli.run_inference
```

## System Architecture

Below is the complete computational architecture mapping the flow of data through the Iterative Proportional Fitting, physics surrogate, and Bayesian components.

```mermaid
---
title: BS-UBEM: Auto-Differentiable Bayesian Spatial Pipeline
---
flowchart TD
    %% Styling - University of Manchester Brand Colours
    classDef person fill:#660099,color:#ffffff,stroke:#333333,stroke-width:2px
    classDef orchestrator fill:#FFCC33,color:#333333,stroke:#660099,stroke-width:3px
    classDef logic fill:#FFCC33,color:#333333,stroke:#333333,stroke-width:2px
    classDef datastore fill:#333333,color:#ffffff,stroke:#FFCC33,stroke-width:2px
    classDef extLib fill:#f4f4f4,color:#333333,stroke:#333333,stroke-width:2px,stroke-dasharray: 4 4

    User["Energy Researcher<br/>[Person]<br/>Executes inference pipeline"]:::person

    InputFS["Input Data Store<br/>[Local File System]<br/>Census Marginals<br/>Pre-trained Models (.pkl)<br/>MSOA Boundaries"]:::datastore
    OutputFS["Output Data Store<br/>[Local File System]<br/>Posterior Traces (.nc)<br/>Decoupled Metrics (.csv)"]:::datastore

    CLI["BS-UBEM CLI Orchestrator<br/>[Python / Rich]<br/>Manages execution flow and state"]:::orchestrator

    subgraph CoreLogic ["Core Physics & Spatial Math"]
        direction TB
        IPF["Iterative Proportional Fitting (IPF)<br/>[NumPy/SciPy]<br/>Generates high-resolution synthetic agents<br/>matching national census marginals"]:::logic

        GP["Gaussian Process Surrogate Model<br/>[Scikit-Learn / PyTensor]<br/>Auto-Differentiable mapping of housing archetypes<br/>to theoretical energy demand (T*) in O(1) time"]:::logic
        
        RSR["Restricted Spatial Regression (RSR)<br/>[NumPy]<br/>Projects the spatial random effect<br/>onto the orthogonal complement of<br/>the Income Deprivation Index (Z)"]:::logic
        
        MCMC["Bayesian Inference Engine<br/>[PyMC NUTS Sampler]<br/>Solves the national-scale spatial graph<br/>using a Sparse 1D Queen-contiguity ICAR prior"]:::logic
    end
    
    PySAL["GeoPandas / PySAL<br/>[External Library]<br/>Builds the MSOA spatial adjacency matrix"]:::extLib

    User -- "Triggers Pipeline" --> CLI
    CLI -- "Loads data" --> InputFS
    CLI -- "Initialises" --> IPF
    IPF -- "Passes Synthetic Agents" --> GP
    GP -- "Passes Differentiable T*" --> RSR
    RSR -- "Passes Orthogonalised Z" --> MCMC
    MCMC -- "Requests Adjacency Edge-List" --> PySAL
    MCMC -- "Writes Posterior Results" --> OutputFS
```


