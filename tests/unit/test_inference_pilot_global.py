import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.inference.pilot_global import build_and_sample_pilot, run_pilot_model
from src.config.settings import PROCESSED_DIR, HEATING_DEFICIT_FILE

@pytest.fixture
def mock_df():
    return pd.DataFrame({
        'msoa21cd': ['M1', 'M2', 'M3'],
        'empirical_gas_kwh': [10000, 15000, 20000],
        'theoretical_gas_kwh': [12000, 14000, 22000],
        'income_dep_score': [0.1, 0.2, 0.3]
    })

@patch('src.inference.pilot_global.pm.fit')
def test_build_and_sample_pilot(mock_fit, mock_df):
    mock_approx = MagicMock()
    mock_trace = MagicMock()
    mock_fit.return_value = mock_approx
    mock_approx.sample.return_value = mock_trace
    
    # mock az.summary to return a simple dataframe
    with patch('src.inference.pilot_global.az.summary', return_value=pd.DataFrame({'mean': [1.0, 2.0]})) as mock_summary:
        summary = build_and_sample_pilot(mock_df, n_fit=2, draws=2)
        
        mock_fit.assert_called_once()
        mock_approx.sample.assert_called_once_with(2)
        mock_summary.assert_called_once()
        assert len(summary) == 2

@patch('src.inference.pilot_global.pd.read_csv')
@patch('src.inference.pilot_global.build_and_sample_pilot')
@patch('pathlib.Path.exists')
def test_run_pilot_model(mock_exists, mock_build, mock_read_csv):
    mock_exists.return_value = True
    
    # Need 2 dataframes to be returned
    df_deficit = pd.DataFrame({'msoa21cd': ['M1'], 'empirical_gas_kwh': [1000], 'theoretical_gas_kwh': [1200]})
    df_conf = pd.DataFrame({'msoa_cd': ['M1'], 'income_dep_score': [0.1]})
    
    mock_read_csv.side_effect = [df_deficit, df_conf]
    
    mock_summary = MagicMock()
    mock_build.return_value = mock_summary
    
    run_pilot_model()
    
    assert mock_read_csv.call_count == 2
    mock_build.assert_called_once()
    mock_summary.to_csv.assert_called_once()

@patch('pathlib.Path.exists')
def test_run_pilot_model_missing_files(mock_exists):
    mock_exists.return_value = False
    with patch('src.inference.pilot_global.logger.error') as mock_error:
        run_pilot_model()
        mock_error.assert_called_once_with("Required data files not found.")
