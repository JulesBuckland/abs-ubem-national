import pytest
import os
import sys
import subprocess
import pandas as pd
from pathlib import Path
import arviz as az

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.mark.requires_fixtures
def test_golden_baseline():
    """
    Runs the pipeline end-to-end in test mode and compares outputs against a golden baseline.
    If the golden baseline does not exist, it creates one.
    """
    # 1. Run the pipeline components
    for module in ["src.data.population", "src.inference.gp_emulator", "src.inference.model_unified"]:
        result = subprocess.run(
            [sys.executable, "-m", module],
            cwd=str(BASE_DIR),
            env=os.environ.copy(),
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"{module} crashed:\n{result.stderr}\n{result.stdout}"

    out_dir = BASE_DIR / "tests" / "fixtures" / "processed"
    golden_dir = BASE_DIR / "tests" / "fixtures" / "golden"
    golden_dir.mkdir(parents=True, exist_ok=True)

    # 2. Check Synthetic Population (Exact Match)
    synth_path = out_dir / "national_synthetic_population_eti.parquet"
    synth_golden = golden_dir / "national_synthetic_population_eti.parquet"
    assert synth_path.exists(), "Synthesis output missing."
    df_synth = pd.read_parquet(synth_path)
    
    if not synth_golden.exists():
        df_synth.to_parquet(synth_golden)
        print(f"Created golden baseline at {synth_golden}")
    else:
        df_golden_synth = pd.read_parquet(synth_golden)
        pd.testing.assert_frame_equal(df_synth, df_golden_synth, check_exact=True)

    # 3. Check Bayesian Trace (Summary check, as MCMC has variance)
    trace_path = out_dir / "national_unified_trace.nc"
    trace_golden = golden_dir / "national_unified_trace_summary.csv"
    assert trace_path.exists(), "Bayesian trace missing."
    
    trace = az.from_netcdf(trace_path)
    df_summary = az.summary(trace).astype(float)
    
    if not trace_golden.exists():
        df_summary.to_csv(trace_golden)
        print(f"Created golden baseline at {trace_golden}")
    else:
        df_golden_summary = pd.read_csv(trace_golden, index_col=0)
        # Check that the index (variables sampled) matches exactly
        pd.testing.assert_index_equal(df_summary.index, df_golden_summary.index)
        # Check values with a tolerance because of MCMC sampling variance
        pd.testing.assert_frame_equal(df_summary, df_golden_summary, check_exact=False, rtol=1e-1, atol=1e-1, check_dtype=False)
