import subprocess
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils.epw_parser import calculate_hdd_from_epw

# --- CONFIG ---
EP_EXE = Path(r"C:\EnergyPlusV25-2-0\energyplus.exe")
WEATHER_FILE = Path("data/raw/physics/Manchester_2030_ColdSnap.epw")
TEMPLATE_FILE = Path("data/raw/physics/seed_template.idf")
SIM_DIR = Path("data/raw/physics/energyplus_sims")
BASELINE_CSV = Path("data/raw/physics/physics_archetypes_baseline.csv")

SIM_DIR.mkdir(parents=True, exist_ok=True)

# --- MATRICES ---
FORMS = {
    "Bungalow":   {"floors": 1, "exposed_walls": 4, "wwr": 0.15},
    "Flat":       {"floors": 1, "exposed_walls": 1, "wwr": 0.20},
    "House":      {"floors": 2, "exposed_walls": 4, "wwr": 0.15},
    "Maisonette": {"floors": 2, "exposed_walls": 2, "wwr": 0.15}
}

AGES = {
    "Pre-1900":  {"wall": 2.1,  "roof": 2.0,  "floor": 1.2, "window": 4.8, "ach": 1.5},
    "1900-1929": {"wall": 2.1,  "roof": 1.5,  "floor": 1.2, "window": 4.8, "ach": 1.5},
    "1930-1949": {"wall": 1.7,  "roof": 1.0,  "floor": 1.0, "window": 4.8, "ach": 1.2},
    "1950-1966": {"wall": 1.5,  "roof": 0.7,  "floor": 0.8, "window": 4.8, "ach": 1.0},
    "1967-1982": {"wall": 1.0,  "roof": 0.4,  "floor": 0.6, "window": 3.0, "ach": 0.8},
    "1983-1995": {"wall": 0.6,  "roof": 0.3,  "floor": 0.4, "window": 2.5, "ach": 0.6},
    "1996-2006": {"wall": 0.45, "roof": 0.2,  "floor": 0.3, "window": 2.0, "ach": 0.5},
    "2007+":     {"wall": 0.3,  "roof": 0.15, "floor": 0.2, "window": 1.6, "ach": 0.5}
}

