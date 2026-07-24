import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.data.population import (
    run_national_synthesis, clean_seed_age_band, clean_seed_type,
    load_and_clean_seed_data, build_seed_lookup_arrays, filter_msoas_for_test_mode,
)

def test_clean_seed_age_band():
    assert clean_seed_age_band(1) == "Pre-1900"
    assert clean_seed_age_band(99) == "1950-1966"

def test_clean_seed_type():
    assert clean_seed_type("Detached") == "House"
    assert clean_seed_type("Unknown") == "House"

@patch('pathlib.Path.exists')
@patch('src.data.population.pd.read_csv')
def test_run_national_synthesis_no_seed(mock_read_csv, mock_exists):
    """A missing seed file must raise, not silently return: a silent skip
    here previously meant a stage could vanish with no output and no error,
    exactly the failure mode the pipeline audit flagged."""
    mock_exists.return_value = False
    with pytest.raises(FileNotFoundError, match="Seed data not found"):
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


@patch('pathlib.Path.exists')
@patch('src.data.population.pd.read_csv')
def test_load_and_clean_seed_data_thermal_classification(mock_read_csv, mock_exists):
    """Hand-computed check of the gas-vs-electric thermal classification and
    the physically-impossible-reading filter (ELECTRIC_BASELOAD_KWH=2000,
    GAS_PRESENCE_THRESHOLD_KWH=500; both from src.config.settings).

    Row A (gas-primary):     Gcons=2000 (>=500) -> thermal = gas = 2000
                             t_star = 2000/106.3 = 18.8  -> kept
    Row B (electric-primary): Gcons=100 (<500), Econs=5000
                             elec_heating = max(0, 5000-2000) = 3000
                             thermal = gas + elec_heating = 100+3000 = 3100
                             t_star = 3100/106.3 = 29.2  -> kept
    Row C (outlier):         Gcons=50000 (>=500) -> thermal = 50000
                             t_star = 50000/106.3 = 470  -> > 400, DROPPED
    All three use PROP_TYPE='Detached' (-> House) and PROP_AGE_BAND=1
    (-> Pre-1900), giving ARCHETYPE_AREA_MEAN area = 106.3.
    """
    mock_exists.return_value = True
    mock_read_csv.return_value = pd.DataFrame({
        'PROP_TYPE': ['Detached', 'Detached', 'Detached'],
        'PROP_AGE_BAND': [1, 1, 1],
        'Gcons2022': [2000, 100, 50000],
        'Econs2022': [3000, 5000, 3000],
        'IMD_BAND_ENG': [1, 1, 1],
        'FLOOR_AREA_BAND': ['A', 'A', 'A'],
    })

    result = load_and_clean_seed_data()

    # Outlier dropped, tenure-expanded x3 (Owned/Social/Private) -> 2*3 = 6 rows
    assert len(result) == 6
    assert set(result['tenure'].unique()) == {'Owned', 'Social', 'Private'}
    thermal_values = sorted(result['empirical_thermal_kwh'].unique())
    np.testing.assert_allclose(thermal_values, [2000.0, 3100.0], atol=1e-9)
    assert (result['property_type'] == 'House').all()
    assert (result['property_age'] == 'Pre-1900').all()


def test_build_seed_lookup_arrays_is_pure_and_correct():
    seed_q = pd.DataFrame({
        'property_type': ['House', 'Flat', 'House'],
        'tenure': ['Owned', 'Social', 'Private'],
        'IMD_BAND_ENG': [1, 2, 3],
        'property_age': ['Pre-1900', '1900-1929', 'Pre-1900'],
        'empirical_thermal_kwh': [1000.0, 2000.0, 3000.0],
        'empirical_gas_kwh': [900.0, 1900.0, 2900.0],
        'FLOOR_AREA_BAND': ['A', 'B', 'C'],
    })
    original = seed_q.copy()

    result = build_seed_lookup_arrays(seed_q)

    # Purity: the input frame must be untouched.
    pd.testing.assert_frame_equal(seed_q, original)

    np.testing.assert_array_equal(result['seed_pt'], ['House', 'Flat', 'House'])
    np.testing.assert_array_equal(result['pt_masks']['House'], [True, False, True])
    np.testing.assert_array_equal(result['pt_masks']['Flat'], [False, True, False])
    np.testing.assert_array_equal(result['pt_masks']['Bungalow'], [False, False, False])
    np.testing.assert_array_equal(result['tenure_masks']['Owned'], [True, False, False])
    np.testing.assert_array_equal(result['seed_thermal'], [1000.0, 2000.0, 3000.0])


def test_filter_msoas_for_test_mode_passthrough_when_no_env_vars(monkeypatch):
    monkeypatch.delenv("E2E_TARGET_LAD", raising=False)
    monkeypatch.delenv("E2E_TARGET_REGION", raising=False)
    msoa_codes = np.array(['E02000001', 'E02000002', 'E02000003'])

    result = filter_msoas_for_test_mode(msoa_codes, region_lookup={})

    np.testing.assert_array_equal(result, msoa_codes)


def test_filter_msoas_for_test_mode_region_filter(monkeypatch):
    monkeypatch.delenv("E2E_TARGET_LAD", raising=False)
    monkeypatch.setenv("E2E_TARGET_REGION", "North West")
    msoa_codes = np.array(['E02000001', 'E02000002', 'E02000003'])
    region_lookup = {
        'E02000001': 'North West',
        'E02000002': 'London',
        'E02000003': 'North West',
    }

    result = filter_msoas_for_test_mode(msoa_codes, region_lookup)

    np.testing.assert_array_equal(sorted(result), ['E02000001', 'E02000003'])


def test_filter_msoas_for_test_mode_region_filter_raises_if_empty(monkeypatch):
    monkeypatch.delenv("E2E_TARGET_LAD", raising=False)
    monkeypatch.setenv("E2E_TARGET_REGION", "Scotland")
    msoa_codes = np.array(['E02000001'])
    region_lookup = {'E02000001': 'North West'}

    with pytest.raises(AssertionError, match="No MSOAs found for region"):
        filter_msoas_for_test_mode(msoa_codes, region_lookup)
