# ABS-UBEM: Agent-Based Spatial Urban Building Energy Model

A highly-scalable, methodologically rigorous Bayesian inference pipeline for decoupling physical building efficiency from socioeconomic energy rationing (fuel poverty).

## Execution (Out-of-the-Box)
To run the fully reproducible Bayesian pipeline:

```bash
# Execute the beautiful Rich CLI interface
python -m src.cli.run_inference
```

## System Architecture (C4 Model)
### Level 1: System Context Diagram
A high-level view showing the user interaction with the ABS-UBEM software boundary.

```mermaid
graph TD
    %% University of Manchester Brand Theme
    classDef person fill:#660099,color:#FFFFFF,stroke:#333333,stroke-width:2px;
    classDef system fill:#660099,color:#FFFFFF,stroke:#FFCC33,stroke-width:3px;

    User["Energy Researcher<br/>[Person]<br/>Executes the reproducible pipeline"]:::person
    System["ABS-UBEM<br/>[Software System]<br/>National-scale spatial Bayesian energy model"]:::system
    
    User -- "Configures and executes pipeline via CLI" --> System
```

### Level 2: Container Diagram
Zooming into the ABS-UBEM software system to show its primary execution containers.

```mermaid
---
title: C4 Level 2 Container Diagram - ABS-UBEM Python CLI Architecture
---
flowchart TD
    %% Styling - University of Manchester Brand Colors
    classDef person fill:#660099,color:#ffffff,stroke:#333333,stroke-width:2px
    classDef container fill:#FFCC33,color:#333333,stroke:#333333,stroke-width:2px
    classDef datastore fill:#333333,color:#ffffff,stroke:#FFCC33,stroke-width:2px
    classDef boundary fill:none,color:#333333,stroke:#660099,stroke-width:2px,stroke-dasharray: 5 5

    %% Legend (Invisible nodes used for legend display)
    subgraph Legend ["Legend"]
        direction LR
        L1["Person"]:::person
        L2["Application Container"]:::container
        L3["Data Store Container"]:::datastore
    end

    %% Actors
    User["👤 Energy Researcher<br/>[Person]<br/>Executes the inference pipeline and reviews posterior results"]:::person

    %% System Boundary
    subgraph ABS_UBEM ["ABS-UBEM Local Environment"]
        direction TB
        
        CLI["⚙️ ABS-UBEM Inference CLI<br/>[Container: Python / PyMC / Rich]<br/>Orchestrates spatial matrix building, GP emulator predictions, and NUTS sampling"]:::container
        
        InputFS["📂 Input Data Store<br/>[Container: Local File System]<br/>Stores synthetic population (.parquet), GP emulator (.pkl), and Geo boundaries"]:::datastore
        
        OutputFS["💾 Output Data Store<br/>[Container: Local File System]<br/>Stores MCMC traces (.nc), decoupled energy metrics (.csv), and WAIC logs"]:::datastore
    end
    class ABS_UBEM boundary

    %% Relationships
    User -- "Runs inference and monitors dashboard via<br/>[Terminal/CLI]" --> CLI
    CLI -- "Reads configuration, models, and spatial data from<br/>[File I/O]" --> InputFS
    CLI -- "Writes posterior traces and T* results to<br/>[File I/O]" --> OutputFS
```

### Level 3: Component Diagram (ABS-UBEM Application)
Zooming inside the application runtime to show the Python logic modules handling the physics-to-spatial pipeline.

```mermaid
graph TD
    %% University of Manchester Brand Theme
    classDef component fill:#FFCC33,color:#333333,stroke:#660099,stroke-width:2px;
    classDef database fill:#FFCC33,color:#333333,stroke:#333333,stroke-width:2px;
    classDef extLib fill:#333333,color:#FFFFFF,stroke:#FFCC33,stroke-width:2px,stroke-dasharray: 5 5;

    subgraph ABS-UBEM Application Boundary
        CLI["CLI Orchestrator<br/>[Python / Rich]<br/>Entry point and progress management"]:::component
        GP["GP Emulator Component<br/>[Python / Scikit-Learn]<br/>Replaces slow archetype matching with O(1) surrogate"]:::component
        RSR["RSR Component<br/>[Python / NumPy]<br/>Orthogonally projects spatial effects away from Z-confounders"]:::component
        MCMC["Bayesian Inference Engine<br/>[Python / PyMC]<br/>Executes Sparse 1D Queen-contiguity ICAR"]:::component
        Data[("Local File System<br/>[Parquet / CSV]<br/>Stores synthetic populations and empirical targets")]:::database
    end
    
    PySAL["GeoPandas / PySAL<br/>[External Library]<br/>Builds the spatial adjacency matrix"]:::extLib

    CLI -- "Reads configuration and data" --> Data
    CLI -- "Triggers emulation" --> GP
    GP -- "T* (Theoretical Energy) Predictions" --> RSR
    RSR -- "Orthogonalized Z-Confounders" --> MCMC
    MCMC -- "Reads Empirical KWh" --> Data
    MCMC -- "Requests Edge-list" --> PySAL
    MCMC -- "Writes Posterior Decoupled T*" --> Data
```

**C4 Legend:**
*   **Purple (`#660099`)**: Primary Actors and Core Systems.
*   **Gold/Yellow (`#FFCC33`)**: Internal Components and Local Storage.
*   **Dark Grey (`#333333`)**: External Third-Party Library Dependencies.


