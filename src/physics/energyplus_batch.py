"""
10b_energyplus_lhs_batch.py
============================
Runs EnergyPlus for every point in the LHS design files produced by
10a_lhs_sampler.py.

Parallelised across available CPU cores via ProcessPoolExecutor.
Supports resume: already-completed runs are skipped.

Inputs:  data/raw/physics/lhs_designs/lhs_*.csv
Outputs: data/raw/physics/lhs_results/lhs_results_{archetype}.csv
         data/raw/physics/lhs_results_combined.csv
"""

import subprocess
import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
import concurrent.futures
import math
import argparse
import re
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("EnergyPlusLHSBatch")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR     = Path(__file__).resolve().parent.parent
PHYSICS_DIR  = BASE_DIR / "data" / "raw" / "physics"
LHS_DIR      = PHYSICS_DIR / "lhs_designs"
RESULTS_DIR  = PHYSICS_DIR / "lhs_results"
SIM_DIR      = PHYSICS_DIR / "lhs_energyplus_sims"
TEMPLATE_FILE = PHYSICS_DIR / "seed_template.idf"
EP_EXE        = Path(r"C:\EnergyPlusV25-2-0\energyplus.exe")

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SIM_DIR.mkdir(parents=True, exist_ok=True)

HEIGHT_PER_FLOOR = 3.0

# ---------------------------------------------------------------------------
# IDF generation
# ---------------------------------------------------------------------------
def _bc(exposed_walls: int, wall_idx: int) -> tuple[str, str, str]:
    """Return (boundary, sun, wind) for wall_idx given exposed_walls count."""
    if wall_idx < exposed_walls:
        return "Outdoors", "SunExposed", "WindExposed"
    return "Adiabatic", "NoSun", "NoWind"

def build_idf(run_id: str, floor_area: float, wall_u: float, ach: float,
              wwr: float, floors: int, exposed_walls: int, north_axis: float,
              occupants: float, lights_w: float, equip_w: float) -> str:
    footprint = floor_area / floors
    side = math.sqrt(footprint)
    total_height = floors * HEIGHT_PER_FLOOR
    zone_vol = footprint * HEIGHT_PER_FLOOR

    wall_area_total = side * total_height * exposed_walls
    window_area     = wall_area_total * wwr
    opaque_wall     = wall_area_total - window_area

    win_side = math.sqrt(window_area)
    win_side = min(win_side, side * 0.8, total_height * 0.8)
    w_x_min  = (side - win_side) / 2
    w_x_max  = w_x_min + win_side
    w_z_min  = (total_height - win_side) / 2
    w_z_max  = w_z_min + win_side

    r_wall   = 1.0 / wall_u

    with open(TEMPLATE_FILE, "r") as f:
        idf = f.read()

    idf = idf.replace("@@ARCHETYPE_NAME@@", run_id)
    idf = idf.replace("@@NORTH_AXIS@@",     f"{north_axis:.1f}")
    idf = idf.replace("@@PEOPLE_COUNT@@",   f"{occupants:.2f}")
    idf = idf.replace("@@LIGHTING_W@@",     f"{lights_w:.2f}")
    idf = idf.replace("@@EQUIPMENT_W@@",    f"{equip_w:.2f}")
    
    idf = idf.replace("@@WALL_R_VALUE@@",   f"{r_wall:.4f}")
    idf = idf.replace("@@ROOF_R_VALUE@@",   "1.0000")
    idf = idf.replace("@@FLOOR_R_VALUE@@",  "0.8333")
    idf = idf.replace("@@WINDOW_U_VALUE@@", f"{2.0:.2f}")
    idf = idf.replace("@@ZONE_VOLUME@@",    f"{zone_vol:.2f}")
    idf = idf.replace("@@SIDE_LENGTH@@",    f"{side:.2f}")
    idf = idf.replace("@@TOTAL_HEIGHT@@",   f"{total_height:.2f}")
    idf = idf.replace("@@W_X_MIN@@",        f"{w_x_min:.2f}")
    idf = idf.replace("@@W_X_MAX@@",        f"{w_x_max:.2f}")
    idf = idf.replace("@@W_Z_MIN@@",        f"{w_z_min:.2f}")
    idf = idf.replace("@@W_Z_MAX@@",        f"{w_z_max:.2f}")

    bc_e, sun_e, wind_e = _bc(exposed_walls, 1)
    bc_n, sun_n, wind_n = _bc(exposed_walls, 2)
    bc_w, sun_w, wind_w = _bc(exposed_walls, 3)
    idf = idf.replace("@@BC_EAST@@",   bc_e).replace("@@SUN_EAST@@",  sun_e).replace("@@WIND_EAST@@",  wind_e)
    idf = idf.replace("@@BC_NORTH@@",  bc_n).replace("@@SUN_NORTH@@", sun_n).replace("@@WIND_NORTH@@", wind_n)
    idf = idf.replace("@@BC_WEST@@",   bc_w).replace("@@SUN_WEST@@",  sun_w).replace("@@WIND_WEST@@",  wind_w)
    return idf

