import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.data.generate_synthetic_data import generate_data

@patch('src.data.generate_synthetic_data.gpd.read_file')
@patch('src.data.generate_synthetic_data.pd.DataFrame.to_csv')
@patch('src.data.generate_synthetic_data.pd.DataFrame.to_parquet')
@patch('src.data.generate_synthetic_data.Path.exists')
def test_generate_data_with_boundaries(mock_exists, mock_to_parquet, mock_to_csv, mock_read_file):
    mock_exists.return_value = True
    mock_read_file.return_value = pd.DataFrame({'MSOA21CD': ['E02000001', 'E02000002']})
    generate_data()
    mock_to_csv.assert_called_once()
    mock_to_parquet.assert_called_once()

@patch('src.data.generate_synthetic_data.pd.DataFrame.to_csv')
@patch('src.data.generate_synthetic_data.pd.DataFrame.to_parquet')
@patch('src.data.generate_synthetic_data.Path.exists')
def test_generate_data_no_boundaries(mock_exists, mock_to_parquet, mock_to_csv):
    mock_exists.return_value = False
    generate_data()
    mock_to_csv.assert_called_once()
    mock_to_parquet.assert_called_once()
