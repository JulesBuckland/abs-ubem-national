import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.inference.model_unified import log_memory, _use_csv_baseline, run_national_unified_model

def test_log_memory():
    # just test it doesn't crash
    log_memory("test_stage")

@patch('src.inference.model_unified.pd.read_csv')
def test_use_csv_baseline(mock_read_csv):
    df = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+']
    })
    
    mock_baseline = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+'],
        'theoretical_gas_kwh': [15000, 5000]
    })
    mock_read_csv.return_value = mock_baseline
    
    result = _use_csv_baseline(df)
    assert 'theoretical_gas_kwh' in result.columns
    assert list(result['theoretical_gas_kwh']) == [15000, 5000]

@patch('src.inference.model_unified.pd.read_csv')
def test_use_csv_baseline_missing(mock_read_csv):
    df = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+']
    })
    
    mock_baseline = pd.DataFrame({
        'property_type': ['House'],
        'property_age': ['Pre-1900'],
        'theoretical_gas_kwh': [15000]
    })
    mock_read_csv.return_value = mock_baseline
    
    with pytest.raises(ValueError, match="FATAL: Failed to map CSV baseline to some archetypes"):
        _use_csv_baseline(df)

@patch('src.inference.model_unified.pd.read_parquet')
@patch('src.inference.model_unified.pd.read_csv')
@patch('src.inference.model_unified.gpd.read_file')
@patch('src.inference.model_unified.libpysal.weights.Queen.from_dataframe')
@patch('src.inference.model_unified.pm.sample')
@patch('src.inference.model_unified.pm.compute_log_likelihood')
@patch('src.inference.model_unified.az.summary')
@patch('src.inference.model_unified.joblib.load')
@patch('src.inference.model_unified.GP_MODEL_PATH')
@patch('pathlib.Path.exists')
@patch('builtins.open')
def test_run_national_unified_model_fallback(
    mock_open, mock_path_exists, mock_gp_path, mock_joblib,
    mock_summary, mock_loglik, mock_sample, 
    mock_queen, mock_gpd_read, mock_read_csv, mock_read_parquet
):
    mock_path_exists.return_value = True
    mock_gp_path.exists.return_value = False # Force fallback to CSV
    
    # Parquet df
    df = pd.DataFrame({
        'msoa21cd': ['M1', 'M2'],
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+'],
        'empirical_thermal_kwh': [10000, 4000]
    })
    mock_read_parquet.return_value = df
    
    # baseline csv and confounders
    df_baseline = pd.DataFrame({
        'property_type': ['House', 'Flat'],
        'property_age': ['Pre-1900', '2007+'],
        'theoretical_gas_kwh': [15000, 5000]
    })
    df_confounders = pd.DataFrame({
        'msoa_cd': ['M1', 'M2'],
        'income_dep_score': [0.1, 0.2]
    })
    mock_read_csv.side_effect = [df_baseline, df_confounders]
    
    # GDF
    mock_gpd_read.return_value = pd.DataFrame({'MSOA21CD': ['M1', 'M2']})
    
    # Queen weights
    mock_w = MagicMock()
    mock_w.neighbors = {0: [1], 1: [0]}
    mock_w.id2i = {0: 0, 1: 1}
    mock_queen.return_value = mock_w
    
    mock_trace = MagicMock()
    mock_sample.return_value = mock_trace
    
    mock_trace.posterior = {'beta_inc': MagicMock(mean=MagicMock(return_value=MagicMock(item=MagicMock(return_value=1.0))))}
    
    with patch('src.inference.model_unified.os.environ.get', return_value="1"):
        trace = run_national_unified_model()
        
    assert trace == mock_trace
    mock_sample.assert_called_once()
