import numpy as np
import pandas as pd

from src.inference.inla.data_export import (
    build_inla_node_frame,
    build_inla_edge_frame,
    export_inla_inputs,
)


def test_build_inla_node_frame_exact_values():
    T_var = np.array([0.1, 0.2, 0.3])
    income_z = np.array([-1.0, 0.0, 1.0])
    theory_log = np.array([2.0, 2.5, 3.0])
    y_obs = np.array([1.5, 2.5, 3.5])

    result = build_inla_node_frame(T_var, income_z, theory_log, y_obs)

    assert list(result.columns) == ["id", "T_var", "income_z", "theory_log", "y_obs"]
    assert result["id"].tolist() == [1, 2, 3]  # 1-indexed, computed by hand
    np.testing.assert_array_equal(result["T_var"].values, T_var)
    np.testing.assert_array_equal(result["income_z"].values, income_z)
    np.testing.assert_array_equal(result["theory_log"].values, theory_log)
    np.testing.assert_array_equal(result["y_obs"].values, y_obs)


def test_build_inla_node_frame_rejects_mismatched_lengths():
    T_var = np.array([0.1, 0.2])
    income_z = np.array([-1.0, 0.0, 1.0])  # deliberately wrong length
    theory_log = np.array([2.0, 2.5, 3.0])
    y_obs = np.array([1.5, 2.5, 3.5])
    try:
        build_inla_node_frame(T_var, income_z, theory_log, y_obs)
        assert False, "expected an AssertionError for mismatched T_var length"
    except AssertionError as e:
        assert "T_var" in str(e)


def test_build_inla_edge_frame_reindexes_zero_to_one_based():
    # 3-node chain, 0-indexed: edges (0,1) and (1,2) -- matches this
    # project's existing tiny-graph convention (test_inference_model_unified.py).
    node1 = np.array([0, 1])
    node2 = np.array([1, 2])

    result = build_inla_edge_frame(node1, node2)

    # Hand-computed: 1-indexing shifts every id up by exactly 1.
    assert result["node1"].tolist() == [1, 2]
    assert result["node2"].tolist() == [2, 3]


def test_build_inla_edge_frame_rejects_mismatched_shapes():
    node1 = np.array([0, 1, 2])
    node2 = np.array([1, 2])  # deliberately wrong length
    try:
        build_inla_edge_frame(node1, node2)
        assert False, "expected an AssertionError for mismatched edge array shapes"
    except AssertionError:
        pass


def test_export_inla_inputs_writes_expected_csv_content(tmp_path):
    node1 = np.array([0, 1])
    node2 = np.array([1, 2])
    T_var = np.array([0.1, 0.2, 0.3])
    income_z = np.array([-1.0, 0.0, 1.0])
    theory_log = np.array([2.0, 2.5, 3.0])
    y_obs = np.array([1.5, 2.5, 3.5])

    paths = export_inla_inputs(node1, node2, T_var, income_z, theory_log, y_obs, tmp_path)

    assert paths["nodes_path"].exists()
    assert paths["edges_path"].exists()

    nodes_roundtrip = pd.read_csv(paths["nodes_path"])
    edges_roundtrip = pd.read_csv(paths["edges_path"])

    assert nodes_roundtrip["id"].tolist() == [1, 2, 3]
    np.testing.assert_allclose(nodes_roundtrip["y_obs"].values, y_obs)
    assert edges_roundtrip["node1"].tolist() == [1, 2]
    assert edges_roundtrip["node2"].tolist() == [2, 3]
