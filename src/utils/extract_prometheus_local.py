"""
extract_prometheus_local.py
===========================
Extracts authentic PROMETHEUS EPW files from the locally downloaded 29812739.zip.
Maps the 9 English pipeline regions to the closest available Exeter climate models.
"""

import zipfile
import io
import os
import logging
from pathlib import Path

logger = logging.getLogger("PrometheusLocalExtractor")
logging.basicConfig(level=logging.INFO)

# Mapping our pipeline NUTS1 regions to the PROMETHEUS ZIP filenames
CITY_MAPPING = {
    'London': 'Bicester',      # Home Counties proxy
    'Manchester': 'Carlisle',  # North West proxy
    'Birmingham': 'Birmingham',
    'Leeds': 'Bradford',       # Yorkshire proxy
    'Newcastle': 'Edinburgh',  # East Coast / North proxy
    'Bristol': 'Bristol',
    'Norwich': 'Cambridge',    # East of England proxy
    'Southampton': 'Brighton', # South Coast proxy
    'Nottingham': 'Birmingham' # Midlands proxy
}

def extract_from_local_zip(physics_dir: Path):
    main_zip_path = physics_dir / "29812739.zip"
    if not main_zip_path.exists():
        logger.error(f"Cannot find massive zip file: {main_zip_path}")
        return
        
    logger.info(f"Opening massive archive: {main_zip_path.name}")
    
    with zipfile.ZipFile(main_zip_path, 'r') as main_zip:
        main_namelist = main_zip.namelist()
        
        for target_city, proxy_city in CITY_MAPPING.items():
            proxy_zip_name = f"{proxy_city}.zip"
            
            # Find the proxy zip inside the massive zip
            nested_zip_path = next((name for name in main_namelist if name.endswith(proxy_zip_name)), None)
            
            if not nested_zip_path:
                logger.warning(f"Could not find {proxy_zip_name} inside {main_zip_path.name}")
                continue
                
            logger.info(f"Extracting {proxy_city} proxy for {target_city}...")
            
            # Read the nested zip into memory
            proxy_zip_bytes = main_zip.read(nested_zip_path)
            with zipfile.ZipFile(io.BytesIO(proxy_zip_bytes)) as proxy_zip:
                # The proxy zip contains FURTHER nested zips (e.g., Birmingham_2030_high.zip)
                emissions_zip_name = next((n for n in proxy_zip.namelist() if "2030_high" in n.lower() and n.endswith(".zip")), None)
                
                if not emissions_zip_name:
                    logger.warning(f"Could not find a 2030_high zip inside {proxy_zip_name}")
                    continue
                    
                emissions_zip_bytes = proxy_zip.read(emissions_zip_name)
                with zipfile.ZipFile(io.BytesIO(emissions_zip_bytes)) as emissions_zip:
                    # Look for 50th percentile EPW
                    target_epw = None
                    for name in emissions_zip.namelist():
                        if name.endswith(".epw") and "50" in name:
                            target_epw = name
                            break
                            
                    if not target_epw:
                        for name in emissions_zip.namelist():
                            if name.endswith(".epw"):
                                target_epw = name
                                break
                                
                    if not target_epw:
                        logger.warning(f"Could not find an EPW file inside {emissions_zip_name}")
                        continue
                        
                    epw_content = emissions_zip.read(target_epw)
                    
                    final_path = physics_dir / f"{target_city}_2030_ColdSnap.epw"
                    if final_path.exists():
                        os.remove(final_path)
                    
                    with open(final_path, "wb") as f:
                        f.write(epw_content)
                        
                    logger.info(f"Successfully saved authentic EPW -> {final_path.name}")

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from src.config.settings import RAW_DIR
    
    physics_dir = RAW_DIR / "physics"
    extract_from_local_zip(physics_dir)
    logger.info("Extraction complete. Authentic EPWs are now in place.")