def run_pipeline():
    df = pd.read_csv(BASELINE_CSV)
    # Filter for standard types
    df = df[df['property_type'].isin(FORMS.keys())].copy()
    
    with open(TEMPLATE_FILE, "r") as f:
        template = f.read()

    results = []

    for idx, row in df.iterrows():
        name = row['Archetype'].replace(" ", "_").replace("+", "plus")
        form_name = row['property_type']
        age_name = row['property_age']
        
        f_spec = FORMS[form_name]
        a_spec = AGES[age_name]
        
        # Geometry
        total_area = row['Mean_Area']
        footprint = total_area / f_spec['floors']
        side = np.sqrt(footprint)
        height_per_floor = 3.0
        total_height = f_spec['floors'] * height_per_floor
        
        # Window (South wall only for simplicity in this 1-zone box)
        target_win_area = total_area * f_spec['wwr'] # Heuristic
        win_side = np.sqrt(target_win_area)
        if win_side > side * 0.8: win_side = side * 0.8
        if win_side > total_height * 0.8: win_side = total_height * 0.8
        
        w_x_min = (side - win_side) / 2
        w_x_max = w_x_min + win_side
        w_z_min = (total_height - win_side) / 2
        w_z_max = w_z_min + win_side

        # Fill Template
        idf = template.replace("@@ARCHETYPE_NAME@@", name)
        idf = idf.replace("@@NORTH_AXIS@@", "0.0")
        idf = idf.replace("@@PEOPLE_COUNT@@", "0.0") # Baseline HLC calculation needs zero internal gains
        idf = idf.replace("@@LIGHTING_W@@", "0.0")
        idf = idf.replace("@@EQUIPMENT_W@@", "0.0")
        idf = idf.replace("@@WALL_R_VALUE@@", f"{1.0/a_spec['wall']:.4f}")
        idf = idf.replace("@@ROOF_R_VALUE@@", f"{1.0/a_spec['roof']:.4f}")
        idf = idf.replace("@@FLOOR_R_VALUE@@", f"{1.0/a_spec['floor']:.4f}")
        idf = idf.replace("@@WINDOW_U_VALUE@@", f"{a_spec['window']:.2f}")
        idf = idf.replace("@@ZONE_VOLUME@@", f"{total_area * total_height:.2f}")
        idf = idf.replace("@@SIDE_LENGTH@@", f"{side:.2f}")
        idf = idf.replace("@@TOTAL_HEIGHT@@", f"{total_height:.2f}")
        idf = idf.replace("@@W_X_MIN@@", f"{w_x_min:.2f}")
        idf = idf.replace("@@W_X_MAX@@", f"{w_x_max:.2f}")
        idf = idf.replace("@@W_Z_MIN@@", f"{w_z_min:.2f}")
        idf = idf.replace("@@W_Z_MAX@@", f"{w_z_max:.2f}")
        
        # Boundary Conditions
        idf = idf.replace("@@BC_EAST@@", "Outdoors" if f_spec['exposed_walls'] >= 2 else "Adiabatic")
        idf = idf.replace("@@SUN_EAST@@", "SunExposed" if f_spec['exposed_walls'] >= 2 else "NoSun")
        idf = idf.replace("@@WIND_EAST@@", "WindExposed" if f_spec['exposed_walls'] >= 2 else "NoWind")
        idf = idf.replace("@@BC_NORTH@@", "Outdoors" if f_spec['exposed_walls'] >= 3 else "Adiabatic")
        idf = idf.replace("@@SUN_NORTH@@", "SunExposed" if f_spec['exposed_walls'] >= 3 else "NoSun")
        idf = idf.replace("@@WIND_NORTH@@", "WindExposed" if f_spec['exposed_walls'] >= 3 else "NoWind")
        idf = idf.replace("@@BC_WEST@@", "Outdoors" if f_spec['exposed_walls'] >= 4 else "Adiabatic")
        idf = idf.replace("@@SUN_WEST@@", "SunExposed" if f_spec['exposed_walls'] >= 4 else "NoSun")
        idf = idf.replace("@@WIND_WEST@@", "WindExposed" if f_spec['exposed_walls'] >= 4 else "NoWind")

        idf_path = SIM_DIR / f"{name}.idf"
        with open(idf_path, "w") as f:
            f.write(idf)

        # Execute with -r flag to generate eplusout.csv
        print(f"Simulating {row['Archetype']}...")
        out_dir = SIM_DIR / name
        out_dir.mkdir(exist_ok=True)
        subprocess.run([str(EP_EXE), "-w", str(WEATHER_FILE), "-d", str(out_dir), "-r", str(idf_path)], 
                       capture_output=True, check=True)
        
        # Parse CSV
        csv_path = out_dir / "eplusout.csv"
        sim_df = pd.read_csv(csv_path)
        
        heat_col = [c for c in sim_df.columns if "Zone Air System Sensible Heating Rate" in c][0]
        temp_col = [c for c in sim_df.columns if "Site Outdoor Air Drybulb Temperature" in c][0]
        
        # We need the simulation hours. 
        # For a clean HLC, we only want hours where heating is actually on (rate > 0)
        active_sim = sim_df[sim_df[heat_col] > 0].copy()
        if len(active_sim) == 0:
            # Fallback to mean of all hours if no heating (shouldn't happen in ColdSnap)
            active_sim = sim_df
            
        avg_heating = active_sim[heat_col].mean()
        avg_out_temp = active_sim[temp_col].mean()
        delta_t = 15.5 - avg_out_temp # Degree Day Base
        
        hlc_cond = avg_heating / delta_t
        vol = total_area * total_height
        hlc_inf = (a_spec['ach'] * vol * 1200) / 3600
        
        total_hlc = hlc_cond + hlc_inf
        results.append(total_hlc)
        print(f"  HLC: {total_hlc:.2f} W/K")

    df['hlc'] = results
    
    # Calculate real HDD for the weather file rather than hardcoding 2500
    true_hdd = calculate_hdd_from_epw(WEATHER_FILE)
    df['theoretical_gas_kwh'] = df['hlc'] * true_hdd * 24 * 1e-3
    df.to_csv(BASELINE_CSV, index=False)
    print("\nProgrammatic EnergyPlus Stage Complete.")

if __name__ == "__main__":
    run_pipeline()
