import numpy as np
import pytest
from pathlib import Path
import pandas as pd
from src.utils.epw_parser import extract_daily_means, calculate_hdd, calculate_hdd_from_epw, get_regional_hdd_map

def test_extract_daily_means():
    temps = np.ones(48) * 10.0
    means = extract_daily_means(temps)
    assert len(means) == 2
    assert means[0] == 10.0

def test_calculate_hdd():
    means = np.array([10.0, 20.0])
    hdd = calculate_hdd(means, 15.5)
    assert hdd == 5.5

def test_calculate_hdd_from_epw(tmp_path):
    epw = tmp_path / "test.epw"
    # Write 8 lines of header
    with open(epw, 'w') as f:
        f.write("\n" * 8)
        # Write 24 lines of data, col 6 is dry bulb temp
        for _ in range(24):
            f.write("a,b,c,d,e,f,10.0\n")
    
    hdd = calculate_hdd_from_epw(epw)
    assert hdd == 5.5

def test_calculate_hdd_from_epw_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        calculate_hdd_from_epw(tmp_path / "missing.epw")

def test_get_regional_hdd_map(tmp_path):
    # Setup files
    cities = ["London"]
    epw = tmp_path / "London_2030_ColdSnap.epw"
    with open(epw, 'w') as f:
        f.write("\n" * 8)
        for _ in range(24):
            f.write("a,b,c,d,e,f,10.0\n")
    
    m = get_regional_hdd_map(tmp_path, cities)
    assert m["London"] == 5.5
    
def test_epw_parser_exception(tmp_path):
    epw = tmp_path / "bad.epw"
    with open(epw, 'w') as f:
        f.write("\n" * 8)
        f.write("a,b,c,d,e,f,NOT_A_FLOAT\n")
    with pytest.raises(RuntimeError):
        calculate_hdd_from_epw(epw)
