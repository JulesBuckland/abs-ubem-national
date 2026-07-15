import pytest
import numpy as np

def test_graph_builder_sparse_edgelist():
    try:
        from src.data.graph_builder import build_graph
    except ImportError:
        pytest.fail("build_graph not implemented yet")
        
    # Build a 5-node graph
    num_nodes = 5
    edges = build_graph(num_nodes)
    
    # Basic validations for a 5-node graph edge-list
    assert isinstance(edges, np.ndarray), "Edge list should be a numpy array"
    assert edges.shape[1] == 2, "Edge list should have 2 columns (source, destination)"
    
    # Check that node indices are within valid range
    assert np.all(edges >= 0), "Node indices must be non-negative"
    assert np.all(edges < num_nodes), f"Node indices must be strictly less than {num_nodes}"
