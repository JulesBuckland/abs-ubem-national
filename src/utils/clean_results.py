import pandas as pd

def clean_results():
    path = 'data/processed/national_bayesian_results.csv'
    df = pd.read_csv(path)
    
    # Remove rows where header is repeated
    df = df[df['msoa21cd'] != 'msoa21cd'].copy()
    
    # Convert to numeric
    for col in df.columns:
        if col != 'msoa21cd':
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Drop NA and duplicates
    df = df.dropna()
    df = df.drop_duplicates(subset=['msoa21cd'])
    
    # Final purification: keep only English MSOAs in the IMD list
    imd_path = 'data/raw/imd/imd_2019_msoa.csv'
    imd_msoas = pd.read_csv(imd_path).iloc[:, 0].tolist()
    df = df[df['msoa21cd'].isin(imd_msoas)].copy()
    
    # We expect 6840
    print(f"Purified count: {len(df)}")
    
    df.to_csv(path, index=False)

if __name__ == "__main__":
    clean_results()