# ---------------------------------------------------------------------------
# Energy Parsing
# ---------------------------------------------------------------------------
def _parse_heating_kwh(out_dir: Path) -> float:
    html_path = out_dir / "eplustbl.htm"
    if not html_path.exists():
        raise RuntimeError(f"FATAL: EnergyPlus failed! No output HTML found in {out_dir}")
    with open(html_path, "r", errors="ignore") as f:
        content = f.read()
    match = re.search(r"End Uses.*?<table.*?>(.*?)</table>", content, re.DOTALL | re.IGNORECASE)
    if match:
        heating_row = re.search(r"<tr>\s*<td[^>]*>\s*Heating\s*</td>(.*?)</tr>", match.group(1), re.DOTALL | re.IGNORECASE)
        if heating_row:
            cols = re.findall(r"<td[^>]*>(.*?)</td>", heating_row.group(1), re.DOTALL)
            total_gj = 0.0
            for c in cols:
                try: 
                    total_gj += float(c.strip())
                except ValueError as e: 
                    logger.debug(f"Skipping non-numeric column value in heating row: {c}")
            return total_gj * 277.778 # Convert GJ to kWh
        else:
            raise RuntimeError(f"Could not find Heating row in eplustbl.htm for {out_dir}")
    else:
        raise RuntimeError(f"Could not find End Uses table in eplustbl.htm for {out_dir}")

