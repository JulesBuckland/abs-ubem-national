"""Component test for src/inference/inla/run_inla.py's run_national_inla_model()
end-to-end: real export -> real Rscript subprocess -> real fit_inla.R fit ->
real result reading -> real T* computation. Only prepare_national_msoa_dataset_for_inla
(the upstream data-loading step, a true external dependency on production
parquet/GIS files) is mocked, per this project's testing standard: mock only
true external dependencies, never the computation actually under test.

Expected values computed independently before running, same construction as
tests/integration/test_fit_inla_component.R's Case 1: no spatial confound,
beta_th/beta_inc set to (approximately) their prior means so recovery should
be close to the true simulated values.
"""
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.inference.inla.run_inla import run_national_inla_model


def _tiny_dataset(n=9):
    # 3x3 grid graph, rook adjacency, matching the pattern used in
    # tests/unit/test_inference_inla_rsr.R and the fit_inla.R component test.
    coords = [(x, y) for y in range(3) for x in range(3)]
    node1, node2 = [], []
    for i in range(n):
        for j in range(i + 1, n):
            xi, yi = coords[i]
            xj, yj = coords[j]
            if (abs(xi - xj) == 1 and yi == yj) or (xi == xj and abs(yi - yj) == 1):
                node1.append(i)
                node2.append(j)

    income_z_raw = np.array([c[0] for c in coords], dtype=float)
    income_z = (income_z_raw - income_z_raw.mean()) / income_z_raw.std()

    beta_th_true, beta_inc_true = -0.3, 0.1
    theory_log = np.full(n, 5.0)
    T_var = np.full(n, 0.1)
    rng = np.random.default_rng(7)
    mu = (theory_log - T_var / 2) + beta_th_true + beta_inc_true * income_z
    y_obs = mu + rng.normal(0, 0.01, n)

    msoa_stats = pd.DataFrame({"msoa21cd": [f"E0200000{i}" for i in range(n)]})

    return {
        "msoa_stats": msoa_stats, "node1": np.array(node1), "node2": np.array(node2),
        "T_var": T_var, "income_z": income_z, "theory_log": theory_log, "y_obs": y_obs,
        "N": n, "n_edges": len(node1),
    }, beta_th_true, beta_inc_true


@patch("src.inference.inla.run_inla.PILOT_MODE", False)
@patch("src.inference.inla.run_inla.prepare_national_msoa_dataset_for_inla")
def test_run_national_inla_model_end_to_end_recovers_fixed_effects(mock_prepare, tmp_path, monkeypatch):
    data, beta_th_true, beta_inc_true = _tiny_dataset()
    mock_prepare.return_value = data

    monkeypatch.setattr("src.inference.inla.run_inla.PROCESSED_DIR", tmp_path)

    result = run_national_inla_model(check_laplace_agreement=False)

    fixed = result["inla_results"]["fixed_effects"]
    assert fixed.loc["(Intercept)", "mean"] == pytest.approx(beta_th_true, abs=0.1)
    assert fixed.loc["income_z", "mean"] == pytest.approx(beta_inc_true, abs=0.1)

    assert result["results_path"].exists()
    saved = pd.read_csv(result["results_path"])
    assert "T_star_kwh" in saved.columns
    assert len(saved) == data["N"]

    assert len(result["spatial_effect_summary"]) == data["N"]
    assert set(result["spatial_effect_summary"].columns) == {
        "msoa21cd", "effect_mean", "effect_sd", "effect_ci_2.5", "effect_ci_97.5"
    }
