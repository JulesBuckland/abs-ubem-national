"""
epw_parser.py
==============
Dynamically parses CIBSE TRY 2016 / Exeter Prometheus .epw files to mathematically
calculate the Heating Degree Days (HDD) for the 9 English regions.

Base temperature for CIBSE standard: 15.5°C
Formula: HDD = sum(max(0, 15.5 - T_mean_daily)) over 365 days.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger("EPWParser")

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config.settings import BASE_TEMP_HDD

def calculate_hdd_from_epw(epw_path: Path) -> float:
    """
    Parses an EPW file, extracts the 8760 hourly dry bulb temperatures,
    calculates daily means, and sums the Heating Degree Days.
    """
    if not epw_path.exists():
        raise FileNotFoundError(f"Missing EPW file: {epw_path}. Cannot calculate valid HDD without real weather data.")

    try:
        # EPW weather data starts on line 9 (index 8). 
        # Column 6 (0-indexed) is Dry Bulb Temperature.
        # We can read it efficiently using pandas.
        df = pd.read_csv(epw_path, skiprows=8, header=None, usecols=[6], names=["dry_bulb_temp"])
        
        # Calculate daily mean temperatures
        # Assuming exactly 8760 hours (365 days * 24 hours). 
        # If leap year 8784, it will just take the floor of days.
        num_days = len(df) // 24
        df = df.iloc[:num_days * 24] # Trim any trailing hours
        
        daily_means = df['dry_bulb_temp'].values.reshape(num_days, 24).mean(axis=1)
        
        # Calculate HDD
        hdd = np.sum(np.maximum(0, BASE_TEMP_HDD - daily_means))
        return float(hdd)
        
    except Exception as e:
        raise RuntimeError(f"Failed to parse EPW {epw_path}: {e}")

def get_regional_hdd_map(physics_dir: Path, cities: list[str]) -> dict[str, float]:
    """
    Given a list of cities and the physics directory containing their EPW files,
    returns a dictionary mapping each city to its calculated HDD.
    """
    hdd_map = {}
    for city in cities:
        # Assuming filename format aligns with our placeholders / actual downloads
        epw_file = physics_dir / f"{city}_2030_ColdSnap.epw"
        hdd = calculate_hdd_from_epw(epw_file)
        hdd_map[city] = hdd
        
    return hdd_map

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from src.config.settings import RAW_DIR, REGIONAL_CENTERS
    PHYSICS_DIR = RAW_DIR / "physics"
    cities = list(REGIONAL_CENTERS.keys())
    hdd_map = get_regional_hdd_map(PHYSICS_DIR, cities)
    for city, hdd in hdd_map.items():
        logger.info(f"{city}: {hdd:.1f} HDD")
