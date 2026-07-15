# Industry-Standard Data Pipeline Testing Plan

In industry, we rely on **Falsifiable End-to-End (E2E) Fixture Testing**. 

Here is the strategy to mathematically guarantee the pipeline is 100% bug-free before running it on the massive national dataset.

## The Strategy: "Tiny Fixtures & Golden Outputs"

1. **The Tiny Fixture**: We will extract exactly **1 Local Authority District (LAD)** containing maybe 2 MSOAs and 10 archetype variations. We save this tiny dataset in a dedicated `tests/fixtures/` folder.
2. **Environment Injection**: We will modify the pipeline so that if we set a flag like `TEST_MODE=1`, it completely ignores the national data and only runs on the tiny fixture.
3. **The 5-Second Run**: Because the data is tiny, the *entire* pipeline (synthesis, GP, Bayesian model) will run in seconds, not hours.
4. **The "Golden" Assertion**: We verify the output of the tiny run *once* by hand to ensure the physics and math are flawless. We save this output as the **Golden Baseline**.
5. **Continuous Verification**: We write a `pytest` suite. Every time we run `pytest`, the test suite runs the pipeline on the tiny fixture. If the output deviates from the Golden Baseline by even 0.0001%, the test **fails immediately**. This makes bugs falsifiable.

## Proposed Changes

### `tests/` (New Test Architecture)

#### [NEW] `tests/generate_fixtures.py`
A script that slices the massive `data/raw/` files into a tiny, self-contained dataset (1 LAD, 10 households) and saves it to `tests/fixtures/`.

#### [NEW] `tests/test_e2e_pipeline.py`
An automated test suite using `pytest`. It will programmatically trigger the pipeline scripts sequentially on the tiny fixture, and automatically assert that:
* No silent drops occurred.
* Physical bounds (like $T^*$) are strictly maintained.
* The output matches the mathematical expectation.

### Pipeline Configuration

#### [MODIFY] `scripts/config.py`
Add logic to dynamically switch paths:
```python
import os
import pandas as pd

TEST_MODE = os.environ.get("TEST_MODE", "0") == "1"

if TEST_MODE:
    RAW_DIR = BASE_DIR / "tests" / "fixtures" / "raw"
    PROCESSED_DIR = BASE_DIR / "tests" / "fixtures" / "processed"
else:
    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"
```
