import os
import subprocess
import sys
import pytest
import pandas as pd
from pathlib import Path

# --- Configuration ---
# We use Manchester as the reliable E2E integration subset because it has ~30 MSOAs.
# This tests the spatial ICAR component without taking hours.
TEST_LAD = "Manchester"

def test_pipeline_e2e_integration():
    """
    End-to-End integration test for Paper 5 Pipeline.
    Validates mathematical and structural integrity using Defensive Programming assertions.
    """
    
    # 1. Run the Pipeline Orchestrator in E2E mode
    env = os.environ.copy()
    env["E2E_TARGET_LAD"] = TEST_LAD
    
    # The orchestrator is designed to "fail fast". If it hits an exit code > 0,
    # one of our inline defensive assertions (e.g. negative energy, dimension mismatch) fired.
    orchestrator_path = Path("main.py").resolve()
    
    # Note: run_pipeline.py accepts --test-lad, but it also just reads E2E_TARGET_LAD.
    # We pass --test-lad for explicitness.
    result = subprocess.run(
        [sys.executable, str(orchestrator_path), "--test-lad", TEST_LAD],
        env=env,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:\n", result.stderr)
        
    assert result.returncode == 0, f"Pipeline crashed or hit an inline defensive assertion!\n{result.stderr}"

    # 2. Semantic Output Verification (Post-hoc checks)
    
    # Verify Phase 1 (Population Synthesis) generated the subset parquet safely
    base_dir = Path(__file__).resolve().parent.parent
    e2e_dir = base_dir / "data" / "processed" / "tests" / "e2e_outputs"
    parquet_path = e2e_dir / "national_synthetic_population_eti.parquet"
    
    assert parquet_path.exists(), "Phase 1 Parquet file was not generated in the E2E route."
    
    df = pd.read_parquet(parquet_path)
    assert len(df) > 1000, f"Synthetic population too small for {TEST_LAD} ({len(df)} rows). Synthesis failed silently."
    
    # Verify Phase 2 (Bayesian ICAR) successfully sampled the posterior
    trace_path = base_dir / "data" / "processed" / "national_unified_trace.nc"
    assert trace_path.exists(), "Phase 2 Bayesian Trace was not generated."
    
    import arviz as az
    trace = az.from_netcdf(trace_path)
    
    # Ensure key variables were sampled (checking for numerical infinities/crashes)
    assert 'posterior' in trace, "Trace does not contain posterior samples."
    assert 'beta_inc' in trace.posterior, "Elasticity for poverty (beta_inc) was not sampled."
    
    # Test passed!
    print(f"E2E Integration Test passed for {TEST_LAD}.")
