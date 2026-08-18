import pytest
import os
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@pytest.fixture(autouse=True)
def test_mode_env(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")

@pytest.mark.requires_fixtures
def test_population_synthesis_isolated():
    """Component test for data synthesis.

    Reads the NEED seed microdata fixture, so it needs tests/fixtures/raw/.
    """
    from src.data.population import run_national_synthesis
    run_national_synthesis()
    
    out_path = BASE_DIR / "tests" / "fixtures" / "processed" / "national_synthetic_population_eti.parquet"
    assert out_path.exists()
    df = pd.read_parquet(out_path)
    assert not df.empty
    assert "floor_area" in df.columns
    assert "empirical_thermal_kwh" in df.columns

@pytest.mark.requires_fixtures
def test_gp_emulator_isolated():
    """Component test for GP emulator.

    Trains on the EnergyPlus LHS results fixture, so it needs
    tests/fixtures/raw/.
    """
    from src.inference.gp_emulator import load_data, train_gp
    df = load_data()
    assert not df.empty
    gp, scaler, X_test, y_test, y_pred, y_std, stats = train_gp(df)
    assert gp is not None
    assert scaler is not None
    assert "r2" in stats
