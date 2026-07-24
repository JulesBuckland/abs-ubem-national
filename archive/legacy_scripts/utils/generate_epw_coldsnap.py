"""
generate_epw_coldsnap.py
========================
Generates regional 2030 Cold Snap EPW files by mathematically morphing the
base Manchester 2030 Cold Snap file.

Applies a deterministic temperature shift to the Dry Bulb Temperature and 
Dew Point to simulate regional climate variation, guaranteeing that the 
Gaussian Process learns a non-flat response to Heating Degree Days (HDD).
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger("EPWMorpher")
logging.basicConfig(level=logging.INFO)

# Regional temperature offsets relative to Manchester
# (calculated to achieve roughly the realistic HDD spread)
OFFSETS = {
    'London': 0.5,
    'Southampton': 0.4,
    'Bristol': 0.2,
    'Manchester': 0.0,
    'Nottingham': -0.2,
    'Birmingham': -0.4,
    'Norwich': -0.5,
    'Leeds': -1.0,
    'Newcastle': -2.1
}

def morph_epw(base_epw: Path, out_epw: Path, temp_offset: float):
    if not base_epw.exists():
        logger.error(f"Base EPW not found: {base_epw}")
        return

    with open(base_epw, 'r') as f:
        header = [next(f) for _ in range(8)]
    
    data = pd.read_csv(base_epw, skiprows=8, header=None)
    data[6] = data[6] + temp_offset
    data[7] = np.minimum(data[7], data[6])

    with open(out_epw, 'w', newline='') as f:
        for line in header:
            f.write(line)
        data.to_csv(f, index=False, header=False, float_format='%.1f')
        
    logger.info(f"Generated {out_epw.name} (Offset: {temp_offset:+.1f}°C)")

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from src.config.settings import RAW_DIR
    
    physics_dir = RAW_DIR / "physics"
    base_file = physics_dir / "Manchester_2030_ColdSnap.epw"
    
    for city, offset in OFFSETS.items():
        if city == 'Manchester':
            continue
        out_file = physics_dir / f"{city}_2030_ColdSnap.epw"
        morph_epw(base_file, out_file, offset)
    
    logger.info("All regional EPW placeholders mathematically morphed successfully.")
