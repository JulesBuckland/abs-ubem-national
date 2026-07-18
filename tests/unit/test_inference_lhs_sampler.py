import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.inference.lhs_sampler import generate_archetype_lhs, verify_discrepancy, main

@patch('src.utils.epw_parser.get_regional_hdd_map')
def test_generate_archetype_lhs(mock_hdd):
    mock_hdd.return_value = {'Manchester': 2500, 'London': 2000}
    with patch('src.inference.lhs_sampler.REGIONAL_CENTERS', {'Manchester': 1}):
        df = generate_archetype_lhs('Arch1', 'House', 'Pre-1900', 100.0)
        
        assert len(df) == 300
        assert 'floor_area' in df.columns
        assert 'hdd' in df.columns
        assert df['area_nominal'].iloc[0] == 100.0

@patch('src.inference.lhs_sampler.pd.read_csv')
@patch('pathlib.Path.glob')
def test_verify_discrepancy(mock_glob, mock_read_csv):
    mock_file = MagicMock()
    mock_file.stem = "lhs_arch1"
    mock_glob.return_value = [mock_file]
    
    # create dummy data
    X = np.random.rand(10, 4)
    df = pd.DataFrame(X, columns=["floor_area", "wall_u", "ach", "wwr"])
    mock_read_csv.return_value = df
    
    with patch('scipy.stats.qmc.discrepancy', return_value=0.01):
        verify_discrepancy(Path('dummy'))

@patch('pathlib.Path.glob')
def test_verify_discrepancy_empty(mock_glob):
    mock_glob.return_value = []
    verify_discrepancy(Path('dummy'))

@patch('src.inference.lhs_sampler.BASELINE_CSV')
@patch('src.inference.lhs_sampler.pd.read_csv')
@patch('src.inference.lhs_sampler.generate_archetype_lhs')
@patch('src.inference.lhs_sampler.OUTPUT_DIR')
@patch('src.inference.lhs_sampler.PHYSICS_DIR')
def test_main(mock_phys, mock_out, mock_gen, mock_read_csv, mock_baseline):
    mock_baseline.exists.return_value = True
    
    df_baseline = pd.DataFrame({
        'property_type': ['House', 'Unknown', 'House'],
        'property_age': ['Pre-1900', 'Pre-1900', 'Unknown'],
        'mean_area': [100.0, 100.0, 100.0],
        'archetype': ['Arch1', 'Arch2', 'Arch3']
    })
    mock_read_csv.return_value = df_baseline
    
    df_gen = pd.DataFrame({'a': [1, 2]})
    mock_gen.return_value = df_gen
    
    main()
    
    # Only the valid row (House, Pre-1900) should be generated
    mock_gen.assert_called_once_with('Arch1', 'House', 'Pre-1900', 100.0)

@patch('src.inference.lhs_sampler.verify_discrepancy')
def test_main_verify(mock_verify):
    main(verify=True)
    mock_verify.assert_called_once()
