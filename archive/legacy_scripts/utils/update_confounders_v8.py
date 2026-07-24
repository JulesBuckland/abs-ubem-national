import pandas as pd
import numpy as np
import requests
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ConfounderUpdateV8")

BASE_DIR = Path(".")
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

LAD_COORDS = {
    'Bolton': (53.5789, -2.4297),
    'Bury': (53.5933, -2.2966),
    'Manchester': (53.4808, -2.2426),
    'Oldham': (53.5409, -2.1114),
    'Rochdale': (53.6150, -2.1550),
    'Salford': (53.4875, -2.2901),
    'Stockport': (53.4106, -2.1575),
    'Tameside': (53.4841, -2.0911),
    'Trafford': (53.4486, -2.3216),
    'Wigan': (53.5450, -2.6319)
}

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
        logger.error(f"Failed to pull PM2.5 for {lat}, {lon}: {e}")
        return 8.5 # Regional average fallback

def update_confounders():
    logger.info("Updating MSOA Confounders with Real Overcrowding and PM2.5 data...")
    
    # 1. Load Overcrowding Data (TS052)
    ts052_path = RAW_DIR / "census" / "ts052_msoa" / "census2021-ts052-msoa.csv"
    if not ts052_path.exists():
        raise FileNotFoundError(f"TS052 data not found at {ts052_path}")
    
    overcrowd_df = pd.read_csv(ts052_path)
    total_col = 'Occupancy rating for bedrooms: Total: All households'
    neg1_col = 'Occupancy rating for bedrooms: Occupancy rating of bedrooms: -1'
    neg2_col = 'Occupancy rating for bedrooms: Occupancy rating of bedrooms: -2 or less'
    
    overcrowd_df['overcrowding_prev'] = (overcrowd_df[neg1_col] + overcrowd_df[neg2_col]) / overcrowd_df[total_col]
    overcrowd_df = overcrowd_df[['geography code', 'overcrowding_prev']]
    overcrowd_df.columns = ['msoa_cd', 'overcrowding_prev']
    
    # 2. Pull PM2.5 for each LAD
    lad_pm25 = []
    for lad, coords in LAD_COORDS.items():
        logger.info(f"Pulling PM2.5 for {lad}...")
        mean_pm25 = get_pm25_annual_mean(coords[0], coords[1])
        lad_pm25.append({'ladnm': lad, 'pm25_val': mean_pm25})
    
    pm25_df = pd.DataFrame(lad_pm25)
    
    # 3. Map PM2.5 to MSOA
    lookup = pd.read_csv(RAW_DIR / "lookup.csv", usecols=['msoa21cd', 'ladnm']).drop_duplicates()
    msoa_pm25 = lookup.merge(pm25_df, on='ladnm')[['msoa21cd', 'pm25_val']].drop_duplicates()
    
    # 4. Merge all into existing confounders
    conf = pd.read_csv(PROCESSED_DIR / "msoa_confounders.csv")
    
    # Drop old overcrowding_prev and no2_val if they exist (we're replacing no2 with pm25)
    cols_to_drop = [c for c in ['overcrowding_prev', 'no2_val', 'pm25_val'] if c in conf.columns]
    conf = conf.drop(columns=cols_to_drop)
    
    conf = conf.merge(overcrowd_df, on='msoa_cd', how='left')
    conf = conf.merge(msoa_pm25, left_on='msoa_cd', right_on='msoa21cd', how='left').drop(columns=['msoa21cd'])
    
    # Fill missing values with strict assertions
    assert conf['overcrowding_prev'].isna().mean() < 0.05, "CRITICAL: Merging dropped >5% of the overcrowding data!"
    conf['overcrowding_prev'] = conf['overcrowding_prev'].fillna(conf['overcrowding_prev'].median())
    
    assert conf['pm25_val'].isna().mean() < 0.05, "CRITICAL: Merging dropped >5% of the pm2.5 data!"
    conf['pm25_val'] = conf['pm25_val'].fillna(conf['pm25_val'].median())
    
    conf.to_csv(PROCESSED_DIR / "msoa_confounders.csv", index=False)
    logger.info(f"Updated confounders saved. Head:\n{conf.head()}")

if __name__ == "__main__":
    update_confounders()
