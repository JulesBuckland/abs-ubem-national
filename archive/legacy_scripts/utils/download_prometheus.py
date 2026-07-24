"""
download_prometheus.py
========================
Downloads authentic UKCP09-based PROMETHEUS 2030s EPW files from the 
University of Exeter Figshare repository.

Extracts the High Emissions (A1FI) 50th percentile file for the 2030s
and formats it into the pipeline's expected naming convention.
"""

import urllib.request
import json
import zipfile
import io
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("PrometheusDownload")
logging.basicConfig(level=logging.INFO)

FIGSHARE_FILES_URL = "https://api.figshare.com/v2/articles/29812739/files?page_size=100"

def fetch_prometheus_files(target_cities: list[str], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Querying Figshare API: {FIGSHARE_FILES_URL}")
    req = urllib.request.Request(FIGSHARE_FILES_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        files_data = json.loads(response.read().decode('utf-8'))
        
    for city in target_cities:
        # Find the zip file for this city
        city_zip_name = f"{city}.zip"
        # London in Prometheus is sometimes named London_Gatwick or London_Heathrow. Let's just find the first match
        file_info = next((f for f in files_data if city.lower() in f['name'].lower()), None)
        
        if not file_info:
            logger.warning(f"Could not find {city} in the Figshare repository.")
            continue
            
        download_url = file_info['download_url']
        logger.info(f"Downloading {city} from {download_url} ({file_info['size'] / 1e6:.1f} MB)...")
        
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            zip_content = response.read()
            
        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            # The main zip contains nested zips like City_2030_high.zip
            target_nested_zip = None
            for name in z.namelist():
                if "2030_high" in name.lower() and name.endswith(".zip"):
                    target_nested_zip = name
                    break
            
            if not target_nested_zip:
                logger.warning(f"Could not find 2030 high emissions zip for {city}.")
                continue
                
            nested_zip_content = z.read(target_nested_zip)
            with zipfile.ZipFile(io.BytesIO(nested_zip_content)) as nested_z:
                target_epw = None
                # Look for 50th percentile EPW
                for name in nested_z.namelist():
                    if name.endswith(".epw") and "50" in name:
                        target_epw = name
                        break
                
                if not target_epw:
                    for name in nested_z.namelist():
                        if name.endswith(".epw"):
                            target_epw = name
                            break
                            
                if not target_epw:
                    logger.warning(f"Could not find EPW inside {target_nested_zip}.")
                    continue
                    
                epw_content = nested_z.read(target_epw)
                
            final_path = output_dir / f"{city}_2030_ColdSnap.epw"
            if final_path.exists():
                os.remove(final_path)
            
            with open(final_path, "wb") as f:
                f.write(epw_content)
                
            logger.info(f"Successfully saved authentic EPW -> {final_path.name}")

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from src.config.settings import RAW_DIR, REGIONAL_CENTERS
    
    physics_dir = RAW_DIR / "physics"
    cities = list(REGIONAL_CENTERS.keys())
    
    fetch_prometheus_files(cities, physics_dir)
    logger.info("PROMETHEUS download complete.")
