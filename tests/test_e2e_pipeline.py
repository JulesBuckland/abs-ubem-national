import pytest
import os
import sys
import subprocess
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.mark.requires_fixtures
def test_pipeline_e2e():
    """
    Runs the pipeline end-to-end on the tiny fixture dataset.
    This guarantees that the logic, data paths, and physical checks work without crashing,
    and output files are generated correctly.
    """
    
    # 1. Synthesis
    result_synthesis = subprocess.run(
        [sys.executable, "-m", "src.data.population"],
        cwd=str(BASE_DIR),
        env=os.environ.copy(),
        capture_output=True,
        text=True
    )
    assert result_synthesis.returncode == 0, f"Population synthesis crashed:\n{result_synthesis.stderr}"
    
    # Verify synthesis output
    synth_path = BASE_DIR / "tests" / "fixtures" / "processed" / "national_synthetic_population_eti.parquet"
    assert synth_path.exists(), "Synthesis output parquet not found."
    df_synth = pd.read_parquet(synth_path)
    assert not df_synth.empty, "Synthetic population is empty."
    assert df_synth['floor_area'].min() >= 20.0, "Physical bounds failure: floor area < 20."

    # 2. GP Emulator
    result_gp = subprocess.run(
        [sys.executable, "-m", "src.inference.gp_emulator"],
        cwd=str(BASE_DIR),
        env=os.environ.copy(),
        capture_output=True,
        text=True
    )
    assert result_gp.returncode == 0, f"GP Emulator crashed:\n{result_gp.stderr}"
    
    # Verify GP output
    gp_path = BASE_DIR / "tests" / "fixtures" / "processed" / "gp_emulator.pkl"
    assert gp_path.exists(), "GP emulator pickle not found."

    # 3. National Unified Model
    result_unified = subprocess.run(
        [sys.executable, "-m", "src.inference.model_unified"],
        cwd=str(BASE_DIR),
        env=os.environ.copy(),
        capture_output=True,
        text=True
    )
    assert result_unified.returncode == 0, f"National Unified Model crashed:\n{result_unified.stderr}"
    
    # Verify Bayesian output
    trace_path = BASE_DIR / "tests" / "fixtures" / "processed" / "national_unified_trace.nc"
    assert trace_path.exists(), "Bayesian trace not found."
