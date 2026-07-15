import pandas as pd
from pathlib import Path
import glob

# --- DIRECTORY STRUCTURE ---
BASE_DIR = Path(".")
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def process_no2():
    print("Processing NO2 data...")
    no2_dir = RAW_DIR / "downloaded" / "no2"
    files = glob.glob(str(no2_dir / "no2_*.csv"))
    
    all_no2 = []
    for f in files:
        df = pd.read_csv(f)
        all_no2.append(df)
    
    no2_df = pd.concat(all_no2)
    no2_df.columns = ['lad_cd', 'no2_val']
    
    # Map LAD to MSOA via lookup
    lookup = pd.read_csv(RAW_DIR / "lookup.csv", usecols=['msoa21cd', 'ladcd']).drop_duplicates()
    
    # Merge
    msoa_no2 = lookup.merge(no2_df, left_on='ladcd', right_on='lad_cd')
    msoa_no2 = msoa_no2[['msoa21cd', 'no2_val']].drop_duplicates()
    
    # Update confounders
    conf = pd.read_csv(PROCESSED_DIR / "msoa_confounders.csv")
    
    if 'no2_val' in conf.columns:
        conf = conf.drop(columns=['no2_val'])
        
    conf = conf.merge(msoa_no2, left_on='msoa_cd', right_on='msoa21cd', how='left').drop(columns=['msoa21cd'])
    
    # Fill missing with median if any (unlikely for GM)
    conf['no2_val'] = conf['no2_val'].fillna(conf['no2_val'].median())
    
    conf.to_csv(PROCESSED_DIR / "msoa_confounders.csv", index=False)
    print(f"Updated msoa_confounders.csv with NO2 data. Head:\n{conf.head()}")

if __name__ == "__main__":
    process_no2()
