import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.inference.calibration import align_datasets, build_and_sample_model, run_calibration
from src.config.settings import PROCESSED_DIR

@pytest.fixture
def mock_datasets():
    gas = pd.DataFrame({'lsoa_cd': ['A', 'B', 'C'], 'annual_gas_kwh': [1000, 2000, 3000]})
    mix = pd.DataFrame({'LSOA21CD': ['B', 'C', 'A'], 'Arch1': [10, 20, 30], 'Arch2': [90, 80, 70]})
    imd = pd.DataFrame({'lsoa_cd': ['C', 'A', 'B'], 'income_score': [1, 2, 3]})
    census = pd.DataFrame({'lsoa_cd': ['A', 'B', 'C'], 'count': [100, 200, 300]})
    priors_raw = pd.DataFrame({'Archetype': ['Arch1', 'Arch2'], 'Mean_Area': [50.0, 60.0]}).set_index('Archetype')
    return gas, mix, imd, census, priors_raw

def test_align_datasets(mock_datasets):
    gas, mix, imd, census, _ = mock_datasets
    # Add an extra row to gas to ensure it gets filtered
    gas = pd.concat([gas, pd.DataFrame({'lsoa_cd': ['D'], 'annual_gas_kwh': [4000]})])
    g, m, i, c = align_datasets(gas, mix, imd, census)
    assert len(g) == 3
    assert len(m) == 3
    assert len(i) == 3
    assert len(c) == 3
    assert list(g['lsoa_cd']) == ['A', 'B', 'C']
    assert list(m['LSOA21CD']) == ['A', 'B', 'C']

@patch('src.inference.calibration.pm.sample')
def test_build_and_sample_model(mock_sample, mock_datasets):
    gas, mix, imd, census, priors_raw = mock_datasets
    mock_trace = MagicMock()
    mock_sample.return_value = mock_trace
    
    trace = build_and_sample_model(gas, mix, imd, priors_raw, census, draws=2, tune=2)
    assert trace == mock_trace
    mock_sample.assert_called_once()

@patch('src.inference.calibration.pd.read_csv')
@patch('src.inference.calibration.build_and_sample_model')
def test_run_calibration(mock_build, mock_read_csv):
    mock_trace = MagicMock()
    mock_build.return_value = mock_trace
    mock_read_csv.return_value = pd.DataFrame({'Archetype': ['Arch1']})
    
    run_calibration()
    
    assert mock_read_csv.call_count == 5
    mock_build.assert_called_once()
    mock_trace.to_netcdf.assert_called_once()
