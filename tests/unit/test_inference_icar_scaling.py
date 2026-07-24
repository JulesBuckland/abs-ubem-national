import numpy as np
import pytest

from src.inference.icar_scaling import compute_icar_scaling_factor


def _dense_reference_scaling_factor(node1, node2, n_nodes):
    """Independent reference implementation using a dense np.linalg.inv,
    to cross-check the sparse splu-based implementation under test."""
    Q = np.zeros((n_nodes, n_nodes))
    for i, j in zip(node1, node2):
        Q[i, i] += 1
        Q[j, j] += 1
        Q[i, j] -= 1
        Q[j, i] -= 1
    jitter = Q.diagonal().max() * np.sqrt(np.finfo(float).eps)
    Q_pert = Q + np.eye(n_nodes) * jitter
    diag_inv = np.diag(np.linalg.inv(Q_pert))
    return float(np.exp(np.mean(np.log(diag_inv))))


def test_matches_independent_dense_reference_on_4_cycle():
    # 4-node cycle: 0-1-2-3-0
    node1 = np.array([0, 1, 2, 3])
    node2 = np.array([1, 2, 3, 0])
    result = compute_icar_scaling_factor(node1, node2, n_nodes=4)
    expected = _dense_reference_scaling_factor(node1, node2, n_nodes=4)
    assert result == pytest.approx(expected, rel=1e-6)


def test_matches_independent_dense_reference_on_5x5_grid():
    n = 5
    node1, node2 = [], []
    for r in range(n):
        for c in range(n):
            idx = r * n + c
            if c + 1 < n:
                node1.append(idx); node2.append(idx + 1)
            if r + 1 < n:
                node1.append(idx); node2.append(idx + n)
    node1, node2 = np.array(node1), np.array(node2)
    result = compute_icar_scaling_factor(node1, node2, n_nodes=n * n)
    expected = _dense_reference_scaling_factor(node1, node2, n_nodes=n * n)
    assert result == pytest.approx(expected, rel=1e-6)


def test_scaling_factor_is_positive_and_finite():
    node1 = np.array([0, 1, 2, 3])
    node2 = np.array([1, 2, 3, 0])
    result = compute_icar_scaling_factor(node1, node2, n_nodes=4)
    assert result > 0
    assert np.isfinite(result)


def test_no_edges_returns_noop_scaling_factor():
    """A single-node (or otherwise disconnected) graph has no spatial
    structure to scale against; this must not crash on float-dtype empty
    arrays (numpy defaults np.array([]) to float64) and must return a
    well-defined no-op value."""
    node1 = np.array([])
    node2 = np.array([])
    result = compute_icar_scaling_factor(node1, node2, n_nodes=1)
    assert result == 1.0


def test_denser_graph_has_smaller_scaling_factor():
    """More connectivity -> stronger smoothing -> smaller marginal variance
    per node, i.e. a smaller scaling factor. A fully-connected 5-node graph
    should have a smaller scaling factor than a 5-node cycle."""
    cycle_n1 = np.array([0, 1, 2, 3, 4])
    cycle_n2 = np.array([1, 2, 3, 4, 0])
    cycle_sf = compute_icar_scaling_factor(cycle_n1, cycle_n2, n_nodes=5)

    complete_n1, complete_n2 = [], []
    for i in range(5):
        for j in range(i + 1, 5):
            complete_n1.append(i); complete_n2.append(j)
    complete_sf = compute_icar_scaling_factor(np.array(complete_n1), np.array(complete_n2), n_nodes=5)

    assert complete_sf < cycle_sf
