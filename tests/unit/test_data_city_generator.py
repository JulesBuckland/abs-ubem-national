import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch
from src.data.city_generator import (
    generate_spatial_grid,
    generate_confounders_and_spatial_field,
    generate_census_marginals,
    generate_seed_microdata
)

@patch('src.data.city_generator.gpd.GeoDataFrame.to_file')
def test_generate_spatial_grid(mock_to_file):
    msoa_codes, centroids = generate_spatial_grid(2, 2)
    assert len(msoa_codes) == 4
    assert centroids.shape == (4, 2)
    mock_to_file.assert_called_once()

@patch('src.data.city_generator.pd.DataFrame.to_csv')
def test_generate_confounders(mock_to_csv):
    msoa_codes = ["fake_0", "fake_1"]
    centroids = np.array([[0.5, 0.5], [1.5, 0.5]])
    df = generate_confounders_and_spatial_field(msoa_codes, centroids, 2)
    assert len(df) == 2
    assert "income_dep_score" in df.columns
    assert "true_omega" in df.columns
    assert mock_to_csv.call_count >= 1

@patch('src.data.city_generator.pd.DataFrame.to_csv')
def test_generate_census_marginals(mock_to_csv):
    msoa_codes = ["fake_0", "fake_1"]
    generate_census_marginals(msoa_codes, 2)
    assert mock_to_csv.call_count == 2

@patch('src.data.city_generator.pd.read_csv')
@patch('src.data.city_generator.pd.DataFrame.to_csv')
def test_generate_seed_microdata(mock_to_csv, mock_read_csv):
    mock_read_csv.return_value = pd.DataFrame({
        "property_type": ["House", "Flat"],
        "property_age": ["1900-1929", "1930-1949"],
        "theoretical_gas_kwh": [15000, 8000]
    })
    confounders = pd.DataFrame({
        "msoa_cd": ["fake_0", "fake_1"],
        "income_dep_score": [0.1, -0.1],
        "true_omega": [0.05, -0.05]
    })
    generate_seed_microdata(confounders, 5)
    mock_to_csv.assert_called_once()
