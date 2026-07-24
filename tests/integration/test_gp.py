"""
10d_integration_test.py
========================
Regression test: verifies that the GP emulator at archetype-nominal input values
recovers the Table 1 HLC values within ±10% (loose) and ±5% (strict).

Also verifies that the GP model file exists and is loadable.

Exit code 0 = all tests passed. Non-zero = failures detected.

INTENTIONALLY NOT PYTEST-DISCOVERABLE, and not run in CI. Unlike the rest of
tests/integration/, this checks the real, production-scale gp_emulator.pkl
(data/processed/, not tests/fixtures/) against the full physics archetype
baseline — artifacts CI never produces (CI only exercises the tiny TEST_MODE
fixture pipeline). Wrapping this in pytest test_* functions would only ever
skip in CI, giving a false impression of coverage; run it manually instead,
after a real (non-TEST_MODE) population synthesis + GP training run.

Usage:
  python tests/integration/test_gp.py            # strict (±5%)
  python tests/integration/test_gp.py --loose    # loose (±10%)
"""

import numpy as np
import pandas as pd
import joblib
import json
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("IntegrationTest")

BASE_DIR      = Path(__file__).resolve().parent.parent
PHYSICS_DIR   = BASE_DIR / "data" / "raw" / "physics"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

MODEL_PATH    = PROCESSED_DIR / "gp_emulator.pkl"
BASELINE_CSV  = PHYSICS_DIR / "physics_archetypes_baseline.csv"
STATS_PATH    = PROCESSED_DIR / "gp_validation_stats.json"

FORM_CODE = {"Flat": 0, "Bungalow": 1, "Maisonette": 2, "House": 3}
CONSTRUCTION_SPECS = {
    "Pre-1900":  {"wall": 2.1,  "ach": 1.5, "wwr": 0.15},
    "1900-1929": {"wall": 2.1,  "ach": 1.5, "wwr": 0.15},
    "1930-1949": {"wall": 1.7,  "ach": 1.2, "wwr": 0.15},
    "1950-1966": {"wall": 1.5,  "ach": 1.0, "wwr": 0.15},
    "1967-1982": {"wall": 1.0,  "ach": 0.8, "wwr": 0.15},
    "1983-1995": {"wall": 0.6,  "ach": 0.6, "wwr": 0.15},
    "1996-2006": {"wall": 0.45, "ach": 0.5, "wwr": 0.15},
    "2007+":     {"wall": 0.3,  "ach": 0.5, "wwr": 0.15},
}
# WWR override for Flat (more glass)
WWR_OVERRIDE = {"Flat": 0.20}


