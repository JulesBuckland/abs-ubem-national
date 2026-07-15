# ABS-UBEM Software Engineering & Test Plan

This document outlines the strict SOLID software engineering strategy and subagent orchestration for implementing the 5-node empirical toy pilot and subsequent scaling. Quality, modularity, and provability are the highest priorities.

## 1. Directory Architecture (SOLID Compliance)
We will restructure the Python implementation away from flat scripts into a proper modular package.

```text
paper 5/
├── src/
│   ├── __init__.    py
│   ├── data/
│   │   ├── synthetic_dgp.py       # Data Generating Process (Breaking Inverse Crime)
│   │   └── graph_builder.py       # 5-Node ICAR adjacency generator
│   ├── physics/
│   │   ├── base_surrogate.py      # Abstract Base Class for surrogates (OCP principle)
│   │   ├── convex_emulator.py     # The safe fallback differentiable polynomial
│   │   └── neural_surrogate.py    # The deep PyTensor neural network
│   └── inference/
│       ├── abs_ubem_model.py      # The joint PyMC ICAR + Physics graphical model
│       └── nuts_runner.py         # The sampler execution and diagnostic logger
├── tests/
│   ├── unit/                      # Isolated tests for physics logic and graph shapes
│   └── e2e/                       # Full NUTS mixing tests on the 5-node pilot
└── scripts/
    └── 01a_run_toy_pilot.py       # The entrypoint script that glues src/ components
```

## 2. Testing Strategy (TDD)
*   **Unit Tests (`tests/unit/`)**: Verify that the PyTensor Differentiable Surrogate outputs expected gradients without crashing, and that the ICAR edge-list generator produces a valid adjacency matrix.
*   **E2E Tests (`tests/e2e/`)**: The actual 5-node toy pilot acts as our E2E test. It asserts that running 1,000 NUTS tuning steps on the joint `abs_ubem_model` results in a Gelman-Rubin ($\hat{R}$) score of $< 1.05$ and exactly $0$ leapfrog divergences.

## 3. Subagent Orchestration Plan

We will deploy a swarm of specialized subagents, each with a strict boundary of responsibility.

### Subagent 1: The TDD Architect (Role: DevOps / QA)
*   **Task:** Scaffold the `src/` and `tests/` directories.
*   **Deliverable:** Write the Pytest configuration and the initial *failing* unit tests and E2E pilot tests.

### Subagent 2: The Physics Engineer (Role: PyTensor Expert)
*   **Task:** Implement `src/physics/convex_emulator.py`. 
*   **Deliverable:** A highly stable, strictly convex differentiable equation written in PyTensor that passes the TDD Architect's unit tests for stable Vector-Jacobian Products (VJPs).

### Subagent 3: The Bayesian Statistician (Role: PyMC Expert)
*   **Task:** Implement `src/inference/abs_ubem_model.py` and `src/data/graph_builder.py`.
*   **Deliverable:** A PyMC model that connects a 5-node spatial edge-list (ICAR) to the outputs of the Physics Engineer's surrogate.

### Subagent 4: The Integration Commander (Role: Main Agent / You)
*   **Task:** Review the subagents' code, write `scripts/01a_run_toy_pilot.py`, and execute the empirical run on the terminal.
*   **Deliverable:** The final $\hat{R}$ and divergence logs proving the architecture works.
