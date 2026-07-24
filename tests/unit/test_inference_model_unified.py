import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.inference.model_unified import (
    log_memory, _use_csv_baseline, run_national_unified_model, build_unified_model,
)

def test_log_memory():
    # just test it doesn't crash
    log_memory("test_stage")

@patch('src.inference.model_unified.pd.read_csv')
def test_use_csv_baseline(mock_read_csv):
    df = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+']
    })
    
    mock_baseline = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+'],
        'theoretical_gas_kwh': [15000, 5000]
    })
    mock_read_csv.return_value = mock_baseline
    
    result = _use_csv_baseline(df)
    assert 'theoretical_gas_kwh' in result.columns
    assert list(result['theoretical_gas_kwh']) == [15000, 5000]

@patch('src.inference.model_unified.pd.read_csv')
def test_use_csv_baseline_missing(mock_read_csv):
    df = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+']
    })
    
    mock_baseline = pd.DataFrame({
        'property_type': ['House'],
        'property_age': ['Pre-1900'],
        'theoretical_gas_kwh': [15000]
    })
    mock_read_csv.return_value = mock_baseline
    
    with pytest.raises(ValueError, match="FATAL: Failed to map CSV baseline to some archetypes"):
        _use_csv_baseline(df)

@patch('src.inference.model_unified.pd.read_parquet')
@patch('src.inference.model_unified.pd.read_csv')
@patch('src.inference.model_unified.gpd.read_file')
@patch('src.inference.model_unified.libpysal.weights.Queen.from_dataframe')
@patch('src.inference.model_unified.pm.sample')
@patch('src.inference.model_unified.pm.compute_log_likelihood')
@patch('src.inference.model_unified.az.summary')
@patch('src.inference.model_unified.joblib.load')
@patch('src.inference.model_unified.GP_MODEL_PATH')
@patch('pathlib.Path.exists')
@patch('builtins.open')
def test_run_national_unified_model_fallback(
    mock_open, mock_path_exists, mock_gp_path, mock_joblib,
    mock_summary, mock_loglik, mock_sample, 
    mock_queen, mock_gpd_read, mock_read_csv, mock_read_parquet
):
    mock_path_exists.return_value = True
    mock_gp_path.exists.return_value = False # Force fallback to CSV
    
    # Parquet df
    df = pd.DataFrame({
        'msoa21cd': ['M1', 'M2'],
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+'],
        'empirical_thermal_kwh': [10000, 4000]
    })
    mock_read_parquet.return_value = df
    
    # baseline csv and confounders
    df_baseline = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+'],
        'theoretical_gas_kwh': [15000, 5000]
    })
    df_confounders = pd.DataFrame({
        'msoa_cd': ['M1', 'M2'],
        'income_dep_score': [0.1, 0.2]
    })
    mock_read_csv.side_effect = [df_baseline, df_confounders]
    
    # GDF
    mock_gpd_read.return_value = pd.DataFrame({'MSOA21CD': ['M1', 'M2']})
    
    # Queen weights
    mock_w = MagicMock()
    mock_w.neighbors = {0: [1], 1: [0]}
    mock_w.id2i = {0: 0, 1: 1}
    mock_queen.return_value = mock_w
    
    mock_trace = MagicMock()
    mock_sample.return_value = mock_trace
    
    mock_trace.posterior = {'beta_inc': MagicMock(mean=MagicMock(return_value=MagicMock(item=MagicMock(return_value=1.0))))}
    
    with patch('src.inference.model_unified.os.environ.get', return_value="1"):
        trace = run_national_unified_model()

    assert trace == mock_trace
    mock_sample.assert_called_once()


# ---------------------------------------------------------------------------
# Real (non-mocked) tests of the actual PyMC model graph built by
# build_unified_model. These exercise the real math the tests above mock out
# entirely (pm.sample is never patched here) — this is the standard the
# testing-paradigm memory calls for: a mocked test that checks pm.sample was
# called cannot catch a wrong prior spec; these can.
# ---------------------------------------------------------------------------

def _tiny_model(icar_scaling_factor=4.0, zt_z_inv_scalar=0.5):
    """A 3-node, 2-edge (0-1, 1-2) synthetic graph small enough to hand-verify."""
    return build_unified_model(
        N=3,
        node1=np.array([0, 1]),
        node2=np.array([1, 2]),
        T_var=np.zeros(3),
        income_z=np.array([-1.0, 0.0, 1.0]),
        theory_log=np.zeros(3),
        y_obs=np.zeros(3),
        icar_scaling_factor=icar_scaling_factor,
        zt_z_inv_scalar=zt_z_inv_scalar,
    )


def test_phi_raw_is_flat_not_normal():
    """Regression guard for the actual bug found this session: phi_raw must
    carry NO independent per-node prior (that competed with the pairwise
    smoothness penalty component-wise instead of only constraining the
    gauge-fixing sum, corrupting identifiability of rho). If this is ever
    changed back to pm.Normal, this test must fail."""
    model = _tiny_model()
    assert type(model["phi_raw"].owner.op).__name__ == "FlatRV"


def test_icar_penalty_matches_hand_computed_value():
    """phi_raw=[1, 3, -2] on edges (0,1),(1,2):
    -0.5 * [(1-3)^2 + (3-(-2))^2] = -0.5 * [4 + 25] = -14.5"""
    model = _tiny_model()
    icar_penalty = model.potentials[0]
    result = icar_penalty.eval({model["phi_raw"]: np.array([1.0, 3.0, -2.0])})
    assert result == pytest.approx(-14.5)


def test_icar_zerosum_matches_hand_computed_formula():
    """Independent re-derivation of pm.ICAR's own zero_sum logp term
    (see pm.ICAR.dist's logp source): matches PyMC's own soft
    gauge-fixing constraint exactly, applied here to the sparse edge-list phi_raw."""
    model = _tiny_model()
    icar_zerosum = model.potentials[1]
    phi_raw_val = np.array([1.0, 3.0, -2.0])
    n, zero_sum_stdev = 3, 0.001
    expected = (
        -0.5 * (phi_raw_val.sum() / (zero_sum_stdev * n)) ** 2
        - np.log(np.sqrt(2.0 * np.pi))
        - np.log(zero_sum_stdev * n)
    )
    result = icar_zerosum.eval({model["phi_raw"]: phi_raw_val})
    assert result == pytest.approx(expected)


def test_phi_deterministic_applies_scaling_factor():
    """phi_raw=[2,4,6] with scaling_factor=4 -> phi = phi_raw/sqrt(4) = [1,2,3]."""
    model = _tiny_model(icar_scaling_factor=4.0)
    phi = model["phi"]
    result = phi.eval({model["phi_raw"]: np.array([2.0, 4.0, 6.0])})
    np.testing.assert_allclose(result, [1.0, 2.0, 3.0])


def test_build_unified_model_samples_without_crashing():
    """Real (unmocked) tiny NUTS run — proves the Flat + Potential
    construction is a valid, sampleable joint density, not just that the
    Python code runs without a NameError."""
    import pymc as pm
    model = _tiny_model()
    with model:
        trace = pm.sample(draws=5, tune=5, chains=1, cores=1, progressbar=False)
    assert trace.posterior["phi"].shape == (1, 5, 3)
    assert np.all(np.isfinite(trace.posterior["phi"].values))