# ---------------------------------------------------------------------------
# Single EnergyPlus run
# ---------------------------------------------------------------------------
def run_single(args: dict) -> dict:
    run_id   = args["run_id"]
    out_dir  = SIM_DIR / run_id
    
    result_file = out_dir / "result.json"
    if args.get("resume", False) and result_file.exists():
        with open(result_file) as f:
            return json.load(f)

    # Calculate SAP 2012 Occupancy based on Floor Area
    A = args["floor_area"]
    if A > 13.9:
        occupants = 1 + 1.76 * (1 - math.exp(-0.000349 * (A - 13.9)**2)) + 0.0013 * (A - 13.9)
    else:
        occupants = 1.0
        
    lights_w = A * 2.0  # nominal
    equip_w = A * 3.0   # nominal

    city = args.get("city", "Manchester")
    weather_file = PHYSICS_DIR / f"{city}_2030_ColdSnap.epw"

    t_h_runs = []
    for axis in [0, 90, 180, 270]:
        run_axis_id = f"{run_id}_axis{axis}"
        axis_dir = out_dir / run_axis_id
        axis_dir.mkdir(parents=True, exist_ok=True)
        idf_path = axis_dir / f"{run_axis_id}.idf"
        
        idf_str = build_idf(
            run_id=run_axis_id,
            floor_area=args["floor_area"],
            wall_u=args["wall_u"],
            ach=args["ach"],
            wwr=args["wwr"],
            floors=args["floors"],
            exposed_walls=args["exposed_walls"],
            north_axis=axis,
            occupants=occupants,
            lights_w=lights_w,
            equip_w=equip_w
        )
        with open(idf_path, "w") as f:
            f.write(idf_str)

        try:
            proc = subprocess.run(
                [str(EP_EXE), "-w", str(weather_file), "-d", str(axis_dir), str(idf_path)],
                capture_output=True, timeout=120
            )
            t_h_runs.append(_parse_heating_kwh(axis_dir))
        except Exception as e:
            logger.warning(f"FAILED {run_axis_id}: {e}")

    # Average the 4 orientations
    T_h = sum(t_h_runs) / max(1, len(t_h_runs)) if t_h_runs else 0.0

    result = {**args, "T_h": T_h, "status": "ok" if t_h_runs else "error"}
    with open(result_file, "w") as f:
        json.dump(result, f)

    return result

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_lhs_batch(max_workers: int = 6, check_completeness: bool = False, resume: bool = False):
    design_files = sorted(LHS_DIR.glob("lhs_*.csv"))
    if not design_files:
        logger.error(f"No LHS design files found in {LHS_DIR}. Run 00a_lhs_sampler.py first.")
        return

    if not EP_EXE.exists():
        logger.error(f"EnergyPlus executable not found at {EP_EXE}")
        return
        
    # Failsafe: Check for placeholder weather files (all exactly 1,546,562 bytes)
    placeholder_found = False
    for wf in PHYSICS_DIR.glob("*.epw"):
        if wf.stat().st_size == 1546562:
            placeholder_found = True
            break
            
    if placeholder_found:
        logger.error("ERROR: Placeholder weather files (1,546,562 bytes) detected in data/raw/physics/! You must download real .epw files before running simulations.")
        # We don't halt here if they really want to proceed, but it's a huge warning.

    logger.info(f"Found {len(design_files)} archetype design files.")

    all_tasks = []
    for design_file in design_files:
        df = pd.read_csv(design_file)
        for _, row in df.iterrows():
            slug = (str(row["archetype"])
                    .replace(" ", "_")
                    .replace("/", "-")
                    .replace("+", "plus"))
            run_id = f"{slug}_s{int(row['sample_id']):04d}"
            task = {
                "run_id":        run_id,
                "archetype":     row["archetype"],
                "property_type": row["property_type"],
                "age_band":      row["age_band"],
                "floor_area":    float(row["floor_area"]),
                "wall_u":        float(row["wall_u"]),
                "ach":           float(row["ach"]),
                "wwr":           float(row["wwr"]),
                "form_code":     int(row["form_code"]),
                "floors":        int(row["floors"]),
                "exposed_walls": int(row["exposed_walls"]),
                "sample_id":     int(row["sample_id"]),
                "resume":        resume,
            }
            # Append city and hdd if defined in LHS
            if "city" in row:
                task["city"] = row["city"]
            if "hdd" in row:
                task["hdd"] = float(row["hdd"])
            all_tasks.append(task)

    logger.info(f"Total runs: {len(all_tasks)}")

    if check_completeness:
        done  = sum(1 for t in all_tasks if (SIM_DIR / t["run_id"] / "result.json").exists())
        total = len(all_tasks)
        logger.info(f"Completeness: {done}/{total} ({100*done/total:.1f}%)")
        return

    results = []
    completed = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_single, task): task for task in all_tasks}
        
        # Wrap as_completed with tqdm for a nice loading bar
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(all_tasks), desc="Simulating"):
            try:
                results.append(future.result())
            except Exception as e:
                task = futures[future]
                logger.warning(f"Worker exception for {task['run_id']}: {e}")
            completed += 1

    df_all = pd.DataFrame(results)
    combined_path = PHYSICS_DIR / "lhs_results_combined.csv"
    df_all.to_csv(combined_path, index=False)
    logger.info(f"Saved combined results → {combined_path}")

    for arch, grp in df_all.groupby("archetype"):
        slug = arch.replace(" ", "_").replace("/", "-").replace("+", "plus")
        out_path = RESULTS_DIR / f"lhs_results_{slug}.csv"
        grp.to_csv(out_path, index=False)

    ok_count = (df_all["status"] == "ok").sum()
    logger.info(f"Done. {ok_count}/{len(df_all)} runs succeeded.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers",             type=int, default=6,
                        help="Number of parallel EnergyPlus workers (default 6)")
    parser.add_argument("--check-completeness",  action="store_true",
                        help="Report completion status without running new simulations.")
    parser.add_argument("--resume",              action="store_true",
                        help="Skip simulations if result.json already exists.")
    args = parser.parse_args()
    run_lhs_batch(max_workers=args.workers, check_completeness=args.check_completeness, resume=args.resume)
