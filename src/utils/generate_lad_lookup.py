import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("LADLookupGenerator")

def generate_lookup():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_lookup = base_dir / "data" / "raw" / "spatial" / "lookup.csv"
    output_path = base_dir / "data" / "processed" / "msoa_lad_lookup.csv"
    
    if not raw_lookup.exists():
        logger.error(f"Raw lookup not found at {raw_lookup}")
        return

    logger.info("Reading raw lookup (selecting msoa21cd and ladcd)...")
    
    try:
        df = pd.read_csv(raw_lookup, usecols=['msoa21cd', 'ladcd'])
        
        logger.info("Cleaning NaNs...")
        df = df.dropna(subset=['msoa21cd', 'ladcd'])
        
        logger.info("Filtering for England (E codes)...")
        # Filter for England MSOAs (starting with E)
        df = df[df['msoa21cd'].str.startswith('E')].copy()

        logger.info("Dropping duplicates...")
        lookup = df.drop_duplicates(subset=['msoa21cd'])

        logger.info(f"Found {len(lookup)} unique MSOAs in England.")

        
        lookup.to_csv(output_path, index=False)
        logger.info(f"Saved lookup to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate lookup: {e}")

if __name__ == "__main__":
    generate_lookup()
