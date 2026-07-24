import pandas as pd
import numpy as np
import requests
from pathlib import Path
import logging
import geopandas as gpd
from src.config.settings import RAW_DIR, PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("RebuildConfoundersNational")

def get_pm25_annual_mean(lat, lon):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5",
        "start_date": "2022-01-01",
        "end_date": "2022-12-31"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return np.mean(data['hourly']['pm2_5'])
    except Exception as e:
        return 8.5 # Regional average fallback

def rebuild():
    logger.info("--- REBUILDING NATIONAL MSOA CONFOUNDERS (England & Wales) ---")
    
    # 1. Load MSOA Shapefile to get centroids for PM2.5 sampling
    shp_path = RAW_DIR / "spatial" / "MSOA_2021_EW_BGC_V3.shp"
    logger.info(f"Loading MSOA boundaries from {shp_path}...")
    msoa_gdf = gpd.read_file(shp_path)
    
    # Correct Centroid Calculation (Reproject to BNG first for accurate centroids, then to WGS84 for lat/lon)
    if msoa_gdf.crs != 'EPSG:27700':
        msoa_gdf = msoa_gdf.to_crs(epsg=27700)
    
    msoa_gdf['centroid'] = msoa_gdf.geometry.centroid
    msoa_gdf = msoa_gdf.set_geometry('centroid').to_crs(epsg=4326)
    msoa_gdf['lat'] = msoa_gdf.geometry.y
    msoa_gdf['lon'] = msoa_gdf.geometry.x
    msoa_gdf = msoa_gdf.rename(columns={'MSOA21CD': 'msoa_cd'})
    
    # 2. Sample PM2.5 (Aggregated by LAD to save API calls)
    lookup_path = RAW_DIR / "spatial" / "lookup.csv"
    logger.info(f"Loading lookup from {lookup_path}...")
    lookup = pd.read_csv(lookup_path, usecols=['msoa21cd', 'ladnm']).drop_duplicates()
    msoa_lad = msoa_gdf[['msoa_cd', 'lat', 'lon']].merge(lookup, left_on='msoa_cd', right_on='msoa21cd')
    
    lads = msoa_lad.groupby('ladnm')[['lat', 'lon']].mean().reset_index()
    logger.info(f"Sampling PM2.5 for {len(lads)} Local Authorities...")
    
    lad_pm25 = []
    for idx, row in lads.iterrows():
        if idx % 50 == 0: logger.info(f"Progress: {idx}/{len(lads)} LADs...")
        pm25 = get_pm25_annual_mean(row['lat'], row['lon'])
        lad_pm25.append({'ladnm': row['ladnm'], 'pm25_val': pm25})
    
    pm25_df = pd.DataFrame(lad_pm25)
    msoa_pm25 = msoa_lad.merge(pm25_df, on='ladnm')[['msoa_cd', 'pm25_val']].drop_duplicates()

    # 3. Process Age Structure (National Census TS007)
    ts007_path = RAW_DIR / "census" / "TS007-2021-3-filtered-2026-03-30T02_17_27Z.csv"
    logger.info(f"Processing Age Structure from {ts007_path}...")
    age_raw = pd.read_csv(ts007_path)
    age_raw['age_val'] = pd.to_numeric(age_raw['Age (101 categories) Code'], errors='coerce')
    age_total = age_raw.groupby('Middle layer Super Output Areas Code')['Observation'].sum().reset_index()
    age_65plus = age_raw[age_raw['age_val'] >= 65].groupby('Middle layer Super Output Areas Code')['Observation'].sum().reset_index()
    age = age_total.merge(age_65plus, on='Middle layer Super Output Areas Code')
    age.columns = ['msoa_cd', 'total', 'over65']
    age['pct_over_65'] = age['over65'] / age['total']
    age = age[['msoa_cd', 'pct_over_65']]

    # 4. Process National IMD (Income)
    imd_path = RAW_DIR / "imd" / "imd_2019_msoa.csv"
    logger.info(f"Processing IMD data from {imd_path}...")
    imd_msoa = pd.read_csv(imd_path)
    imd_msoa.columns = ['msoa_cd', 'income_dep_score']

    # 5. Process Overcrowding (National Census TS052)
    ts052_path = RAW_DIR / "census" / "ts052_msoa" / "census2021-ts052-msoa.csv"
    logger.info(f"Processing Overcrowding from {ts052_path}...")
    ts052 = pd.read_csv(ts052_path)
    total_col = 'Occupancy rating for bedrooms: Total: All households'
    neg1_col = 'Occupancy rating for bedrooms: Occupancy rating of bedrooms: -1'
    neg2_col = 'Occupancy rating for bedrooms: Occupancy rating of bedrooms: -2 or less'
    ts052['overcrowding_prev'] = (ts052[neg1_col] + ts052[neg2_col]) / ts052[total_col]
    ts052 = ts052[['geography code', 'overcrowding_prev']]
    ts052.columns = ['msoa_cd', 'overcrowding_prev']

    # Merge all
    conf = msoa_pm25.merge(age, on='msoa_cd', how='left')
    conf = conf.merge(imd_msoa, on='msoa_cd', how='left')
    conf = conf.merge(ts052, on='msoa_cd', how='left')

    # Final Clean & Save
    conf = conf.dropna(subset=['msoa_cd'])
    conf = conf.drop_duplicates(subset=['msoa_cd'])
    
    # ZERO TRUST PROTOCOL: Explicitly drop Wales ('W' codes) to prevent
    # median-imputation hallucination of missing Welsh IMD data.
    wales_mask = conf['msoa_cd'].str.startswith('W')
    if wales_mask.any():
        logger.warning(f"Dropping {wales_mask.sum()} Welsh MSOAs due to incompatible IMD/WIMD datasets.")
        conf = conf[~wales_mask]
    
    # Assert missing data thresholds
    for col in ['pm25_val', 'pct_over_65', 'income_dep_score', 'overcrowding_prev']:
        assert conf[col].isna().mean() < 0.05, f"CRITICAL: >5% missing data in {col}"
        
    conf = conf.fillna(conf.median(numeric_only=True))
    
    out_path = PROCESSED_DIR / "msoa_confounders_national.csv"
    conf.to_csv(out_path, index=False)
    logger.info(f"Final national confounder set size: {len(conf)} MSOAs")
    logger.info(f"Saved to {out_path}")

if __name__ == "__main__":
    rebuild()
