import pytest
import numpy as np
from src.data.graph_builder import build_graph

def test_build_graph_default():
    edges = build_graph()
    expected = np.array([[0, 1], [1, 2], [2, 3], [3, 4]], dtype=np.int32)
    np.testing.assert_array_equal(edges, expected)

def test_build_graph_custom():
    edges = build_graph(3)
    expected = np.array([[0, 1], [1, 2]], dtype=np.int32)
    np.testing.assert_array_equal(edges, expected)
