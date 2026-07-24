import arviz as az
import numpy as np
import pandas as pd
import pytest

from src.utils.compute_spatial_effect_summary import compute_spatial_effect_summary


@pytest.fixture
def tiny_trace_and_results(tmp_path):
    """A 3-MSOA, single-draw case with a hand-computed expected omega_star.

    phi = [1.0, -0.5, -0.5], theta = [0.2, 0.2, -0.4] (both zero-mean, as the
    real model enforces), rho = 0.64, sigma_spatial = 2.0.

    omega = sigma_spatial * (sqrt(1-rho)*theta + sqrt(rho)*phi)
          = 2 * (0.6*theta + 0.8*phi) = [1.84, -0.56, -1.28]

    income_dep_score = [10, 20, 30] -> standardized Z = [-1, 0, 1] (sample std=10)
    Z'Z = 2, Z'omega = -1.84 + 0 - 1.28 = -3.12
    projection = (Z'omega / Z'Z) * Z = -1.56 * Z = [1.56, 0, -1.56]
    omega_star = omega - projection = [0.28, -0.56, 0.28]
    """
    idata = az.from_dict(
        {
            "posterior": {
                "phi": np.array([[[1.0, -0.5, -0.5]]]),
                "theta": np.array([[[0.2, 0.2, -0.4]]]),
                "rho": np.array([[0.64]]),
                "sigma_spatial": np.array([[2.0]]),
            }
        }
    )
    trace_path = tmp_path / "tiny_trace.nc"
    idata.to_netcdf(trace_path)

    results_path = tmp_path / "tiny_results.csv"
    pd.DataFrame(
        {
            "msoa21cd": ["E02000001", "E02000002", "E02000003"],
            "income_dep_score": [10.0, 20.0, 30.0],
        }
    ).to_csv(results_path, index=False)

    return trace_path, results_path


def test_compute_spatial_effect_summary_matches_hand_computed_values(tiny_trace_and_results):
    trace_path, results_path = tiny_trace_and_results
    out = compute_spatial_effect_summary(trace_path=trace_path, results_path=results_path)

    assert list(out["msoa21cd"]) == ["E02000001", "E02000002", "E02000003"]
    np.testing.assert_allclose(out["effect_mean"].values, [0.28, -0.56, 0.28], atol=1e-9)
    # Single draw: SD is 0 and both percentiles equal the point estimate.
    np.testing.assert_allclose(out["effect_sd"].values, [0.0, 0.0, 0.0], atol=1e-9)
    np.testing.assert_allclose(out["effect_ci_2.5"].values, [0.28, -0.56, 0.28], atol=1e-9)
    np.testing.assert_allclose(out["effect_ci_97.5"].values, [0.28, -0.56, 0.28], atol=1e-9)


def test_compute_spatial_effect_summary_is_orthogonal_to_income_z(tiny_trace_and_results):
    """The defining RSR property: the projected effect must be exactly
    orthogonal to the income confounder Z, for every draw. This is the
    mathematical guarantee that omega_star cannot be stealing variance
    from income_z (the Hodges-Reich confounding this projection exists
    to prevent)."""
    trace_path, results_path = tiny_trace_and_results
    out = compute_spatial_effect_summary(trace_path=trace_path, results_path=results_path)

    df = pd.read_csv(results_path)
    income_z = (df["income_dep_score"] - df["income_dep_score"].mean()) / df[
        "income_dep_score"
    ].std()
    assert abs(np.sum(income_z.values * out["effect_mean"].values)) < 1e-9


def test_row_count_mismatch_between_trace_and_results_raises(tiny_trace_and_results):
    trace_path, results_path = tiny_trace_and_results
    df = pd.read_csv(results_path)
    bad_results_path = results_path.parent / "mismatched_results.csv"
    df.iloc[:2].to_csv(bad_results_path, index=False)  # drop a row -> N mismatch

    with pytest.raises(AssertionError, match="Trace has"):
        compute_spatial_effect_summary(trace_path=trace_path, results_path=bad_results_path)


def test_unsorted_msoa21cd_raises(tiny_trace_and_results):
    trace_path, results_path = tiny_trace_and_results
    df = pd.read_csv(results_path)
    shuffled_path = results_path.parent / "shuffled_results.csv"
    df.iloc[[1, 0, 2]].to_csv(shuffled_path, index=False)  # break sort order

    with pytest.raises(AssertionError, match="no longer sorted"):
        compute_spatial_effect_summary(trace_path=trace_path, results_path=shuffled_path)
