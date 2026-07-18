import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.data.population import run_national_synthesis, clean_seed_age_band, clean_seed_type

def test_clean_seed_age_band():
    assert clean_seed_age_band(1) == "Pre-1900"
    assert clean_seed_age_band(99) == "1950-1966"

def test_clean_seed_type():
    assert clean_seed_type("Detached") == "House"
    assert clean_seed_type("Unknown") == "House"

@patch('pathlib.Path.exists')
@patch('src.data.population.pd.read_csv')
def test_run_national_synthesis_no_seed(mock_read_csv, mock_exists):
    mock_exists.return_value = False
    run_national_synthesis()
    mock_read_csv.assert_not_called()

@patch('src.data.population.pd.DataFrame.to_parquet')
@patch('src.data.population.pd.read_csv')
@patch('pathlib.Path.exists')
@patch('src.utils.data_contracts.population_schema')
@patch('src.utils.epw_parser.get_regional_hdd_map')
@patch('src.utils.tracker.log_distribution')
def test_run_national_synthesis_success(
    mock_log_dist, mock_get_hdd, mock_schema, mock_exists, mock_read_csv, mock_to_parquet
):
    mock_exists.return_value = True

    mock_schema.validate = MagicMock(side_effect=lambda df: df)
    mock_get_hdd.return_value = {"Manchester": 2500}

    def mock_read_csv_side_effect(path, *args, **kwargs):
        path_str = str(path).lower()
        if "need" in path_str:
            return pd.DataFrame({
                'property_type_raw': ['Detached', 'Flat'] * 20,
                'property_age_band': [1, 2] * 20,
                'empirical_gas_kwh': [15000, 5000] * 20,
                'empirical_elec_kwh': [3000, 2000] * 20,
                'IMD_BAND_ENG': [5, 6] * 20,
                'FLOOR_AREA_BAND': [3, 2] * 20
            })
        elif "ts044" in path_str or "housing" in path_str:
            return pd.DataFrame({
                'geography code': ['E02000001'],
                'Accommodation type: Detached': [100],
                'Accommodation type: Semi-detached': [50],
                'Accommodation type: Terraced': [50],
                'Accommodation type: In a purpose-built block of flats or tenement': [20],
                'Accommodation type: Part of a converted or shared house, including bedsits': [10],
                'Accommodation type: A caravan or other mobile or temporary structure': [5]
            })
        elif "ts054" in path_str or "tenure" in path_str:
            return pd.DataFrame({
                'Middle layer Super Output Areas Code': ['E02000001', 'E02000001', 'E02000001'],
                'Tenure of household (9 categories) Code': [1, 3, 5],
                'Observation': [100, 50, 50]
            })
        elif "region" in path_str:
            return pd.DataFrame({
                'msoa21cd': ['E02000001'],
                'region': ['North West']
            })
        elif "confounders" in path_str:
            return pd.DataFrame({
                'msoa_cd': ['E02000001'],
                'income_dep_score': [0.1]
            })
        return pd.DataFrame()

    mock_read_csv.side_effect = mock_read_csv_side_effect

    run_national_synthesis()
    mock_to_parquet.assert_called_once()
