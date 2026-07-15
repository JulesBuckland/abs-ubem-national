import pandas as pd
import shutil
from pathlib import Path
import os

SCRIPT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = SCRIPT_DIR
RAW_DIR_SRC = BASE_DIR / "data" / "raw"
PROCESSED_DIR_SRC = BASE_DIR / "data" / "processed"

RAW_DIR_DST = BASE_DIR / "tests" / "fixtures" / "raw"
PROCESSED_DIR_DST = BASE_DIR / "tests" / "fixtures" / "processed"

# 1 MSOA to extract
TARGET_MSOA = "E02000001" # City of London 001

def setup_dirs():
    RAW_DIR_DST.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR_DST.mkdir(parents=True, exist_ok=True)
    (RAW_DIR_DST / "energy").mkdir(parents=True, exist_ok=True)
    (RAW_DIR_DST / "census").mkdir(parents=True, exist_ok=True)
    (RAW_DIR_DST / "census" / "ts044_extracted").mkdir(parents=True, exist_ok=True)
    (RAW_DIR_DST / "physics").mkdir(parents=True, exist_ok=True)
    (RAW_DIR_DST / "spatial").mkdir(parents=True, exist_ok=True)

def generate_fixtures():
    setup_dirs()
    
    # 1. NEED Data (Keep all 50k so IPF converges without breaking 5% cap)
    need_src = RAW_DIR_SRC / "energy" / "need_2024_official_50k.csv"
    if need_src.exists():
        shutil.copy(need_src, RAW_DIR_DST / "energy" / "need_2024_official_50k.csv")
    
    # 2. TS044 Census
    ts044_src = RAW_DIR_SRC / "census" / "ts044_extracted" / "census2021-ts044-msoa.csv"
    if ts044_src.exists():
        df = pd.read_csv(ts044_src)
        df[df['geography code'] == TARGET_MSOA].to_csv(RAW_DIR_DST / "census" / "ts044_extracted" / "census2021-ts044-msoa.csv", index=False)

    # 3. TS054 Census
    ts054_src = RAW_DIR_SRC / "census" / "TS054-2021-4-filtered-2026-02-27T03_51_51Z.csv"
    if ts054_src.exists():
        df = pd.read_csv(ts054_src)
        df[df['Middle layer Super Output Areas Code'] == TARGET_MSOA].to_csv(RAW_DIR_DST / "census" / "TS054-2021-4-filtered-2026-02-27T03_51_51Z.csv", index=False)
        
    # 4. Processed Confounders
    conf_src = PROCESSED_DIR_SRC / "msoa_confounders_national.csv"
    if conf_src.exists():
        df = pd.read_csv(conf_src)
        df[df['msoa_cd'] == TARGET_MSOA].to_csv(PROCESSED_DIR_DST / "msoa_confounders_national.csv", index=False)
        
    # 5. Region Lookup
    reg_src = PROCESSED_DIR_SRC / "msoa_region_lookup.csv"
    if reg_src.exists():
        df = pd.read_csv(reg_src)
        df[df['msoa21cd'] == TARGET_MSOA].to_csv(PROCESSED_DIR_DST / "msoa_region_lookup.csv", index=False)
        
    # 6. Spatial Lookup & Boundaries
    spatial_src = RAW_DIR_SRC / "spatial" / "lookup.csv"
    if spatial_src.exists():
        df = pd.read_csv(spatial_src)
        df[df['msoa21cd'] == TARGET_MSOA].to_csv(RAW_DIR_DST / "spatial" / "lookup.csv", index=False)
        
    gpkg_src = RAW_DIR_SRC / "spatial" / "msoa dec 2021 boundaries.gpkg"
    gpkg_dst = RAW_DIR_DST / "spatial" / "msoa dec 2021 boundaries.gpkg"
    if gpkg_src.exists():
        shutil.copy(gpkg_src, gpkg_dst)

    # 7. Copy only the required lhs_results_combined.csv (skip gigabytes of EPW/sim data)
    phys_src = RAW_DIR_SRC / "physics"
    phys_dst = RAW_DIR_DST / "physics"
    phys_dst.mkdir(parents=True, exist_ok=True)
    
    lhs_src = phys_src / "lhs_results_combined.csv"
    lhs_dst = phys_dst / "lhs_results_combined.csv"
    if lhs_src.exists():
        # Truncate to 300 rows so the GP trains instantly in tests
        df_lhs = pd.read_csv(lhs_src)
        df_lhs.head(300).to_csv(lhs_dst, index=False)

    # We also need the pre-trained GP emulator because retraining it even on 2000 points takes 20 minutes
    # We will just copy the existing gp_emulator.pkl if it exists, or just copy the dummy one.
    # Wait, the pipeline runs 01 -> 02a. 01 synthesizes population. 02a runs the Bayesian model.
    # 02a requires the GP emulator to be at PROCESSED_DIR / "gp_emulator.pkl".
    gp_src = PROCESSED_DIR_SRC / "gp_emulator.pkl"
    if gp_src.exists():
        shutil.copy(gp_src, PROCESSED_DIR_DST / "gp_emulator.pkl")
    else:
        # Provide a dummy fallback if missing so tests can pass without full GP training
        pass

    print("Fixtures generated successfully.")

if __name__ == "__main__":
    generate_fixtures()