def run_tests(tolerance: float = 0.05) -> bool:
    """
    Returns True if all checks pass.
    tolerance: fractional tolerance (0.05 = ±5%)
    """
    all_pass = True

    # -------------------------------------------------------------------------
    # Test 1: Model file exists and loads cleanly
    # -------------------------------------------------------------------------
    logger.info("Test 1: Model file integrity")
    if not MODEL_PATH.exists():
        logger.error(f"FAIL | gp_emulator.pkl not found at {MODEL_PATH}")
        return False

    try:
        payload = joblib.load(MODEL_PATH)
        gp      = payload["gp"]
        scaler  = payload["scaler"]
        features = payload["features"]
        logger.info(f"PASS | Model loaded. Features: {features}")
    except Exception as e:
        logger.error(f"FAIL | Model load error: {e}")
        return False

    # -------------------------------------------------------------------------
    # Test 2: Validation R² gate
    # -------------------------------------------------------------------------
    logger.info("Test 2: Training R² gate (≥ 0.99)")
    if STATS_PATH.exists():
        with open(STATS_PATH) as f:
            stats = json.load(f)
        r2 = stats.get("r2", 0)
        if r2 >= 0.99:
            logger.info(f"PASS | R² = {r2:.4f}")
        else:
            logger.warning(f"FAIL | R² = {r2:.4f} < 0.99")
            all_pass = False
    else:
        logger.warning("SKIP | gp_validation_stats.json not found — skipping R² gate")

    # -------------------------------------------------------------------------
    # Test 3: Archetype-nominal recovery
    # -------------------------------------------------------------------------
    logger.info(f"Test 3: Archetype-nominal T_h recovery (tolerance ±{tolerance*100:.0f}%)")
    baseline = pd.read_csv(BASELINE_CSV)
    baseline.columns = [c.strip() for c in baseline.columns]

    # Identify column names defensively
    type_col  = next(c for c in baseline.columns if "type"  in c.lower() and "property" in c.lower())
    age_col   = next(c for c in baseline.columns if "age"   in c.lower() and "property" in c.lower())
    area_col  = next(c for c in baseline.columns if "area"  in c.lower() and "mean"     in c.lower())
    arch_col  = next((c for c in baseline.columns if c.lower() == "archetype"), baseline.columns[0])
    th_col    = next(c for c in baseline.columns if "theoretical" in c.lower() and "gas" in c.lower())

    failures = []
    for _, row in baseline.iterrows():
        ptype = str(row[type_col]).strip()
        age   = str(row[age_col]).strip()
        area  = float(row[area_col])
        arch  = str(row[arch_col]).strip()
        T_ref = float(row[th_col])   # Table 1 value

        specs = CONSTRUCTION_SPECS.get(age)
        if specs is None or ptype not in FORM_CODE:
            logger.warning(f"SKIP | Unknown archetype: {arch} ({age}, {ptype})")
            continue

        wwr = WWR_OVERRIDE.get(ptype, specs["wwr"])
        # Append 1760.2 (Manchester HDD) as the 6th feature
        X_nominal = np.array([[area, specs["wall"], specs["ach"], wwr, FORM_CODE[ptype], 1760.2]])
        
        # -------------------------------------------------------------
        # SHAPE ASSERTIONS
        # -------------------------------------------------------------
        assert X_nominal.shape[1] == len(features), f"FATAL: Feature dimension mismatch! Expected {len(features)}, got {X_nominal.shape[1]}"
        
        X_s = scaler.transform(X_nominal)
        T_pred = gp.predict(X_s)[0]

        pct_err = abs(T_pred - T_ref) / T_ref
        status  = "PASS" if pct_err <= tolerance else "FAIL"
        if status == "FAIL":
            all_pass = False
            failures.append((arch, T_ref, T_pred, pct_err))
        logger.info(f"{status} | {arch:<35} | Table1={T_ref:,.0f}  GP={T_pred:,.0f}  err={pct_err*100:.1f}%")

    if failures:
        logger.warning(f"\n{len(failures)} archetypes exceeded ±{tolerance*100:.0f}% tolerance:")
        for arch, ref, pred, err in failures:
            logger.warning(f"  {arch}: {ref:,.0f} → {pred:,.0f}  ({err*100:.1f}%)")
    else:
        logger.info(f"All {len(baseline)} archetypes within ±{tolerance*100:.0f}% tolerance.")

    # -------------------------------------------------------------------------
    # Test 4: Monotonicity check (higher wall_u → higher T_h)
    # -------------------------------------------------------------------------
    logger.info("Test 4: Monotonicity — higher wall U-value → higher predicted T_h")
    u_lo = np.array([[80.0, 0.3,  0.5, 0.15, 3, 1760.2]])
    u_hi = np.array([[80.0, 2.1,  0.5, 0.15, 3, 1760.2]])
    T_lo = gp.predict(scaler.transform(u_lo))[0]
    T_hi = gp.predict(scaler.transform(u_hi))[0]
    if T_hi > T_lo:
        logger.info(f"PASS | T(U=2.1)={T_hi:,.0f} > T(U=0.3)={T_lo:,.0f}")
    else:
        logger.warning(f"FAIL | Monotonicity violated: T(U=2.1)={T_hi:,.0f} ≤ T(U=0.3)={T_lo:,.0f}")
        all_pass = False

    # -------------------------------------------------------------------------
    # Test 5: Area scaling direction (larger area → larger T_h)
    # -------------------------------------------------------------------------
    logger.info("Test 5: Monotonicity — larger floor area → higher predicted T_h")
    a_sm = np.array([[50.0,  1.0, 0.8, 0.15, 3, 1760.2]])
    a_lg = np.array([[120.0, 1.0, 0.8, 0.15, 3, 1760.2]])
    T_sm = gp.predict(scaler.transform(a_sm))[0]
    T_lg = gp.predict(scaler.transform(a_lg))[0]
    if T_lg > T_sm:
        logger.info(f"PASS | T(120m²)={T_lg:,.0f} > T(50m²)={T_sm:,.0f}")
    else:
        logger.warning(f"FAIL | Area monotonicity violated: T(120m²)={T_lg:,.0f} ≤ T(50m²)={T_sm:,.0f}")
        all_pass = False

    return all_pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loose", action="store_true",
                        help="Use ±10%% tolerance instead of ±5%%")
    args = parser.parse_args()
    tolerance = 0.10 if args.loose else 0.05

    ok = run_tests(tolerance=tolerance)
    logger.info("\n" + ("=" * 50))
    logger.info("ALL INTEGRATION TESTS PASSED" if ok else "INTEGRATION TESTS FAILED")
    logger.info("=" * 50)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
