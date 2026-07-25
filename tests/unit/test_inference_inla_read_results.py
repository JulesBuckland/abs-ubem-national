import json

import numpy as np
import pandas as pd
import pytest

from src.inference.inla.read_results import (
    read_inla_fixed_effects,
    read_inla_random_effects,
    read_inla_hyperpar_transformed,
    read_inla_metadata,
    build_spatial_effect_summary_from_inla,
    load_inla_results,
    InlaGateFailedError,
)

# CSV text below is verbatim-format-matched against a real fit_inla.R CLI
# run on tiny synthetic data (6 nodes), inspected directly, to make sure
# this reader's column-name/shape assumptions match real R output exactly
# rather than a guessed format.
FIXED_EFFECTS_CSV = '''"","mean","sd","0.025quant","0.5quant","0.975quant","mode","kld"
"(Intercept)",-0.245192312733501,0.00791824117090208,-0.261768575459667,-0.245119221924957,-0.229089008084786,-0.245139206296229,5.01742864463797e-06
"income_z",0.199149718267041,0.00412566685632178,0.190323228828704,0.199154851868759,0.20794085596658,0.199152522955873,0.000349951287437807
'''

def _random_effects_csv(n):
    lines = ['"ID","mean","sd","0.025quant","0.5quant","0.975quant","mode","kld"']
    for i in range(1, 2 * n + 1):
        val = 0.01 * i  # arbitrary but deterministic, hand-traceable value
        lines.append(f'{i},{val},0.005,{val - 0.01},{val},{val + 0.01},{val},1e-06')
    return "\n".join(lines) + "\n"


def test_read_inla_fixed_effects_parses_intercept_and_income_z_by_name(tmp_path):
    path = tmp_path / "inla_fixed_effects.csv"
    path.write_text(FIXED_EFFECTS_CSV)

    result = read_inla_fixed_effects(path)

    assert result.loc["(Intercept)", "mean"] == pytest.approx(-0.245192312733501)
    assert result.loc["income_z", "mean"] == pytest.approx(0.199149718267041)


def test_read_inla_random_effects_splits_2n_rows_into_b_and_u(tmp_path):
    n = 6
    path = tmp_path / "inla_random_effects.csv"
    path.write_text(_random_effects_csv(n))

    result = read_inla_random_effects(path, n=n)

    assert set(result.keys()) == {"b", "u"}
    assert len(result["b"]) == n
    assert len(result["u"]) == n
    # Hand-computed: row i (1-indexed) has mean=0.01*i. b = rows 1..n, u = rows n+1..2n.
    np.testing.assert_allclose(result["b"]["mean"].values, [0.01 * i for i in range(1, n + 1)])
    np.testing.assert_allclose(result["u"]["mean"].values, [0.01 * i for i in range(n + 1, 2 * n + 1)])


def test_read_inla_random_effects_rejects_wrong_row_count(tmp_path):
    path = tmp_path / "inla_random_effects.csv"
    path.write_text(_random_effects_csv(6))  # 12 rows, but we'll claim n=5 (expects 10)
    with pytest.raises(AssertionError):
        read_inla_random_effects(path, n=5)


def test_read_inla_hyperpar_transformed(tmp_path):
    path = tmp_path / "inla_hyperpar_transformed.csv"
    pd.DataFrame({"rho": [0.6], "sigma_spatial": [2.0], "sigma_err": [0.5]}).to_csv(path, index=False)

    result = read_inla_hyperpar_transformed(path)

    assert result == {"rho": 0.6, "sigma_spatial": 2.0, "sigma_err": 0.5}


def test_read_inla_metadata(tmp_path):
    path = tmp_path / "inla_metadata.json"
    payload = {"mode": "final", "gate_passed": True, "gate_problems": []}
    path.write_text(json.dumps(payload))

    result = read_inla_metadata(path)

    assert result == payload


def test_build_spatial_effect_summary_from_inla_matches_schema_and_values():
    b_df = pd.DataFrame({
        "mean": [0.1, 0.2, 0.3],
        "sd": [0.01, 0.02, 0.03],
        "0.025quant": [0.08, 0.16, 0.24],
        "0.975quant": [0.12, 0.24, 0.36],
    })
    msoa_codes = np.array(["E02000001", "E02000002", "E02000003"])

    result = build_spatial_effect_summary_from_inla(b_df, msoa_codes)

    assert list(result.columns) == ["msoa21cd", "effect_mean", "effect_sd", "effect_ci_2.5", "effect_ci_97.5"]
    np.testing.assert_array_equal(result["msoa21cd"].values, msoa_codes)
    np.testing.assert_allclose(result["effect_mean"].values, [0.1, 0.2, 0.3])
    np.testing.assert_allclose(result["effect_ci_2.5"].values, [0.08, 0.16, 0.24])
    np.testing.assert_allclose(result["effect_ci_97.5"].values, [0.12, 0.24, 0.36])


def test_build_spatial_effect_summary_from_inla_rejects_length_mismatch():
    b_df = pd.DataFrame({"mean": [0.1, 0.2], "sd": [0.01, 0.02],
                         "0.025quant": [0.08, 0.16], "0.975quant": [0.12, 0.24]})
    msoa_codes = np.array(["E02000001", "E02000002", "E02000003"])  # 3, but b_df has 2
    with pytest.raises(AssertionError):
        build_spatial_effect_summary_from_inla(b_df, msoa_codes)


def _write_full_output_dir(tmp_path, n=3):
    (tmp_path / "inla_metadata.json").write_text(json.dumps({
        "mode": "final", "gate_passed": True, "gate_problems": [],
    }))
    (tmp_path / "inla_fixed_effects.csv").write_text(FIXED_EFFECTS_CSV)
    (tmp_path / "inla_random_effects.csv").write_text(_random_effects_csv(n))
    pd.DataFrame({"rho": [0.6], "sigma_spatial": [2.0], "sigma_err": [0.5]}).to_csv(
        tmp_path / "inla_hyperpar_transformed.csv", index=False)
    pd.DataFrame({"id": range(1, n + 1), "cpo": [0.1] * n, "pit": [0.5] * n, "failure": [0] * n}).to_csv(
        tmp_path / "inla_cpo.csv", index=False)
    pd.DataFrame({"waic": [123.4], "dic": [125.6]}).to_csv(tmp_path / "inla_ic.csv", index=False)


def test_load_inla_results_reads_everything_when_gate_passed(tmp_path):
    _write_full_output_dir(tmp_path, n=3)

    result = load_inla_results(tmp_path, n=3)

    assert result["metadata"]["gate_passed"] is True
    assert result["fixed_effects"].loc["income_z", "mean"] == pytest.approx(0.199149718267041)
    assert len(result["random_effects"]["b"]) == 3
    assert result["hyperpar"]["rho"] == 0.6
    assert result["ic"]["waic"] == pytest.approx(123.4)


def test_load_inla_results_raises_when_gate_failed(tmp_path):
    (tmp_path / "inla_metadata_DIAGNOSTIC_FAILED_GATE.json").write_text(json.dumps({
        "mode": "final", "gate_passed": False, "gate_problems": ["mode.status=1"],
    }))

    with pytest.raises(InlaGateFailedError):
        load_inla_results(tmp_path, n=3)


def test_load_inla_results_raises_file_not_found_when_nothing_present(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_inla_results(tmp_path, n=3)
