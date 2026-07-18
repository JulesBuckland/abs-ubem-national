import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.physics.energyplus_client import (
    filter_standard_types, calculate_geometry, fill_template,
    calculate_hlc, enrich_dataframe, FORMS, AGES,
    process_row, process_all_rows, run_pipeline, read_file_content, write_file_content, run_energyplus
)

def test_filter_standard_types():
    df = pd.DataFrame({'property_type': ['Bungalow', 'Unknown', 'Flat']})
    res = filter_standard_types(df, FORMS)
    assert len(res) == 2
    assert 'Unknown' not in res['property_type'].values
    assert df is not res

def test_calculate_geometry():
    f_spec = FORMS["Bungalow"]
    geo = calculate_geometry(100.0, f_spec)
    assert np.isclose(geo['zone_volume'], 300.0)
    assert np.isclose(geo['side'], 10.0)
    assert np.isclose(geo['total_height'], 3.0)

def test_fill_template():
    template = "Name: @@ARCHETYPE_NAME@@, Vol: @@ZONE_VOLUME@@, BC_EAST: @@BC_EAST@@, SUN_EAST: @@SUN_EAST@@, WIND_EAST: @@WIND_EAST@@, BC_NORTH: @@BC_NORTH@@, BC_WEST: @@BC_WEST@@"
    geo = {"zone_volume": 300.0, "side": 10.0, "total_height": 3.0, "w_x_min": 1.0, "w_x_max": 2.0, "w_z_min": 1.0, "w_z_max": 2.0}
    res = fill_template(template, "TestArc", FORMS["Bungalow"], AGES["Pre-1900"], geo)
    assert "Name: TestArc" in res
    assert "Vol: 300.00" in res
    assert "BC_EAST: Outdoors" in res
    assert "BC_NORTH: Outdoors" in res
    assert "BC_WEST: Outdoors" in res

def test_calculate_hlc():
    df = pd.DataFrame({
        "Zone Air System Sensible Heating Rate [W](Hourly)": [1000.0, 0.0, 2000.0],
        "Site Outdoor Air Drybulb Temperature [C](Hourly)": [5.5, 10.0, 5.5]
    })
    hlc = calculate_hlc(df, 1.0, 300.0)
    assert np.isclose(hlc, 250.0)

def test_calculate_hlc_empty_active():
    df = pd.DataFrame({
        "Zone Air System Sensible Heating Rate [W](Hourly)": [0.0, 0.0],
        "Site Outdoor Air Drybulb Temperature [C](Hourly)": [5.5, 5.5]
    })
    hlc = calculate_hlc(df, 1.0, 300.0)
    assert np.isclose(hlc, 100.0)

def test_calculate_hlc_no_cols():
    df = pd.DataFrame()
    hlc = calculate_hlc(df, 1.0, 300.0)
    assert hlc == 0.0

def test_enrich_dataframe():
    df = pd.DataFrame({'A': [1]})
    res = enrich_dataframe(df, [100.0], 2000.0)
    assert 'hlc' in res.columns
    assert 'theoretical_gas_kwh' in res.columns
    assert res['hlc'].iloc[0] == 100.0
    assert res is not df

def test_read_write_file_content(tmp_path):
    f = tmp_path / "test.txt"
    write_file_content(f, "hello")
    assert read_file_content(f) == "hello"

def test_run_energyplus(monkeypatch):
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)
    run_energyplus(Path("ep"), Path("wf"), Path("od"), Path("idf"))
    mock_run.assert_called_once()

def test_process_row(monkeypatch):
    row = pd.Series({
        'Archetype': 'A B',
        'property_type': 'Bungalow',
        'property_age': 'Pre-1900',
        'Mean_Area': 100.0
    })
    monkeypatch.setattr("src.physics.energyplus_client.calculate_hlc", lambda df, ach, vol: 100.0)
    monkeypatch.setattr("src.physics.energyplus_client.write_file_content", lambda p, c: None)
    monkeypatch.setattr("src.physics.energyplus_client.run_energyplus", lambda e, w, o, i: None)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(Path, "mkdir", lambda self, **kwargs: None)
    monkeypatch.setattr(pd, "read_csv", lambda p: pd.DataFrame())
    res = process_row(row, "Template")
    assert res == 100.0

def test_process_row_no_csv(monkeypatch):
    row = pd.Series({
        'Archetype': 'A B',
        'property_type': 'Bungalow',
        'property_age': 'Pre-1900',
        'Mean_Area': 100.0
    })
    monkeypatch.setattr("src.physics.energyplus_client.write_file_content", lambda p, c: None)
    monkeypatch.setattr("src.physics.energyplus_client.run_energyplus", lambda e, w, o, i: None)
    monkeypatch.setattr(Path, "exists", lambda self: False)
    monkeypatch.setattr(Path, "mkdir", lambda self, **kwargs: None)
    res = process_row(row, "Template")
    assert res == 0.0

def test_process_all_rows(monkeypatch):
    monkeypatch.setattr("src.physics.energyplus_client.process_row", lambda r, t: 10.0)
    df = pd.DataFrame({'A': [1, 2]})
    res = process_all_rows(df, "T")
    assert res == [10.0, 10.0]

def test_run_pipeline(monkeypatch):
    monkeypatch.setattr("src.physics.energyplus_client.SIM_DIR", MagicMock())
    monkeypatch.setattr(pd, "read_csv", lambda p: pd.DataFrame({
        'Archetype': ['A B'],
        'property_type': ['Bungalow'],
        'property_age': ['Pre-1900'],
        'Mean_Area': [100.0]
    }))
    monkeypatch.setattr("src.physics.energyplus_client.read_file_content", lambda p: "template")
    monkeypatch.setattr("src.physics.energyplus_client.process_all_rows", lambda df, t: [100.0])
    monkeypatch.setattr("src.physics.energyplus_client.calculate_hdd_from_epw", lambda p: 2500.0)
    mock_to_csv = MagicMock()
    monkeypatch.setattr(pd.DataFrame, "to_csv", mock_to_csv)
    run_pipeline()
    mock_to_csv.assert_called_once()
